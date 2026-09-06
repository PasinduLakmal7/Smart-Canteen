import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import numpy as np

# Inject mock ultralytics to sys.modules if not available
if "ultralytics" not in sys.modules:
    mock_ultralytics = MagicMock()
    mock_yolo_class = MagicMock()
    mock_ultralytics.YOLO = mock_yolo_class
    sys.modules["ultralytics"] = mock_ultralytics

from src.inference.detector import FoodDetector

class TestFoodDetectorService(unittest.TestCase):
    def setUp(self):
        self.dummy_model_path = "models/production/best.pt"

    @patch("os.path.exists")
    def test_detector_raises_on_missing_model(self, mock_exists):
        mock_exists.return_value = False
        with self.assertRaises(FileNotFoundError):
            FoodDetector("non_existent.pt")

    @patch("src.inference.detector.Path.exists")
    @patch("src.inference.detector.YOLO")
    def test_detector_output_schema_and_inference(self, mock_yolo_cls, mock_exists):
        mock_exists.return_value = True

        mock_yolo_inst = MagicMock()
        mock_yolo_inst.names = {0: "string_hoppers", 1: "kottu"}
        mock_yolo_cls.return_value = mock_yolo_inst

        # Mock predicted box return
        mock_box = MagicMock()
        mock_xyxy = MagicMock()
        mock_xyxy.tolist.return_value = [101.4, 92.1, 530.8, 410.2]
        mock_box.xyxy = [mock_xyxy]

        mock_cls = MagicMock()
        mock_cls.item.return_value = 0
        mock_box.cls = [mock_cls]

        mock_conf = MagicMock()
        mock_conf.item.return_value = 0.942
        mock_box.conf = [mock_conf]

        mock_result = MagicMock()
        mock_result.boxes = [mock_box]
        mock_yolo_inst.predict.return_value = [mock_result]

        detector = FoodDetector(self.dummy_model_path)
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)

        detections = detector.detect(dummy_frame)

        self.assertEqual(len(detections), 1)
        det = detections[0]
        self.assertEqual(det["class_id"], 0)
        self.assertEqual(det["food_name"], "string_hoppers")
        self.assertEqual(det["confidence"], 0.942)
        self.assertEqual(det["bbox"]["x1"], 101)
        self.assertEqual(det["bbox"]["y1"], 92)
        self.assertEqual(det["bbox"]["x2"], 531)
        self.assertEqual(det["bbox"]["y2"], 410)

if __name__ == "__main__":
    unittest.main()
