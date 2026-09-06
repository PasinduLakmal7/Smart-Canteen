from typing import Dict, Any, Optional

from src.dataset.scanner import DatasetScanner
from src.dataset.validator import ImageValidator
from src.dataset.deduplicator import DatasetDeduplicator
from src.dataset.annotator import DatasetAnnotator
from src.dataset.splitter import DatasetSplitter
from src.dataset.exporter import YOLOExporter
from src.dataset.manifest import ManifestManager
from src.utils.hashing import compute_dataset_fingerprint
from src.utils.logging import dataset_logger

class DatasetPipeline:
    """
    Orchestrates the complete dataset preparation pipeline:
    1. Scanner: Discovers categories and images
    2. Validator: Validates integrity and dimensions
    3. Deduplicator: Identifies duplicates
    4. Annotator: Auto-generates bounding box suggestions
    5. Manifest: Tracks state in data/manifest.json
    6. Splitter: Assigns stratified train/val/test splits
    7. Exporter: Generates YOLO label files and data.yaml
    """
    def __init__(self):
        self.scanner = DatasetScanner()
        self.validator = ImageValidator()
        self.deduplicator = DatasetDeduplicator()
        self.annotator = DatasetAnnotator()
        self.splitter = DatasetSplitter()
        self.exporter = YOLOExporter()
        self.manifest = ManifestManager()

    def run(self, auto_approve_unreviewed: bool = True) -> Dict[str, Any]:
        """
        Runs the end-to-end dataset preparation pipeline.
        
        Args:
            auto_approve_unreviewed: If True, automatically approves auto-suggested annotations
                                     so single-command training can proceed out-of-the-box.
        """
        dataset_logger.info("--- Starting Dataset Preparation Pipeline ---")

        # 1. Scan raw images
        scan_res = self.scanner.scan()
        if scan_res["total_images"] == 0:
            dataset_logger.warning("No images found in data/raw/. Please add food images into data/raw/<food_name>/ folders.")
            return {
                "success": False,
                "message": "No images found under data/raw/",
                "total_images": 0
            }

        # 2. Validate images
        val_res = self.validator.validate_dataset(scan_res["categories"])

        # 3. Deduplicate
        dedup_res = self.deduplicator.process(val_res["valid_items"])

        # 4. Generate/Load Annotations & Update Manifest
        clean_items = dedup_res["clean_items"]
        annotations_map = {}
        for item in clean_items:
            ann = self.annotator.get_or_create_annotation(item)
            if auto_approve_unreviewed and ann.get("status") == "needs_review":
                ann["status"] = "approved"
                self.annotator.save_annotation(ann)

            item["status"] = ann.get("status", "needs_review")
            annotations_map[item["id"]] = ann

            # Check if manifest already has split
            existing_item = self.manifest.get_item(item["id"])
            if existing_item and existing_item.get("split"):
                item["split"] = existing_item["split"]

        # 5. Split Dataset
        split_items = self.splitter.assign_splits(clean_items)

        # 6. Save Manifest
        image_hashes = []
        for item in split_items:
            self.manifest.set_item(item["id"], item)
            image_hashes.append(item["sha256"])

        fingerprint = compute_dataset_fingerprint(
            image_hashes=image_hashes,
            classes=scan_res["classes"],
            config_dict={"classes": scan_res["classes"]}
        )
        self.manifest.data["fingerprint"] = fingerprint
        self.manifest.save()

        # 7. Export Approved Items to YOLO
        approved_items = [it for it in split_items if it.get("status") == "approved"]
        export_res = self.exporter.export(approved_items, annotations_map)

        summary = {
            "success": True,
            "total_raw_scanned": scan_res["total_images"],
            "valid_images": val_res["report"]["valid_images"],
            "rejected_images": val_res["report"]["rejected_images"],
            "unique_images": len(clean_items),
            "approved_images": len(approved_items),
            "splits": export_res["counts"],
            "classes": scan_res["classes"],
            "data_yaml": export_res["data_yaml_path"],
            "fingerprint": fingerprint
        }

        dataset_logger.info(f"Dataset Pipeline completed successfully: {summary}")
        return summary
