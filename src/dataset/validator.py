import json
import shutil
from pathlib import Path
from typing import Dict, List, Any, Tuple
from PIL import Image
import cv2

from src.utils.paths import REJECTED_DATA_DIR, REPORTS_DIR, ensure_dir
from src.utils.logging import dataset_logger

MIN_DIMENSION = 32

class ImageValidator:
    """
    Validates image readability, dimensions, and format integrity.
    Quarantines corrupted or unreadable images into data/rejected/ and generates a report.
    """
    def __init__(self, rejected_dir: Path = REJECTED_DATA_DIR, report_dir: Path = REPORTS_DIR):
        self.rejected_dir = Path(rejected_dir)
        self.report_dir = Path(report_dir)

    def validate_file(self, file_path: Path) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validates a single image file.
        Returns (is_valid, error_reason, metadata_dict).
        """
        path = Path(file_path)
        if not path.is_file():
            return False, "File does not exist", {}
            
        if path.stat().st_size == 0:
            return False, "File is 0 bytes (empty)", {}

        # PIL validation
        try:
            with Image.open(path) as img:
                img.verify()  # Verifies file integrity
            # Re-open after verify to inspect dimensions & format
            with Image.open(path) as img:
                width, height = img.size
                img_format = img.format
                mode = img.mode
        except Exception as e:
            return False, f"PIL cannot read or verify image: {str(e)}", {}

        if width < MIN_DIMENSION or height < MIN_DIMENSION:
            return False, f"Resolution too low: {width}x{height} (minimum is {MIN_DIMENSION}x{MIN_DIMENSION})", {}

        # OpenCV validation
        try:
            cv_img = cv2.imread(str(path))
            if cv_img is None:
                return False, "OpenCV failed to decode image array", {}
        except Exception as e:
            return False, f"OpenCV read error: {str(e)}", {}

        meta = {
            "width": width,
            "height": height,
            "format": img_format,
            "mode": mode,
            "file_size": path.stat().st_size
        }
        return True, "", meta

    def validate_dataset(self, category_images: Dict[str, List[Path]]) -> Dict[str, Any]:
        """
        Validates all images in the category dictionary.
        Moves invalid files to data/rejected/<category>/
        Writes reports/dataset_validation.json.
        """
        ensure_dir(self.rejected_dir)
        ensure_dir(self.report_dir)

        valid_items: Dict[str, List[Dict[str, Any]]] = {}
        rejected_items: List[Dict[str, Any]] = []

        total_scanned = 0
        valid_count = 0
        rejected_count = 0

        for cat, img_paths in category_images.items():
            valid_items[cat] = []
            for path in img_paths:
                total_scanned += 1
                is_valid, reason, meta = self.validate_file(path)
                if is_valid:
                    valid_count += 1
                    valid_items[cat].append({
                        "path": path,
                        "class": cat,
                        "width": meta["width"],
                        "height": meta["height"],
                        "format": meta["format"],
                        "file_size": meta["file_size"]
                    })
                else:
                    rejected_count += 1
                    dest_cat_dir = ensure_dir(self.rejected_dir / cat)
                    dest_path = dest_cat_dir / path.name
                    # Move to rejected folder
                    try:
                        shutil.move(str(path), str(dest_path))
                        dataset_logger.warning(f"Quarantined corrupted image {path.name} to {dest_path}: {reason}")
                    except Exception as e:
                        dataset_logger.error(f"Failed to move rejected file {path}: {e}")

                    rejected_items.append({
                        "original_path": str(path),
                        "quarantined_path": str(dest_path),
                        "class": cat,
                        "reason": reason
                    })

        report = {
            "total_images": total_scanned,
            "valid_images": valid_count,
            "rejected_images": rejected_count,
            "rejected_details": rejected_items
        }

        report_path = self.report_dir / "dataset_validation.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        dataset_logger.info(f"Validation complete: {valid_count} valid, {rejected_count} rejected.")
        return {
            "valid_items": valid_items,
            "report": report
        }
