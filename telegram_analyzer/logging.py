"""
Logging module for the Telegram Analyzer package.

This module provides logging functionality for the application,
with configurable log levels and output destinations.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from telegram_analyzer import config


def setup_logging(
    log_level: str = config.LOG_LEVEL,
    log_format: str = config.LOG_FORMAT,
    log_file: Optional[str] = config.LOG_FILE
) -> logging.Logger:
    """
    Set up logging for the application.

    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: The format string for log messages
        log_file: Optional path to a log file

    Returns:
        A configured logger instance
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    # Create logger
    logger = logging.getLogger("telegram_analyzer")
    logger.setLevel(numeric_level)
    logger.handlers = []  # Clear any existing handlers

    # Create formatter
    formatter = logging.Formatter(log_format)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Create file handler if log_file is specified
    if log_file:
        # Ensure the directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Create a default logger instance
logger = setup_logging()