import os
import sys
import yaml
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import torch

from src.utils.paths import (
    PROCESSED_DATA_DIR, FOOD_DETECTION_RUNS_DIR, TRAINING_CONFIG_PATH,
    MANIFEST_PATH, ensure_dir
)
from src.utils.logging import training_logger
from src.dataset.manifest import ManifestManager

class YOLO11Trainer:
    """
    Automated trainer for YOLO11 on the Smart Canteen food dataset.
    Features:
      - Adaptive CPU/GPU resource throttling.
      - Modes: 'smoke' (2 epochs), 'baseline' (15 epochs), 'final' (50 epochs + early stopping).
      - Interruption resume capability (--resume).
      - Dataset change fingerprint detection.
      - Standardized timestamped run outputs.
    """
    def __init__(self, config_path: Path = TRAINING_CONFIG_PATH):
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def detect_hardware(self) -> Dict[str, Any]:
        """
        Inspects CPU core count, RAM, and hardware acceleration to compute safe training defaults.
        """
        device = "cpu"
        if torch.cuda.is_available():
            device = "0"
            device_name = torch.cuda.get_device_name(0)
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = "mps"
            device_name = "Apple Silicon MPS"
        else:
            device = "cpu"
            device_name = f"CPU ({os.cpu_count() or 2} logical cores)"

        # Safe defaults
        if device == "cpu":
            batch = self.config.get("hardware", {}).get("cpu_batch_size", 4)
            workers = min(2, os.cpu_count() or 1)
        else:
            batch = self.config.get("hardware", {}).get("gpu_batch_size", 16)
            workers = min(4, os.cpu_count() or 2)

        info = {
            "device": device,
            "device_name": device_name,
            "recommended_batch": batch,
            "recommended_workers": workers
        }
        training_logger.info(f"Hardware Detected: {device_name} | Recommended Batch: {batch}, Workers: {workers}")
        return info

    def check_dataset_changes(self) -> bool:
        """
        Checks if the dataset has changed since the last training run.
        """
        manifest = ManifestManager()
        current_fp = manifest.data.get("fingerprint", "")
        if not current_fp:
            return True

        # Check last run metadata
        runs = sorted(list(FOOD_DETECTION_RUNS_DIR.glob("*/metadata.json")), reverse=True)
        if runs:
            try:
                with open(runs[0], "r", encoding="utf-8") as f:
                    last_meta = json.load(f)
                if last_meta.get("dataset_fingerprint") == current_fp:
                    training_logger.warning("Dataset fingerprint unchanged since last run. Retraining might be redundant.")
                    return False
            except Exception:
                pass
        return True

    def train(
        self,
        mode: str = "baseline",
        epochs: Optional[int] = None,
        batch: Optional[int] = None,
        imgsz: Optional[int] = None,
        resume: bool = False,
        resume_weights: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes YOLO training run.
        """
        from ultralytics import YOLO

        data_yaml = PROCESSED_DATA_DIR / "data.yaml"
        if not data_yaml.exists():
            training_logger.error(f"data.yaml not found at {data_yaml}. Run 'python manage.py prepare-data' first.")
            raise FileNotFoundError("YOLO dataset not prepared. Please run 'python manage.py prepare-data' first.")

        # Check changes
        if not resume:
            self.check_dataset_changes()

        hw_info = self.detect_hardware()
        mode_cfg = self.config.get("modes", {}).get(mode, {})

        run_epochs = epochs or mode_cfg.get("epochs", 15)
        run_batch = batch or mode_cfg.get("batch", hw_info["recommended_batch"])
        run_patience = mode_cfg.get("patience", 5)
        run_imgsz = imgsz or self.config.get("model", {}).get("imgsz", 640)
        base_weights = self.config.get("model", {}).get("base_weights", "yolo11n.pt")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_name = f"run_{mode}_{timestamp}"
        run_dir = FOOD_DETECTION_RUNS_DIR / run_name

        training_logger.info("=" * 60)
        training_logger.info(f"Starting Training: Mode='{mode}', Epochs={run_epochs}, Batch={run_batch}, Device={hw_info['device']}")
        training_logger.info(f"Run Output Directory: {run_dir}")
        training_logger.info("=" * 60)

        if resume:
            weights_to_load = resume_weights or "last.pt"
            training_logger.info(f"Resuming training from weights: {weights_to_load}")
            model = YOLO(weights_to_load)
            results = model.train(resume=True)
        else:
            model = YOLO(base_weights)
            results = model.train(
                data=str(data_yaml.resolve()).replace("\\", "/"),
                epochs=run_epochs,
                batch=run_batch,
                imgsz=run_imgsz,
                patience=run_patience,
                device=hw_info["device"],
                workers=hw_info["recommended_workers"],
                project=str(FOOD_DETECTION_RUNS_DIR.resolve()).replace("\\", "/"),
                name=run_name,
                val=self.config.get("optimizer", {}).get("val", True),
                plots=self.config.get("optimizer", {}).get("plots", True),
                save=True,
                verbose=True
            )

        # Write run metadata
        manifest = ManifestManager()
        metadata = {
            "run_name": run_name,
            "mode": mode,
            "timestamp": timestamp,
            "dataset_fingerprint": manifest.data.get("fingerprint", ""),
            "epochs_requested": run_epochs,
            "batch_size": run_batch,
            "imgsz": run_imgsz,
            "device": hw_info["device_name"],
            "base_weights": base_weights,
            "output_dir": str(run_dir)
        }

        metadata_path = run_dir / "metadata.json"
        ensure_dir(run_dir)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        training_logger.info(f"Training finished successfully. Checkpoint saved in {run_dir / 'weights'}")
        return {
            "success": True,
            "run_name": run_name,
            "run_dir": str(run_dir),
            "best_weights": str(run_dir / "weights" / "best.pt"),
            "last_weights": str(run_dir / "weights" / "last.pt")
        }
