import os
from pathlib import Path
from typing import Union

# Project Root is the directory containing manage.py / pyproject.toml
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Standard Directory Paths
CONFIGS_DIR = PROJECT_ROOT / "configs"
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
ANNOTATIONS_DIR = DATA_DIR / "annotations"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REJECTED_DATA_DIR = DATA_DIR / "rejected"
MANIFEST_PATH = DATA_DIR / "manifest.json"

MODELS_DIR = PROJECT_ROOT / "models"
CANDIDATES_MODEL_DIR = MODELS_DIR / "candidates"
PRODUCTION_MODEL_DIR = MODELS_DIR / "production"
PRODUCTION_MODEL_PATH = PRODUCTION_MODEL_DIR / "best.pt"
MODEL_REGISTRY_PATH = MODELS_DIR / "registry.json"

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
PREDICTIONS_DIR = OUTPUTS_DIR / "predictions"
LOGS_DIR = OUTPUTS_DIR / "logs"

RUNS_DIR = PROJECT_ROOT / "runs"
FOOD_DETECTION_RUNS_DIR = RUNS_DIR / "food_detection"

REPORTS_DIR = PROJECT_ROOT / "reports"
EVALUATIONS_REPORT_DIR = REPORTS_DIR / "evaluations"

CLASSES_CONFIG_PATH = CONFIGS_DIR / "classes.yaml"
TRAINING_CONFIG_PATH = CONFIGS_DIR / "training.yaml"
APPLICATION_CONFIG_PATH = CONFIGS_DIR / "application.yaml"

# Face Data & Models (Phase 4)
FACE_DATA_DIR = DATA_DIR / "face_data"
FACE_MODELS_DIR = MODELS_DIR / "face_recognition"

# Database Paths (Phase 2, 3 & 4)
DATABASE_DIR = PROJECT_ROOT / "database"
DATABASE_PATH = DATA_DIR / "canteen_database.db"
DATABASE_SEED_DIR = DATABASE_DIR / "seed"
FOODS_SEED_PATH = DATABASE_SEED_DIR / "foods_seed.json"
EMPLOYEES_SEED_PATH = DATABASE_SEED_DIR / "employees_seed.json"
FACE_SEED_PATH = DATABASE_SEED_DIR / "face_seed.json"


def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensures that a directory exists, creating all parents if necessary."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def ensure_project_structure() -> None:
    """Creates all required project directories and .gitkeep files."""
    directories = [
        CONFIGS_DIR,
        RAW_DATA_DIR,
        ANNOTATIONS_DIR,
        PROCESSED_DATA_DIR,
        REJECTED_DATA_DIR,
        FACE_DATA_DIR,
        CANDIDATES_MODEL_DIR,
        PRODUCTION_MODEL_DIR,
        FACE_MODELS_DIR,
        PREDICTIONS_DIR,
        LOGS_DIR,
        FOOD_DETECTION_RUNS_DIR,
        REPORTS_DIR,
        EVALUATIONS_REPORT_DIR,
    ]
    for d in directories:
        ensure_dir(d)
        gitkeep = d / ".gitkeep"
        if not gitkeep.exists():
            try:
                gitkeep.touch(exist_ok=True)
            except Exception:
                pass

