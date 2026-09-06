"""
Smart Canteen Phase 4: Biometric Face Recognition Subsystem
Provides modular face detection, 128D metric embedding extraction,
vector cosine matching, database persistence, and profile integration.
"""

from src.face_recognition.schemas import (
    FaceBoundingBox,
    FaceDetection,
    FaceRegisterRequest,
    FaceRegisterResponse,
    FaceRecognizeResponse,
    EnrolledEmployeeSummary,
    ThresholdEvaluationReport
)

__all__ = [
    "FaceBoundingBox",
    "FaceDetection",
    "FaceRegisterRequest",
    "FaceRegisterResponse",
    "FaceRecognizeResponse",
    "EnrolledEmployeeSummary",
    "ThresholdEvaluationReport"
]
