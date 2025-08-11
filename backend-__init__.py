"""
Backend Module Initialization
"""

# This file makes the backend directory a Python package
# Import all modules for easier access

from .ocr_processor import OCRProcessor
from .medicine_extractor import MedicineExtractor
from .reminder_system import ReminderSystem
from .voice_assistant import VoiceAssistant
from .database_handler import DatabaseHandler

__all__ = [
    'OCRProcessor',
    'MedicineExtractor', 
    'ReminderSystem',
    'VoiceAssistant',
    'DatabaseHandler'
]