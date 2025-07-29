#!/usr/bin/env python3
"""
Voice Recognition Module for NEXA
Handles speech-to-text conversion with continuous listening
"""

import speech_recognition as sr
import threading
import time
import logging
from typing import Callable, Optional
import queue

class VoiceRecognition:
    """Voice recognition system for NEXA AI Butler"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.is_listening = False
        self.callback: Optional[Callable] = None
        self.listen_thread: Optional[threading.Thread] = None
        
        # Configure recognizer for better performance
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_threshold = 0.3
        
        # Initialize microphone
        self._initialize_microphone()
    
    def _initialize_microphone(self):
        """Initialize and calibrate microphone"""
        try:
            self.microphone = sr.Microphone()
            
            # Calibrate for ambient noise
            with self.microphone as source:
                self.logger.info("Calibrating microphone for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                self.logger.info("Microphone calibration complete")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize microphone: {e}")
            self.microphone = None
    
    def start_listening(self, callback: Callable):
        """Start continuous voice recognition"""
        if self.microphone is None:
            self.logger.error("Cannot start listening: microphone not available")
            return False
        
        if self.is_listening:
            self.logger.warning("Already listening")
            return True
        
        self.callback = callback
        self.is_listening = True
        
        # Start listening thread
        self.listen_thread = threading.Thread(target=self._listen_continuously, daemon=True)
        self.listen_thread.start()
        
        self.logger.info("Voice recognition started")
        return True
    
    def stop_listening(self):
        """Stop voice recognition"""
        self.is_listening = False
        self.callback = None
        
        if self.listen_thread:
            self.listen_thread.join(timeout=2)
        
        self.logger.info("Voice recognition stopped")
    
    def _listen_continuously(self):
        """Continuous listening loop"""
        while self.is_listening:
            try:
                # Listen for audio with timeout
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                
                # Process audio in background
                threading.Thread(target=self._process_audio, args=(audio,), daemon=True).start()
                
            except sr.WaitTimeoutError:
                # Timeout is normal, continue listening
                continue
            except Exception as e:
                self.logger.error(f"Error during listening: {e}")
                time.sleep(1)
    
    def _process_audio(self, audio):
        """Process audio data to text"""
        try:
            # Use Google Speech Recognition (works offline with basic commands)
            text = self.recognizer.recognize_google(audio, language='en-IN')
            
            if text and self.callback:
                # Clean up the text
                cleaned_text = self._clean_text(text)
                if cleaned_text:
                    self.logger.info(f"Recognized: {cleaned_text}")
                    self.callback(cleaned_text)
                    
        except sr.UnknownValueError:
            # Could not understand audio - this is normal, don't log
            pass
        except sr.RequestError as e:
            self.logger.error(f"Speech recognition service error: {e}")
        except Exception as e:
            self.logger.error(f"Error processing audio: {e}")
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize recognized text"""
        if not text:
            return ""
        
        # Convert to lowercase and strip
        cleaned = text.lower().strip()
        
        # Remove common speech recognition artifacts
        artifacts = ['um', 'uh', 'er', 'ah']
        words = cleaned.split()
        words = [word for word in words if word not in artifacts]
        
        return ' '.join(words)
    
    def recognize_once(self, timeout: int = 5) -> Optional[str]:
        """Recognize speech once with timeout"""
        if self.microphone is None:
            return None
        
        try:
            with self.microphone as source:
                self.logger.info("Listening for command...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=5)
            
            text = self.recognizer.recognize_google(audio, language='en-IN')
            cleaned_text = self._clean_text(text)
            
            self.logger.info(f"Recognized: {cleaned_text}")
            return cleaned_text
            
        except sr.WaitTimeoutError:
            self.logger.info("No speech detected within timeout")
            return None
        except sr.UnknownValueError:
            self.logger.info("Could not understand audio")
            return None
        except sr.RequestError as e:
            self.logger.error(f"Speech recognition error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return None
    
    def is_microphone_available(self) -> bool:
        """Check if microphone is available"""
        return self.microphone is not None
    
    def get_microphone_list(self) -> list:
        """Get list of available microphones"""
        try:
            return sr.Microphone.list_microphone_names()
        except Exception as e:
            self.logger.error(f"Error getting microphone list: {e}")
            return []
    
    def set_microphone(self, device_index: Optional[int] = None):
        """Set specific microphone device"""
        try:
            self.microphone = sr.Microphone(device_index=device_index)
            
            # Recalibrate
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            self.logger.info(f"Microphone set to device index: {device_index}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set microphone: {e}")
            return False