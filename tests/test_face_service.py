"""
Integration tests for FaceRecognitionService and Phase 3 Profile loading.
"""

import pytest
import numpy as np
import cv2
from pathlib import Path

from database.connection import init_database
from src.profiles.employee_service import EmployeeService
from src.profiles.profile_service import ProfileService
from src.profiles.schemas import EmployeeCreate, UserProfileCreate
from src.face_recognition.service import FaceRecognitionService
from src.face_recognition.detector import FaceDetector
from src.face_recognition.schemas import FaceBoundingBox, FaceDetection


class MockDetector(FaceDetector):
    """Deterministic detector for testing without relying on camera frames."""
    def detect_faces(self, image):
        if image is None or image.size == 0:
            return []
        return [
            FaceDetection(
                bbox=FaceBoundingBox(x=10, y=10, width=80, height=80),
                confidence=0.98,
                quality_score=0.95,
                is_valid=True
            )
        ]


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_canteen.db"
    init_database(db_file)
    return db_file


@pytest.fixture
def face_system(temp_db):
    emp_svc = EmployeeService(db_path=temp_db)
    prof_svc = ProfileService(db_path=temp_db)
    det = MockDetector()
    service = FaceRecognitionService(
        db_path=temp_db,
        detector=det,
        employee_service=emp_svc,
        profile_service=prof_svc
    )
    return service, emp_svc, prof_svc


def test_face_registration_and_recognition_flow(face_system):
    service, emp_svc, prof_svc = face_system

    # 1. Create employee & profile in Phase 3
    emp = emp_svc.create_employee(EmployeeCreate(
        employee_code="EMP999",
        first_name="Test",
        last_name="User",
        department="QA",
        email="test.qa@canteen.lk"
    ))
    emp_id = emp["id"] if isinstance(emp, dict) else emp.id

    prof_svc.create_or_update_profile(emp_id, UserProfileCreate(
        age=28,
        height_cm=175.0,
        weight_kg=72.0,
        daily_calorie_target=2200.0,
        diet_type="normal",
        health_goal="maintain"
    ))

    # 2. Register Face sample
    test_img = np.full((150, 150, 3), 150, dtype=np.uint8)
    reg_resp = service.register_face("EMP999", test_img, sample_tag="frontal")

    assert reg_resp.success is True
    assert reg_resp.employee_code == "EMP999"
    assert reg_resp.embedding_id > 0

    # 3. Live Recognition
    rec_resp = service.recognize_face(test_img, threshold=0.60)

    assert rec_resp.matched is True
    assert rec_resp.employee_code == "EMP999"
    assert rec_resp.employee_name == "Test User"
    assert rec_resp.confidence > 0.80

    # 4. Verify Phase 3 Profile is seamlessly attached
    assert rec_resp.employee_profile is not None
    assert rec_resp.employee_profile["employee_code"] == "EMP999"
    assert rec_resp.employee_profile["profile"]["daily_calorie_target"] == 2200.0
    assert rec_resp.employee_profile["profile"]["bmi"] > 20.0



def test_face_registration_rejects_unknown_employee(face_system):
    service, _, _ = face_system
    test_img = np.full((150, 150, 3), 150, dtype=np.uint8)

    with pytest.raises(ValueError, match="does not exist"):
        service.register_face("NONEXISTENT", test_img)


def test_deactivate_face_biometrics(face_system):
    service, emp_svc, _ = face_system
    emp = emp_svc.create_employee(EmployeeCreate(
        employee_code="EMP888",
        first_name="Jane",
        last_name="Doe",
        department="Finance",
        email="jane.doe@canteen.lk"
    ))

    test_img = np.full((150, 150, 3), 150, dtype=np.uint8)
    service.register_face("EMP888", test_img, sample_tag="frontal")

    enrolled = service.list_enrolled_employees()
    assert any(e.employee_code == "EMP888" for e in enrolled)

    # Deactivate
    deactivated = service.deactivate_employee_biometrics("EMP888")
    assert deactivated is True

    enrolled_after = service.list_enrolled_employees()
    assert not any(e.employee_code == "EMP888" for e in enrolled_after)
