"""
API Integration tests for Phase 4 Face Recognition Endpoints.
"""

import io
import pytest
import numpy as np
import cv2
from starlette.testclient import TestClient

from src.application.app import app
from database.connection import init_database
from database.seed.seed_runner import seed_database_if_empty
from src.face_recognition.detector import FaceDetector
from src.face_recognition.schemas import FaceBoundingBox, FaceDetection


class MockDetector(FaceDetector):
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


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    test_db = tmp_path / "test_api_canteen.db"
    init_database(test_db)
    seed_database_if_empty(test_db)

    # Monkeypatch repository & services to use test_db
    from src.application import face_api, profile_api
    mock_det = MockDetector()
    monkeypatch.setattr(face_api.face_service, "detector", mock_det)
    monkeypatch.setattr(face_api.face_service.repository, "db_path", test_db)
    monkeypatch.setattr(face_api.face_service.employee_service.repository, "db_path", test_db)
    monkeypatch.setattr(face_api.face_service.profile_service.repository, "db_path", test_db)
    monkeypatch.setattr(profile_api.employee_service.repository, "db_path", test_db)
    monkeypatch.setattr(profile_api.profile_service.repository, "db_path", test_db)



@pytest.fixture
def client():
    return TestClient(app)


def generate_test_image_bytes() -> bytes:
    img = np.full((120, 120, 3), 160, dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


def test_api_list_enrolled_faces(client):
    res = client.get("/api/v1/face/enrolled")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "enrolled_employees" in data


def test_api_register_face_and_recognize(client):
    img_bytes = generate_test_image_bytes()

    # 1. Register face for EMP001 (Kamal)
    files = {"file": ("face.jpg", img_bytes, "image/jpeg")}
    data = {"employee_code": "EMP001", "sample_tag": "frontal"}

    reg_res = client.post("/api/v1/face/register", data=data, files=files)
    assert reg_res.status_code == 201
    reg_json = reg_res.json()
    assert reg_json["success"] is True
    assert reg_json["data"]["employee_code"] == "EMP001"

    # 2. Live Recognize
    rec_files = {"file": ("query.jpg", img_bytes, "image/jpeg")}
    rec_res = client.post("/api/v1/face/recognize", files=rec_files)
    assert rec_res.status_code == 200
    rec_json = rec_res.json()
    assert rec_json["success"] is True
    assert rec_json["data"]["matched"] is True
    assert rec_json["data"]["employee_code"] == "EMP001"
    assert rec_json["data"]["employee_profile"] is not None


def test_api_evaluate_threshold(client):
    res = client.post("/api/v1/face/evaluate?threshold=0.60")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True


def test_api_deactivate_face(client):
    res = client.delete("/api/v1/face/EMP001")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
