#!/usr/bin/env python3
"""
Main GUI Window for NEXA AI Butler
Floating widget with mic button and text console
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import logging
from datetime import datetime
from typing import Optional
import keyboard

class NexaMainWindow:
    """Main GUI window for NEXA AI Butler"""
    
    def __init__(self, nexa_core):
        self.nexa_core = nexa_core
        self.logger = logging.getLogger(__name__)
        
        # GUI state
        self.is_listening = False
        self.is_minimized = False
        self.theme = 'dark'  # 'light' or 'dark'
        
        # Create main window
        self.root = tk.Tk()
        self.setup_window()
        self.create_widgets()
        self.setup_hotkeys()
        
        # Connect callbacks
        self.nexa_core.set_status_callback(self.update_status)
        self.nexa_core.set_response_callback(self.add_response)
        
        self.logger.info("NEXA GUI initialized")
    
    def setup_window(self):
        """Configure main window properties"""
        self.root.title("NEXA AI Butler")
        self.root.geometry("400x600")
        self.root.resizable(True, True)
        
        # Make window stay on top initially
        self.root.attributes('-topmost', True)
        
        # Set window icon (if available)
        try:
            # You can add an icon file here
            # self.root.iconbitmap('nexa_icon.ico')
            pass
        except:
            pass
        
        # Configure window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Apply theme
        self.apply_theme()
    
    def apply_theme(self):
        """Apply dark/light theme"""
        if self.theme == 'dark':
            bg_color = '#2b2b2b'
            fg_color = '#ffffff'
            entry_bg = '#3c3c3c'
            button_bg = '#404040'
        else:
            bg_color = '#f0f0f0'
            fg_color = '#000000'
            entry_bg = '#ffffff'
            button_bg = '#e0e0e0'
        
        self.root.configure(bg=bg_color)
        
        # Store colors for widget creation
        self.colors = {
            'bg': bg_color,
            'fg': fg_color,
            'entry_bg': entry_bg,
            'button_bg': button_bg,
            'accent': '#4a9eff',
            'success': '#4caf50',
            'warning': '#ff9800',
            'error': '#f44336'
        }
    
    def create_widgets(self):
        """Create and layout GUI widgets"""
        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        self.create_header(main_frame)
        
        # Status bar
        self.create_status_bar(main_frame)
        
        # Chat/Response area
        self.create_chat_area(main_frame)
        
        # Input area
        self.create_input_area(main_frame)
        
        # Control buttons
        self.create_control_buttons(main_frame)
        
        # Quick actions
        self.create_quick_actions(main_frame)
    
    def create_header(self, parent):
        """Create header with title and controls"""
        header_frame = tk.Frame(parent, bg=self.colors['bg'])
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Title
        title_label = tk.Label(
            header_frame,
            text="NEXA AI Butler",
            font=('Arial', 16, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['accent']
        )
        title_label.pack(side=tk.LEFT)
        
        # Control buttons
        controls_frame = tk.Frame(header_frame, bg=self.colors['bg'])
        controls_frame.pack(side=tk.RIGHT)
        
        # Theme toggle
        theme_btn = tk.Button(
            controls_frame,
            text="🌙" if self.theme == 'light' else "☀️",
            command=self.toggle_theme,
            bg=self.colors['button_bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            width=3
        )
        theme_btn.pack(side=tk.RIGHT, padx=2)
        
        # Minimize button
        minimize_btn = tk.Button(
            controls_frame,
            text="−",
            command=self.minimize_window,
            bg=self.colors['button_bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            width=3
        )
        minimize_btn.pack(side=tk.RIGHT, padx=2)
        
        # Always on top toggle
        self.topmost_var = tk.BooleanVar(value=True)
        topmost_btn = tk.Checkbutton(
            controls_frame,
            text="📌",
            variable=self.topmost_var,
            command=self.toggle_topmost,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            selectcolor=self.colors['button_bg'],
            relief=tk.FLAT
        )
        topmost_btn.pack(side=tk.RIGHT, padx=2)
    
    def create_status_bar(self, parent):
        """Create status bar"""
        status_frame = tk.Frame(parent, bg=self.colors['bg'])
        status_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.status_label = tk.Label(
            status_frame,
            text="Ready",
            font=('Arial', 9),
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT)
        
        # Time display
        self.time_label = tk.Label(
            status_frame,
            text="",
            font=('Arial', 9),
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            anchor=tk.E
        )
        self.time_label.pack(side=tk.RIGHT)
        
        # Update time
        self.update_time()
    
    def create_chat_area(self, parent):
        """Create chat/response display area"""
        chat_frame = tk.LabelFrame(
            parent,
            text="Conversation",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Arial', 10, 'bold')
        )
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            height=15,
            bg=self.colors['entry_bg'],
            fg=self.colors['fg'],
            font=('Consolas', 10),
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure text tags for different message types
        self.chat_display.tag_configure('user', foreground=self.colors['accent'])
        self.chat_display.tag_configure('nexa', foreground=self.colors['success'])
        self.chat_display.tag_configure('system', foreground=self.colors['warning'])
        self.chat_display.tag_configure('error', foreground=self.colors['error'])
        
        # Welcome message
        self.add_system_message("NEXA AI Butler initialized. Ready to assist!")
    
    def create_input_area(self, parent):
        """Create text input area"""
        input_frame = tk.Frame(parent, bg=self.colors['bg'])
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Text input
        self.text_input = tk.Entry(
            input_frame,
            bg=self.colors['entry_bg'],
            fg=self.colors['fg'],
            font=('Arial', 11),
            relief=tk.FLAT,
            bd=5
        )
        self.text_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.text_input.bind('<Return>', self.send_text_command)
        self.text_input.bind('<KeyPress>', self.on_text_input)
        
        # Send button
        send_btn = tk.Button(
            input_frame,
            text="Send",
            command=self.send_text_command,
            bg=self.colors['accent'],
            fg='white',
            font=('Arial', 10, 'bold'),
            relief=tk.FLAT,
            padx=15
        )
        send_btn.pack(side=tk.RIGHT)
    
    def create_control_buttons(self, parent):
        """Create main control buttons"""
        control_frame = tk.Frame(parent, bg=self.colors['bg'])
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Voice control button (main mic button)
        self.voice_btn = tk.Button(
            control_frame,
            text="🎤 Start Listening",
            command=self.toggle_voice_recognition,
            bg=self.colors['success'],
            fg='white',
            font=('Arial', 12, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        self.voice_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Stop button
        stop_btn = tk.Button(
            control_frame,
            text="⏹️ Stop",
            command=self.stop_all,
            bg=self.colors['error'],
            fg='white',
            font=('Arial', 10, 'bold'),
            relief=tk.FLAT,
            padx=15
        )
        stop_btn.pack(side=tk.RIGHT)
    
    def create_quick_actions(self, parent):
        """Create quick action buttons"""
        actions_frame = tk.LabelFrame(
            parent,
            text="Quick Actions",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Arial', 10, 'bold')
        )
        actions_frame.pack(fill=tk.X)
        
        # Create button grid
        buttons_frame = tk.Frame(actions_frame, bg=self.colors['bg'])
        buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Quick action buttons
        quick_actions = [
            ("📋 Tasks", self.show_tasks),
            ("📁 Organize", self.organize_files),
            ("📊 Summary", self.show_summary),
            ("🕒 Time", self.show_time),
            ("📋 Clipboard", self.show_clipboard),
            ("⚙️ Settings", self.show_settings)
        ]
        
        for i, (text, command) in enumerate(quick_actions):
            btn = tk.Button(
                buttons_frame,
                text=text,
                command=command,
                bg=self.colors['button_bg'],
                fg=self.colors['fg'],
                font=('Arial', 9),
                relief=tk.FLAT,
                padx=10,
                pady=5
            )
            btn.grid(row=i//3, column=i%3, padx=2, pady=2, sticky='ew')
        
        # Configure grid weights
        for i in range(3):
            buttons_frame.columnconfigure(i, weight=1)
    
    def setup_hotkeys(self):
        """Setup global hotkeys"""
        try:
            # Ctrl+Shift+N to activate NEXA
            keyboard.add_hotkey('ctrl+shift+n', self.hotkey_activate)
            
            # Ctrl+Shift+M to toggle mic
            keyboard.add_hotkey('ctrl+shift+m', self.hotkey_toggle_mic)
            
            self.logger.info("Hotkeys registered: Ctrl+Shift+N (activate), Ctrl+Shift+M (toggle mic)")
        except Exception as e:
            self.logger.error(f"Failed to register hotkeys: {e}")
    
    def hotkey_activate(self):
        """Hotkey to activate NEXA window"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.text_input.focus_set()
    
    def hotkey_toggle_mic(self):
        """Hotkey to toggle microphone"""
        self.toggle_voice_recognition()
    
    def toggle_voice_recognition(self):
        """Toggle voice recognition on/off"""
        if self.is_listening:
            self.nexa_core.stop_listening()
            self.voice_btn.configure(
                text="🎤 Start Listening",
                bg=self.colors['success']
            )
            self.is_listening = False
            self.add_system_message("Voice recognition stopped")
        else:
            self.nexa_core.start_listening()
            self.voice_btn.configure(
                text="🔴 Listening...",
                bg=self.colors['error']
            )
            self.is_listening = True
            self.add_system_message("Voice recognition started - speak your command")
    
    def send_text_command(self, event=None):
        """Send text command to NEXA"""
        command = self.text_input.get().strip()
        if command:
            self.add_user_message(command)
            self.text_input.delete(0, tk.END)
            
            # Process command in background
            threading.Thread(
                target=self.nexa_core.process_text_command,
                args=(command,),
                daemon=True
            ).start()
    
    def on_text_input(self, event):
        """Handle text input events"""
        # You can add typing indicators or other features here
        pass
    
    def stop_all(self):
        """Stop all NEXA operations"""
        self.nexa_core.stop_listening()
        self.is_listening = False
        self.voice_btn.configure(
            text="🎤 Start Listening",
            bg=self.colors['success']
        )
        self.add_system_message("All operations stopped")
    
    def add_user_message(self, message: str):
        """Add user message to chat display"""
        timestamp = datetime.now().strftime("%H:%M")
        self.add_to_chat(f"[{timestamp}] You: {message}", 'user')
    
    def add_response(self, response: str):
        """Add NEXA response to chat display"""
        timestamp = datetime.now().strftime("%H:%M")
        self.add_to_chat(f"[{timestamp}] NEXA: {response}", 'nexa')
    
    def add_system_message(self, message: str):
        """Add system message to chat display"""
        timestamp = datetime.now().strftime("%H:%M")
        self.add_to_chat(f"[{timestamp}] System: {message}", 'system')
    
    def add_to_chat(self, message: str, tag: str = 'system'):
        """Add message to chat display"""
        self.chat_display.configure(state=tk.NORMAL)
        self.chat_display.insert(tk.END, message + "\n", tag)
        self.chat_display.configure(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def update_status(self, status: str):
        """Update status bar"""
        self.status_label.configure(text=status)
    
    def update_time(self):
        """Update time display"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.configure(text=current_time)
        self.root.after(1000, self.update_time)
    
    def toggle_theme(self):
        """Toggle between light and dark theme"""
        self.theme = 'light' if self.theme == 'dark' else 'dark'
        self.apply_theme()
        # You would need to recreate widgets or update their colors here
        # For simplicity, we'll just show a message
        self.add_system_message(f"Theme changed to {self.theme} mode")
    
    def toggle_topmost(self):
        """Toggle always on top"""
        self.root.attributes('-topmost', self.topmost_var.get())
    
    def minimize_window(self):
        """Minimize window to system tray (simplified)"""
        self.root.iconify()
        self.is_minimized = True
    
    # Quick action methods
    def show_tasks(self):
        """Show pending tasks"""
        self.nexa_core.process_text_command("show my tasks")
    
    def organize_files(self):
        """Organize files"""
        self.nexa_core.process_text_command("organize my downloads")
    
    def show_summary(self):
        """Show daily summary"""
        self.nexa_core.process_text_command("show my daily summary")
    
    def show_time(self):
        """Show current time"""
        self.nexa_core.process_text_command("what time is it")
    
    def show_clipboard(self):
        """Show clipboard history"""
        self.nexa_core.process_text_command("show my clipboard history")
    
    def show_settings(self):
        """Show settings dialog"""
        messagebox.showinfo("Settings", "Settings panel coming soon!")
    
    def on_closing(self):
        """Handle window closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit NEXA?"):
            self.nexa_core.shutdown()
            try:
                keyboard.unhook_all()
            except:
                pass
            self.root.destroy()
    
    def run(self):
        """Start the GUI main loop"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()
        except Exception as e:
            self.logger.error(f"GUI error: {e}")
            self.on_closing()