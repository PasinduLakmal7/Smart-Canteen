import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO

from src.utils.paths import PRODUCTION_MODEL_PATH, APPLICATION_CONFIG_PATH
from src.utils.logging import app_logger

class FoodDetector:
    """
    Core decoupled Food Detector service.
    Encapsulates YOLO inference and returns clean structured JSON-compatible dictionaries.
    """
    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        conf_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None,
        device: Optional[str] = "cpu"
    ):
        target_model = Path(model_path) if model_path else PRODUCTION_MODEL_PATH
        if not target_model.exists():
            app_logger.error(f"Model weights not found at {target_model}")
            raise FileNotFoundError(
                f"Model checkpoint not found at {target_model}. "
                "Please train a model ('python manage.py train') and promote it ('python manage.py promote-model') first."
            )

        self.model_path = target_model
        self.conf_threshold = conf_threshold if conf_threshold is not None else 0.25
        self.iou_threshold = iou_threshold if iou_threshold is not None else 0.45
        self.device = device or "cpu"

        app_logger.info(f"Loading YOLO FoodDetector model from: {self.model_path}")
        self.model = YOLO(str(self.model_path))
        self.class_names = self.model.names
        app_logger.info(f"FoodDetector initialized with {len(self.class_names)} classes: {self.class_names}")

    def detect(
        self,
        image_input: Union[str, Path, np.ndarray, Image.Image],
        conf: Optional[float] = None,
        iou: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Runs object detection inference on an image file, OpenCV array, or PIL image.
        Returns:
            [
                {
                    "class_id": 0,
                    "food_name": "string_hoppers",
                    "confidence": 0.942,
                    "bbox": {"x1": 100, "y1": 80, "x2": 450, "y2": 380}
                }
            ]
        """
        # Convert PIL Image or path to OpenCV numpy array if needed
        if isinstance(image_input, (str, Path)):
            path = Path(image_input)
            if not path.exists():
                raise FileNotFoundError(f"Image not found at {path}")
            frame = cv2.imread(str(path))
            if frame is None:
                raise ValueError(f"Failed to read image array from {path}")
        elif isinstance(image_input, Image.Image):
            frame = cv2.cvtColor(np.array(image_input), cv2.COLOR_RGB2BGR)
        elif isinstance(image_input, np.ndarray):
            frame = image_input
        else:
            raise TypeError("Unsupported image input type. Use file path, numpy array, or PIL Image.")

        conf_thresh = conf if conf is not None else self.conf_threshold
        iou_thresh = iou if iou is not None else self.iou_threshold

        try:
            results = self.model.predict(
                source=frame,
                conf=conf_thresh,
                iou=iou_thresh,
                device=self.device,
                verbose=False
            )
        except Exception as e:
            app_logger.error(f"Inference error in FoodDetector: {e}")
            raise e

        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                xyxy = box.xyxy[0].tolist() if hasattr(box.xyxy[0], "tolist") else box.xyxy[0]
                x1, y1, x2, y2 = [int(round(float(v))) for v in xyxy]

                cls_tensor = box.cls[0]
                class_id = int(cls_tensor.item()) if hasattr(cls_tensor, "item") else int(cls_tensor)

                conf_tensor = box.conf[0]
                confidence = float(conf_tensor.item()) if hasattr(conf_tensor, "item") else float(conf_tensor)

                food_name = self.class_names.get(class_id, f"class_{class_id}")

                detections.append({
                    "class_id": class_id,
                    "food_name": food_name,
                    "confidence": round(confidence, 4),
                    "bbox": {
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2
                    }
                })

        return detections
