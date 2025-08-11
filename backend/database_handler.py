"""
Database Handler Module for MediScan
Handles data persistence and retrieval
"""

import json
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import logging
import uuid

logger = logging.getLogger(__name__)

class DatabaseHandler:
    """
    Handles database operations for MediScan
    Uses JSON files for simplicity, can be extended to use SQLite or other databases
    """
    
    def __init__(self, data_dir: str = "data"):
        """Initialize database handler"""
        self.data_dir = data_dir
        self.medicines_file = os.path.join(data_dir, "medicines.json")
        self.users_file = os.path.join(data_dir, "users.json")
        self.settings_file = os.path.join(data_dir, "settings.json")
        
        self._ensure_data_directory()
        self._initialize_files()
    
    def _ensure_data_directory(self):
        """Ensure data directory exists"""
        os.makedirs(self.data_dir, exist_ok=True)
    
    def _initialize_files(self):
        """Initialize data files if they don't exist"""
        files_to_init = [
            (self.medicines_file, []),
            (self.users_file, {}),
            (self.settings_file, self._get_default_settings())
        ]
        
        for file_path, default_data in files_to_init:
            if not os.path.exists(file_path):
                try:
                    with open(file_path, 'w') as f:
                        json.dump(default_data, f, indent=2)
                except Exception as e:
                    logger.error(f"Error creating {file_path}: {e}")
    
    def _get_default_settings(self) -> Dict:
        """Get default application settings"""
        return {
            "voice_enabled": True,
            "voice_language": "en-US",
            "voice_engine": "pyttsx3",
            "reminder_days_before_expiry": 7,
            "default_reminder_time": "09:00",
            "theme": "light",
            "auto_backup": True,
            "backup_frequency": "daily"
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
            # Add unique ID and timestamp if not present
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
            
            logger.info(f"{'Updated' if updated else 'Saved'} medicine: {medicine_data.get('name', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving medicine: {e}")
            return False
    
    def load_medicines(self) -> List[Dict]:
        """
        Load all medicines from database
        
        Returns:
            List of medicine dictionaries
        """
        try:
            if os.path.exists(self.medicines_file):
                with open(self.medicines_file, 'r') as f:
                    medicines = json.load(f)
                    
                # Add calculated fields
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
        medicines = self.load_medicines()
        query_lower = query.lower()
        
        matching_medicines = []
        for medicine in medicines:
            # Search in multiple fields
            search_fields = [
                medicine.get('name', ''),
                medicine.get('manufacturer', ''),
                medicine.get('batch_no', ''),
                medicine.get('dosage', ''),
                medicine.get('form', '')
            ]
            
            if any(query_lower in str(field).lower() for field in search_fields if field):
                matching_medicines.append(medicine)
        
        return matching_medicines
    
    def get_expiring_medicines(self, days_ahead: int = 7) -> List[Dict]:
        """
        Get medicines expiring within specified days
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of expiring medicine dictionaries
        """
        medicines = self.load_medicines()
        expiring_medicines = []
        
        for medicine in medicines:
            days_until_expiry = medicine.get('days_until_expiry')
            if days_until_expiry is not None and 0 <= days_until_expiry <= days_ahead:
                expiring_medicines.append(medicine)
        
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
    
    def save_user_data(self, user_id: str, user_data: Dict) -> bool:
        """
        Save user data
        
        Args:
            user_id: Unique user identifier
            user_data: User data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load existing users
            users = {}
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r') as f:
                    users = json.load(f)
            
            # Add timestamp
            user_data['updated_at'] = datetime.now().isoformat()
            
            # Save user data
            users[user_id] = user_data
            
            with open(self.users_file, 'w') as f:
                json.dump(users, f, indent=2, default=str)
            
            logger.info(f"Saved user data for: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving user data: {e}")
            return False
    
    def load_user_data(self, user_id: str) -> Optional[Dict]:
        """
        Load user data
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            User data dictionary or None if not found
        """
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r') as f:
                    users = json.load(f)
                    return users.get(user_id)
            return None
            
        except Exception as e:
            logger.error(f"Error loading user data: {e}")
            return None
    
    def save_settings(self, settings: Dict) -> bool:
        """
        Save application settings
        
        Args:
            settings: Settings dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            
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
            backup_path: Path for backup file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"backup/mediscan_backup_{timestamp}.json"
            
            # Ensure backup directory exists
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Collect all data
            backup_data = {
                'timestamp': datetime.now().isoformat(),
                'medicines': self.load_medicines(),
                'settings': self.load_settings(),
                'version': '1.0'
            }
            
            # Load users data
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
            
            # Restore medicines
            if 'medicines' in backup_data:
                with open(self.medicines_file, 'w') as f:
                    json.dump(backup_data['medicines'], f, indent=2, default=str)
            
            # Restore settings
            if 'settings' in backup_data:
                with open(self.settings_file, 'w') as f:
                    json.dump(backup_data['settings'], f, indent=2)
            
            # Restore users
            if 'users' in backup_data:
                with open(self.users_file, 'w') as f:
                    json.dump(backup_data['users'], f, indent=2, default=str)
            
            logger.info(f"Data restored from backup: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring data: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """
        Get database statistics
        
        Returns:
            Statistics dictionary
        """
        medicines = self.load_medicines()
        
        stats = {
            'total_medicines': len(medicines),
            'expired_medicines': len(self.get_expired_medicines()),
            'expiring_soon': len(self.get_expiring_medicines()),
            'by_form': {},
            'by_manufacturer': {},
            'scan_types': {'label': 0, 'prescription': 0}
        }
        
        # Count by form and manufacturer
        for medicine in medicines:
            form = medicine.get('form', 'Unknown')
            manufacturer = medicine.get('manufacturer', 'Unknown')
            scan_type = medicine.get('scan_type', 'Unknown')
            
            stats['by_form'][form] = stats['by_form'].get(form, 0) + 1
            stats['by_manufacturer'][manufacturer] = stats['by_manufacturer'].get(manufacturer, 0) + 1
            
            if scan_type in stats['scan_types']:
                stats['scan_types'][scan_type] += 1
        
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
            medicines = self.load_medicines()
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            original_count = len(medicines)
            
            # Filter out old medicines
            medicines = [
                m for m in medicines 
                if datetime.fromisoformat(m.get('created_at', datetime.now().isoformat())) >= cutoff_date
            ]
            
            removed_count = original_count - len(medicines)
            
            if removed_count > 0:
                with open(self.medicines_file, 'w') as f:
                    json.dump(medicines, f, indent=2, default=str)
                
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
                expiry_dt = datetime.strptime(expiry_date, '%Y-%m-%d')
                today = datetime.now()
                delta = expiry_dt - today
                medicine['days_until_expiry'] = delta.days
            except ValueError:
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