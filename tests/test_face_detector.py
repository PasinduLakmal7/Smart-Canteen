"""
Unit tests for FaceDetector and Image Preprocessing in Phase 4.
"""

import pytest
import numpy as np
import cv2

from src.face_recognition.detector import FaceDetector
from src.face_recognition.schemas import FaceBoundingBox, FaceDetection


def create_synthetic_face_image(width=300, height=300, num_faces=1) -> np.ndarray:
    """Helper that generates a clean synthetic test image with simple face-like features."""
    img = np.full((height, width, 3), 180, dtype=np.uint8)
    for i in range(num_faces):
        center_x = int(width * (i + 1) / (num_faces + 1))
        center_y = int(height / 2)
        # Draw face oval
        cv2.ellipse(img, (center_x, center_y), (45, 60), 0, 0, 360, (220, 200, 180), -1)
        # Eyes
        cv2.circle(img, (center_x - 18, center_y - 15), 5, (50, 40, 30), -1)
        cv2.circle(img, (center_x + 18, center_y - 15), 5, (50, 40, 30), -1)
        # Nose
        cv2.line(img, (center_x, center_y - 5), (center_x, center_y + 12), (80, 60, 50), 2)
        # Mouth
        cv2.ellipse(img, (center_x, center_y + 28), (18, 6), 0, 0, 180, (40, 30, 80), 2)
    return img


def test_face_detector_init():
    detector = FaceDetector()
    assert detector.min_face_size == 50
    assert detector.blur_threshold == 30.0


def test_face_detector_blur_calculation():
    # Sharp image
    sharp_img = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
    sharp_score = FaceDetector.calculate_blur_score(sharp_img)
    assert sharp_score > 50.0

    # Blurry image
    blurry_img = cv2.GaussianBlur(sharp_img, (25, 25), 0)
    blurry_score = FaceDetector.calculate_blur_score(blurry_img)
    assert blurry_score < sharp_score


def test_face_detector_align_and_crop():
    detector = FaceDetector()
    img = np.full((300, 300, 3), 200, dtype=np.uint8)
    det = FaceDetection(
        bbox=FaceBoundingBox(x=50, y=50, width=100, height=120),
        confidence=0.95,
        quality_score=0.9,
        is_valid=True
    )
    cropped = detector.align_and_crop(img, det, target_size=(112, 112))
    assert cropped.shape == (112, 112, 3)
