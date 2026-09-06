import os
import cv2
import numpy as np
from typing import List, Dict, Any
from ultralytics import YOLO
from src.utils.logger import logger
from src.utils.helpers import load_yaml

class FoodDetector:
    """
    Core modular API component to detect food items using a trained YOLO model.
    Encapsulates all inference logic, ensuring it remains isolated from UI/business layers.
    """
    def __init__(
        self,
        model_path: str,
        conf_threshold: float = None,
        iou_threshold: float = None
    ):
        """
        Initializes the Food Detector.
        
        Args:
            model_path: Path to the trained YOLO model (.pt)
            conf_threshold: Overriding detection confidence threshold (defaults to model_config.yaml)
            iou_threshold: Overriding NMS IoU threshold (defaults to model_config.yaml)
        """
        if not os.path.exists(model_path):
            logger.error(f"YOLO model file not found at: {model_path}")
            raise FileNotFoundError(f"Model checkpoint not found at {model_path}")
            
        logger.info(f"Loading YOLO model checkpoint: {model_path}")
        self.model = YOLO(model_path)
        
        # Load configs
        try:
            model_config = load_yaml("configs/model_config.yaml").get("yolo", {})
            self.conf_threshold = conf_threshold if conf_threshold is not None else model_config.get("confidence_threshold", 0.25)
            self.iou_threshold = iou_threshold if iou_threshold is not None else model_config.get("iou_threshold", 0.45)
            logger.info(f"Model configurations loaded: Conf={self.conf_threshold}, IoU={self.iou_threshold}")
        except Exception as e:
            logger.warning(f"Could not load configs: {e}. Falling back to default thresholds.")
            self.conf_threshold = conf_threshold if conf_threshold is not None else 0.25
            self.iou_threshold = iou_threshold if iou_threshold is not None else 0.45

        # Class names map from YOLO model (pre-trained/loaded from checkpoint)
        self.model_names = self.model.names
        logger.info(f"Loaded {len(self.model_names)} class names from the checkpoint: {self.model_names}")

    def detect_frame(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detects food items in a single frame/image array (OpenCV BGR format).
        
        Args:
            frame: Numpy BGR array representing the image.
            
        Returns:
            A list of detected objects in the format:
            [
                {
                    "class_id": 0,
                    "food_name": "string_hoppers",
                    "confidence": 0.94,
                    "bbox": {
                        "x1": 120,
                        "y1": 80,
                        "x2": 500,
                        "y2": 420
                    }
                }
            ]
        """
        if frame is None:
            logger.error("Received empty frame for detection.")
            raise ValueError("Input frame cannot be None.")
            
        detections = []
        try:
            # Run prediction (verbose=False to avoid cluttering stdout during fast inference)
            results = self.model.predict(
                source=frame,
                conf=self.conf_threshold,
                iou=self.iou_threshold,
                verbose=False
            )
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # Get coordinates
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    class_id = int(box.cls[0].item())
                    confidence = float(box.conf[0].item())
                    
                    # Fetch class name (fallback to index if not in model metadata)
                    food_name = self.model_names.get(class_id, f"class_{class_id}")
                    
                    detections.append({
                        "class_id": class_id,
                        "food_name": food_name,
                        "confidence": round(confidence, 4),
                        "bbox": {
                            "x1": int(round(x1)),
                            "y1": int(round(y1)),
                            "x2": int(round(x2)),
                            "y2": int(round(y2))
                        }
                    })
        except Exception as e:
            logger.error(f"Error occurred during frame prediction: {e}")
            raise e
            
        logger.debug(f"Detected {len(detections)} items in frame.")
        return detections

    def detect_image(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Loads an image from a file path and detects food items.
        
        Args:
            image_path: Absolute or relative path to the image file.
            
        Returns:
            Structured list of detections.
        """
        if not os.path.exists(image_path):
            logger.error(f"Image not found at path: {image_path}")
            raise FileNotFoundError(f"Image not found at {image_path}")
            
        frame = cv2.imread(image_path)
        if frame is None:
            logger.error(f"Failed to load image from {image_path}. Check if file is corrupted.")
            raise ValueError(f"Invalid image file at {image_path}")
            
        return self.detect_frame(frame)
