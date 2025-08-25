"""
Voice Assistant Module for MediScan
Handles text-to-speech and voice feedback functionality
"""

import pyttsx3
import threading
from typing import Optional, List, Dict
import logging
from typing import Optional, Dict
import os

try:
    from gtts import gTTS
    import pygame
    import tempfile
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

logger = logging.getLogger(__name__)

class VoiceAssistant:
    """
    Voice assistant for MediScan application
    Provides text-to-speech functionality using multiple engines
    """
    
    def __init__(self, engine_type: str = "pyttsx3", language: str = "en-US"):
        """
        Initialize voice assistant
        
        Args:
            engine_type: TTS engine to use ("pyttsx3" or "gtts")
            language: Language code for TTS
        """
        self.engine_type = engine_type
        self.language = language
        self.is_speaking = False
        self.engine = None
        
        # Initialize the TTS engine
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize the TTS engine"""
        try:
            if self.engine_type == "pyttsx3":
                self._initialize_pyttsx3()
            elif self.engine_type == "gtts" and GTTS_AVAILABLE:
                self._initialize_gtts()
            else:
                logger.warning("Falling back to pyttsx3")
                self._initialize_pyttsx3()
        except Exception as e:
            logger.error(f"Error initializing voice engine: {e}")
            self.engine = None
    
    def _initialize_pyttsx3(self):
        """Initialize pyttsx3 engine"""
        try:
            self.engine = pyttsx3.init()
            
            # Set properties
            voices = self.engine.getProperty('voices')
            
            # Try to find a voice matching the language
            selected_voice = None
            for voice in voices:
                if self.language.startswith('en') and 'english' in voice.name.lower():
                    selected_voice = voice.id
                    break
                elif self.language.startswith('hi') and 'hindi' in voice.name.lower():
                    selected_voice = voice.id
                    break
            
            if selected_voice:
                self.engine.setProperty('voice', selected_voice)
            
            # Set speech rate and volume
            self.engine.setProperty('rate', 180)  # Speed of speech
            self.engine.setProperty('volume', 0.9)  # Volume level (0.0 to 1.0)
            
            logger.info(f"pyttsx3 engine initialized with language: {self.language}")
            
        except Exception as e:
            logger.error(f"Error initializing pyttsx3: {e}")
            self.engine = None
    
    def _initialize_gtts(self):
        """Initialize gTTS engine"""
        if not GTTS_AVAILABLE:
            logger.error("gTTS dependencies not available")
            return
        
        try:
            # Initialize pygame for audio playback
            pygame.mixer.init()
            logger.info(f"gTTS engine initialized with language: {self.language}")
            
        except Exception as e:
            logger.error(f"Error initializing gTTS: {e}")
    
    def speak(self, text: str, async_mode: bool = True) -> bool:
        """
        Convert text to speech
        
        Args:
            text: Text to speak
            async_mode: Whether to speak asynchronously
            
        Returns:
            True if successful, False otherwise
        """
        if not text or not text.strip():
            return False
        
        if self.is_speaking:
            logger.info("Already speaking, skipping new request")
            return False
        
        try:
            if async_mode:
                # Speak in a separate thread
                thread = threading.Thread(target=self._speak_sync, args=(text,))
                thread.daemon = True
                thread.start()
                return True
            else:
                return self._speak_sync(text)
                
        except Exception as e:
            logger.error(f"Error in speak method: {e}")
            return False
    
    def _speak_sync(self, text: str) -> bool:
        """
        Synchronous speech method
        
        Args:
            text: Text to speak
            
        Returns:
            True if successful, False otherwise
        """
        self.is_speaking = True
        
        try:
            if self.engine_type == "pyttsx3" and self.engine:
                return self._speak_pyttsx3(text)
            elif self.engine_type == "gtts" and GTTS_AVAILABLE:
                return self._speak_gtts(text)
            else:
                logger.error("No valid TTS engine available")
                return False
                
        finally:
            self.is_speaking = False
    
    def _speak_pyttsx3(self, text: str) -> bool:
        """Speak using pyttsx3"""
        try:
            self.engine.say(text)
            self.engine.runAndWait()
            logger.info(f"Spoke text: {text[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error speaking with pyttsx3: {e}")
            return False
    
    def _speak_gtts(self, text: str) -> bool:
        """Speak using gTTS"""
        try:
            # Create gTTS object
            lang_code = self.language.split('-')[0]  # Extract language code
            tts = gTTS(text=text, lang=lang_code, slow=False)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_filename = temp_file.name
                tts.save(temp_filename)
            
            # Play the audio file
            pygame.mixer.music.load(temp_filename)
            pygame.mixer.music.play()
            
            # Wait for playback to complete
            while pygame.mixer.music.get_busy():
                threading.Event().wait(0.1)
            
            # Clean up temporary file
            try:
                os.unlink(temp_filename)
            except:
                pass
            
            logger.info(f"Spoke text using gTTS: {text[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error speaking with gTTS: {e}")
            return False
    
    def stop_speaking(self):
        """Stop current speech"""
        try:
            if self.engine_type == "pyttsx3" and self.engine:
                self.engine.stop()
            elif self.engine_type == "gtts" and GTTS_AVAILABLE:
                pygame.mixer.music.stop()
            
            self.is_speaking = False
            logger.info("Speech stopped")
            
        except Exception as e:
            logger.error(f"Error stopping speech: {e}")
    
    def set_language(self, language: str):
        """
        Set the language for TTS
        
        Args:
            language: Language code (e.g., 'en-US', 'hi-IN')
        """
        self.language = language
        logger.info(f"Language set to: {language}")
        
        # Reinitialize engine with new language
        self._initialize_engine()
    
    def set_speech_rate(self, rate: int):
        """
        Set speech rate for pyttsx3
        
        Args:
            rate: Speech rate (words per minute)
        """
        if self.engine_type == "pyttsx3" and self.engine:
            try:
                self.engine.setProperty('rate', rate)
                logger.info(f"Speech rate set to: {rate}")
            except Exception as e:
                logger.error(f"Error setting speech rate: {e}")
    
    def set_volume(self, volume: float):
        """
        Set volume for pyttsx3
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        if self.engine_type == "pyttsx3" and self.engine:
            try:
                self.engine.setProperty('volume', max(0.0, min(1.0, volume)))
                logger.info(f"Volume set to: {volume}")
            except Exception as e:
                logger.error(f"Error setting volume: {e}")
    
    def get_available_voices(self) -> List[Dict]:
        """
        Get list of available voices (pyttsx3 only)
        
        Returns:
            List of voice information dictionaries
        """
        voices = []
        
        if self.engine_type == "pyttsx3" and self.engine:
            try:
                engine_voices = self.engine.getProperty('voices')
                for voice in engine_voices:
                    voices.append({
                        'id': voice.id,
                        'name': voice.name,
                        'languages': getattr(voice, 'languages', []),
                        'gender': getattr(voice, 'gender', 'unknown'),
                        'age': getattr(voice, 'age', 'unknown')
                    })
            except Exception as e:
                logger.error(f"Error getting voices: {e}")
        
        return voices
    
    def test_speech(self) -> bool:
        """
        Test the speech functionality
        
        Returns:
            True if test successful, False otherwise
        """
        test_text = "Hello! This is a test of the MediScan voice assistant."
        return self.speak(test_text, async_mode=False)
    
    def speak_medicine_reminder(self, medicine_name: str, time_str: str, 
                               dosage: str = None) -> bool:
        """
        Speak a medicine reminder
        
        Args:
            medicine_name: Name of the medicine
            time_str: Time string
            dosage: Dosage information
            
        Returns:
            True if successful, False otherwise
        """
        text = f"Medicine reminder: It's time to take {medicine_name}"
        
        if dosage:
            text += f", {dosage}"
        
        text += f" at {time_str}."
        
        return self.speak(text)
    
    def speak_expiry_alert(self, medicine_name: str, days_until_expiry: int) -> bool:
        """
        Speak an expiry alert
        
        Args:
            medicine_name: Name of the medicine
            days_until_expiry: Days until expiry
            
        Returns:
            True if successful, False otherwise
        """
        if days_until_expiry <= 0:
            text = f"Alert: {medicine_name} has expired. Please do not use it."
        elif days_until_expiry == 1:
            text = f"Alert: {medicine_name} expires tomorrow. Please get a replacement."
        elif days_until_expiry <= 7:
            text = f"Alert: {medicine_name} expires in {days_until_expiry} days. Consider getting a replacement soon."
        else:
            text = f"Notice: {medicine_name} expires in {days_until_expiry} days."
        
        return self.speak(text)
    
    def speak_scan_result(self, medicine_info: Dict) -> bool:
        """
        Speak the result of a medicine scan
        
        Args:
            medicine_info: Dictionary containing medicine information
            
        Returns:
            True if successful, False otherwise
        """
        medicine_name = medicine_info.get('name', 'unknown medicine')
        dosage = medicine_info.get('dosage', '')
        expiry_date = medicine_info.get('expiry_date', '')
        
        text = f"Scanned {medicine_name}"
        
        if dosage:
            text += f", {dosage}"
        
        if expiry_date:
            text += f". Expires on {expiry_date}"
        
        text += "."
        
        return self.speak(text)
    
    def is_available(self) -> bool:
        """
        Check if voice assistant is available
        
        Returns:
            True if available, False otherwise
        """
        return self.engine is not None
    
    def get_status(self) -> Dict:
        """
        Get voice assistant status
        
        Returns:
            Dictionary containing status information
        """
        return {
            'engine_type': self.engine_type,
            'language': self.language,
            'is_speaking': self.is_speaking,
            'available': self.is_available(),
            'gtts_available': GTTS_AVAILABLE
        }