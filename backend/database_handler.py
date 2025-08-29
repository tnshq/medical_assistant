"""
Database Handler Module for MediScan
Handles data persistence and retrieval with enhanced functionality
"""

import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import uuid
import threading

logger = logging.getLogger(__name__)

class DatabaseHandler:
    """
    Handles database operations for MediScan
    Uses JSON files for simplicity with option to extend to SQLite
    """

    def __init__(self, data_dir: str = "data"):
        """Initialize database handler"""
        self.data_dir = data_dir
        self.medicines_file = os.path.join(data_dir, "medicines.json")
        self.users_file = os.path.join(data_dir, "users.json")
        self.settings_file = os.path.join(data_dir, "settings.json")
        self.scan_history_file = os.path.join(data_dir, "scan_history.json")

        self._lock = threading.Lock()

        self._ensure_data_directory()
        self._initialize_files()

    def _ensure_data_directory(self):
        """Ensure data directory exists"""
        os.makedirs(self.data_dir, exist_ok=True)
        logger.info(f"Data directory ensured: {self.data_dir}")

    def _initialize_files(self):
        """Initialize data files if they don't exist"""
        files_to_init = [
            (self.medicines_file, []),
            (self.users_file, {}),
            (self.settings_file, self._get_default_settings()),
            (self.scan_history_file, [])
        ]

        for file_path, default_data in files_to_init:
            if not os.path.exists(file_path):
                try:
                    with open(file_path, 'w') as f:
                        json.dump(default_data, f, indent=2)
                    logger.info(f"Initialized {file_path}")
                except Exception as e:
                    logger.error(f"Error creating {file_path}: {e}")

    def _get_default_settings(self) -> Dict:
        """Get default application settings"""
        return {
            "voice_enabled": True,
            "voice_language": "en-US",
            "voice_rate": 150,
            "voice_volume": 0.9,
            "reminder_days_before_expiry": 7,
            "default_reminder_time": "09:00",
            "theme": "light",
            "auto_backup": True,
            "backup_frequency": "daily",
            "ocr_engine": "google_vision",
            "app_version": "1.0.0",
            "last_updated": datetime.now().isoformat()
        }

    def save_medicine(self, medicine_data: Dict) -> bool:
        """
        Save medicine data to database

        Args:
            medicine_data: Dictionary containing medicine information

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._lock:
                # Add metadata if not present
                if 'id' not in medicine_data:
                    medicine_data['id'] = str(uuid.uuid4())

                if 'created_at' not in medicine_data:
                    medicine_data['created_at'] = datetime.now().isoformat()

                medicine_data['updated_at'] = datetime.now().isoformat()

                # Load existing medicines
                medicines = self.load_medicines()

                # Check if medicine already exists (update if found)
                updated = False
                for i, existing in enumerate(medicines):
                    if existing.get('id') == medicine_data.get('id'):
                        medicines[i] = medicine_data
                        updated = True
                        break

                # Add new medicine if not updated
                if not updated:
                    medicines.append(medicine_data)

                # Save back to file
                with open(self.medicines_file, 'w') as f:
                    json.dump(medicines, f, indent=2, default=str)

                action = 'Updated' if updated else 'Saved'
                logger.info(f"{action} medicine: {medicine_data.get('name', 'Unknown')}")
                return True

        except Exception as e:
            logger.error(f"Error saving medicine: {e}")
            return False

    def load_medicines(self) -> List[Dict]:
        """
        Load all medicines from database

        Returns:
            List of medicine dictionaries with calculated fields
        """
        try:
            if os.path.exists(self.medicines_file):
                with open(self.medicines_file, 'r') as f:
                    medicines = json.load(f)

                # Add calculated fields to each medicine
                for medicine in medicines:
                    self._add_calculated_fields(medicine)

                return medicines
            else:
                return []

        except Exception as e:
            logger.error(f"Error loading medicines: {e}")
            return []

    def get_medicine_by_id(self, medicine_id: str) -> Optional[Dict]:
        """
        Get a specific medicine by ID

        Args:
            medicine_id: Unique identifier for the medicine

        Returns:
            Medicine dictionary or None if not found
        """
        medicines = self.load_medicines()
        for medicine in medicines:
            if medicine.get('id') == medicine_id:
                return medicine
        return None

    def delete_medicine(self, medicine_id: str) -> bool:
        """
        Delete a medicine from database

        Args:
            medicine_id: Unique identifier for the medicine

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._lock:
                medicines = self.load_medicines()
                original_count = len(medicines)
                medicines = [m for m in medicines if m.get('id') != medicine_id]

                if len(medicines) < original_count:
                    with open(self.medicines_file, 'w') as f:
                        json.dump(medicines, f, indent=2, default=str)
                    logger.info(f"Deleted medicine with ID: {medicine_id}")
                    return True
                else:
                    logger.warning(f"Medicine with ID {medicine_id} not found")
                    return False

        except Exception as e:
            logger.error(f"Error deleting medicine: {e}")
            return False

    def search_medicines(self, query: str) -> List[Dict]:
        """
        Search medicines by name, manufacturer, or other fields

        Args:
            query: Search query string

        Returns:
            List of matching medicine dictionaries
        """
        if not query or not query.strip():
            return []

        medicines = self.load_medicines()
        query_lower = query.lower().strip()
        matching_medicines = []

        for medicine in medicines:
            # Search in multiple fields
            search_fields = [
                medicine.get('name', ''),
                medicine.get('manufacturer', ''),
                medicine.get('batch_no', ''),
                medicine.get('dosage', ''),
                medicine.get('form', ''),
                medicine.get('instructions', '')
            ]

            # Check if query matches any field
            if any(query_lower in str(field).lower() for field in search_fields if field):
                matching_medicines.append(medicine)

        return matching_medicines

    def get_expiring_medicines(self, days_ahead: int = 7) -> List[Dict]:
        """
        Get medicines expiring within specified days

        Args:
            days_ahead: Number of days to look ahead

        Returns:
            List of expiring medicine dictionaries sorted by expiry date
        """
        medicines = self.load_medicines()
        expiring_medicines = []

        for medicine in medicines:
            days_until_expiry = medicine.get('days_until_expiry')
            if days_until_expiry is not None and 0 <= days_until_expiry <= days_ahead:
                expiring_medicines.append(medicine)

        # Sort by days until expiry (most urgent first)
        return sorted(expiring_medicines, key=lambda x: x.get('days_until_expiry', float('inf')))

    def get_expired_medicines(self) -> List[Dict]:
        """
        Get all expired medicines

        Returns:
            List of expired medicine dictionaries
        """
        medicines = self.load_medicines()
        expired_medicines = []

        for medicine in medicines:
            days_until_expiry = medicine.get('days_until_expiry')
            if days_until_expiry is not None and days_until_expiry < 0:
                expired_medicines.append(medicine)

        return expired_medicines

    def get_medicines_by_form(self, form: str) -> List[Dict]:
        """
        Get medicines by form (tablet, capsule, etc.)

        Args:
            form: Medicine form to filter by

        Returns:
            List of medicine dictionaries
        """
        medicines = self.load_medicines()
        return [m for m in medicines if m.get('form', '').lower() == form.lower()]

    def get_medicines_by_manufacturer(self, manufacturer: str) -> List[Dict]:
        """
        Get medicines by manufacturer

        Args:
            manufacturer: Manufacturer name to filter by

        Returns:
            List of medicine dictionaries
        """
        medicines = self.load_medicines()
        return [m for m in medicines if manufacturer.lower() in m.get('manufacturer', '').lower()]

    def save_scan_history(self, scan_data: Dict) -> bool:
        """
        Save scan history entry

        Args:
            scan_data: Dictionary containing scan information

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._lock:
                # Add metadata
                scan_entry = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.now().isoformat(),
                    'scan_type': scan_data.get('scan_type', 'unknown'),
                    'success': scan_data.get('success', False),
                    'medicines_found': scan_data.get('medicines_found', 0),
                    'confidence': scan_data.get('confidence', 0.0),
                    'ocr_engine': scan_data.get('ocr_engine', 'unknown'),
                    'processing_time': scan_data.get('processing_time', 0.0),
                    'error': scan_data.get('error', None)
                }

                # Load existing history
                history = []
                if os.path.exists(self.scan_history_file):
                    with open(self.scan_history_file, 'r') as f:
                        history = json.load(f)

                history.append(scan_entry)

                # Keep only last 500 entries
                if len(history) > 500:
                    history = history[-500:]

                # Save history
                with open(self.scan_history_file, 'w') as f:
                    json.dump(history, f, indent=2, default=str)

                return True

        except Exception as e:
            logger.error(f"Error saving scan history: {e}")
            return False

    def get_scan_history(self, days: int = 30) -> List[Dict]:
        """
        Get scan history for specified days

        Args:
            days: Number of days to retrieve

        Returns:
            List of scan history entries
        """
        try:
            if not os.path.exists(self.scan_history_file):
                return []

            with open(self.scan_history_file, 'r') as f:
                history = json.load(f)

            # Filter by date if specified
            if days > 0:
                cutoff_date = datetime.now() - timedelta(days=days)
                history = [
                    entry for entry in history
                    if datetime.fromisoformat(entry['timestamp']) >= cutoff_date
                ]

            return sorted(history, key=lambda x: x['timestamp'], reverse=True)

        except Exception as e:
            logger.error(f"Error getting scan history: {e}")
            return []

    def save_settings(self, settings: Dict) -> bool:
        """
        Save application settings

        Args:
            settings: Settings dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._lock:
                # Load current settings
                current_settings = self.load_settings()

                # Update with new settings
                current_settings.update(settings)
                current_settings['last_updated'] = datetime.now().isoformat()

                # Save settings
                with open(self.settings_file, 'w') as f:
                    json.dump(current_settings, f, indent=2)

                logger.info("Settings saved successfully")
                return True

        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return False

    def load_settings(self) -> Dict:
        """
        Load application settings

        Returns:
            Settings dictionary
        """
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            else:
                return self._get_default_settings()

        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            return self._get_default_settings()

    def backup_data(self, backup_path: str = None) -> bool:
        """
        Create backup of all data

        Args:
            backup_path: Path for backup file (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = os.path.join(self.data_dir, "backups")
                os.makedirs(backup_dir, exist_ok=True)
                backup_path = os.path.join(backup_dir, f"mediscan_backup_{timestamp}.json")

            # Collect all data
            backup_data = {
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0',
                'medicines': self.load_medicines(),
                'settings': self.load_settings(),
                'scan_history': self.get_scan_history(days=0)  # All history
            }

            # Load users data if exists
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r') as f:
                    backup_data['users'] = json.load(f)

            # Save backup
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)

            logger.info(f"Backup created: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False

    def restore_data(self, backup_path: str) -> bool:
        """
        Restore data from backup

        Args:
            backup_path: Path to backup file

        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(backup_path):
                logger.error(f"Backup file not found: {backup_path}")
                return False

            with open(backup_path, 'r') as f:
                backup_data = json.load(f)

            with self._lock:
                # Restore medicines
                if 'medicines' in backup_data:
                    with open(self.medicines_file, 'w') as f:
                        json.dump(backup_data['medicines'], f, indent=2, default=str)

                # Restore settings
                if 'settings' in backup_data:
                    with open(self.settings_file, 'w') as f:
                        json.dump(backup_data['settings'], f, indent=2)

                # Restore scan history
                if 'scan_history' in backup_data:
                    with open(self.scan_history_file, 'w') as f:
                        json.dump(backup_data['scan_history'], f, indent=2, default=str)

                # Restore users
                if 'users' in backup_data:
                    with open(self.users_file, 'w') as f:
                        json.dump(backup_data['users'], f, indent=2, default=str)

            logger.info(f"Data restored from backup: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Error restoring data: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics

        Returns:
            Statistics dictionary
        """
        medicines = self.load_medicines()
        scan_history = self.get_scan_history(days=30)

        stats = {
            'total_medicines': len(medicines),
            'expired_medicines': len(self.get_expired_medicines()),
            'expiring_soon': len(self.get_expiring_medicines()),
            'scans_last_30_days': len(scan_history),
            'successful_scans': len([s for s in scan_history if s.get('success', False)]),
            'by_form': {},
            'by_manufacturer': {},
            'by_scan_type': {}
        }

        # Count by form and manufacturer
        for medicine in medicines:
            form = medicine.get('form', 'Unknown')
            manufacturer = medicine.get('manufacturer', 'Unknown')
            scan_type = medicine.get('scan_type', 'Unknown')

            stats['by_form'][form] = stats['by_form'].get(form, 0) + 1
            stats['by_manufacturer'][manufacturer] = stats['by_manufacturer'].get(manufacturer, 0) + 1
            stats['by_scan_type'][scan_type] = stats['by_scan_type'].get(scan_type, 0) + 1

        return stats

    def cleanup_old_data(self, days_old: int = 365) -> int:
        """
        Clean up old data

        Args:
            days_old: Remove data older than this many days

        Returns:
            Number of records removed
        """
        try:
            with self._lock:
                removed_count = 0
                cutoff_date = datetime.now() - timedelta(days=days_old)

                # Clean medicines
                medicines = self.load_medicines()
                original_count = len(medicines)

                medicines = [
                    m for m in medicines
                    if datetime.fromisoformat(m.get('created_at', datetime.now().isoformat())) >= cutoff_date
                ]

                if len(medicines) < original_count:
                    with open(self.medicines_file, 'w') as f:
                        json.dump(medicines, f, indent=2, default=str)
                    removed_count += original_count - len(medicines)

                # Clean scan history
                scan_history = self.get_scan_history(days=0)
                original_history_count = len(scan_history)

                scan_history = [
                    entry for entry in scan_history
                    if datetime.fromisoformat(entry['timestamp']) >= cutoff_date
                ]

                if len(scan_history) < original_history_count:
                    with open(self.scan_history_file, 'w') as f:
                        json.dump(scan_history, f, indent=2, default=str)
                    removed_count += original_history_count - len(scan_history)

                if removed_count > 0:
                    logger.info(f"Cleaned up {removed_count} old records")

                return removed_count

        except Exception as e:
            logger.error(f"Error cleaning up data: {e}")
            return 0

    def _add_calculated_fields(self, medicine: Dict):
        """Add calculated fields to medicine data"""
        # Calculate days until expiry
        expiry_date = medicine.get('expiry_date')
        if expiry_date:
            try:
                # Try different date formats
                for date_format in ['%Y-%m-%d', '%m/%Y', '%m-%Y', '%d/%m/%Y']:
                    try:
                        expiry_dt = datetime.strptime(expiry_date, date_format)
                        today = datetime.now()
                        delta = expiry_dt - today
                        medicine['days_until_expiry'] = delta.days
                        break
                    except ValueError:
                        continue
                else:
                    medicine['days_until_expiry'] = None
            except Exception:
                medicine['days_until_expiry'] = None
        else:
            medicine['days_until_expiry'] = None

        # Add expiry status
        days_until_expiry = medicine.get('days_until_expiry')
        if days_until_expiry is not None:
            if days_until_expiry < 0:
                medicine['expiry_status'] = 'expired'
            elif days_until_expiry <= 7:
                medicine['expiry_status'] = 'expiring_soon'
            elif days_until_expiry <= 30:
                medicine['expiry_status'] = 'expiring_this_month'
            else:
                medicine['expiry_status'] = 'safe'
        else:
            medicine['expiry_status'] = 'unknown'

        # Add age of medicine record
        created_at = medicine.get('created_at')
        if created_at:
            try:
                created_dt = datetime.fromisoformat(created_at)
                age_days = (datetime.now() - created_dt).days
                medicine['record_age_days'] = age_days
            except ValueError:
                medicine['record_age_days'] = None
        else:
            medicine['record_age_days'] = None

    def get_all_medicines(self) -> List[Dict]:
        """Get all medicines (alias for load_medicines for compatibility)"""
        return self.load_medicines()
