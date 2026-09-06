"""
Face Recognition Domain Service for Phase 4.
Orchestrates face detection, quality validation, multi-sample enrollment,
vector similarity matching, unknown rejection, and seamless Phase 3 Profile loading.
"""

import base64
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path
import numpy as np
import cv2

from src.face_recognition.schemas import (
    FaceDetection,
    FaceRegisterRequest,
    FaceRegisterResponse,
    FaceRecognizeResponse,
    EnrolledEmployeeSummary,
    ThresholdEvaluationReport
)
from src.face_recognition.detector import FaceDetector
from src.face_recognition.embedder import FaceEmbedder
from src.face_recognition.matcher import FaceMatcher
from src.face_recognition.repository import FaceRepository
from src.profiles.employee_service import EmployeeService
from src.profiles.profile_service import ProfileService
from src.utils.logging import app_logger


class FaceRecognitionService:
    """
    High-level orchestrator for Biometric Face Recognition.
    Connects Camera Feeds -> Feature Embeddings -> Database -> Phase 3 Employee Profiles.
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        default_threshold: float = 0.60,
        detector: Optional[FaceDetector] = None,
        embedder: Optional[FaceEmbedder] = None,
        matcher: Optional[FaceMatcher] = None,
        repository: Optional[FaceRepository] = None,
        employee_service: Optional[EmployeeService] = None,
        profile_service: Optional[ProfileService] = None
    ):
        self.repository = repository or FaceRepository(db_path)
        self.detector = detector or FaceDetector()
        self.embedder = embedder or FaceEmbedder()
        self.matcher = matcher or FaceMatcher(default_threshold=default_threshold)
        self.employee_service = employee_service or EmployeeService(db_path)
        self.profile_service = profile_service or ProfileService(db_path)

    @staticmethod
    def decode_image(image_input: Union[np.ndarray, bytes, str]) -> np.ndarray:
        """Decodes raw bytes, base64 string, or returns existing numpy array."""
        if isinstance(image_input, np.ndarray):
            return image_input

        if isinstance(image_input, str):
            # Check if base64 data URL
            if "," in image_input:
                image_input = image_input.split(",", 1)[1]
            image_bytes = base64.b64decode(image_input)
        elif isinstance(image_input, bytes):
            image_bytes = image_input
        else:
            raise ValueError("Unsupported image input format.")

        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image bytes into valid BGR frame.")
        return img

    def register_face(
        self,
        employee_id_or_code: Union[int, str],
        image_input: Union[np.ndarray, bytes, str],
        sample_tag: str = "frontal"
    ) -> FaceRegisterResponse:
        """
        Enrolls a new biometric face sample for an employee.
        
        Strict Validation Pipeline:
        1. Validates employee exists in Phase 3 database.
        2. Detects face(s).
        3. Rejects if 0 faces found.
        4. Rejects if > 1 faces found (single-subject constraint).
        5. Validates face size and sharpness.
        6. Crops & aligns face.
        7. Extracts 128D feature embedding vector.
        8. Stores embedding in database.
        """
        emp = self.employee_service.get_employee(str(employee_id_or_code))
        if not emp:
            raise ValueError(f"Employee '{employee_id_or_code}' does not exist. Register employee in Phase 3 first.")

        img = self.decode_image(image_input)
        detections = self.detector.detect_faces(img)

        # 1. Reject if no face detected
        if len(detections) == 0:
            raise ValueError("No face detected in image. Please ensure your face is clearly visible to the camera.")

        # 2. Reject if multiple faces detected
        if len(detections) > 1:
            raise ValueError("Multiple faces detected in image. Please ensure only one person is present during enrollment.")

        face_det = detections[0]

        # 3. Reject if face is blurry or invalid
        if not face_det.is_valid:
            raise ValueError(face_det.error_reason or "Face image quality is insufficient for biometric enrollment.")

        # 4. Align, crop, and extract 128D feature vector
        aligned_face = self.detector.align_and_crop(img, face_det)
        embedding = self.embedder.extract_embedding(aligned_face)

        emp_id = emp["id"] if isinstance(emp, dict) else emp.id
        emp_code = emp["employee_code"] if isinstance(emp, dict) else emp.employee_code
        emp_fname = emp["first_name"] if isinstance(emp, dict) else emp.first_name
        emp_lname = emp["last_name"] if isinstance(emp, dict) else emp.last_name

        # 5. Persist to SQLite
        emb_id = self.repository.save_embedding(
            employee_id=emp_id,
            embedding=embedding,
            model_name=self.embedder.model_name,
            sample_tag=sample_tag,
            quality_score=face_det.quality_score
        )

        return FaceRegisterResponse(
            success=True,
            employee_id=emp_id,
            employee_code=emp_code,
            sample_tag=sample_tag,
            embedding_id=emb_id,
            quality_score=face_det.quality_score,
            message=f"Biometric face sample ({sample_tag}) enrolled successfully for {emp_fname} {emp_lname}."
        )

    def recognize_face(
        self,
        image_input: Union[np.ndarray, bytes, str],
        threshold: Optional[float] = None
    ) -> FaceRecognizeResponse:
        """
        Live identification from camera frame.
        Performs 1:N vector search and connects directly to Phase 3 Profile.
        """
        effective_threshold = threshold if threshold is not None else self.matcher.default_threshold
        img = self.decode_image(image_input)
        detections = self.detector.detect_faces(img)

        if len(detections) == 0:
            return FaceRecognizeResponse(
                matched=False,
                threshold=effective_threshold,
                message="No face detected in camera view."
            )

        # Select primary face (largest area)
        primary_face = max(detections, key=lambda d: d.bbox.width * d.bbox.height)
        aligned_face = self.detector.align_and_crop(img, primary_face)
        query_embedding = self.embedder.extract_embedding(aligned_face)

        # Load enrolled gallery from SQLite
        gallery = self.repository.get_all_active_embeddings()
        if not gallery:
            return FaceRecognizeResponse(
                matched=False,
                threshold=effective_threshold,
                message="No enrolled employees in the database gallery."
            )

        is_match, top_match, ranked_matches = self.matcher.find_best_match(
            query_embedding=query_embedding,
            gallery_embeddings=gallery,
            threshold=effective_threshold
        )

        if not is_match or top_match is None:
            return FaceRecognizeResponse(
                matched=False,
                confidence=top_match.similarity if top_match else 0.0,
                distance=top_match.distance if top_match else 0.0,
                threshold=effective_threshold,
                top_matches=ranked_matches,
                message="Unknown person. Biometric similarity is below verification threshold."
            )

        # 4. Identity Verified -> Fetch Complete Phase 3 Profile
        emp = self.employee_service.get_employee(top_match.employee_code)
        complete_profile = self.profile_service.get_complete_profile(top_match.employee_code)
        profile_dict = complete_profile.model_dump() if complete_profile else None

        if emp:
            emp_name = f"{emp['first_name']} {emp['last_name']}" if isinstance(emp, dict) else f"{emp.first_name} {emp.last_name}"
            emp_dept = emp.get("department", "General") if isinstance(emp, dict) else getattr(emp, "department", "General")
        else:
            emp_name = top_match.employee_code
            emp_dept = "General"

        return FaceRecognizeResponse(
            matched=True,
            employee_id=top_match.employee_id,
            employee_code=top_match.employee_code,
            employee_name=emp_name,
            department=emp_dept,
            confidence=top_match.similarity,
            distance=top_match.distance,
            threshold=effective_threshold,
            top_matches=ranked_matches,
            employee_profile=profile_dict,
            message=f"Employee identified: {emp_name} ({top_match.employee_code}) with {top_match.similarity * 100:.1f}% confidence."
        )

    def list_enrolled_employees(self) -> List[EnrolledEmployeeSummary]:
        """Lists summaries of all employees with active biometric enrollments."""
        return self.repository.list_enrolled_employees()

    def deactivate_employee_biometrics(self, employee_id_or_code: Union[int, str]) -> bool:
        """Deactivates all biometric samples for an employee."""
        emp = self.employee_service.get_employee(str(employee_id_or_code))
        if not emp:
            return False
        emp_id = emp["id"] if isinstance(emp, dict) else emp.id
        count = self.repository.deactivate_by_employee(emp_id)
        return count > 0

    def evaluate_benchmark(
        self,
        genuine_pairs: List[Tuple[List[float], List[float]]],
        impostor_pairs: List[Tuple[List[float], List[float]]],
        threshold: float = 0.60
    ) -> ThresholdEvaluationReport:
        """Runs threshold benchmark evaluation for research documentation."""
        return self.matcher.evaluate_threshold(genuine_pairs, impostor_pairs, threshold)
