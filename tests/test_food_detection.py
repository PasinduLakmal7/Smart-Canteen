import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import numpy as np

# Mock ultralytics module in sys.modules to prevent ModuleNotFoundError when it is not installed
mock_ultralytics = MagicMock()
mock_yolo_class = MagicMock()
mock_ultralytics.YOLO = mock_yolo_class
sys.modules['ultralytics'] = mock_ultralytics

# Mock torch module
sys.modules['torch'] = MagicMock()

# Import the class under test
from src.food_detection.detector import FoodDetector

class TestFoodDetector(unittest.TestCase):
    
    def setUp(self):
        self.dummy_model_path = "models/food_detection/best.pt"

    @patch('os.path.exists')
    def test_detector_init_file_not_found(self, mock_exists):
        # Arrange
        mock_exists.return_value = False
        
        # Act & Assert
        with self.assertRaises(FileNotFoundError):
            FoodDetector("non_existent_weights.pt")

    @patch('os.path.exists')
    def test_detector_init_success(self, mock_exists):
        # Arrange
        mock_exists.return_value = True
        mock_yolo_instance = MagicMock()
        mock_yolo_instance.names = {0: "string_hoppers"}
        mock_yolo_class.return_value = mock_yolo_instance
        
        # Act
        detector = FoodDetector(self.dummy_model_path)
        
        # Assert
        self.assertEqual(detector.model_names[0], "string_hoppers")
        self.assertEqual(detector.conf_threshold, 0.25)
        self.assertEqual(detector.iou_threshold, 0.45)

    @patch('os.path.exists')
    def test_detector_detect_frame_invalid_input(self, mock_exists):
        # Arrange
        mock_exists.return_value = True
        mock_yolo_instance = MagicMock()
        mock_yolo_instance.names = {0: "string_hoppers"}
        mock_yolo_class.return_value = mock_yolo_instance
        detector = FoodDetector(self.dummy_model_path)
        
        # Act & Assert
        with self.assertRaises(ValueError):
            detector.detect_frame(None)

    @patch('os.path.exists')
    def test_detector_detect_frame_success(self, mock_exists):
        # Arrange
        mock_exists.return_value = True
        mock_yolo_instance = MagicMock()
        mock_yolo_instance.names = {0: "string_hoppers"}
        mock_yolo_class.return_value = mock_yolo_instance
        
        # Setup mock prediction return
        mock_box = MagicMock()
        mock_xyxy_element = MagicMock()
        mock_xyxy_element.tolist.return_value = [100.2, 80.5, 300.7, 400.1]
        mock_box.xyxy = [mock_xyxy_element]
        
        mock_cls_tensor = MagicMock()
        mock_cls_tensor.item.return_value = 0
        mock_box.cls = [mock_cls_tensor]
        
        mock_conf_tensor = MagicMock()
        mock_conf_tensor.item.return_value = 0.9423
        mock_box.conf = [mock_conf_tensor]
        
        mock_result = MagicMock()
        mock_result.boxes = [mock_box]
        mock_yolo_instance.predict.return_value = [mock_result]
        
        detector = FoodDetector(self.dummy_model_path)
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Act
        detections = detector.detect_frame(dummy_frame)
        
        # Assert
        self.assertEqual(len(detections), 1)
        det = detections[0]
        self.assertEqual(det["class_id"], 0)
        self.assertEqual(det["food_name"], "string_hoppers")
        self.assertEqual(det["confidence"], 0.9423)
        self.assertEqual(det["bbox"]["x1"], 100)
        self.assertEqual(det["bbox"]["y1"], 80)
        self.assertEqual(det["bbox"]["x2"], 301)
        self.assertEqual(det["bbox"]["y2"], 400)
        
        # Verify predict arguments
        mock_yolo_instance.predict.assert_called_once()
        args, kwargs = mock_yolo_instance.predict.call_args
        self.assertEqual(kwargs["conf"], 0.25)
        self.assertEqual(kwargs["iou"], 0.45)

if __name__ == '__main__':
    unittest.main()
