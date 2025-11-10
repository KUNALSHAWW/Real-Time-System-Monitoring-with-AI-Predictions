"""
Logger setup and configuration
"""

import logging
import json
from datetime import datetime
from pythonjsonlogger import jsonlogger
from core.config import settings
import os


def setup_logging():
    """Configure structured logging"""
    
    logger = logging.getLogger("system_monitoring")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # JSON formatter for structured logging
    json_formatter = jsonlogger.JsonFormatter()
    
    # File handler
    file_handler = logging.FileHandler(settings.LOG_FILE)
    file_handler.setFormatter(json_formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(f"system_monitoring.{name}")
