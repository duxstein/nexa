#!/usr/bin/env python3
"""
Logger utility for NEXA
Provides consistent logging configuration across all components
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import sys
import os

def setup_logger(name: str = 'NEXA', level: str = 'INFO', log_dir: str = None) -> logging.Logger:
    """Setup and configure logger for NEXA
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files (default: ~/.nexa/logs)
    
    Returns:
        Configured logger instance
    """
    
    # Create log directory
    if log_dir:
        log_path = Path(log_dir)
    else:
        log_path = Path.home() / '.nexa' / 'logs'
    
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Set level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(module)s:%(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # File handler - detailed logs
    log_file = log_path / f'nexa_{datetime.now().strftime("%Y%m%d")}.log'
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Console handler - simple logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # Error file handler - errors only
    error_file = log_path / f'nexa_errors_{datetime.now().strftime("%Y%m%d")}.log'
    error_handler = logging.handlers.RotatingFileHandler(
        error_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    # Log startup message
    logger.info(f"Logger '{name}' initialized with level {level}")
    logger.info(f"Log files location: {log_path}")
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get existing logger or create new one with default settings"""
    logger = logging.getLogger(name)
    
    # If logger has no handlers, set it up with default settings
    if not logger.handlers:
        return setup_logger(name)
    
    return logger

def set_log_level(logger_name: str, level: str):
    """Change log level for existing logger"""
    logger = logging.getLogger(logger_name)
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Update console handler level
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
            handler.setLevel(numeric_level)

def cleanup_old_logs(log_dir: str = None, days: int = 30):
    """Clean up log files older than specified days"""
    try:
        if log_dir:
            log_path = Path(log_dir)
        else:
            log_path = Path.home() / '.nexa' / 'logs'
        
        if not log_path.exists():
            return
        
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        deleted_count = 0
        for log_file in log_path.glob('*.log*'):
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
                deleted_count += 1
        
        if deleted_count > 0:
            logger = get_logger('NEXA.LogCleanup')
            logger.info(f"Cleaned up {deleted_count} old log files")
            
    except Exception as e:
        logger = get_logger('NEXA.LogCleanup')
        logger.error(f"Error cleaning up old logs: {e}")

class NEXALogFilter(logging.Filter):
    """Custom log filter for NEXA components"""
    
    def __init__(self, component: str = None):
        super().__init__()
        self.component = component
    
    def filter(self, record):
        # Add component info to record
        if self.component:
            record.component = self.component
        
        # Filter out noisy third-party logs
        if record.name.startswith('urllib3'):
            return record.levelno >= logging.WARNING
        
        if record.name.startswith('requests'):
            return record.levelno >= logging.WARNING
        
        return True

class PerformanceLogger:
    """Context manager for performance logging"""
    
    def __init__(self, logger: logging.Logger, operation: str, level: int = logging.INFO):
        self.logger = logger
        self.operation = operation
        self.level = level
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.log(self.level, f"Starting {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            if exc_type:
                self.logger.error(f"{self.operation} failed after {duration:.2f}s: {exc_val}")
            else:
                self.logger.log(self.level, f"{self.operation} completed in {duration:.2f}s")

def log_function_call(logger: logging.Logger, level: int = logging.DEBUG):
    """Decorator to log function calls"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__name__}"
            logger.log(level, f"Calling {func_name}")
            try:
                result = func(*args, **kwargs)
                logger.log(level, f"{func_name} completed successfully")
                return result
            except Exception as e:
                logger.error(f"{func_name} failed: {e}")
                raise
        return wrapper
    return decorator

def log_exception(logger: logging.Logger, message: str = None):
    """Decorator to log exceptions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = message or f"Exception in {func.__name__}"
                logger.exception(f"{error_msg}: {e}")
                raise
        return wrapper
    return decorator

# Configure third-party loggers
def configure_third_party_loggers():
    """Configure third-party library loggers to reduce noise"""
    # Reduce urllib3 logging
    logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
    
    # Reduce requests logging
    logging.getLogger('requests.packages.urllib3').setLevel(logging.WARNING)
    
    # Reduce PIL logging
    logging.getLogger('PIL').setLevel(logging.WARNING)
    
    # Reduce matplotlib logging
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    
    # Reduce asyncio logging
    logging.getLogger('asyncio').setLevel(logging.WARNING)

# Initialize on import
configure_third_party_loggers()