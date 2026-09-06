"""
Pydantic Schemas for Phase 4 Face Recognition Subsystem.
Strict DTOs for face detection, multi-sample enrollment, vector matching, and evaluation reports.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class FaceBoundingBox(BaseModel):
    """Bounding box coordinates for detected face."""
    x: int = Field(..., description="Top-left X pixel coordinate")
    y: int = Field(..., description="Top-left Y pixel coordinate")
    width: int = Field(..., description="Bounding box width in pixels")
    height: int = Field(..., description="Bounding box height in pixels")


class FacialLandmarkPoint(BaseModel):
    """2D landmark coordinate (e.g. eye, nose tip, mouth corner)."""
    name: str = Field(..., description="Landmark name (e.g. right_eye, left_eye, nose, right_mouth, left_mouth)")
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")


class FaceDetection(BaseModel):
    """Individual face detection result from detector engine."""
    bbox: FaceBoundingBox
    landmarks: Optional[List[FacialLandmarkPoint]] = None
    confidence: float = Field(..., ge=0.0, le=1.0, description="Face detection confidence score")
    quality_score: float = Field(1.0, ge=0.0, le=1.0, description="Image sharpness and quality score")
    is_valid: bool = Field(True, description="Whether face satisfies registration/recognition constraints")
    error_reason: Optional[str] = Field(None, description="Reason if face rejected (e.g. blur, too small)")


class FaceRegisterRequest(BaseModel):
    """Request schema for enrolling an employee face embedding."""
    employee_code: str = Field(..., description="Unique employee code (e.g. EMP001)")
    sample_tag: str = Field("frontal", description="Sample perspective: 'frontal', 'left', 'right', 'glasses'")
    image_base64: Optional[str] = Field(None, description="Base64 encoded image string (optional if uploading file)")


class FaceRegisterResponse(BaseModel):
    """Response returned after successful face enrollment."""
    success: bool
    employee_id: int
    employee_code: str
    sample_tag: str
    embedding_id: int
    quality_score: float
    message: str


class FaceMatchDetail(BaseModel):
    """Match comparison details."""
    employee_id: int
    employee_code: str
    similarity: float = Field(..., ge=-1.0, le=1.0, description="Cosine similarity score")
    distance: float = Field(..., ge=0.0, description="Euclidean distance")
    sample_tag: str


class FaceRecognizeResponse(BaseModel):
    """Response returned upon live face recognition."""
    matched: bool
    employee_id: Optional[int] = None
    employee_code: Optional[str] = None
    employee_name: Optional[str] = None
    department: Optional[str] = None
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Match confidence / similarity score")
    distance: float = Field(0.0, ge=0.0, description="Vector Euclidean distance")
    threshold: float = Field(0.60, description="Matching threshold applied")
    top_matches: Optional[List[FaceMatchDetail]] = None
    employee_profile: Optional[Dict[str, Any]] = Field(None, description="Phase 3 Complete Profile (biometrics, diet, goals)")
    message: str


class EnrolledEmployeeSummary(BaseModel):
    """Summary of enrolled face biometric samples for an employee."""
    employee_id: int
    employee_code: str
    name: str
    department: str
    sample_count: int
    sample_tags: List[str]
    active: bool


class ThresholdEvaluationReport(BaseModel):
    """Statistical evaluation metrics for research and thesis validation."""
    total_samples: int
    threshold_tested: float
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    false_acceptance_rate: float
    false_rejection_rate: float
    avg_inference_time_ms: float
    recommendation: str
