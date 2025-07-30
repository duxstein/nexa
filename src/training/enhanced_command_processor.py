#!/usr/bin/env python3
"""
Enhanced Command Processor with AI Integration
Combines rule-based patterns with trained ML models for better command understanding
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
from pathlib import Path

# Import the AI trainer
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.training.ai_trainer import AITrainer

class EnhancedCommandProcessor:
    """Enhanced command processor with AI capabilities"""
    
    def __init__(self, nexa_core):
        self.logger = logging.getLogger(__name__)
        self.nexa_core = nexa_core
        
        # Initialize AI trainer
        self.ai_trainer = AITrainer()
        
        # Confidence threshold for AI predictions
        self.confidence_threshold = 0.7
        
        # Command mappings for AI predictions
        self.command_mappings = {
            'open_chrome': self._open_chrome,
            'open_firefox': self._open_firefox,
            'open_edge': self._open_edge,
            'open_notepad': self._open_notepad,
            'open_calculator': self._open_calculator,
            'open_explorer': self._open_explorer,
            'open_taskmgr': self._open_taskmgr,
            'open_word': self._open_word,
            'open_excel': self._open_excel,
            'open_powerpoint': self._open_powerpoint,
            'open_outlook': self._open_outlook,
            'open_teams': self._open_teams,
            'open_vscode': self._open_vscode,
            'open_spotify': self._open_spotify,
            'open_steam': self._open_steam,
            'open_discord': self._open_discord,
            
            'set_reminder_time': self._set_reminder_time,
            'set_reminder_datetime': self._set_reminder_datetime,
            'set_reminder_relative': self._set_reminder_relative,
            'set_recurring_reminder': self._set_recurring_reminder,
            'add_task': self._add_task,
            'add_task_due': self._add_task_due,
            'add_task_priority': self._add_task_priority,
            'list_reminders': self._list_reminders,
            'list_tasks': self._list_tasks,
            'delete_reminder': self._delete_reminder,
            'delete_task': self._delete_task,
            
            'open_and_search': self._open_and_search,
            'open_and_action': self._open_and_action,
            'open_and_create': self._open_and_create,
            'open_and_play': self._open_and_play,
            'focus_mode': self._focus_mode,
            'gaming_mode': self._gaming_mode,
            'morning_routine': self._morning_routine,
            'evening_routine': self._evening_routine
        }
        
        # Fallback rule-based patterns (original patterns)
        self.fallback_patterns = {
            r'open\s+(chrome|google chrome)': self._open_chrome,
            r'open\s+(firefox|mozilla)': self._open_firefox,
            r'open\s+(edge|microsoft edge)': self._open_edge,
            r'open\s+(notepad|text editor)': self._open_notepad,
            r'open\s+(calculator|calc)': self._open_calculator,
            r'open\s+(file explorer|explorer)': self._open_explorer,
            r'open\s+(task manager)': self._open_taskmgr,
            r'open\s+(word|ms word)': self._open_word,
            r'open\s+(excel|ms excel)': self._open_excel,
            r'open\s+(powerpoint|ppt)': self._open_powerpoint,
            r'open\s+(outlook|email)': self._open_outlook,
            r'open\s+(teams|microsoft teams)': self._open_teams,
            r'open\s+(vscode|vs code|code editor)': self._open_vscode,
            r'open\s+(spotify|music player)': self._open_spotify,
            r'open\s+(steam|gaming)': self._open_steam,
            r'open\s+(discord|chat)': self._open_discord,
        }
    
    def process(self, command: str) -> str:
        """Process command using AI first, fallback to rules"""
        if not command:
            return "I didn't catch that. Could you please repeat?"
        
        command = command.lower().strip()
        self.logger.info(f"Processing enhanced command: {command}")
        
        # Try AI-based processing
        ai_result = self._process_with_ai(command)
        if ai_result:
            return ai_result
        
        # Fallback to rule-based processing
        return self._process_with_rules(command)
    
    def _process_with_ai(self, command: str) -> Optional[str]:
        """Process command using trained AI models"""
        try:
            trained_models = self.ai_trainer.get_trained_models()
            
            for model_key in trained_models:
                result = self.ai_trainer.predict_command(command, model_key)
                
                if 'error' not in result and result['confidence'] >= self.confidence_threshold:
                    predicted_command = result['predicted_command']
                    
                    if predicted_command in self.command_mappings:
                        self.logger.info(f"AI matched '{command}' -> {predicted_command} (confidence: {result['confidence']:.2f})")
                        return self.command_mappings[predicted_command](command, result)
            
            return None
            
        except Exception as e:
            self.logger.error(f"AI processing error: {e}")
            return None
    
    def _process_with_rules(self, command: str) -> str:
        """Fallback to rule-based processing"""
        for pattern, handler in self.fallback_patterns.items():
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                try:
                    return handler(command, match)
                except Exception as e:
                    self.logger.error(f"Rule-based handler error: {e}")
                    return f"I encountered an error: {str(e)}"
        
        return "I didn't understand that command. Try rephrasing or check available commands."
    
    def _open_chrome(self, command: str, context: Any = None) -> str:
        """Open Chrome browser"""
        try:
            self.nexa_core.system_controller.launch_application('chrome')
            return "Opening Chrome browser for you."
        except Exception as e:
            return f"I couldn't open Chrome: {str(e)}"
    
    def _open_firefox(self, command: str, context: Any = None) -> str:
        """Open Firefox browser"""
        try:
            self.nexa_core.system_controller.launch_application('firefox')
            return "Opening Firefox browser for you."
        except Exception as e:
            return f"I couldn't open Firefox: {str(e)}"
    
    def _open_edge(self, command: str, context: Any = None) -> str:
        """Open Edge browser"""
        try:
            self.nexa_core.system_controller.launch_application('edge')
            return "Opening Microsoft Edge for you."
        except Exception as e:
            return f"I couldn't open Edge: {str(e)}"
    
    def _open_notepad(self, command: str, context: Any = None) -> str:
        """Open Notepad"""
        try:
            self.nexa_core.system_controller.launch_application('notepad')
            return "Opening Notepad for you."
        except Exception as e:
            return f"I couldn't open Notepad: {str(e)}"
    
    def _open_calculator(self, command: str, context: Any = None) -> str:
        """Open Calculator"""
        try:
            self.nexa_core.system_controller.launch_application('calculator')
            return "Opening Calculator for you."
        except Exception as e:
            return f"I couldn't open Calculator: {str(e)}"
    
    def _open_explorer(self, command: str, context: Any = None) -> str:
        """Open File Explorer"""
        try:
            self.nexa_core.system_controller.launch_application('explorer')
            return "Opening File Explorer for you."
        except Exception as e:
            return f"I couldn't open File Explorer: {str(e)}"
    
    def _open_taskmgr(self, command: str, context: Any = None) -> str:
        """Open Task Manager"""
        try:
            self.nexa_core.system_controller.launch_application('taskmgr')
            return "Opening Task Manager for you."
        except Exception as e:
            return f"I couldn't open Task Manager: {str(e)}"
    
    def _open_word(self, command: str, context: Any = None) -> str:
        """Open Microsoft Word"""
        try:
            self.nexa_core.system_controller.launch_application('word')
            return "Opening Microsoft Word for you."
        except Exception as e:
            return f"I couldn't open Word: {str(e)}"
    
    def _open_excel(self, command: str, context: Any = None) -> str:
        """Open Microsoft Excel"""
        try:
            self.nexa_core.system_controller.launch_application('excel')
            return "Opening Microsoft Excel for you."
        except Exception as e:
            return f"I couldn't open Excel: {str(e)}"
    
    def _open_powerpoint(self, command: str, context: Any = None) -> str:
        """Open Microsoft PowerPoint"""
        try:
            self.nexa_core.system_controller.launch_application('powerpoint')
            return "Opening Microsoft PowerPoint for you."
        except Exception as e:
            return f"I couldn't open PowerPoint: {str(e)}"
    
    def _open_outlook(self, command: str, context: Any = None) -> str:
        """Open Microsoft Outlook"""
        try:
            self.nexa_core.system_controller.launch_application('outlook')
            return "Opening Microsoft Outlook for you."
        except Exception as e:
            return f"I couldn't open Outlook: {str(e)}"
    
    def _open_teams(self, command: str, context: Any = None) -> str:
        """Open Microsoft Teams"""
        try:
            self.nexa_core.system_controller.launch_application('teams')
            return "Opening Microsoft Teams for you."
        except Exception as e:
            return f"I couldn't open Teams: {str(e)}"
    
    def _open_vscode(self, command: str, context: Any = None) -> str:
        """Open Visual Studio Code"""
        try:
            self.nexa_core.system_controller.launch_application('vscode')
            return "Opening Visual Studio Code for you."
        except Exception as e:
            return f"I couldn't open VS Code: {str(e)}"
    
    def _open_spotify(self, command: str, context: Any = None) -> str:
        """Open Spotify"""
        try:
            self.nexa_core.system_controller.launch_application('spotify')
            return "Opening Spotify for you."
        except Exception as e:
            return f"I couldn't open Spotify: {str(e)}"
    
    def _open_steam(self, command: str, context: Any = None) -> str:
        """Open Steam"""
        try:
            self.nexa_core.system_controller.launch_application('steam')
            return "Opening Steam for you."
        except Exception as e:
            return f"I couldn't open Steam: {str(e)}"
    
    def _open_discord(self, command: str, context: Any = None) -> str:
        """Open Discord"""
        try:
            self.nexa_core.system_controller.launch_application('discord')
            return "Opening Discord for you."
        except Exception as e:
            return f"I couldn't open Discord: {str(e)}"
    
    def _set_reminder_time(self, command: str, context: Any = None) -> str:
        """Set reminder with specific time"""
        try:
            # Parse time from command
            import re
            time_pattern = r'(\d{1,2}(?::\d{2})?(?:\s*[ap]m)?)'
            match = re.search(time_pattern, command, re.IGNORECASE)
            
            if match:
                time_str = match.group(1)
                task = command.replace("remind me", "").replace("at " + time_str, "").strip()
                
                # Add task to task manager
                self.nexa_core.task_manager.add_task(
                    description=f"Reminder: {task}",
                    due_date=None,
                    reminder_time=time_str
                )
                
                return f"I'll remind you to {task} at {time_str}."
            
            return "I couldn't understand the time format. Please use formats like '3pm' or '15:30'."
            
        except Exception as e:
            return f"Error setting reminder: {str(e)}"
    
    def _add_task(self, command: str, context: Any = None) -> str:
        """Add a new task"""
        try:
            task = command.replace("add task", "").replace("create task", "").strip()
            self.nexa_core.task_manager.add_task(description=task)
            return f"Added task: {task}"
        except Exception as e:
            return f"Error adding task: {str(e)}"
    
    def _list_tasks(self, command: str, context: Any = None) -> str:
        """List all pending tasks"""
        try:
            tasks = self.nexa_core.task_manager.get_pending_tasks()
            if not tasks:
                return "You have no pending tasks."
            
            task_list = "Here are your pending tasks:\n"
            for i, task in enumerate(tasks, 1):
                task_list += f"{i}. {task.description}"
                if task.due_date:
                    task_list += f" (due: {task.due_date})"
                task_list += "\n"
            
            return task_list.strip()
        except Exception as e:
            return f"Error listing tasks: {str(e)}"
    
    def _open_and_search(self, command: str, context: Any = None) -> str:
        """Open app and perform search"""
        try:
            self.nexa_core.system_controller.launch_application('chrome')
            return "Opening Chrome. You can search for your query in the browser."
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _focus_mode(self, command: str, context: Any = None) -> str:
        """Enable focus mode"""
        try:
            self.nexa_core.system_controller.launch_application('spotify')
            return "Focus mode activated. I've opened Spotify for focus music."
        except Exception as e:
            return f"Error setting focus mode: {str(e)}"
    
    def _morning_routine(self, command: str, context: Any = None) -> str:
        """Execute morning routine"""
        try:
            apps = ['chrome', 'outlook', 'teams']
            for app in apps:
                self.nexa_core.system_controller.launch_application(app)
            return "Morning routine started! I've opened Chrome, Outlook, and Teams."
        except Exception as e:
            return f"Error starting morning routine: {str(e)}"
    
    def get_training_status(self) -> Dict[str, Any]:
        """Get current training status"""
        return {
            'trained_models': self.ai_trainer.get_trained_models(),
            'available_datasets': self.ai_trainer.get_available_datasets(),
            'confidence_threshold': self.confidence_threshold
        }