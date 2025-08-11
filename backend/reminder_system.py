"""
Reminder System Module for MediScan
Handles medicine reminders and notifications
"""

import json
import os
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple
import logging
import uuid

logger = logging.getLogger(__name__)

class ReminderSystem:
    """
    Manages medicine reminders and notifications
    """
    
    def __init__(self, data_file: str = "data/reminders.json"):
        """Initialize the reminder system"""
        self.data_file = data_file
        self.reminders = []
        self.reminder_history = []
        self._ensure_data_directory()
        self._load_reminders()
    
    def _ensure_data_directory(self):
        """Ensure data directory exists"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
    
    def _load_reminders(self):
        """Load reminders from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.reminders = data.get('reminders', [])
                    self.reminder_history = data.get('history', [])
        except Exception as e:
            logger.error(f"Error loading reminders: {e}")
            self.reminders = []
            self.reminder_history = []
    
    def _save_reminders(self):
        """Save reminders to file"""
        try:
            data = {
                'reminders': self.reminders,
                'history': self.reminder_history
            }
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving reminders: {e}")
    
    def create_reminder(self, medicine_info: Dict, reminder_type: str, 
                       reminder_time: time = None) -> Dict:
        """
        Create a new reminder for a medicine
        
        Args:
            medicine_info: Dictionary containing medicine information
            reminder_type: Type of reminder (Daily, Twice Daily, etc.)
            reminder_time: Time for the reminder
            
        Returns:
            Dictionary containing the created reminder
        """
        if reminder_time is None:
            reminder_time = time(9, 0)  # Default to 9:00 AM
        
        reminder = {
            'id': str(uuid.uuid4()),
            'medicine_id': medicine_info.get('id', str(uuid.uuid4())),
            'medicine_name': medicine_info.get('name', 'Unknown Medicine'),
            'type': reminder_type,
            'time': reminder_time.strftime('%H:%M'),
            'active': True,
            'created_date': datetime.now().isoformat(),
            'last_taken': None,
            'next_reminder': self._calculate_next_reminder(reminder_type, reminder_time),
            'expiry_date': medicine_info.get('expiry_date'),
            'dosage': medicine_info.get('dosage'),
            'instructions': self._get_reminder_instructions(reminder_type),
            'missed_count': 0,
            'taken_count': 0
        }
        
        # Add multiple times for certain reminder types
        if reminder_type == "Twice Daily":
            reminder['times'] = [reminder_time.strftime('%H:%M'), 
                               (datetime.combine(datetime.today(), reminder_time) + timedelta(hours=12)).time().strftime('%H:%M')]
        elif reminder_type == "Three Times Daily":
            reminder['times'] = [
                reminder_time.strftime('%H:%M'),
                (datetime.combine(datetime.today(), reminder_time) + timedelta(hours=8)).time().strftime('%H:%M'),
                (datetime.combine(datetime.today(), reminder_time) + timedelta(hours=16)).time().strftime('%H:%M')
            ]
        elif reminder_type == "Weekly":
            reminder['day_of_week'] = datetime.now().weekday()
        
        self.reminders.append(reminder)
        self._save_reminders()
        
        logger.info(f"Created reminder for {reminder['medicine_name']}")
        return reminder
    
    def _calculate_next_reminder(self, reminder_type: str, reminder_time: time) -> str:
        """Calculate the next reminder datetime"""
        now = datetime.now()
        today = now.date()
        
        if reminder_type == "Daily":
            next_time = datetime.combine(today, reminder_time)
            if next_time <= now:
                next_time += timedelta(days=1)
        elif reminder_type == "Twice Daily":
            morning_time = reminder_time
            evening_time = (datetime.combine(today, reminder_time) + timedelta(hours=12)).time()
            
            morning_datetime = datetime.combine(today, morning_time)
            evening_datetime = datetime.combine(today, evening_time)
            
            if now < morning_datetime:
                next_time = morning_datetime
            elif now < evening_datetime:
                next_time = evening_datetime
            else:
                next_time = datetime.combine(today + timedelta(days=1), morning_time)
        elif reminder_type == "Three Times Daily":
            times = [
                reminder_time,
                (datetime.combine(today, reminder_time) + timedelta(hours=8)).time(),
                (datetime.combine(today, reminder_time) + timedelta(hours=16)).time()
            ]
            
            next_time = None
            for t in times:
                candidate = datetime.combine(today, t)
                if candidate > now:
                    next_time = candidate
                    break
            
            if next_time is None:
                next_time = datetime.combine(today + timedelta(days=1), reminder_time)
        elif reminder_type == "Weekly":
            days_ahead = 7  # Next week same day
            next_time = datetime.combine(today + timedelta(days=days_ahead), reminder_time)
        else:  # Custom or other types
            next_time = datetime.combine(today + timedelta(days=1), reminder_time)
        
        return next_time.isoformat()
    
    def _get_reminder_instructions(self, reminder_type: str) -> str:
        """Get instructions for the reminder type"""
        instructions = {
            "Daily": "Take once daily",
            "Twice Daily": "Take twice daily (morning and evening)",
            "Three Times Daily": "Take three times daily (morning, afternoon, evening)",
            "Weekly": "Take once weekly",
            "Custom": "Follow custom schedule"
        }
        return instructions.get(reminder_type, "Follow prescribed dosage")
    
    def check_due_reminders(self) -> List[Dict]:
        """Check for reminders that are due"""
        now = datetime.now()
        due_reminders = []
        
        for reminder in self.reminders:
            if not reminder['active']:
                continue
            
            try:
                next_reminder_time = datetime.fromisoformat(reminder['next_reminder'])
                
                # Check if reminder is due (within 15 minutes)
                time_diff = (next_reminder_time - now).total_seconds()
                if -900 <= time_diff <= 900:  # 15 minutes window
                    due_reminders.append(reminder)
                    
                    # Update next reminder time
                    reminder['next_reminder'] = self._calculate_next_reminder(
                        reminder['type'], 
                        datetime.strptime(reminder['time'], '%H:%M').time()
                    )
            except (ValueError, KeyError) as e:
                logger.error(f"Error processing reminder {reminder.get('id', 'unknown')}: {e}")
        
        if due_reminders:
            self._save_reminders()
        
        return due_reminders
    
    def mark_as_taken(self, reminder_id: str, taken_time: datetime = None) -> bool:
        """Mark a reminder as taken"""
        if taken_time is None:
            taken_time = datetime.now()
        
        for reminder in self.reminders:
            if reminder['id'] == reminder_id:
                reminder['last_taken'] = taken_time.isoformat()
                reminder['taken_count'] += 1
                
                # Add to history
                history_entry = {
                    'reminder_id': reminder_id,
                    'medicine_name': reminder['medicine_name'],
                    'taken_time': taken_time.isoformat(),
                    'scheduled_time': reminder['next_reminder'],
                    'status': 'taken'
                }
                self.reminder_history.append(history_entry)
                
                # Update next reminder
                reminder['next_reminder'] = self._calculate_next_reminder(
                    reminder['type'],
                    datetime.strptime(reminder['time'], '%H:%M').time()
                )
                
                self._save_reminders()
                logger.info(f"Marked reminder {reminder_id} as taken")
                return True
        
        return False
    
    def mark_as_missed(self, reminder_id: str, missed_time: datetime = None) -> bool:
        """Mark a reminder as missed"""
        if missed_time is None:
            missed_time = datetime.now()
        
        for reminder in self.reminders:
            if reminder['id'] == reminder_id:
                reminder['missed_count'] += 1
                
                # Add to history
                history_entry = {
                    'reminder_id': reminder_id,
                    'medicine_name': reminder['medicine_name'],
                    'missed_time': missed_time.isoformat(),
                    'scheduled_time': reminder['next_reminder'],
                    'status': 'missed'
                }
                self.reminder_history.append(history_entry)
                
                # Update next reminder
                reminder['next_reminder'] = self._calculate_next_reminder(
                    reminder['type'],
                    datetime.strptime(reminder['time'], '%H:%M').time()
                )
                
                self._save_reminders()
                logger.info(f"Marked reminder {reminder_id} as missed")
                return True
        
        return False
    
    def pause_reminder(self, reminder_id: str) -> bool:
        """Pause a reminder"""
        for reminder in self.reminders:
            if reminder['id'] == reminder_id:
                reminder['active'] = False
                self._save_reminders()
                logger.info(f"Paused reminder {reminder_id}")
                return True
        return False
    
    def resume_reminder(self, reminder_id: str) -> bool:
        """Resume a paused reminder"""
        for reminder in self.reminders:
            if reminder['id'] == reminder_id:
                reminder['active'] = True
                # Recalculate next reminder
                reminder['next_reminder'] = self._calculate_next_reminder(
                    reminder['type'],
                    datetime.strptime(reminder['time'], '%H:%M').time()
                )
                self._save_reminders()
                logger.info(f"Resumed reminder {reminder_id}")
                return True
        return False
    
    def delete_reminder(self, reminder_id: str) -> bool:
        """Delete a reminder"""
        for i, reminder in enumerate(self.reminders):
            if reminder['id'] == reminder_id:
                del self.reminders[i]
                self._save_reminders()
                logger.info(f"Deleted reminder {reminder_id}")
                return True
        return False
    
    def get_upcoming_reminders(self, hours_ahead: int = 24) -> List[Dict]:
        """Get upcoming reminders within specified hours"""
        now = datetime.now()
        future_time = now + timedelta(hours=hours_ahead)
        upcoming = []
        
        for reminder in self.reminders:
            if not reminder['active']:
                continue
            
            try:
                next_time = datetime.fromisoformat(reminder['next_reminder'])
                if now <= next_time <= future_time:
                    upcoming.append(reminder)
            except ValueError:
                continue
        
        return sorted(upcoming, key=lambda x: x['next_reminder'])
    
    def get_overdue_reminders(self) -> List[Dict]:
        """Get overdue reminders"""
        now = datetime.now()
        overdue = []
        
        for reminder in self.reminders:
            if not reminder['active']:
                continue
            
            try:
                next_time = datetime.fromisoformat(reminder['next_reminder'])
                if next_time < now - timedelta(hours=1):  # More than 1 hour overdue
                    overdue.append(reminder)
            except ValueError:
                continue
        
        return overdue
    
    def get_compliance_report(self, days: int = 30) -> List[Dict]:
        """Get compliance report for the last N days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        compliance_data = []
        for reminder in self.reminders:
            reminder_compliance = {
                'medicine_name': reminder['medicine_name'],
                'reminder_type': reminder['type'],
                'taken': reminder.get('taken_count', 0),
                'missed': reminder.get('missed_count', 0),
                'compliance_rate': 0
            }
            
            total = reminder_compliance['taken'] + reminder_compliance['missed']
            if total > 0:
                reminder_compliance['compliance_rate'] = (
                    reminder_compliance['taken'] / total
                ) * 100
            
            compliance_data.append(reminder_compliance)
        
        return compliance_data
    
    def get_history(self, days: int = 30) -> List[Dict]:
        """Get reminder history for the last N days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_history = []
        for entry in self.reminder_history:
            try:
                entry_time = datetime.fromisoformat(entry.get('taken_time') or entry.get('missed_time'))
                if entry_time >= cutoff_date:
                    recent_history.append(entry)
            except (ValueError, KeyError):
                continue
        
        return sorted(recent_history, key=lambda x: x.get('taken_time') or x.get('missed_time'), reverse=True)
    
    def send_test_notification(self):
        """Send a test notification"""
        test_notification = {
            'title': 'MediScan Test Notification',
            'message': 'This is a test notification from MediScan reminder system.',
            'timestamp': datetime.now().isoformat()
        }
        logger.info(f"Test notification: {test_notification}")
        return test_notification
    
    def get_expiry_alerts(self, days_ahead: int = 7) -> List[Dict]:
        """Get medicines expiring within specified days"""
        alerts = []
        cutoff_date = datetime.now().date() + timedelta(days=days_ahead)
        
        for reminder in self.reminders:
            if not reminder.get('expiry_date'):
                continue
            
            try:
                expiry_date = datetime.strptime(reminder['expiry_date'], '%Y-%m-%d').date()
                if expiry_date <= cutoff_date:
                    days_until_expiry = (expiry_date - datetime.now().date()).days
                    alerts.append({
                        'medicine_name': reminder['medicine_name'],
                        'expiry_date': reminder['expiry_date'],
                        'days_until_expiry': days_until_expiry,
                        'reminder_id': reminder['id'],
                        'urgency': 'high' if days_until_expiry <= 3 else 'medium' if days_until_expiry <= 7 else 'low'
                    })
            except ValueError:
                continue
        
        return sorted(alerts, key=lambda x: x['days_until_expiry'])
    
    def load_reminders(self) -> List[Dict]:
        """Load and return all reminders"""
        self._load_reminders()
        return self.reminders
    
    def get_reminder_by_id(self, reminder_id: str) -> Optional[Dict]:
        """Get a specific reminder by ID"""
        for reminder in self.reminders:
            if reminder['id'] == reminder_id:
                return reminder
        return None
    
    def update_reminder(self, reminder_id: str, updates: Dict) -> bool:
        """Update a reminder with new information"""
        for reminder in self.reminders:
            if reminder['id'] == reminder_id:
                for key, value in updates.items():
                    if key in reminder:
                        reminder[key] = value
                
                # Recalculate next reminder if time changed
                if 'time' in updates or 'type' in updates:
                    reminder['next_reminder'] = self._calculate_next_reminder(
                        reminder['type'],
                        datetime.strptime(reminder['time'], '%H:%M').time()
                    )
                
                self._save_reminders()
                return True
        return False