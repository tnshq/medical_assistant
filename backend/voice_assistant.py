"""
Voice Assistant Module for MediScan
Handles text-to-speech and voice commands for elderly users
"""

import pyttsx3
import threading
import logging
import time
from typing import Optional, Dict
import re

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class VoiceAssistant:
    """
    Voice assistant with text-to-speech capabilities
    Designed to be elderly-friendly with clear, slow speech
    """

    def __init__(self, language: str = "en-US"):
        """
        Initialize voice assistant

        Args:
            language: Language code (default: en-US)
        """
        self.language = language
        self.is_speaking = False
        self._speak_lock = threading.Lock()
        self.engine = None
        self.voice_enabled = True
        self._initialize_engine()

    def _initialize_engine(self):
        """Initialize the pyttsx3 engine with elderly-friendly settings"""
        try:
            self.engine = pyttsx3.init()

            if self.engine:
                # Get available voices
                voices = self.engine.getProperty('voices')
                selected_voice = None

                # Try to find appropriate voice
                for voice in voices:
                    # Prefer female voices as they're often clearer for elderly
                    if hasattr(voice, 'gender') and 'female' in str(voice.gender).lower():
                        selected_voice = voice.id
                        break
                    elif hasattr(voice, 'name'):
                        # Look for clear English voices
                        if any(keyword in voice.name.lower() for keyword in ['zira', 'hazel', 'susan']):
                            selected_voice = voice.id
                            break

                # Set voice if found
                if selected_voice:
                    self.engine.setProperty('voice', selected_voice)

                # Set elderly-friendly speaking parameters
                self.engine.setProperty('rate', 150)      # Slower speech rate
                self.engine.setProperty('volume', 0.9)    # High volume

                logger.info(f"Voice engine initialized successfully with language: {self.language}")
            else:
                logger.error("Failed to initialize pyttsx3 engine")

        except Exception as e:
            logger.error(f"Error initializing voice engine: {e}")
            self.engine = None

    def speak(self, text: str, priority: str = "normal", async_mode: bool = True) -> bool:
        """
        Speak text using TTS

        Args:
            text: Text to speak
            priority: Priority level (high, normal, low)
            async_mode: Whether to speak asynchronously

        Returns:
            True if speaking started successfully, False otherwise
        """
        if not text or not text.strip():
            return False

        if not self.voice_enabled:
            logger.info(f"Voice disabled, would speak: {text}")
            return False

        # Clean text for better speech
        cleaned_text = self._clean_text_for_speech(text)

        with self._speak_lock:
            # Stop current speech for high priority messages
            if priority == "high" and self.is_speaking:
                self.stop_speaking()
                time.sleep(0.1)  # Brief pause
            elif self.is_speaking and priority != "high":
                return False  # Don't interrupt for normal priority

            self.is_speaking = True

        try:
            if async_mode:
                thread = threading.Thread(
                    target=self._speak_sync, 
                    args=(cleaned_text,),
                    daemon=True
                )
                thread.start()
                return True
            else:
                return self._speak_sync(cleaned_text)

        except Exception as e:
            logger.error(f"Error in speak method: {e}")
            with self._speak_lock:
                self.is_speaking = False
            return False

    def _speak_sync(self, text: str) -> bool:
        """Synchronously speak text"""
        try:
            if self.engine:
                self.engine.say(text)
                self.engine.runAndWait()
                return True
            else:
                logger.error("No voice engine available")
                return False

        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")
            return False

        finally:
            with self._speak_lock:
                self.is_speaking = False

    def stop_speaking(self):
        """Stop current speech"""
        try:
            if self.engine:
                self.engine.stop()

            with self._speak_lock:
                self.is_speaking = False

        except Exception as e:
            logger.error(f"Error stopping speech: {e}")

    def set_voice_enabled(self, enabled: bool):
        """Enable or disable voice output"""
        self.voice_enabled = enabled
        logger.info(f"Voice {'enabled' if enabled else 'disabled'}")

    def set_speech_rate(self, rate: int):
        """
        Set speech rate

        Args:
            rate: Speech rate (words per minute, 100-300, default 150 for elderly)
        """
        if self.engine:
            try:
                # Clamp rate to reasonable range for elderly users
                rate = max(100, min(250, rate))
                self.engine.setProperty('rate', rate)
                logger.info(f"Speech rate set to {rate}")
            except Exception as e:
                logger.error(f"Error setting speech rate: {e}")

    def set_volume(self, volume: float):
        """
        Set speech volume

        Args:
            volume: Volume level (0.0 to 1.0)
        """
        if self.engine:
            try:
                volume = max(0.0, min(1.0, volume))
                self.engine.setProperty('volume', volume)
                logger.info(f"Volume set to {volume}")
            except Exception as e:
                logger.error(f"Error setting volume: {e}")

    def test_voice(self) -> bool:
        """Test voice functionality"""
        test_message = "Hello! This is a voice test. Can you hear me clearly?"
        return self.speak(test_message, priority="high", async_mode=False)

    def _clean_text_for_speech(self, text: str) -> str:
        """Clean text to make it more speech-friendly"""
        # Remove or replace problematic characters
        text = re.sub(r'[_*#]', ' ', text)  # Remove markdown
        text = re.sub(r'\n+', '. ', text)   # Replace newlines with pauses
        text = re.sub(r'\s+', ' ', text)    # Normalize whitespace

        # Replace abbreviations with full words for clarity
        replacements = {
            'mg': 'milligrams',
            'ml': 'milliliters', 
            'g': 'grams',
            'mcg': 'micrograms',
            'Dr.': 'Doctor',
            'Mr.': 'Mister',
            'Mrs.': 'Missus',
            'Ms.': 'Miss',
            '&': 'and',
            '%': 'percent'
        }

        for abbrev, full in replacements.items():
            text = re.sub(r'\b' + re.escape(abbrev) + r'\b', full, text, flags=re.IGNORECASE)

        return text.strip()

    # Specialized medicine-related speech methods

    def speak_medicine_reminder(self, medicine_name: str, dosage: str = None, 
                              time_str: str = None, instructions: str = None) -> bool:
        """
        Speak a medicine reminder with clear, structured information

        Args:
            medicine_name: Name of the medicine
            dosage: Dosage information
            time_str: Time for taking medicine
            instructions: Additional instructions

        Returns:
            True if spoken successfully
        """
        message_parts = ["Medicine reminder."]

        if time_str:
            message_parts.append(f"It is time to take your medicine.")

        message_parts.append(f"Please take {medicine_name}.")

        if dosage:
            message_parts.append(f"The dosage is {dosage}.")

        if instructions:
            message_parts.append(f"Instructions: {instructions}.")

        message_parts.append("Please confirm when you have taken your medicine.")

        full_message = " ".join(message_parts)
        return self.speak(full_message, priority="high")

    def speak_scan_result(self, medicine_info: Dict) -> bool:
        """
        Speak the results of a medicine scan

        Args:
            medicine_info: Dictionary with medicine information

        Returns:
            True if spoken successfully
        """
        name = medicine_info.get('name', 'unknown medicine')
        dosage = medicine_info.get('dosage', '')
        expiry_date = medicine_info.get('expiry_date', '')

        message_parts = [f"Scanned medicine: {name}."]

        if dosage:
            message_parts.append(f"Dosage: {dosage}.")

        if expiry_date:
            message_parts.append(f"This medicine expires on {expiry_date}.")

        message_parts.append("Scan completed successfully.")

        full_message = " ".join(message_parts)
        return self.speak(full_message)

    def speak_expiry_warning(self, medicine_name: str, days_until_expiry: int) -> bool:
        """
        Speak expiry warning

        Args:
            medicine_name: Name of the medicine
            days_until_expiry: Days until expiry

        Returns:
            True if spoken successfully
        """
        if days_until_expiry < 0:
            message = f"Important warning: {medicine_name} has expired. Please do not use this medicine and consult your doctor for a replacement."
        elif days_until_expiry == 0:
            message = f"Important warning: {medicine_name} expires today. Please check with your pharmacist or doctor for a replacement."
        elif days_until_expiry <= 3:
            message = f"Important notice: {medicine_name} will expire in {days_until_expiry} days. Please arrange for a replacement soon."
        else:
            message = f"Notice: {medicine_name} will expire in {days_until_expiry} days. Please plan to get a replacement."

        return self.speak(message, priority="high")

    def speak_reminder_confirmation(self, medicine_name: str, action: str) -> bool:
        """
        Speak confirmation for reminder actions

        Args:
            medicine_name: Name of the medicine
            action: Action taken (taken, missed, etc.)

        Returns:
            True if spoken successfully
        """
        if action == "taken":
            message = f"Thank you. I have recorded that you have taken {medicine_name}."
        elif action == "missed":
            message = f"I have noted that you missed {medicine_name}. Please try to take it as soon as possible, or consult your doctor."
        elif action == "skipped":
            message = f"I have recorded that you skipped {medicine_name}."
        else:
            message = f"Action recorded for {medicine_name}."

        return self.speak(message)

    def speak_error_message(self, error_type: str, context: str = "") -> bool:
        """
        Speak user-friendly error messages

        Args:
            error_type: Type of error
            context: Additional context

        Returns:
            True if spoken successfully
        """
        error_messages = {
            'scan_failed': 'I could not read the medicine label clearly. Please try scanning again with better lighting.',
            'no_medicine_found': 'I could not find any medicine information in the image. Please make sure the label is clearly visible.',
            'network_error': 'There is a network connection problem. Please check your internet connection and try again.',
            'voice_error': 'There is a problem with the voice system. The application will continue to work normally.',
            'reminder_error': 'There was a problem setting up the reminder. Please try again.',
            'general_error': 'Something went wrong. Please try again or contact support if the problem continues.'
        }

        message = error_messages.get(error_type, error_messages['general_error'])

        if context:
            message += f" Details: {context}"

        return self.speak(message, priority="high")

    def is_available(self) -> bool:
        """Check if voice assistant is available"""
        return self.engine is not None

    def get_status(self) -> Dict[str, any]:
        """Get current status of voice assistant"""
        return {
            'available': self.is_available(),
            'language': self.language,
            'is_speaking': self.is_speaking,
            'voice_enabled': self.voice_enabled,
            'engine': 'pyttsx3' if self.engine else None
        }

    def update_settings(self, rate: int = None, volume: float = None, enabled: bool = None):
        """
        Update voice settings

        Args:
            rate: Speech rate
            volume: Volume level
            enabled: Whether voice is enabled
        """
        if rate is not None:
            self.set_speech_rate(rate)

        if volume is not None:
            self.set_volume(volume)

        if enabled is not None:
            self.set_voice_enabled(enabled)

        logger.info("Voice settings updated")
