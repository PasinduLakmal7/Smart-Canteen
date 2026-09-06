import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import cv2
import numpy as np

# Ensure workspace root is in python path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils.paths import ANNOTATIONS_DIR, RAW_DATA_DIR, MANIFEST_PATH
from src.dataset.manifest import ManifestManager
from src.dataset.annotator import DatasetAnnotator
from src.utils.logging import app_logger

# State variables for mouse interaction
drawing = False
ix, iy = -1, -1
temp_box = None

def mouse_callback(event, x, y, flags, param):
    global drawing, ix, iy, temp_box
    current_data = param

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y
        temp_box = [ix, iy, ix, iy]

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            temp_box = [min(ix, x), min(iy, y), max(ix, x), max(iy, y)]

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        x1, y1 = min(ix, x), min(iy, y)
        x2, y2 = max(ix, x), max(iy, y)
        if (x2 - x1) > 10 and (y2 - y1) > 10:
            current_data["objects"].append({
                "class": current_data["class"],
                "bbox": [x1, y1, x2, y2],
                "confidence": 1.0,
                "source": "manual_review"
            })
        temp_box = None

def review_cli():
    """
    Interactive Annotation Review Tool.
    Keys:
      [A] - Approve current annotation
      [R] - Reject current annotation
      [D] - Delete all bounding boxes
      [N] or [Space] - Next image
      [P] - Previous image
      [Q] or [ESC] - Save & Exit
    """
    manifest = ManifestManager()
    annotator = DatasetAnnotator()

    ann_files = sorted(list(ANNOTATIONS_DIR.glob("*.json")))
    if not ann_files:
        print("\n[INFO] No annotation files found in data/annotations/.")
        print("Please run: python manage.py prepare-data first.\n")
        return

    print("=" * 60)
    print(" Smart Canteen - Interactive Annotation Review Tool")
    print("=" * 60)
    print(" Controls:")
    print("   [A]       : Approve annotation (status = approved)")
    print("   [R]       : Reject annotation  (status = rejected)")
    print("   [D]       : Delete all boxes on this image")
    print("   [Drag]    : Draw new bounding box with mouse")
    print("   [N]/[SPC] : Next image")
    print("   [P]       : Previous image")
    print("   [Q]/[ESC] : Save & Exit")
    print("=" * 60)

    window_name = "Annotation Review [Smart Canteen]"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 900, 700)

    idx = 0
    while 0 <= idx < len(ann_files):
        ann_path = ann_files[idx]
        with open(ann_path, "r", encoding="utf-8") as f:
            ann_data = json.load(f)

        img_path = Path(ann_data.get("image_path", ""))
        if not img_path.exists():
            idx += 1
            continue

        raw_img = cv2.imread(str(img_path))
        if raw_img is None:
            idx += 1
            continue

        cv2.setMouseCallback(window_name, mouse_callback, ann_data)

        while True:
            display_img = raw_img.copy()
            h, w = display_img.shape[:2]

            # Draw existing boxes
            status = ann_data.get("status", "needs_review")
            if status == "approved":
                color = (0, 255, 0)  # Green
            elif status == "rejected":
                color = (0, 0, 255)  # Red
            else:
                color = (0, 255, 255)  # Yellow (needs review)

            for obj in ann_data.get("objects", []):
                bbox = obj.get("bbox", [])
                if len(bbox) == 4:
                    x1, y1, x2, y2 = [int(v) for v in bbox]
                    cv2.rectangle(display_img, (x1, y1), (x2, y2), color, 2)
                    label = f"{obj.get('class', ann_data['class'])}"
                    cv2.putText(display_img, label, (x1, max(20, y1 - 8)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # Draw currently dragged temp box
            if temp_box:
                cv2.rectangle(display_img, (temp_box[0], temp_box[1]),
                              (temp_box[2], temp_box[3]), (255, 100, 0), 2)

            # Draw top overlay status bar
            overlay_h = 45
            cv2.rectangle(display_img, (0, 0), (w, overlay_h), (30, 30, 30), cv2.FILLED)
            info_text = f"[{idx+1}/{len(ann_files)}] {ann_data.get('filename')} | Class: {ann_data.get('class')} | Status: {status.upper()}"
            cv2.putText(display_img, info_text, (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            cv2.imshow(window_name, display_img)
            key = cv2.waitKey(20) & 0xFF

            if key in [ord('q'), 27]:  # Q or ESC
                annotator.save_annotation(ann_data)
                cv2.destroyAllWindows()
                print("\n[INFO] Annotation review session ended. Saved all progress.\n")
                return

            elif key == ord('a'):  # Approve
                ann_data["status"] = "approved"
                annotator.save_annotation(ann_data)
                # Update manifest
                item = manifest.get_item(ann_data["image_id"])
                if item:
                    item["status"] = "approved"
                    manifest.save()
                idx += 1
                break

            elif key == ord('r'):  # Reject
                ann_data["status"] = "rejected"
                annotator.save_annotation(ann_data)
                item = manifest.get_item(ann_data["image_id"])
                if item:
                    item["status"] = "rejected"
                    manifest.save()
                idx += 1
                break

            elif key == ord('d'):  # Delete boxes
                ann_data["objects"] = []
                annotator.save_annotation(ann_data)

            elif key in [ord('n'), 32]:  # Next or Space
                annotator.save_annotation(ann_data)
                idx += 1
                break

            elif key == ord('p'):  # Prev
                annotator.save_annotation(ann_data)
                idx = max(0, idx - 1)
                break

    cv2.destroyAllWindows()
    print("\n[SUCCESS] Reached the end of the annotation queue.\n")

if __name__ == "__main__":
    review_cli()
