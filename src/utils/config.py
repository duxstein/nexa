#!/usr/bin/env python3
"""
Configuration Manager for NEXA
Handles loading and accessing settings from a YAML file.
"""

import yaml
import logging
from pathlib import Path

class Config:
    """Manages loading and accessing configuration settings."""
    
    def __init__(self, config_path: str = 'config.yaml'):
        self.logger = logging.getLogger(__name__)
        self.config_path = Path(config_path)
        self.settings = self._load_config()

    def _load_config(self) -> dict:
        """Loads the configuration from the YAML file."""
        if not self.config_path.exists():
            self.logger.warning(f"Config file not found at {self.config_path}. Creating a default one.")
            self._create_default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                self.logger.info(f"Configuration loaded from {self.config_path}")
                return config_data
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            return self._get_default_settings()

    def _create_default_config(self):
        """Creates a default configuration file."""
        default_settings = self._get_default_settings()
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(default_settings, f, default_flow_style=False)
            self.logger.info(f"Default config file created at {self.config_path}")
        except Exception as e:
            self.logger.error(f"Could not create default config file: {e}")

    def get(self, key, default=None):
        """Retrieves a setting value by key."""
        return self.settings.get(key, default)

    def _get_default_settings(self) -> dict:
        """Returns the default configuration settings."""
        return {
            'gui': {
                'theme': 'dark',
                'always_on_top': True,
                'transparent_glass': False
            },
            'hotkeys': {
                'activate_nexa': 'ctrl+shift+n',
                'toggle_mic': 'ctrl+shift+m'
            },
            'user': {
                'name': 'sir'
            },
            'paths': {
                'log_directory': 'logs',
                'database_file': 'nexa_data.db'
            }
        }