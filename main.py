#!/usr/bin/env python3
"""
NEXA - Indian-English AI Butler
A personal productivity and workspace assistant for Windows

Author: AI Assistant
Version: 1.0.0
"""

import sys
import os
import threading
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.nexa_core import NexaCore
from src.gui.main_window import NexaMainWindow
from src.utils.logger import setup_logger

def main():
    """Main entry point for NEXA AI Butler"""
    try:
        # Setup logging
        logger = setup_logger()
        logger.info("Starting NEXA AI Butler...")
        
        # Initialize NEXA core
        nexa_core = NexaCore()
        
        # Initialize GUI
        app = NexaMainWindow(nexa_core)
        
        # Start the application
        logger.info("NEXA is ready to assist!")
        app.run()
        
    except Exception as e:
        print(f"Error starting NEXA: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()