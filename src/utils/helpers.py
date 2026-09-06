import os
import yaml
import torch
from typing import Any, Dict
from src.utils.logger import logger

def load_yaml(file_path: str) -> Dict[str, Any]:
    """
    Load a YAML file safely and return as dictionary.
    """
    if not os.path.exists(file_path):
        logger.error(f"YAML file not found: {file_path}")
        raise FileNotFoundError(f"YAML configuration file not found at {file_path}")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            logger.debug(f"Loaded config from {file_path}")
            return data or {}
    except Exception as e:
        logger.error(f"Error loading YAML file {file_path}: {e}")
        raise e

def ensure_dir(dir_path: str) -> str:
    """
    Ensure a directory exists, creating it if it doesn't.
    """
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
        logger.debug(f"Created directory: {dir_path}")
    return dir_path

def get_device() -> str:
    """
    Checks for available hardware acceleration and returns device name ('cuda' or 'cpu').
    """
    if torch.cuda.is_available():
        device = "cuda"
    else:
        device = "cpu"
    logger.info(f"Using device: {device} (GPU Available: {torch.cuda.is_available()})")
    return device
