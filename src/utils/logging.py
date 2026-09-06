import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from src.utils.paths import LOGS_DIR, ensure_dir

load_dotenv()

_LOGGERS = {}

def get_logger(name: str = "smart_canteen", log_file_name: Optional[str] = "app.log") -> logging.Logger:
    """
    Returns a configured logger that outputs structured logs to both console and a rotating file.
    """
    key = f"{name}:{log_file_name}"
    if key in _LOGGERS:
        return _LOGGERS[key]

    logger = logging.getLogger(name)
    logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
    logger.propagate = False

    # Prevent duplicate handlers
    if not logger.handlers:
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)-7s [%(name)s:%(funcName)s:%(lineno)d] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File Handler
        if log_file_name:
            ensure_dir(LOGS_DIR)
            log_file = LOGS_DIR / log_file_name
            try:
                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=10 * 1024 * 1024,  # 10MB
                    backupCount=5,
                    encoding="utf-8"
                )
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                print(f"Warning: Could not create RotatingFileHandler at {log_file}: {e}")

    _LOGGERS[key] = logger
    return logger

# Default loggers
app_logger = get_logger("app", "app.log")
dataset_logger = get_logger("dataset", "dataset.log")
training_logger = get_logger("training", "training.log")
