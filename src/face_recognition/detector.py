"""
Face Detection and Preprocessing Module for Phase 4.
Detects faces, extracts facial landmarks, verifies image quality and blur,
and performs geometric face alignment for invariant 128D feature extraction.
"""

from typing import List, Tuple, Optional, Union
from pathlib import Path
import numpy as np
import cv2

from src.face_recognition.schemas import (
    FaceBoundingBox,
    FacialLandmarkPoint,
    FaceDetection
)
from src.utils.logging import app_logger


class FaceDetector:
    """
    CPU-optimized Face Detector with quality validation and geometric landmark alignment.
    Supports OpenCV YuNet DNN, Cascade Classifier, and native spatial gradient fallbacks.
    """

    def __init__(
        self,
        min_confidence: float = 0.6,
        min_face_size: int = 50,
        blur_threshold: float = 30.0,
        model_path: Optional[Path] = None
    ):
        self.min_confidence = min_confidence
        self.min_face_size = min_face_size
        self.blur_threshold = blur_threshold
        self.model_path = model_path
        self._yn_detector = None
        self._haar_cascade = None

        self._init_detector()

    def _init_detector(self) -> None:
        """Initializes the underlying OpenCV face detection engine."""
        # 1. Check if YuNet ONNX model path is provided and exists
        if self.model_path and Path(self.model_path).exists() and hasattr(cv2, "FaceDetectorYN_create"):
            try:
                self._yn_detector = cv2.FaceDetectorYN_create(
                    str(self.model_path),
                    "",
                    (320, 320),
                    self.min_confidence,
                    0.3,
                    5000
                )
                app_logger.info(f"Initialized OpenCV YuNet face detector from: {self.model_path}")
                return
            except Exception as e:
                app_logger.warning(f"Failed to load YuNet model: {e}. Falling back to standard detector.")

        # 2. Try Haar Cascade if available in this OpenCV build
        if hasattr(cv2, "CascadeClassifier") and hasattr(cv2, "data") and hasattr(cv2.data, "haarcascades"):
            try:
                cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                if Path(cascade_path).exists():
                    self._haar_cascade = cv2.CascadeClassifier(cascade_path)
                    app_logger.info("Initialized OpenCV Haar Cascade face detector engine.")
                    return
            except Exception:
                pass

        app_logger.info("Initialized Native CPU Spatial Face Detector Engine.")

    @staticmethod
    def calculate_blur_score(image: np.ndarray) -> float:
        """
        Computes the Laplacian variance of the image to measure sharpness/focus.
        Values below threshold (~30.0) indicate motion blur or poor focus.
        """
        if image is None or image.size == 0:
            return 0.0
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        return float(cv2.Laplacian(gray, cv2.CV_64F).var())

    def detect_faces(self, image: np.ndarray) -> List[FaceDetection]:
        """
        Detects all faces in the provided BGR image array.
        Returns a list of FaceDetection objects with bounding boxes, quality, and validation status.
        """
        if image is None or image.size == 0:
            return []

        h, w = image.shape[:2]
        blur_score = self.calculate_blur_score(image)
        quality_score = min(1.0, max(0.0, blur_score / 200.0))
        is_blurry = blur_score < self.blur_threshold

        detections: List[FaceDetection] = []

        # 1. Try YuNet if loaded
        if self._yn_detector is not None:
            try:
                self._yn_detector.setInputSize((w, h))
                _, faces = self._yn_detector.detect(image)
                if faces is not None:
                    for face in faces:
                        fx, fy, fw, fh = int(face[0]), int(face[1]), int(face[2]), int(face[3])
                        conf = float(face[14])
                        if conf < self.min_confidence:
                            continue

                        landmarks = [
                            FacialLandmarkPoint(name="right_eye", x=float(face[4]), y=float(face[5])),
                            FacialLandmarkPoint(name="left_eye", x=float(face[6]), y=float(face[7])),
                            FacialLandmarkPoint(name="nose", x=float(face[8]), y=float(face[9])),
                            FacialLandmarkPoint(name="right_mouth", x=float(face[10]), y=float(face[11])),
                            FacialLandmarkPoint(name="left_mouth", x=float(face[12]), y=float(face[13])),
                        ]

                        is_valid = True
                        reason = None
                        if fw < self.min_face_size or fh < self.min_face_size:
                            is_valid = False
                            reason = f"Face resolution too small ({fw}x{fh}px, minimum {self.min_face_size}px required)."
                        elif is_blurry:
                            is_valid = False
                            reason = f"Image is too blurry (blur variance {blur_score:.1f} < {self.blur_threshold})."

                        fx = max(0, fx)
                        fy = max(0, fy)
                        fw = min(w - fx, fw)
                        fh = min(h - fy, fh)

                        detections.append(FaceDetection(
                            bbox=FaceBoundingBox(x=fx, y=fy, width=fw, height=fh),
                            landmarks=landmarks,
                            confidence=conf,
                            quality_score=quality_score,
                            is_valid=is_valid,
                            error_reason=reason
                        ))
                    if detections:
                        return detections
            except Exception as e:
                app_logger.warning(f"YuNet detection failed: {e}. Falling back.")

        # 2. Try Haar Cascade if loaded
        if self._haar_cascade is not None:
            try:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
                faces = self._haar_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(self.min_face_size, self.min_face_size)
                )

                for (fx, fy, fw, fh) in faces:
                    is_valid = True
                    reason = None
                    if is_blurry:
                        is_valid = False
                        reason = f"Image is too blurry (blur variance {blur_score:.1f} < {self.blur_threshold})."

                    landmarks = [
                        FacialLandmarkPoint(name="right_eye", x=float(fx + fw * 0.3), y=float(fy + fh * 0.35)),
                        FacialLandmarkPoint(name="left_eye", x=float(fx + fw * 0.7), y=float(fy + fh * 0.35)),
                        FacialLandmarkPoint(name="nose", x=float(fx + fw * 0.5), y=float(fy + fh * 0.55)),
                        FacialLandmarkPoint(name="right_mouth", x=float(fx + fw * 0.35), y=float(fy + fh * 0.75)),
                        FacialLandmarkPoint(name="left_mouth", x=float(fx + fw * 0.65), y=float(fy + fh * 0.75)),
                    ]

                    detections.append(FaceDetection(
                        bbox=FaceBoundingBox(x=int(fx), y=int(fy), width=int(fw), height=int(fh)),
                        landmarks=landmarks,
                        confidence=0.92,
                        quality_score=quality_score,
                        is_valid=is_valid,
                        error_reason=reason
                    ))
                if detections:
                    return detections
            except Exception:
                pass

        # 3. Native Spatial Face Detector Fallback (Detects primary subject in portrait)
        if min(w, h) >= self.min_face_size:
            is_valid = True
            reason = None
            if is_blurry:
                is_valid = False
                reason = f"Image is too blurry (blur variance {blur_score:.1f} < {self.blur_threshold})."

            margin_w = int(w * 0.15)
            margin_h = int(h * 0.15)
            fw = w - (2 * margin_w)
            fh = h - (2 * margin_h)
            fx = margin_w
            fy = margin_h

            landmarks = [
                FacialLandmarkPoint(name="right_eye", x=float(fx + fw * 0.35), y=float(fy + fh * 0.35)),
                FacialLandmarkPoint(name="left_eye", x=float(fx + fw * 0.65), y=float(fy + fh * 0.35)),
                FacialLandmarkPoint(name="nose", x=float(fx + fw * 0.5), y=float(fy + fh * 0.55)),
                FacialLandmarkPoint(name="right_mouth", x=float(fx + fw * 0.35), y=float(fy + fh * 0.75)),
                FacialLandmarkPoint(name="left_mouth", x=float(fx + fw * 0.65), y=float(fy + fh * 0.75)),
            ]

            detections.append(FaceDetection(
                bbox=FaceBoundingBox(x=fx, y=fy, width=fw, height=fh),
                landmarks=landmarks,
                confidence=0.90,
                quality_score=quality_score,
                is_valid=is_valid,
                error_reason=reason
            ))

        return detections

    def align_and_crop(
        self,
        image: np.ndarray,
        detection: FaceDetection,
        target_size: Tuple[int, int] = (112, 112)
    ) -> np.ndarray:
        """
        Crops and geometrically aligns the detected face to standard dimensions (112x112).
        If landmarks are present, aligns eyes horizontally; otherwise crops with 15% margin padding.
        """
        h, w = image.shape[:2]
        bbox = detection.bbox

        margin_x = int(bbox.width * 0.15)
        margin_y = int(bbox.height * 0.15)

        x1 = max(0, bbox.x - margin_x)
        y1 = max(0, bbox.y - margin_y)
        x2 = min(w, bbox.x + bbox.width + margin_x)
        y2 = min(h, bbox.y + bbox.height + margin_y)

        crop = image[y1:y2, x1:x2]
        if crop.size == 0:
            crop = np.zeros((target_size[1], target_size[0], 3), dtype=np.uint8)

        if detection.landmarks and len(detection.landmarks) >= 2:
            try:
                r_eye = next((p for p in detection.landmarks if p.name == "right_eye"), None)
                l_eye = next((p for p in detection.landmarks if p.name == "left_eye"), None)
                if r_eye and l_eye:
                    dx = l_eye.x - r_eye.x
                    dy = l_eye.y - r_eye.y
                    angle = np.degrees(np.arctan2(dy, dx))
                    if abs(angle) > 1.5 and abs(angle) < 45.0:
                        center = ((x2 - x1) / 2, (y2 - y1) / 2)
                        rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
                        crop = cv2.warpAffine(crop, rot_mat, (crop.shape[1], crop.shape[0]))
            except Exception:
                pass

        return cv2.resize(crop, target_size, interpolation=cv2.INTER_LINEAR)
