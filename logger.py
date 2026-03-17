"""
Structured logging configuration for the Discord bot.
Centralizes all logging setup with support for file rotation, JSON formatting,
and different log levels per module.
"""

import logging
import logging.handlers
import os
import json
from datetime import datetime
from typing import Optional
from pathlib import Path

from config import Config


class JSONFormatter(logging.Formatter):
    """Formats log records as JSON for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "guild_id"):
            log_data["guild_id"] = record.guild_id
        
        return json.dumps(log_data)


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    json_format: bool = False,
    include_file_handler: bool = True,
) -> None:
    """
    Configure logging for the entire application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        json_format: Whether to use JSON formatting for logs
        include_file_handler: Whether to write logs to files
    """
    # Validate log level
    log_level = log_level.upper()
    if log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        log_level = "INFO"
    
    numeric_level = getattr(logging, log_level)
    
    # Create logs directory
    if include_file_handler:
        Path(log_dir).mkdir(exist_ok=True)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Choose formatter
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
            datefmt="%H:%M:%S",
        )
    
    # Console handler (always)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handlers (optional)
    if include_file_handler:
        # General log file
        general_file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, "bot.log"),
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
        )
        general_file_handler.setLevel(numeric_level)
        general_file_handler.setFormatter(formatter)
        root_logger.addHandler(general_file_handler)
        
        # Error log file (only ERROR and above)
        error_file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, "error.log"),
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=3,
        )
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(formatter)
        root_logger.addHandler(error_file_handler)
    
    # Set third-party library log levels
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("discord.opus").setLevel(logging.CRITICAL)
    logging.getLogger("discord.ext.voice_recv").setLevel(logging.WARNING)
    logging.getLogger("faster_whisper").setLevel(logging.WARNING)
    
    root_logger.info("Logging configured: level=%s, file_logging=%s", log_level, include_file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class ContextFilter(logging.Filter):
    """Add context information (user_id, guild_id) to log records."""
    
    def __init__(self, user_id: Optional[int] = None, guild_id: Optional[int] = None):
        super().__init__()
        self.user_id = user_id
        self.guild_id = guild_id
    
    def filter(self, record: logging.LogRecord) -> bool:
        if self.user_id:
            record.user_id = self.user_id
        if self.guild_id:
            record.guild_id = self.guild_id
        return True
