import os
import shutil
import yaml
from pathlib import Path
from typing import Dict, List, Any

from src.utils.paths import PROCESSED_DATA_DIR, CLASSES_CONFIG_PATH, ensure_dir
from src.utils.logging import dataset_logger

class YOLOExporter:
    """
    Exports approved dataset items into YOLO-standard folder structure:
    data/processed/
      ├── train/ (images, labels)
      ├── valid/ (images, labels)
      ├── test/  (images, labels)
      └── data.yaml
    """
    def __init__(
        self,
        processed_dir: Path = PROCESSED_DATA_DIR,
        classes_config_path: Path = CLASSES_CONFIG_PATH
    ):
        self.processed_dir = Path(processed_dir)
        self.classes_config_path = Path(classes_config_path)

    def load_class_mapping(self) -> Dict[str, int]:
        """
        Loads deterministic class-to-ID mapping from configs/classes.yaml.
        """
        if not self.classes_config_path.exists():
            raise FileNotFoundError(f"Class configuration not found at {self.classes_config_path}")

        with open(self.classes_config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        classes_list = data.get("classes", [])
        return {cls_name: idx for idx, cls_name in enumerate(classes_list)}

    def export(self, approved_items: List[Dict[str, Any]], annotations_map: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Processes approved items, converts annotations to YOLO format,
        and saves images and labels into processed splits.
        """
        class_to_id = self.load_class_mapping()
        id_to_class = {v: k for k, v in class_to_id.items()}

        # Create split folders
        splits = ["train", "valid", "test"]
        for split in splits:
            ensure_dir(self.processed_dir / split / "images")
            ensure_dir(self.processed_dir / split / "labels")

        exported_counts = {"train": 0, "valid": 0, "test": 0}

        for item in approved_items:
            split = item.get("split", "train")
            if split not in splits:
                split = "train"

            item_id = item["id"]
            is_background = (str(item.get("class", "")).lower() in ["background", "negative", "none", "natural"])
            ann = annotations_map.get(item_id, {})
            if not is_background and (not ann or not ann.get("objects")):
                continue

            img_path = Path(item["path"])
            if not img_path.exists():
                rel_str = str(item["path"]).replace("/app/", "").replace("\\app\\", "").lstrip("/\\")
                cand = Path(rel_str)
                if cand.exists():
                    img_path = cand
                else:
                    continue

            width = float(item["width"])
            height = float(item["height"])

            # 1. Generate normalized YOLO label lines
            label_lines = []
            if not is_background:
                for obj in ann.get("objects", []):
                    obj_cls = obj.get("class", item["class"])
                    if obj_cls not in class_to_id:
                        continue
                    cls_id = class_to_id[obj_cls]
                    bbox = obj.get("bbox", [])
                    if len(bbox) == 4:
                        x1, y1, x2, y2 = bbox
                        # Clamp coordinates to image boundaries
                        x1 = max(0.0, min(width, float(x1)))
                        y1 = max(0.0, min(height, float(y1)))
                        x2 = max(0.0, min(width, float(x2)))
                        y2 = max(0.0, min(height, float(y2)))

                        bw = max(1.0, x2 - x1)
                        bh = max(1.0, y2 - y1)
                        xc = x1 + bw / 2.0
                        yc = y1 + bh / 2.0

                        # Normalize to [0, 1]
                        norm_xc = max(0.0, min(1.0, xc / width))
                        norm_yc = max(0.0, min(1.0, yc / height))
                        norm_w = max(0.0, min(1.0, bw / width))
                        norm_h = max(0.0, min(1.0, bh / height))

                        label_lines.append(f"{cls_id} {norm_xc:.6f} {norm_yc:.6f} {norm_w:.6f} {norm_h:.6f}")

            if not is_background and not label_lines:
                continue

            # Standardized target image filename: <class>_<short_hash><ext>
            target_filename = f"{item['class']}_{item_id[:10]}{img_path.suffix.lower()}"
            dest_img = self.processed_dir / split / "images" / target_filename
            dest_lbl = self.processed_dir / split / "labels" / f"{Path(target_filename).stem}.txt"

            # Copy image and write label file
            try:
                shutil.copy2(str(img_path), str(dest_img))
                with open(dest_lbl, "w", encoding="utf-8") as f:
                    f.write("\n".join(label_lines) + "\n")
                exported_counts[split] += 1
            except Exception as e:
                dataset_logger.error(f"Failed to export {img_path} to {dest_img}: {e}")

        # 2. Write data.yaml (auto-detects Docker container /app path vs host path)
        if Path("/app/data/processed").exists() or Path("/app").exists():
            resolved_path = "/app/data/processed"
        else:
            resolved_path = str(self.processed_dir.resolve()).replace("\\", "/")

        data_yaml_content = {
            "path": resolved_path,
            "train": "train/images",
            "val": "valid/images",
            "test": "test/images",
            "names": id_to_class
        }

        data_yaml_path = self.processed_dir / "data.yaml"
        with open(data_yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(data_yaml_content, f, sort_keys=False)

        dataset_logger.info(
            f"Exported YOLO dataset to {self.processed_dir}: "
            f"{exported_counts['train']} train, {exported_counts['valid']} valid, {exported_counts['test']} test."
        )

        return {
            "counts": exported_counts,
            "data_yaml_path": str(data_yaml_path),
            "classes": id_to_class
        }
