#!/usr/bin/env python3
"""
NEXA Core - Main AI Butler Engine
Handles voice recognition, command processing, and system integration
"""

import threading
import time
import queue
import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable

from ..speech.voice_recognition import VoiceRecognition
from ..speech.text_to_speech import TextToSpeech
from ..commands.command_processor import CommandProcessor
from ..file_manager.file_organizer import FileOrganizer
from ..tasks.task_manager import TaskManager
from ..system.system_controller import SystemController
from ..clipboard.clipboard_manager import ClipboardManager
from ..activity.activity_tracker import ActivityTracker
from ..utils.config import Config
from ..utils.database import Database

class NexaCore:
    """Main NEXA AI Butler Core System"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = Config()
        self.database = Database()
        
        # Initialize components
        self.voice_recognition = VoiceRecognition()
        self.text_to_speech = TextToSpeech()
        self.command_processor = CommandProcessor(self)
        self.file_organizer = FileOrganizer()
        self.task_manager = TaskManager(self.database)
        self.system_controller = SystemController()
        self.clipboard_manager = ClipboardManager()
        self.activity_tracker = ActivityTracker(self.database)
        
        # State management
        self.is_listening = False
        self.is_active = True
        self.command_queue = queue.Queue()
        
        # Callbacks for GUI updates
        self.status_callback: Optional[Callable] = None
        self.response_callback: Optional[Callable] = None
        
        # Start background threads
        self._start_background_services()
        
        # Welcome message
        self._greet_user()
    
    def _start_background_services(self):
        """Start background services and threads"""
        # Command processing thread
        self.command_thread = threading.Thread(target=self._process_commands, daemon=True)
        self.command_thread.start()
        
        # Activity tracking thread
        self.activity_thread = threading.Thread(target=self._track_activity, daemon=True)
        self.activity_thread.start()
        
        # Clipboard monitoring thread
        self.clipboard_thread = threading.Thread(target=self._monitor_clipboard, daemon=True)
        self.clipboard_thread.start()
    
    def _greet_user(self):
        """Provide personalized greeting based on time of day"""
        current_hour = datetime.now().hour
        
        if 5 <= current_hour < 12:
            greeting = "Good morning, sir. Your laptop is fully charged and tasks await."
        elif 12 <= current_hour < 17:
            greeting = "Good afternoon! Ready to tackle the day's challenges?"
        elif 17 <= current_hour < 21:
            greeting = "Evening's here — would you like some focus music?"
        else:
            greeting = "Working late tonight? I'm here to assist you."
        
        self.speak(greeting)
        self.logger.info(f"NEXA greeted user: {greeting}")
    
    def start_listening(self):
        """Start voice recognition"""
        if not self.is_listening:
            self.is_listening = True
            self.voice_recognition.start_listening(self._on_voice_command)
            self._update_status("Listening...")
            self.logger.info("Voice recognition started")
    
    def stop_listening(self):
        """Stop voice recognition"""
        if self.is_listening:
            self.is_listening = False
            self.voice_recognition.stop_listening()
            self._update_status("Ready")
            self.logger.info("Voice recognition stopped")
    
    def process_text_command(self, command: str):
        """Process text command directly"""
        self.command_queue.put(('text', command))
        self.logger.info(f"Text command queued: {command}")
    
    def _on_voice_command(self, command: str):
        """Handle voice command from speech recognition"""
        self.command_queue.put(('voice', command))
        self.logger.info(f"Voice command queued: {command}")
    
    def _process_commands(self):
        """Background thread to process commands"""
        while self.is_active:
            try:
                if not self.command_queue.empty():
                    command_type, command_text = self.command_queue.get(timeout=1)
                    self._execute_command(command_type, command_text)
                else:
                    time.sleep(0.1)
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error processing command: {e}")
    
    def _execute_command(self, command_type: str, command_text: str):
        """Execute a command and provide response"""
        try:
            self._update_status(f"Processing: {command_text[:30]}...")
            
            # Process command
            response = self.command_processor.process(command_text)
            
            # Provide response
            if response:
                self.speak(response)
                self._update_response(response)
            
            self._update_status("Ready")
            
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            self.speak(error_msg)
            self._update_response(error_msg)
            self.logger.error(f"Command execution error: {e}")
    
    def speak(self, text: str):
        """Convert text to speech with Indian-English accent"""
        self.text_to_speech.speak(text)
    
    def _track_activity(self):
        """Background thread to track user activity"""
        while self.is_active:
            try:
                self.activity_tracker.update_current_activity()
                time.sleep(30)  # Update every 30 seconds
            except Exception as e:
                self.logger.error(f"Activity tracking error: {e}")
                time.sleep(60)
    
    def _monitor_clipboard(self):
        """Background thread to monitor clipboard changes"""
        while self.is_active:
            try:
                self.clipboard_manager.check_for_changes()
                time.sleep(1)  # Check every second
            except Exception as e:
                self.logger.error(f"Clipboard monitoring error: {e}")
                time.sleep(5)
    
    def get_daily_summary(self) -> str:
        """Get daily productivity summary"""
        return self.activity_tracker.get_daily_summary()
    
    def get_pending_tasks(self) -> List[Dict]:
        """Get pending tasks"""
        return self.task_manager.get_pending_tasks()
    
    def get_clipboard_history(self) -> List[str]:
        """Get clipboard history"""
        return self.clipboard_manager.get_history()
    
    def set_status_callback(self, callback: Callable):
        """Set callback for status updates"""
        self.status_callback = callback
    
    def set_response_callback(self, callback: Callable):
        """Set callback for response updates"""
        self.response_callback = callback
    
    def _update_status(self, status: str):
        """Update status via callback"""
        if self.status_callback:
            self.status_callback(status)
    
    def _update_response(self, response: str):
        """Update response via callback"""
        if self.response_callback:
            self.response_callback(response)
    
    def shutdown(self):
        """Shutdown NEXA gracefully"""
        self.logger.info("Shutting down NEXA...")
        self.is_active = False
        self.stop_listening()
        
        # Save any pending data
        self.activity_tracker.save_session()
        self.task_manager.save_tasks()
        
        self.speak("Goodbye, sir. Until next time.")
        self.logger.info("NEXA shutdown complete")