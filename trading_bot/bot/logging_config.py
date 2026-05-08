"""
Logging configuration for the trading bot.
Sets up both file and console handlers with structured formatting.
"""

import logging
import os
from datetime import datetime


LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configure and return the root logger with file + console handlers.

    A new timestamped log file is created per session so historical runs
    are preserved and easy to diff.
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOG_DIR, f"trading_bot_{timestamp}.log")

    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Root logger
    logger = logging.getLogger("trading_bot")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Avoid duplicate handlers if called more than once
    if logger.handlers:
        return logger

    # --- File handler (DEBUG and above – captures everything) ---
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

    # --- Console handler (INFO and above – human-friendly) ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info("Logging initialised → %s", log_file)
    return logger


def get_logger(name: str) -> logging.Logger:
    """Return a child logger scoped to *name*."""
    return logging.getLogger(f"trading_bot.{name}")
