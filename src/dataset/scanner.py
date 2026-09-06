import os
import yaml
from pathlib import Path
from typing import Dict, List, Any

from src.utils.paths import RAW_DATA_DIR, CLASSES_CONFIG_PATH, ensure_dir
from src.utils.logging import dataset_logger

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

class DatasetScanner:
    """
    Scans data/raw/ directory to dynamically discover food categories and image files.
    Updates the class registry configs/classes.yaml automatically without breaking existing IDs.
    """
    def __init__(self, raw_dir: Path = RAW_DATA_DIR, classes_config_path: Path = CLASSES_CONFIG_PATH):
        self.raw_dir = Path(raw_dir)
        self.classes_config_path = Path(classes_config_path)

    def scan(self) -> Dict[str, Any]:
        """
        Scans data/raw/ and returns discovered classes and images.
        Returns:
            {
                "categories": {
                    "string_hoppers": [Path(...), Path(...)],
                    "kottu": [...]
                },
                "total_images": 120,
                "classes": ["kottu", "string_hoppers", ...]
            }
        """
        ensure_dir(self.raw_dir)
        categories: Dict[str, List[Path]] = {}
        
        # Look for category subdirectories
        for entry in self.raw_dir.iterdir():
            if entry.is_dir() and not entry.name.startswith("."):
                cat_name = entry.name.strip().lower()
                image_files = []
                for file_path in entry.rglob("*"):
                    if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                        image_files.append(file_path)
                categories[cat_name] = sorted(image_files)

        all_classes = sorted(list(categories.keys()))
        total_images = sum(len(imgs) for imgs in categories.values())
        
        dataset_logger.info(f"Scanner discovered {len(all_classes)} categories with {total_images} total images.")
        
        # Synchronize class registry in configs/classes.yaml
        if all_classes:
            self.sync_class_registry(all_classes)
            
        return {
            "categories": categories,
            "classes": all_classes,
            "total_images": total_images
        }

    def sync_class_registry(self, discovered_classes: List[str]) -> List[str]:
        """
        Ensures configs/classes.yaml contains all discovered classes.
        Preserves existing class list order, appending new classes alphabetically.
        """
        registered_classes: List[str] = []
        if self.classes_config_path.exists():
            try:
                with open(self.classes_config_path, "r", encoding="utf-8") as f:
                    content = yaml.safe_load(f) or {}
                    registered_classes = content.get("classes", [])
            except Exception as e:
                dataset_logger.warning(f"Could not read classes.yaml: {e}")

        # Add any newly discovered classes (ignoring background / negative classes)
        background_names = ["background", "natural", "negative", "none"]
        new_classes = [c for c in discovered_classes if c not in registered_classes and c.lower() not in background_names]
        if new_classes:
            registered_classes.extend(sorted(new_classes))
            ensure_dir(self.classes_config_path.parent)
            with open(self.classes_config_path, "w", encoding="utf-8") as f:
                yaml.dump({"classes": registered_classes}, f, sort_keys=False)
            dataset_logger.info(f"Updated classes.yaml with new categories: {new_classes}")
            
        return registered_classes
