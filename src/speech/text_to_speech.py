#!/usr/bin/env python3
"""
Text-to-Speech Module for NEXA
Provides Indian-English voice with personality
"""

import pyttsx3
import threading
import queue
import logging
import time
from typing import Optional

class TextToSpeech:
    """Text-to-speech system with Indian-English accent and personality"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.engine: Optional[pyttsx3.Engine] = None
        self.is_speaking = False
        self.speech_queue = queue.Queue()
        
        # Initialize TTS engine
        self._initialize_engine()
        
        # Start speech processing thread
        self.speech_thread = threading.Thread(target=self._process_speech_queue, daemon=True)
        self.speech_thread.start()
    
    def _initialize_engine(self):
        """Initialize and configure the TTS engine"""
        try:
            self.engine = pyttsx3.init()
            
            # Configure voice properties for Indian-English accent
            self._configure_voice()
            
            self.logger.info("TTS engine initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize TTS engine: {e}")
            self.engine = None
    
    def _configure_voice(self):
        """Configure voice properties for Indian-English accent"""
        if not self.engine:
            return
        
        try:
            # Get available voices
            voices = self.engine.getProperty('voices')
            
            # Try to find an Indian or female voice (often sounds more refined)
            selected_voice = None
            for voice in voices:
                voice_name = voice.name.lower()
                if any(keyword in voice_name for keyword in ['indian', 'india', 'zira', 'hazel']):
                    selected_voice = voice.id
                    break
            
            # If no Indian voice found, use the first female voice
            if not selected_voice:
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        selected_voice = voice.id
                        break
            
            # Set voice
            if selected_voice:
                self.engine.setProperty('voice', selected_voice)
                self.logger.info(f"Voice set to: {selected_voice}")
            
            # Configure speech rate (slightly slower for clarity)
            self.engine.setProperty('rate', 180)  # Default is usually 200
            
            # Configure volume
            self.engine.setProperty('volume', 0.9)
            
        except Exception as e:
            self.logger.error(f"Error configuring voice: {e}")
    
    def speak(self, text: str, priority: bool = False):
        """Add text to speech queue"""
        if not text or not self.engine:
            return
        
        # Add personality touches to common responses
        enhanced_text = self._enhance_text_with_personality(text)
        
        if priority:
            # Add to front of queue for urgent messages
            temp_queue = queue.Queue()
            temp_queue.put(enhanced_text)
            
            # Move existing items to temp queue
            while not self.speech_queue.empty():
                try:
                    temp_queue.put(self.speech_queue.get_nowait())
                except queue.Empty:
                    break
            
            # Replace main queue
            self.speech_queue = temp_queue
        else:
            self.speech_queue.put(enhanced_text)
        
        self.logger.info(f"Added to speech queue: {text[:50]}...")
    
    def speak_immediately(self, text: str):
        """Speak text immediately, interrupting current speech"""
        if not text or not self.engine:
            return
        
        try:
            # Stop current speech
            self.engine.stop()
            
            # Clear queue
            while not self.speech_queue.empty():
                try:
                    self.speech_queue.get_nowait()
                except queue.Empty:
                    break
            
            # Speak immediately
            enhanced_text = self._enhance_text_with_personality(text)
            self.engine.say(enhanced_text)
            self.engine.runAndWait()
            
        except Exception as e:
            self.logger.error(f"Error in immediate speech: {e}")
    
    def _process_speech_queue(self):
        """Process speech queue in background thread"""
        while True:
            try:
                if not self.speech_queue.empty():
                    text = self.speech_queue.get(timeout=1)
                    self._speak_text(text)
                else:
                    time.sleep(0.1)
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error processing speech queue: {e}")
                time.sleep(1)
    
    def _speak_text(self, text: str):
        """Actually speak the text"""
        if not self.engine:
            return
        
        try:
            self.is_speaking = True
            self.engine.say(text)
            self.engine.runAndWait()
            self.is_speaking = False
            
        except Exception as e:
            self.logger.error(f"Error speaking text: {e}")
            self.is_speaking = False
    
    def _enhance_text_with_personality(self, text: str) -> str:
        """Add personality touches to text for Indian-English butler character"""
        # Convert to string if not already
        text = str(text).strip()
        
        # Add personality based on content
        personality_enhancements = {
            # Greetings
            'good morning': 'Good morning, sir.',
            'good afternoon': 'Good afternoon, sir.',
            'good evening': 'Good evening, sir.',
            
            # Confirmations
            'done': 'Done, sir.',
            'completed': 'Task completed successfully.',
            'finished': 'All finished, sir.',
            
            # File operations
            'file moved': 'File relocated as requested, sir.',
            'file deleted': 'File removed from the system.',
            'folder created': 'New folder created and ready for use.',
            'files organized': 'Files organized perfectly. Much better now!',
            
            # System operations
            'opening': 'Opening that for you right away.',
            'closing': 'Closing as requested.',
            'launching': 'Launching the application now.',
            
            # Errors
            'error': 'I apologize, but there seems to be an issue.',
            'failed': 'I\'m afraid that didn\'t work as expected.',
            'not found': 'I couldn\'t locate that item, sir.',
        }
        
        # Check for personality enhancements
        text_lower = text.lower()
        for trigger, enhancement in personality_enhancements.items():
            if trigger in text_lower:
                return enhancement
        
        # Add sir/madam for politeness if it's a response
        if len(text) > 10 and not text.endswith(('.', '!', '?')):
            if not any(word in text_lower for word in ['sir', 'madam', 'hello', 'hi']):
                text += ', sir.'
        
        return text
    
    def stop_speaking(self):
        """Stop current speech and clear queue"""
        if self.engine:
            try:
                self.engine.stop()
                
                # Clear queue
                while not self.speech_queue.empty():
                    try:
                        self.speech_queue.get_nowait()
                    except queue.Empty:
                        break
                
                self.is_speaking = False
                self.logger.info("Speech stopped and queue cleared")
                
            except Exception as e:
                self.logger.error(f"Error stopping speech: {e}")
    
    def is_busy(self) -> bool:
        """Check if currently speaking"""
        return self.is_speaking or not self.speech_queue.empty()
    
    def get_available_voices(self) -> list:
        """Get list of available voices"""
        if not self.engine:
            return []
        
        try:
            voices = self.engine.getProperty('voices')
            return [(voice.id, voice.name) for voice in voices]
        except Exception as e:
            self.logger.error(f"Error getting voices: {e}")
            return []
    
    def set_voice(self, voice_id: str) -> bool:
        """Set specific voice by ID"""
        if not self.engine:
            return False
        
        try:
            self.engine.setProperty('voice', voice_id)
            self.logger.info(f"Voice changed to: {voice_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error setting voice: {e}")
            return False
    
    def set_rate(self, rate: int) -> bool:
        """Set speech rate (words per minute)"""
        if not self.engine:
            return False
        
        try:
            # Clamp rate between 50 and 300
            rate = max(50, min(300, rate))
            self.engine.setProperty('rate', rate)
            self.logger.info(f"Speech rate set to: {rate}")
            return True
        except Exception as e:
            self.logger.error(f"Error setting rate: {e}")
            return False
    
    def set_volume(self, volume: float) -> bool:
        """Set speech volume (0.0 to 1.0)"""
        if not self.engine:
            return False
        
        try:
            # Clamp volume between 0.0 and 1.0
            volume = max(0.0, min(1.0, volume))
            self.engine.setProperty('volume', volume)
            self.logger.info(f"Speech volume set to: {volume}")
            return True
        except Exception as e:
            self.logger.error(f"Error setting volume: {e}")
            return False