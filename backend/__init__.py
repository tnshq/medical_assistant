"""
Backend Module Initialization for MediScan
This file makes the backend directory a Python package
"""

# Import all modules for easier access
try:
    from .ocr_processor import OCRProcessor
    from .medicine_extractor import MedicineExtractor
    from .reminder_system import ReminderSystem
    from .voice_assistant import VoiceAssistant
    from .database_handler import DatabaseHandler
except ImportError as e:
    # Handle relative import issues
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    from ocr_processor import OCRProcessor
    from medicine_extractor import MedicineExtractor
    from reminder_system import ReminderSystem
    from voice_assistant import VoiceAssistant
    from database_handler import DatabaseHandler

__all__ = [
    'OCRProcessor',
    'MedicineExtractor', 
    'ReminderSystem',
    'VoiceAssistant',
    'DatabaseHandler'
]

__version__ = "1.0.0"
__author__ = "MediScan Team"