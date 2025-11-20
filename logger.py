"""
Logging Utility Module
Centralized logging configuration for the Weather Reporting System
"""

import logging
import sys
from typing import Optional
from config import Config


def setup_logger(
    name: str,
    level: Optional[str] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up and configure a logger with consistent formatting
    
    Args:
        name: Logger name (usually __name__ of the module)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs to
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    
    # Set level from config or parameter
    log_level = level or Config.LOG_LEVEL
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(Config.LOG_FORMAT)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def log_error(logger: logging.Logger, error: Exception, context: str = "") -> None:
    """
    Log an error with context information
    
    Args:
        logger: Logger instance
        error: Exception to log
        context: Additional context information
    """
    error_msg = f"{context}: {type(error).__name__}: {str(error)}" if context else f"{type(error).__name__}: {str(error)}"
    logger.error(error_msg, exc_info=True)


def log_success(logger: logging.Logger, message: str, **kwargs) -> None:
    """
    Log a success message with optional key-value pairs
    
    Args:
        logger: Logger instance
        message: Success message
        **kwargs: Additional key-value pairs to log
    """
    if kwargs:
        details = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        logger.info(f"✅ {message} | {details}")
    else:
        logger.info(f"✅ {message}")


def log_warning(logger: logging.Logger, message: str, **kwargs) -> None:
    """
    Log a warning message with optional key-value pairs
    
    Args:
        logger: Logger instance
        message: Warning message
        **kwargs: Additional key-value pairs to log
    """
    if kwargs:
        details = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        logger.warning(f"⚠️ {message} | {details}")
    else:
        logger.warning(f"⚠️ {message}")


# Export for easy importing
__all__ = ['setup_logger', 'log_error', 'log_success', 'log_warning']
