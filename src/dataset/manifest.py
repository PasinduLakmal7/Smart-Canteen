import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from src.utils.paths import MANIFEST_PATH, DATA_DIR, ensure_dir
from src.utils.logging import dataset_logger

class ManifestManager:
    """
    Manages the central dataset manifest (data/manifest.json).
    Maintains image states, class assignments, hashes, review statuses, and split allocations.
    """
    def __init__(self, manifest_path: Path = MANIFEST_PATH):
        self.manifest_path = Path(manifest_path)
        self.data: Dict[str, Any] = {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "fingerprint": "",
            "items": {}
        }
        self.load()

    def load(self) -> None:
        """Loads manifest from disk if it exists."""
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                dataset_logger.debug(f"Loaded manifest with {len(self.data.get('items', {}))} items.")
            except Exception as e:
                dataset_logger.error(f"Error loading manifest from {self.manifest_path}: {e}")

    def save(self) -> None:
        """Writes manifest to disk."""
        ensure_dir(self.manifest_path.parent)
        self.data["updated_at"] = datetime.now().isoformat()
        try:
            with open(self.manifest_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
            dataset_logger.debug(f"Saved manifest to {self.manifest_path}")
        except Exception as e:
            dataset_logger.error(f"Error saving manifest: {e}")
            raise e

    def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        return self.data.get("items", {}).get(item_id)

    def set_item(self, item_id: str, item_data: Dict[str, Any]) -> None:
        if "items" not in self.data:
            self.data["items"] = {}
        self.data["items"][item_id] = item_data

    def get_all_items(self) -> Dict[str, Dict[str, Any]]:
        return self.data.get("items", {})

    def get_approved_items(self) -> List[Dict[str, Any]]:
        return [
            item for item in self.data.get("items", {}).values()
            if item.get("status") == "approved"
        ]

    def remove_item(self, item_id: str) -> None:
        if item_id in self.data.get("items", {}):
            del self.data["items"][item_id]

    def get_classes(self) -> List[str]:
        classes = set()
        for item in self.data.get("items", {}).values():
            if "class" in item:
                classes.add(item["class"])
        return sorted(list(classes))
