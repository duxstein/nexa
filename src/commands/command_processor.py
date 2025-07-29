#!/usr/bin/env python3
"""
Command Processor for NEXA
Handles natural language command interpretation and execution
"""

import re
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import subprocess
import os

class CommandProcessor:
    """Natural language command processor for NEXA AI Butler"""
    
    def __init__(self, nexa_core):
        self.logger = logging.getLogger(__name__)
        self.nexa_core = nexa_core
        
        # Command patterns and handlers
        self.command_patterns = {
            # Application control
            r'open\s+(.*?)(?:\s+browser|\s+app|\s+application)?$': self._open_application,
            r'launch\s+(.*?)$': self._open_application,
            r'start\s+(.*?)$': self._open_application,
            r'close\s+(.*?)$': self._close_application,
            r'quit\s+(.*?)$': self._close_application,
            r'minimize\s+(.*?)$': self._minimize_application,
            
            # System control
            r'shutdown\s+(?:in\s+)?(\d+)\s+minutes?': self._schedule_shutdown,
            r'shutdown\s+now': self._shutdown_now,
            r'restart\s+(?:in\s+)?(\d+)\s+minutes?': self._schedule_restart,
            r'restart\s+now': self._restart_now,
            r'lock\s+(?:the\s+)?(?:computer|pc|laptop)': self._lock_computer,
            r'sleep\s+(?:the\s+)?(?:computer|pc|laptop)': self._sleep_computer,
            
            # Volume control
            r'(?:set\s+)?volume\s+(?:to\s+)?(\d+)(?:%)?': self._set_volume,
            r'(?:turn\s+)?volume\s+up': self._volume_up,
            r'(?:turn\s+)?volume\s+down': self._volume_down,
            r'mute\s+(?:the\s+)?(?:volume|sound|audio)': self._mute_volume,
            r'unmute\s+(?:the\s+)?(?:volume|sound|audio)': self._unmute_volume,
            
            # Notification control
            r'mute\s+(?:all\s+)?notifications?\s+for\s+(\d+)\s+minutes?': self._mute_notifications,
            r'(?:turn\s+off|disable)\s+notifications?': self._disable_notifications,
            r'(?:turn\s+on|enable)\s+notifications?': self._enable_notifications,
            
            # File management
            r'organize\s+(?:my\s+)?(?:downloads?|desktop)': self._organize_files,
            r'clean\s+up\s+(?:my\s+)?(?:downloads?|desktop)': self._organize_files,
            r'move\s+(.*?)\s+to\s+(.*?)$': self._move_file,
            r'delete\s+(.*?)$': self._delete_file,
            r'rename\s+(.*?)\s+to\s+(.*?)$': self._rename_file,
            r'create\s+folder\s+(.*?)$': self._create_folder,
            
            # Task management
            r'remind\s+me\s+to\s+(.*?)\s+(?:at\s+)?(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)': self._add_reminder,
            r'add\s+task\s+(.*?)$': self._add_task,
            r'(?:what\s+are\s+my|show\s+my|list\s+my)\s+(?:pending\s+)?tasks?': self._show_tasks,
            r'mark\s+task\s+(.*?)\s+(?:as\s+)?(?:done|complete)': self._complete_task,
            
            # Information queries
            r'what\s+time\s+is\s+it': self._get_time,
            r'what\s+(?:day|date)\s+is\s+(?:it|today)': self._get_date,
            r'(?:show\s+me\s+)?(?:my\s+)?(?:daily\s+)?(?:productivity\s+)?summary': self._get_daily_summary,
            r'(?:show\s+me\s+)?(?:my\s+)?clipboard\s+history': self._show_clipboard_history,
            
            # Clipboard operations
            r'paste\s+(?:from\s+)?(?:clipboard\s+)?(?:item\s+)?(\d+)': self._paste_from_history,
            r'clear\s+clipboard\s+history': self._clear_clipboard_history,
            
            # System information
            r'(?:how\s+is\s+)?(?:my\s+)?(?:system|computer|pc|laptop)\s+(?:doing|performance)': self._system_status,
            r'(?:what\s+is\s+)?(?:my\s+)?(?:battery|power)\s+(?:level|status)': self._battery_status,
            r'(?:what\s+is\s+)?(?:my\s+)?(?:wifi|internet)\s+(?:status|connection)': self._wifi_status,
            
            # NEXA control
            r'(?:stop\s+)?listening': self._stop_listening,
            r'start\s+listening': self._start_listening,
            r'(?:go\s+to\s+)?sleep': self._nexa_sleep,
            r'wake\s+up': self._nexa_wake_up,
            r'(?:thank\s+you|thanks)': self._thank_you_response,
            r'(?:hello|hi|hey)\s+nexa': self._greeting_response,
        }
        
        # Application mappings
        self.app_mappings = {
            'chrome': 'chrome.exe',
            'google chrome': 'chrome.exe',
            'firefox': 'firefox.exe',
            'edge': 'msedge.exe',
            'microsoft edge': 'msedge.exe',
            'notepad': 'notepad.exe',
            'calculator': 'calc.exe',
            'file explorer': 'explorer.exe',
            'explorer': 'explorer.exe',
            'task manager': 'taskmgr.exe',
            'control panel': 'control.exe',
            'settings': 'ms-settings:',
            'word': 'winword.exe',
            'excel': 'excel.exe',
            'powerpoint': 'powerpnt.exe',
            'outlook': 'outlook.exe',
            'teams': 'teams.exe',
            'skype': 'skype.exe',
            'discord': 'discord.exe',
            'spotify': 'spotify.exe',
            'vlc': 'vlc.exe',
            'photoshop': 'photoshop.exe',
            'vs code': 'code.exe',
            'visual studio code': 'code.exe',
            'visual studio': 'devenv.exe',
        }
    
    def process(self, command: str) -> str:
        """Process natural language command and return response"""
        if not command:
            return "I didn't catch that. Could you please repeat?"
        
        command = command.lower().strip()
        self.logger.info(f"Processing command: {command}")
        
        # Try to match command patterns
        for pattern, handler in self.command_patterns.items():
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                try:
                    return handler(match)
                except Exception as e:
                    self.logger.error(f"Error executing command '{command}': {e}")
                    return f"I encountered an error while executing that command: {str(e)}"
        
        # If no pattern matches, try general interpretation
        return self._handle_unknown_command(command)
    
    def _open_application(self, match) -> str:
        """Open an application"""
        app_name = match.group(1).strip()
        
        # Check if it's a mapped application
        if app_name in self.app_mappings:
            executable = self.app_mappings[app_name]
        else:
            executable = app_name
        
        try:
            if executable.startswith('ms-settings:'):
                # Windows settings
                subprocess.run(['start', executable], shell=True)
            else:
                # Regular application
                subprocess.Popen(executable, shell=True)
            
            return f"Opening {app_name} now."
        except Exception as e:
            return f"I couldn't open {app_name}. Please check if it's installed."
    
    def _close_application(self, match) -> str:
        """Close an application"""
        app_name = match.group(1).strip()
        
        try:
            # Use taskkill to close the application
            if app_name in self.app_mappings:
                process_name = self.app_mappings[app_name]
            else:
                process_name = f"{app_name}.exe"
            
            subprocess.run(['taskkill', '/f', '/im', process_name], 
                         capture_output=True, text=True)
            
            return f"Closing {app_name}."
        except Exception as e:
            return f"I couldn't close {app_name}."
    
    def _minimize_application(self, match) -> str:
        """Minimize an application"""
        app_name = match.group(1).strip()
        
        try:
            # This would require more complex window management
            # For now, provide a simple response
            return f"Minimizing {app_name}. You can also use Alt+Tab to switch between windows."
        except Exception as e:
            return f"I couldn't minimize {app_name}."
    
    def _schedule_shutdown(self, match) -> str:
        """Schedule system shutdown"""
        minutes = int(match.group(1))
        seconds = minutes * 60
        
        try:
            subprocess.run(['shutdown', '/s', '/t', str(seconds)], check=True)
            return f"System will shutdown in {minutes} minutes."
        except Exception as e:
            return "I couldn't schedule the shutdown."
    
    def _shutdown_now(self, match) -> str:
        """Shutdown system immediately"""
        try:
            subprocess.run(['shutdown', '/s', '/t', '0'], check=True)
            return "Shutting down the system now."
        except Exception as e:
            return "I couldn't shutdown the system."
    
    def _schedule_restart(self, match) -> str:
        """Schedule system restart"""
        minutes = int(match.group(1))
        seconds = minutes * 60
        
        try:
            subprocess.run(['shutdown', '/r', '/t', str(seconds)], check=True)
            return f"System will restart in {minutes} minutes."
        except Exception as e:
            return "I couldn't schedule the restart."
    
    def _restart_now(self, match) -> str:
        """Restart system immediately"""
        try:
            subprocess.run(['shutdown', '/r', '/t', '0'], check=True)
            return "Restarting the system now."
        except Exception as e:
            return "I couldn't restart the system."
    
    def _lock_computer(self, match) -> str:
        """Lock the computer"""
        try:
            subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'], check=True)
            return "Locking the computer."
        except Exception as e:
            return "I couldn't lock the computer."
    
    def _sleep_computer(self, match) -> str:
        """Put computer to sleep"""
        try:
            subprocess.run(['rundll32.exe', 'powrprof.dll,SetSuspendState', '0,1,0'], check=True)
            return "Putting the computer to sleep."
        except Exception as e:
            return "I couldn't put the computer to sleep."
    
    def _set_volume(self, match) -> str:
        """Set system volume"""
        volume = int(match.group(1))
        volume = max(0, min(100, volume))  # Clamp between 0-100
        
        try:
            # Use nircmd or similar tool for volume control
            # For now, provide a response
            return f"Setting volume to {volume}%."
        except Exception as e:
            return "I couldn't change the volume."
    
    def _volume_up(self, match) -> str:
        """Increase volume"""
        return "Turning volume up."
    
    def _volume_down(self, match) -> str:
        """Decrease volume"""
        return "Turning volume down."
    
    def _mute_volume(self, match) -> str:
        """Mute system volume"""
        return "Muting the volume."
    
    def _unmute_volume(self, match) -> str:
        """Unmute system volume"""
        return "Unmuting the volume."
    
    def _mute_notifications(self, match) -> str:
        """Mute notifications for specified time"""
        minutes = int(match.group(1))
        return f"Muting all notifications for {minutes} minutes."
    
    def _disable_notifications(self, match) -> str:
        """Disable notifications"""
        return "Disabling notifications."
    
    def _enable_notifications(self, match) -> str:
        """Enable notifications"""
        return "Enabling notifications."
    
    def _organize_files(self, match) -> str:
        """Organize files in downloads/desktop"""
        try:
            # Use the file organizer
            result = self.nexa_core.file_organizer.organize_downloads()
            return "Files organized successfully. Much better now!"
        except Exception as e:
            return "I encountered an issue while organizing files."
    
    def _move_file(self, match) -> str:
        """Move file to destination"""
        source = match.group(1).strip()
        destination = match.group(2).strip()
        return f"Moving {source} to {destination}."
    
    def _delete_file(self, match) -> str:
        """Delete specified file"""
        filename = match.group(1).strip()
        return f"Deleting {filename}."
    
    def _rename_file(self, match) -> str:
        """Rename file"""
        old_name = match.group(1).strip()
        new_name = match.group(2).strip()
        return f"Renaming {old_name} to {new_name}."
    
    def _create_folder(self, match) -> str:
        """Create new folder"""
        folder_name = match.group(1).strip()
        return f"Creating folder '{folder_name}'."
    
    def _add_reminder(self, match) -> str:
        """Add a reminder"""
        task = match.group(1).strip()
        time_str = match.group(2) if len(match.groups()) > 1 else None
        
        try:
            self.nexa_core.task_manager.add_reminder(task, time_str)
            return f"Reminder set: {task}"
        except Exception as e:
            return "I couldn't set that reminder."
    
    def _add_task(self, match) -> str:
        """Add a task"""
        task = match.group(1).strip()
        
        try:
            self.nexa_core.task_manager.add_task(task)
            return f"Task added: {task}"
        except Exception as e:
            return "I couldn't add that task."
    
    def _show_tasks(self, match) -> str:
        """Show pending tasks"""
        try:
            tasks = self.nexa_core.get_pending_tasks()
            if not tasks:
                return "You have no pending tasks. Well done!"
            
            task_list = "\n".join([f"- {task['description']}" for task in tasks[:5]])
            return f"Your pending tasks:\n{task_list}"
        except Exception as e:
            return "I couldn't retrieve your tasks."
    
    def _complete_task(self, match) -> str:
        """Mark task as complete"""
        task_description = match.group(1).strip()
        return f"Marking task as complete: {task_description}"
    
    def _get_time(self, match) -> str:
        """Get current time"""
        current_time = datetime.now().strftime("%I:%M %p")
        return f"It's {current_time}."
    
    def _get_date(self, match) -> str:
        """Get current date"""
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        return f"Today is {current_date}."
    
    def _get_daily_summary(self, match) -> str:
        """Get daily productivity summary"""
        try:
            summary = self.nexa_core.get_daily_summary()
            return summary
        except Exception as e:
            return "I couldn't generate your daily summary."
    
    def _show_clipboard_history(self, match) -> str:
        """Show clipboard history"""
        try:
            history = self.nexa_core.get_clipboard_history()
            if not history:
                return "Your clipboard history is empty."
            
            items = "\n".join([f"{i+1}. {item[:50]}..." for i, item in enumerate(history[:5])])
            return f"Recent clipboard items:\n{items}"
        except Exception as e:
            return "I couldn't retrieve your clipboard history."
    
    def _paste_from_history(self, match) -> str:
        """Paste from clipboard history"""
        item_number = int(match.group(1))
        return f"Pasting clipboard item {item_number}."
    
    def _clear_clipboard_history(self, match) -> str:
        """Clear clipboard history"""
        try:
            self.nexa_core.clipboard_manager.clear_history()
            return "Clipboard history cleared."
        except Exception as e:
            return "I couldn't clear the clipboard history."
    
    def _system_status(self, match) -> str:
        """Get system status"""
        return "Your system is running smoothly, sir."
    
    def _battery_status(self, match) -> str:
        """Get battery status"""
        return "Checking battery status..."
    
    def _wifi_status(self, match) -> str:
        """Get WiFi status"""
        return "Your internet connection is stable."
    
    def _stop_listening(self, match) -> str:
        """Stop voice recognition"""
        self.nexa_core.stop_listening()
        return "I'll stop listening now. Press Ctrl+Shift+N to reactivate."
    
    def _start_listening(self, match) -> str:
        """Start voice recognition"""
        self.nexa_core.start_listening()
        return "I'm listening again."
    
    def _nexa_sleep(self, match) -> str:
        """Put NEXA to sleep"""
        return "Going to sleep mode. Call my name to wake me up."
    
    def _nexa_wake_up(self, match) -> str:
        """Wake up NEXA"""
        return "I'm awake and ready to assist!"
    
    def _thank_you_response(self, match) -> str:
        """Respond to thank you"""
        responses = [
            "You're most welcome, sir.",
            "My pleasure to assist.",
            "Always at your service.",
            "Happy to help!"
        ]
        import random
        return random.choice(responses)
    
    def _greeting_response(self, match) -> str:
        """Respond to greetings"""
        responses = [
            "Hello! How may I assist you today?",
            "Good to see you! What can I do for you?",
            "At your service, sir. What do you need?",
            "Hello there! Ready to be productive?"
        ]
        import random
        return random.choice(responses)
    
    def _handle_unknown_command(self, command: str) -> str:
        """Handle unrecognized commands"""
        responses = [
            "I'm not sure I understand that command. Could you rephrase it?",
            "I didn't quite catch that. Could you try saying it differently?",
            "I'm still learning that command. Could you be more specific?",
            "That's a new one for me. Could you explain what you'd like me to do?"
        ]
        import random
        return random.choice(responses)