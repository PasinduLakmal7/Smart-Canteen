import cv2
import numpy as np
from typing import List, Dict, Any, Tuple
from src.utils.logger import logger

def draw_detections(
    image: np.ndarray,
    detections: List[Dict[str, Any]],
    color_map: Dict[str, Tuple[int, int, int]] = None
) -> np.ndarray:
    """
    Draws bounding boxes and labels on the image based on detection results.
    
    Args:
        image: Original OpenCV image (numpy array, BGR)
        detections: List of detection dictionaries:
            [{"class_id": int, "food_name": str, "confidence": float, "bbox": {"x1": int, "y1": int, "x2": int, "y2": int}}]
        color_map: Optional mapping from food_name to BGR color tuple. Default colors used if None.
        
    Returns:
        Annotated image (numpy array, BGR)
    """
    annotated_image = image.copy()
    
    # Pre-defined bright colors for bounding boxes
    default_colors = [
        (0, 255, 0),    # Green
        (255, 0, 0),    # Blue
        (0, 0, 255),    # Red
        (0, 255, 255),  # Yellow
        (255, 0, 255),  # Magenta
        (255, 255, 0),  # Cyan
    ]

    for det in detections:
        bbox = det.get("bbox", {})
        x1, y1 = int(bbox.get("x1", 0)), int(bbox.get("y1", 0))
        x2, y2 = int(bbox.get("x2", 0)), int(bbox.get("y2", 0))
        food_name = det.get("food_name", "unknown")
        confidence = det.get("confidence", 0.0)
        
        # Decide color
        if color_map and food_name in color_map:
            color = color_map[food_name]
        else:
            class_id = det.get("class_id", 0)
            color = default_colors[class_id % len(default_colors)]
            
        # Draw bounding box rectangle
        cv2.rectangle(annotated_image, (x1, y1), (x2, y2), color, 2)
        
        # Build text label
        label = f"{food_name} {confidence:.0%}"
        
        # Get text size to draw background rectangle for text readability
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 1
        (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, thickness)
        
        # Text background box coordinates
        bg_x1, bg_y1 = x1, max(0, y1 - text_height - 10)
        bg_x2, bg_y2 = x1 + text_width + 10, max(text_height, y1)
        
        # Draw background rectangle
        cv2.rectangle(annotated_image, (bg_x1, bg_y1), (bg_x2, bg_y2), color, cv2.FILLED)
        
        # Draw white text (or black depending on luminance)
        # Use white text by default
        cv2.putText(annotated_image, label, (x1 + 5, bg_y2 - 5), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
        
    logger.debug(f"Drew {len(detections)} detections on image of size {image.shape[:2]}")
    return annotated_image

def save_image(image: np.ndarray, save_path: str) -> bool:
    """
    Saves the image to the specified path.
    """
    try:
        # Ensure parent directory exists
        parent_dir = os.path.dirname(save_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
            
        success = cv2.imwrite(save_path, image)
        if success:
            logger.info(f"Image successfully saved to: {save_path}")
        else:
            logger.error(f"Failed to save image to: {save_path}")
        return success
    except Exception as e:
        logger.error(f"Error saving image to {save_path}: {e}")
        return False
