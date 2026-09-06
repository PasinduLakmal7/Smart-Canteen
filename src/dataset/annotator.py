import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import cv2
import numpy as np

from src.utils.paths import ANNOTATIONS_DIR, ensure_dir
from src.utils.logging import dataset_logger

class DatasetAnnotator:
    """
    Manages annotation lifecycle for raw food images.
    Auto-suggests initial bounding boxes using computer vision saliency heuristics,
    assigning status='needs_review' until reviewed and approved.
    """
    def __init__(self, annotations_dir: Path = ANNOTATIONS_DIR):
        self.annotations_dir = Path(annotations_dir)
        ensure_dir(self.annotations_dir)

    def load_ground_truth_label(self, image_path: Path, class_name: str, width: int, height: int) -> Optional[List[Dict[str, Any]]]:
        """
        Checks if a companion .txt label file (YOLO box or polygon format) exists next to the image.
        Parses all objects and converts to pixel bounding boxes.
        """
        txt_path = image_path.with_suffix('.txt')
        if not txt_path.exists():
            # Fallback for cross-environment container/host path resolution
            rel_str = str(image_path).replace("/app/", "").replace("\\app\\", "").lstrip("/\\")
            cand = Path(rel_str).with_suffix('.txt')
            if cand.exists():
                txt_path = cand
            else:
                return None

        objects = []
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    tokens = line.split()
                    if len(tokens) == 5:
                        # Standard YOLO box: class xc yc w h (normalized 0..1)
                        _, xc, yc, bw, bh = map(float, tokens)
                        x1 = max(0, int((xc - bw / 2.0) * width))
                        y1 = max(0, int((yc - bh / 2.0) * height))
                        x2 = min(width, int((xc + bw / 2.0) * width))
                        y2 = min(height, int((yc + bh / 2.0) * height))
                    elif len(tokens) > 5 and len(tokens) % 2 == 1:
                        # YOLO Polygon segmentation format: class x1 y1 x2 y2 ...
                        coords = [float(v) for v in tokens[1:]]
                        xs = [coords[i] for i in range(0, len(coords), 2)]
                        ys = [coords[i] for i in range(1, len(coords), 2)]
                        x1 = max(0, int(min(xs) * width))
                        y1 = max(0, int(min(ys) * height))
                        x2 = min(width, int(max(xs) * width))
                        y2 = min(height, int(max(ys) * height))
                    else:
                        continue

                    if x2 > x1 and y2 > y1:
                        objects.append({
                            "class": class_name,
                            "bbox": [x1, y1, x2, y2],
                            "confidence": 1.0,
                            "source": "ground_truth_file"
                        })
            if objects:
                return objects
        except Exception as e:
            dataset_logger.warning(f"Failed to parse ground truth label {txt_path}: {e}")
        return None

    def suggest_bounding_box(self, image_path: Path, class_name: str, width: int, height: int) -> List[Dict[str, Any]]:
        """
        Generates bounding box. If class is 'background', returns empty list (0 labels).
        First checks for ground-truth .txt file, then falls back to edge/contour saliency,
        and finally centered plate fallback.
        """
        if class_name.lower() in ["background", "negative", "none", "natural"]:
            return []

        gt_boxes = self.load_ground_truth_label(image_path, class_name, width, height)
        if gt_boxes:
            return gt_boxes

        try:
            img = cv2.imread(str(image_path))
            if img is not None:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                blurred = cv2.GaussianBlur(gray, (5, 5), 0)
                # Otsu thresholding for dominant object foreground
                _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # Filter contours with reasonable area (at least 5% of image area)
                min_area = (width * height) * 0.05
                candidate_boxes = []
                for c in contours:
                    area = cv2.contourArea(c)
                    if area >= min_area:
                        x, y, w, h = cv2.boundingRect(c)
                        # Add a 5% margin
                        margin_x = int(w * 0.05)
                        margin_y = int(h * 0.05)
                        x1 = max(0, x - margin_x)
                        y1 = max(0, y - margin_y)
                        x2 = min(width, x + w + margin_x)
                        y2 = min(height, y + h + margin_y)
                        candidate_boxes.append([x1, y1, x2, y2])

                if candidate_boxes:
                    # Select the largest candidate bounding box
                    candidate_boxes.sort(key=lambda b: (b[2] - b[0]) * (b[3] - b[1]), reverse=True)
                    best_box = candidate_boxes[0]
                    return [{
                        "class": class_name,
                        "bbox": best_box,
                        "confidence": 0.85,
                        "source": "auto_contour"
                    }]
        except Exception as e:
            dataset_logger.debug(f"Auto-contour heuristic failed for {image_path}: {e}")

        # Standard centered plate fallback (10% padding from image edges)
        pad_x = int(width * 0.10)
        pad_y = int(height * 0.10)
        fallback_box = [pad_x, pad_y, width - pad_x, height - pad_y]
        return [{
            "class": class_name,
            "bbox": fallback_box,
            "confidence": 0.70,
            "source": "auto_center"
        }]

    def get_or_create_annotation(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieves existing annotation or creates a new suggested annotation file.
        """
        item_id = item["id"]  # SHA256
        ann_file = self.annotations_dir / f"{item_id}.json"

        if ann_file.exists():
            try:
                with open(ann_file, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                # Check if we should upgrade auto_contour with newly added ground_truth_file
                gt_boxes = self.load_ground_truth_label(Path(item["path"]), item["class"], item["width"], item["height"])
                if gt_boxes and any(obj.get("source") in ["auto_contour", "auto_center"] for obj in existing.get("objects", [])):
                    existing["objects"] = gt_boxes
                    existing["status"] = "approved"
                    self.save_annotation(existing)
                    return existing
                return existing
            except Exception as e:
                dataset_logger.error(f"Error loading existing annotation {ann_file}: {e}")

        # Create suggestion or load ground truth
        boxes = self.suggest_bounding_box(
            Path(item["path"]),
            item["class"],
            item["width"],
            item["height"]
        )

        ann_data = {
            "image_id": item_id,
            "image_path": str(item["path"]),
            "filename": item.get("filename", Path(item["path"]).name),
            "class": item["class"],
            "width": item["width"],
            "height": item["height"],
            "status": "needs_review",  # Requires user review / approval
            "objects": boxes
        }

        self.save_annotation(ann_data)
        return ann_data

    def save_annotation(self, annotation_data: Dict[str, Any]) -> None:
        """Saves annotation data to disk."""
        item_id = annotation_data["image_id"]
        ann_file = self.annotations_dir / f"{item_id}.json"
        with open(ann_file, "w", encoding="utf-8") as f:
            json.dump(annotation_data, f, indent=2)

    def approve_annotation(self, image_id: str) -> Optional[Dict[str, Any]]:
        """Sets status of an annotation to 'approved'."""
        ann_file = self.annotations_dir / f"{image_id}.json"
        if not ann_file.exists():
            return None
        with open(ann_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["status"] = "approved"
        self.save_annotation(data)
        dataset_logger.info(f"Approved annotation for {image_id}")
        return data

    def reject_annotation(self, image_id: str) -> Optional[Dict[str, Any]]:
        """Sets status of an annotation to 'rejected'."""
        ann_file = self.annotations_dir / f"{image_id}.json"
        if not ann_file.exists():
            return None
        with open(ann_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["status"] = "rejected"
        self.save_annotation(data)
        dataset_logger.info(f"Rejected annotation for {image_id}")
        return data

    def get_all_annotations(self) -> List[Dict[str, Any]]:
        """Returns all annotation records on disk."""
        records = []
        for f in self.annotations_dir.glob("*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    records.append(json.load(fp))
            except Exception:
                pass
        return records
