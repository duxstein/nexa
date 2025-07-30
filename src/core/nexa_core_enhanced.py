#!/usr/bin/env python3
"""
Enhanced NEXA Core - AI Butler with Machine Learning Integration
Integrates traditional command processing with AI-based command understanding
"""

import threading
import time
import queue
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Callable

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.speech.voice_recognition import VoiceRecognition
from src.speech.text_to_speech import TextToSpeech
from src.commands.command_processor import CommandProcessor
from src.training.enhanced_command_processor import EnhancedCommandProcessor
from src.file_manager.file_organizer import FileOrganizer
from src.tasks.task_manager import TaskManager
from src.system.system_controller import SystemController
from src.clipboard.clipboard_manager import ClipboardManager
from src.activity.activity_tracker import ActivityTracker
from src.utils.config import Config
from src.utils.database import Database

class NexaCoreEnhanced:
    """Enhanced NEXA AI Butler Core with ML Integration"""
    
    def __init__(self, use_ai=True):
        self.logger = logging.getLogger(__name__)
        self.config = Config('config.yaml')
        self.use_ai = use_ai
        
        # Load training configuration
        try:
            with open('training_config.json', 'r') as f:
                self.training_config = json.load(f)
        except FileNotFoundError:
            self.training_config = {"training": {"enabled": True}}
            self.logger.warning("Training config not found, using defaults")
        
        self.database = Database(self.config.get('paths', {}).get('database_file', 'nexa_data.db'))
        
        # Initialize components
        self.voice_recognition = VoiceRecognition()
        self.text_to_speech = TextToSpeech()
        
        # Choose command processor based on AI availability
        if self.use_ai and self.training_config['training']['enabled']:
            try:
                self.command_processor = EnhancedCommandProcessor()
                self.logger.info("Using AI-enhanced command processor")
            except Exception as e:
                self.logger.warning(f"AI processor failed, falling back to rules: {e}")
                self.command_processor = CommandProcessor(self)
        else:
            self.command_processor = CommandProcessor(self)
            self.logger.info("Using rule-based command processor")
        
        self.file_organizer = FileOrganizer()
        db_connection = self.database.get_connection()
        self.task_manager = TaskManager(db_connection)
        self.system_controller = SystemController()
        self.clipboard_manager = ClipboardManager()
        self.activity_tracker = ActivityTracker(db_connection)
        
        # State management
        self.is_listening = False
        self.is_active = True
        self.command_queue = queue.Queue()
        
        # Callbacks for GUI updates
        self.status_callback: Optional[Callable] = None
        self.response_callback: Optional[Callable] = None
        
        # AI training status
        self.ai_models_loaded = False
        
        # Start background services
        self._start_background_services()
        
        # Welcome message
        self._greet_user()
        
        # Initialize AI training if enabled
        if self.use_ai:
            self._initialize_ai_training()
    
    def _initialize_ai_training(self):
        """Initialize AI training components"""
        try:
            from ..training.ai_trainer import AITrainer
            self.ai_trainer = AITrainer()
            self.ai_models_loaded = len(self.ai_trainer.get_trained_models()) > 0
            
            if self.ai_models_loaded:
                self.logger.info(f"Loaded {len(self.ai_trainer.get_trained_models())} AI models")
            else:
                self.logger.info("No AI models found, consider running training")
                
        except Exception as e:
            self.logger.warning(f"Could not initialize AI training: {e}")
            self.ai_models_loaded = False
    
    def _start_background_services(self):
        """Start background services and threads"""
        # Command processing thread
        self.command_thread = threading.Thread(target=self._process_commands, daemon=True)
        self.command_thread.start()
        
        # Start activity tracking and clipboard monitoring
        self.activity_tracker.start_tracking()
        self.clipboard_manager.start_monitoring()
    
    def _greet_user(self):
        """Provide personalized greeting based on time of day"""
        current_hour = datetime.now().hour
        
        if 5 <= current_hour < 12:
            greeting = "Good morning, sir. Your AI assistant is ready with enhanced understanding."
        elif 12 <= current_hour < 17:
            greeting = "Good afternoon! My AI models are trained and ready for complex commands."
        elif 17 <= current_hour < 21:
            greeting = "Evening's here — ready to handle your requests with AI precision."
        else:
            greeting = "Working late tonight? My AI understanding is here to help."
        
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
            
            # Log command type for analysis
            processing_method = "AI" if hasattr(self.command_processor, 'use_ai') else "Rules"
            self.logger.info(f"Processing with {processing_method}: {command_text}")
            
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
    
    def train_ai_models(self, dataset_name=None, model_type="naive_bayes"):
        """Train AI models on demand"""
        if not self.use_ai:
            return "AI training is disabled"
        
        try:
            if dataset_name:
                result = self.ai_trainer.train_traditional_model(dataset_name, model_type)
                if 'error' not in result:
                    self.ai_models_loaded = True
                    return f"Trained {dataset_name} with {model_type} - Accuracy: {result['accuracy']:.2f}"
                else:
                    return f"Training failed: {result['error']}"
            else:
                # Train all datasets
                from ..training.train_nexa import train_all_models
                train_all_models()
                self.ai_models_loaded = True
                return "All AI models trained successfully"
                
        except Exception as e:
            return f"Training error: {str(e)}"
    
    def get_ai_status(self):
        """Get current AI training status"""
        if not self.use_ai:
            return {"enabled": False, "message": "AI training disabled"}
        
        try:
            models = self.ai_trainer.get_trained_models()
            return {
                "enabled": True,
                "models_loaded": len(models),
                "available_models": list(models),
                "using_ai_processor": isinstance(self.command_processor, EnhancedCommandProcessor)
            }
        except Exception as e:
            return {"enabled": True, "error": str(e)}
    
    def speak(self, text: str):
        """Convert text to speech"""
        self.text_to_speech.speak(text)
    
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
        self.logger.info("Shutting down enhanced NEXA...")
        self.is_active = False
        self.stop_listening()
        
        # Stop background services
        self.activity_tracker.stop_tracking()
        self.clipboard_manager.stop_monitoring()
        
        self.speak("Goodbye, sir. AI models saved for next time.")
        self.logger.info("Enhanced NEXA shutdown complete")