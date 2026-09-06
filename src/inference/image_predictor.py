import os
import cv2
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

from src.utils.paths import PREDICTIONS_DIR, PRODUCTION_MODEL_PATH, ensure_dir
from src.utils.logging import app_logger
from src.inference.detector import FoodDetector

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

def draw_annotations(image: cv2.Mat, detections: List[Dict[str, Any]]) -> cv2.Mat:
    """Draws colored bounding boxes, labels, and confidence tags on image."""
    annotated = image.copy()
    colors = [
        (46, 204, 113),  # Emerald Green
        (52, 152, 219),  # Peter River Blue
        (241, 196, 15),  # Sunflower Yellow
        (230, 126, 34),  # Carrot Orange
        (155, 89, 182),  # Amethyst Purple
        (26, 188, 156),  # Turquoise
        (231, 76, 60),   # Alizarin Red
    ]

    for det in detections:
        bbox = det["bbox"]
        x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]
        food_name = det["food_name"]
        conf = det["confidence"]
        cls_id = det["class_id"]

        color = colors[cls_id % len(colors)]

        # Bounding box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 3)

        # Label tag
        label = f"{food_name.replace('_', ' ').title()} {conf:.1%}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        (tw, th), baseline = cv2.getTextSize(label, font, font_scale, thickness)

        bg_y1 = max(0, y1 - th - 10)
        bg_y2 = y1
        bg_x1 = x1
        bg_x2 = x1 + tw + 10

        cv2.rectangle(annotated, (bg_x1, bg_y1), (bg_x2, bg_y2), color, cv2.FILLED)
        cv2.putText(annotated, label, (x1 + 5, y1 - 5), font, font_scale, (255, 255, 255), thickness)

    return annotated

def predict_single_image(
    image_path: Union[str, Path],
    model_path: Optional[Union[str, Path]] = None,
    output_dir: Path = PREDICTIONS_DIR,
    conf_threshold: Optional[float] = None
) -> Dict[str, Any]:
    """
    Runs prediction on a single image and writes annotated output.
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Input image not found at {path}")

    detector = FoodDetector(model_path=model_path, conf_threshold=conf_threshold)
    raw_img = cv2.imread(str(path))
    if raw_img is None:
        raise ValueError(f"Failed to decode image from {path}")

    detections = detector.detect(raw_img)
    annotated_img = draw_annotations(raw_img, detections)

    ensure_dir(output_dir)
    out_path = output_dir / f"{path.stem}_pred{path.suffix.lower()}"
    cv2.imwrite(str(out_path), annotated_img)

    app_logger.info(f"Predicted {len(detections)} food items. Saved annotated image to: {out_path}")
    return {
        "input_image": str(path),
        "output_image": str(out_path),
        "detections": detections
    }

def predict_folder(
    folder_path: Union[str, Path],
    model_path: Optional[Union[str, Path]] = None,
    output_dir: Path = PREDICTIONS_DIR,
    conf_threshold: Optional[float] = None
) -> Dict[str, Any]:
    """
    Batch predicts all images inside a folder and writes results.csv.
    """
    folder = Path(folder_path)
    if not folder.is_dir():
        raise NotADirectoryError(f"Directory not found at {folder}")

    detector = FoodDetector(model_path=model_path, conf_threshold=conf_threshold)
    ensure_dir(output_dir)

    all_detections_records = []
    processed_count = 0

    image_files = [f for f in folder.rglob("*") if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS]

    for img_p in image_files:
        raw_img = cv2.imread(str(img_p))
        if raw_img is None:
            continue

        dets = detector.detect(raw_img)
        annotated = draw_annotations(raw_img, dets)
        out_p = output_dir / f"{img_p.stem}_pred{img_p.suffix.lower()}"
        cv2.imwrite(str(out_p), annotated)

        processed_count += 1
        for d in dets:
            all_detections_records.append({
                "filename": img_p.name,
                "relative_path": str(img_p),
                "class_id": d["class_id"],
                "food_name": d["food_name"],
                "confidence": d["confidence"],
                "x1": d["bbox"]["x1"],
                "y1": d["bbox"]["y1"],
                "x2": d["bbox"]["x2"],
                "y2": d["bbox"]["y2"],
                "output_image": str(out_p)
            })

    # Save results.csv
    csv_path = output_dir / "results.csv"
    df = pd.DataFrame(all_detections_records)
    df.to_csv(csv_path, index=False)

    app_logger.info(f"Processed {processed_count} images. Exported summary CSV to {csv_path}")
    return {
        "total_images": processed_count,
        "total_detections": len(all_detections_records),
        "results_csv": str(csv_path),
        "output_dir": str(output_dir)
    }
