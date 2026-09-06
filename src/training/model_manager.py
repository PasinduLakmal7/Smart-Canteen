import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from src.utils.paths import (
    MODELS_DIR, CANDIDATES_MODEL_DIR, PRODUCTION_MODEL_DIR,
    PRODUCTION_MODEL_PATH, MODEL_REGISTRY_PATH, ensure_dir
)
from src.utils.logging import training_logger
from src.dataset.manifest import ManifestManager

class ModelManager:
    """
    Manages candidate models, versioning, and production model promotion.
    Maintains models/registry.json.
    """
    def __init__(
        self,
        registry_path: Path = MODEL_REGISTRY_PATH,
        production_model_path: Path = PRODUCTION_MODEL_PATH,
        candidates_dir: Path = CANDIDATES_MODEL_DIR
    ):
        self.registry_path = Path(registry_path)
        self.production_model_path = Path(production_model_path)
        self.candidates_dir = Path(candidates_dir)
        self.registry = self._load_registry()

    def _load_registry(self) -> Dict[str, Any]:
        ensure_dir(self.registry_path.parent)
        if self.registry_path.exists():
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                training_logger.error(f"Error loading model registry: {e}")
        return {
            "production_model": None,
            "candidates": []
        }

    def save_registry(self) -> None:
        ensure_dir(self.registry_path.parent)
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(self.registry, f, indent=2)

    def register_candidate(self, run_name: str, weights_path: Path, metrics: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Registers a new candidate model in models/candidates/ and models/registry.json.
        """
        weights_path = Path(weights_path)
        if not weights_path.exists():
            raise FileNotFoundError(f"Candidate weights not found at {weights_path}")

        candidate_id = f"cand_{run_name}"
        candidate_filename = f"{candidate_id}.pt"
        
        manifest = ManifestManager()
        classes = manifest.get_classes()
        dataset_fingerprint = manifest.data.get("fingerprint", "")

        ensure_dir(self.candidates_dir)
        target_path = self.candidates_dir / candidate_filename
        shutil.copy2(str(weights_path), str(target_path))

        candidate_record = {
            "candidate_id": candidate_id,
            "created_at": datetime.now().isoformat(),
            "source_run": run_name,
            "weights_path": str(target_path.resolve()),
            "classes": classes,
            "dataset_fingerprint": dataset_fingerprint,
            "metrics": metrics or {}
        }

        self.registry["candidates"].append(candidate_record)
        self.save_registry()

        training_logger.info(f"Registered candidate model '{candidate_id}' in {target_path}")
        return candidate_record

    def promote_candidate(self, candidate_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Promotes a candidate model to production (models/production/best.pt).
        """
        candidates = self.registry.get("candidates", [])
        if not candidates:
            raise ValueError("No candidates available in registry to promote.")

        target_cand = None
        if candidate_id:
            for c in candidates:
                if c["candidate_id"] == candidate_id:
                    target_cand = c
                    break
            if not target_cand:
                raise ValueError(f"Candidate '{candidate_id}' not found in registry.")
        else:
            target_cand = candidates[-1]

        cand_weights = Path(target_cand["weights_path"])
        if not cand_weights.exists():
            raise FileNotFoundError(f"Candidate weights missing from {cand_weights}")

        ensure_dir(self.production_model_path.parent)
        shutil.copy2(str(cand_weights), str(self.production_model_path))

        prod_record = {
            "promoted_at": datetime.now().isoformat(),
            "candidate_id": target_cand["candidate_id"],
            "source_run": target_cand.get("source_run"),
            "dataset_fingerprint": target_cand.get("dataset_fingerprint"),
            "classes": target_cand.get("classes", []),
            "metrics": target_cand.get("metrics", {}),
            "production_path": str(self.production_model_path.resolve())
        }

        self.registry["production_model"] = prod_record
        self.save_registry()

        training_logger.info(f"Promoted candidate '{target_cand['candidate_id']}' to production at {self.production_model_path}")
        return prod_record
