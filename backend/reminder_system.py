"""
Reminder System Module for MediScan
Handles medicine reminders and notifications with enhanced features
"""

import json
import os
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple
import logging
import uuid
import threading
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class Reminder:
    """Data class for reminder information"""
    id: str
    medicine_id: str
    medicine_name: str
    dosage: str
    frequency: str
    times: List[str]
    start_date: str
    duration_days: int
    instructions: str
    active: bool
    created_at: str
    last_taken: Optional[str] = None
    missed_count: int = 0
    taken_count: int = 0
    next_reminder: Optional[str] = None

class ReminderSystem:
    """
    Enhanced reminder system for medicine management
    """

    def __init__(self, data_dir: str = "data"):
        """Initialize the reminder system"""
        self.data_dir = data_dir
        self.reminders_file = os.path.join(data_dir, "reminders.json")
        self.history_file = os.path.join(data_dir, "reminder_history.json")

        self.reminders: List[Dict] = []
        self.reminder_history: List[Dict] = []
        self._lock = threading.Lock()

        self._ensure_data_directory()
        self._load_data()

    def _ensure_data_directory(self):
        """Ensure data directory exists"""
        os.makedirs(self.data_dir, exist_ok=True)

    def _load_data(self):
        """Load reminders and history from files"""
        try:
            # Load reminders
            if os.path.exists(self.reminders_file):
                with open(self.reminders_file, 'r') as f:
                    self.reminders = json.load(f)

            # Load history
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    self.reminder_history = json.load(f)

            logger.info(f"Loaded {len(self.reminders)} reminders and {len(self.reminder_history)} history entries")

        except Exception as e:
            logger.error(f"Error loading reminder data: {e}")
            self.reminders = []
            self.reminder_history = []

    def _save_data(self):
        """Save reminders and history to files"""
        try:
            with self._lock:
                # Save reminders
                with open(self.reminders_file, 'w') as f:
                    json.dump(self.reminders, f, indent=2, default=str)

                # Save history
                with open(self.history_file, 'w') as f:
                    json.dump(self.reminder_history, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error saving reminder data: {e}")

    def create_reminder(self, reminder_data: Dict) -> bool:
        """
        Create a new reminder

        Args:
            reminder_data: Dictionary containing reminder information

        Returns:
            True if created successfully, False otherwise
        """
        try:
            # Ensure required fields
            required_fields = ['medicine_name', 'dosage', 'frequency', 'times']
            for field in required_fields:
                if field not in reminder_data:
                    logger.error(f"Missing required field: {field}")
                    return False

            # Create reminder with defaults
            reminder = {
                'id': str(uuid.uuid4()),
                'medicine_id': reminder_data.get('medicine_id', str(uuid.uuid4())),
                'medicine_name': reminder_data['medicine_name'],
                'dosage': reminder_data['dosage'],
                'frequency': reminder_data['frequency'],
                'times': reminder_data['times'],
                'start_date': reminder_data.get('start_date', datetime.now().date().isoformat()),
                'duration_days': reminder_data.get('duration_days', 30),
                'instructions': reminder_data.get('instructions', ''),
                'active': reminder_data.get('active', True),
                'created_at': reminder_data.get('created_at', datetime.now().isoformat()),
                'last_taken': None,
                'missed_count': 0,
                'taken_count': 0
            }

            # Calculate next reminder
            reminder['next_reminder'] = self._calculate_next_reminder_time(reminder)

            with self._lock:
                self.reminders.append(reminder)
                self._save_data()

            logger.info(f"Created reminder for {reminder['medicine_name']}")
            return True

        except Exception as e:
            logger.error(f"Error creating reminder: {e}")
            return False

    def _calculate_next_reminder_time(self, reminder: Dict) -> str:
        """Calculate the next reminder time"""
        try:
            now = datetime.now()
            today = now.date()
            times = reminder.get('times', [])

            if not times:
                return (now + timedelta(days=1)).isoformat()

            # Find next time today or tomorrow
            next_datetime = None

            for time_str in sorted(times):
                try:
                    time_obj = datetime.strptime(time_str, '%H:%M').time()
                    candidate = datetime.combine(today, time_obj)

                    if candidate > now:
                        next_datetime = candidate
                        break
                except ValueError:
                    continue

            # If no time found today, use first time tomorrow
            if not next_datetime and times:
                try:
                    time_obj = datetime.strptime(sorted(times)[0], '%H:%M').time()
                    next_datetime = datetime.combine(today + timedelta(days=1), time_obj)
                except ValueError:
                    next_datetime = now + timedelta(days=1)

            return next_datetime.isoformat() if next_datetime else (now + timedelta(days=1)).isoformat()

        except Exception as e:
            logger.error(f"Error calculating next reminder time: {e}")
            return (datetime.now() + timedelta(days=1)).isoformat()

    def get_active_reminders(self) -> List[Dict]:
        """Get all active reminders"""
        return [r for r in self.reminders if r.get('active', False)]

    def get_todays_reminders(self) -> List[Dict]:
        """Get reminders scheduled for today"""
        today = datetime.now().date()
        todays_reminders = []

        for reminder in self.get_active_reminders():
            try:
                start_date = datetime.fromisoformat(reminder['start_date']).date()
                duration_days = reminder.get('duration_days', 30)
                end_date = start_date + timedelta(days=duration_days)

                # Check if reminder is active for today
                if start_date <= today <= end_date:
                    todays_reminders.append(reminder)

            except (ValueError, KeyError):
                continue

        return todays_reminders

    def get_due_reminders(self, tolerance_minutes: int = 15) -> List[Dict]:
        """
        Get reminders that are due within tolerance window

        Args:
            tolerance_minutes: Minutes of tolerance for due reminders

        Returns:
            List of due reminders
        """
        now = datetime.now()
        due_reminders = []

        for reminder in self.get_active_reminders():
            try:
                next_time_str = reminder.get('next_reminder')
                if not next_time_str:
                    continue

                next_time = datetime.fromisoformat(next_time_str)
                time_diff_minutes = (next_time - now).total_seconds() / 60

                # Check if reminder is due (within tolerance)
                if -tolerance_minutes <= time_diff_minutes <= tolerance_minutes:
                    due_reminders.append(reminder)

            except (ValueError, KeyError) as e:
                logger.error(f"Error processing reminder {reminder.get('id', 'unknown')}: {e}")

        return due_reminders

    def mark_taken(self, reminder_id: str, taken_time: str = None) -> bool:
        """
        Mark a reminder as taken

        Args:
            reminder_id: ID of the reminder
            taken_time: Time when taken (ISO format, defaults to now)

        Returns:
            True if marked successfully
        """
        if taken_time is None:
            taken_time = datetime.now().isoformat()

        try:
            with self._lock:
                for reminder in self.reminders:
                    if reminder['id'] == reminder_id:
                        reminder['last_taken'] = taken_time
                        reminder['taken_count'] = reminder.get('taken_count', 0) + 1

                        # Calculate next reminder time
                        reminder['next_reminder'] = self._calculate_next_reminder_time(reminder)

                        # Add to history
                        self._add_to_history(reminder_id, 'taken', taken_time)

                        self._save_data()
                        logger.info(f"Marked reminder {reminder_id} as taken")
                        return True

                logger.warning(f"Reminder {reminder_id} not found")
                return False

        except Exception as e:
            logger.error(f"Error marking reminder as taken: {e}")
            return False

    def mark_missed(self, reminder_id: str, missed_time: str = None) -> bool:
        """
        Mark a reminder as missed

        Args:
            reminder_id: ID of the reminder
            missed_time: Time when missed (ISO format, defaults to now)

        Returns:
            True if marked successfully
        """
        if missed_time is None:
            missed_time = datetime.now().isoformat()

        try:
            with self._lock:
                for reminder in self.reminders:
                    if reminder['id'] == reminder_id:
                        reminder['missed_count'] = reminder.get('missed_count', 0) + 1

                        # Calculate next reminder time
                        reminder['next_reminder'] = self._calculate_next_reminder_time(reminder)

                        # Add to history
                        self._add_to_history(reminder_id, 'missed', missed_time)

                        self._save_data()
                        logger.info(f"Marked reminder {reminder_id} as missed")
                        return True

                logger.warning(f"Reminder {reminder_id} not found")
                return False

        except Exception as e:
            logger.error(f"Error marking reminder as missed: {e}")
            return False

    def disable_reminder(self, reminder_id: str) -> bool:
        """Disable a reminder"""
        try:
            with self._lock:
                for reminder in self.reminders:
                    if reminder['id'] == reminder_id:
                        reminder['active'] = False
                        self._save_data()
                        logger.info(f"Disabled reminder {reminder_id}")
                        return True

                return False

        except Exception as e:
            logger.error(f"Error disabling reminder: {e}")
            return False

    def delete_reminder(self, reminder_id: str) -> bool:
        """Delete a reminder"""
        try:
            with self._lock:
                original_count = len(self.reminders)
                self.reminders = [r for r in self.reminders if r['id'] != reminder_id]

                if len(self.reminders) < original_count:
                    self._save_data()
                    logger.info(f"Deleted reminder {reminder_id}")
                    return True

                return False

        except Exception as e:
            logger.error(f"Error deleting reminder: {e}")
            return False

    def get_upcoming_reminders(self, hours_ahead: int = 24) -> List[Dict]:
        """Get upcoming reminders within specified hours"""
        now = datetime.now()
        future_time = now + timedelta(hours=hours_ahead)
        upcoming = []

        for reminder in self.get_active_reminders():
            try:
                next_time_str = reminder.get('next_reminder')
                if next_time_str:
                    next_time = datetime.fromisoformat(next_time_str)
                    if now <= next_time <= future_time:
                        upcoming.append(reminder)
            except ValueError:
                continue

        return sorted(upcoming, key=lambda x: x.get('next_reminder', ''))

    def get_overdue_reminders(self, hours_overdue: int = 2) -> List[Dict]:
        """Get reminders that are overdue"""
        now = datetime.now()
        cutoff_time = now - timedelta(hours=hours_overdue)
        overdue = []

        for reminder in self.get_active_reminders():
            try:
                next_time_str = reminder.get('next_reminder')
                if next_time_str:
                    next_time = datetime.fromisoformat(next_time_str)
                    if next_time < cutoff_time:
                        overdue.append(reminder)
            except ValueError:
                continue

        return overdue

    def get_compliance_report(self, days: int = 30) -> Dict[str, any]:
        """
        Get compliance report for the specified period

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with compliance statistics
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        total_taken = 0
        total_missed = 0
        medicine_stats = {}

        # Analyze history
        for entry in self.reminder_history:
            try:
                entry_time = datetime.fromisoformat(entry['timestamp'])
                if entry_time >= cutoff_date:
                    medicine_name = entry.get('medicine_name', 'Unknown')

                    if medicine_name not in medicine_stats:
                        medicine_stats[medicine_name] = {'taken': 0, 'missed': 0}

                    if entry['action'] == 'taken':
                        total_taken += 1
                        medicine_stats[medicine_name]['taken'] += 1
                    elif entry['action'] == 'missed':
                        total_missed += 1
                        medicine_stats[medicine_name]['missed'] += 1

            except (ValueError, KeyError):
                continue

        total_doses = total_taken + total_missed
        overall_compliance = (total_taken / total_doses * 100) if total_doses > 0 else 0

        return {
            'period_days': days,
            'total_doses': total_doses,
            'total_taken': total_taken,
            'total_missed': total_missed,
            'overall_compliance_percent': round(overall_compliance, 1),
            'medicine_breakdown': medicine_stats
        }

    def _add_to_history(self, reminder_id: str, action: str, timestamp: str):
        """Add an entry to reminder history"""
        try:
            # Find reminder details
            reminder_name = "Unknown"
            for reminder in self.reminders:
                if reminder['id'] == reminder_id:
                    reminder_name = reminder['medicine_name']
                    break

            history_entry = {
                'id': str(uuid.uuid4()),
                'reminder_id': reminder_id,
                'medicine_name': reminder_name,
                'action': action,
                'timestamp': timestamp
            }

            self.reminder_history.append(history_entry)

            # Keep only last 1000 entries to prevent file from growing too large
            if len(self.reminder_history) > 1000:
                self.reminder_history = self.reminder_history[-1000:]

        except Exception as e:
            logger.error(f"Error adding to history: {e}")

    def get_reminder_by_id(self, reminder_id: str) -> Optional[Dict]:
        """Get a reminder by its ID"""
        for reminder in self.reminders:
            if reminder['id'] == reminder_id:
                return reminder
        return None

    def update_reminder(self, reminder_id: str, updates: Dict) -> bool:
        """
        Update a reminder with new information

        Args:
            reminder_id: ID of the reminder to update
            updates: Dictionary of fields to update

        Returns:
            True if updated successfully
        """
        try:
            with self._lock:
                for reminder in self.reminders:
                    if reminder['id'] == reminder_id:
                        # Update fields
                        for key, value in updates.items():
                            if key in reminder:
                                reminder[key] = value

                        # Recalculate next reminder if timing changed
                        if any(key in updates for key in ['times', 'frequency', 'active']):
                            reminder['next_reminder'] = self._calculate_next_reminder_time(reminder)

                        self._save_data()
                        logger.info(f"Updated reminder {reminder_id}")
                        return True

                return False

        except Exception as e:
            logger.error(f"Error updating reminder: {e}")
            return False

    def get_all_reminders(self) -> List[Dict]:
        """Get all reminders (active and inactive)"""
        return self.reminders.copy()

    def load_reminders(self) -> List[Dict]:
        """Load and return all reminders (for backward compatibility)"""
        return self.get_all_reminders()

    def cleanup_old_history(self, days_old: int = 90):
        """
        Clean up old history entries

        Args:
            days_old: Remove entries older than this many days
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            original_count = len(self.reminder_history)

            self.reminder_history = [
                entry for entry in self.reminder_history
                if datetime.fromisoformat(entry['timestamp']) >= cutoff_date
            ]

            removed_count = original_count - len(self.reminder_history)

            if removed_count > 0:
                self._save_data()
                logger.info(f"Cleaned up {removed_count} old history entries")

        except Exception as e:
            logger.error(f"Error cleaning up history: {e}")
