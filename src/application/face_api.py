"""
FastAPI REST API Routes for Phase 4 Face Recognition Subsystem.
Provides endpoints for employee biometric enrollment, live camera recognition,
enrolled registry queries, biometric deactivation, and threshold evaluation.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form, Body
import base64

from src.face_recognition.schemas import (
    FaceRegisterRequest,
    FaceRegisterResponse,
    FaceRecognizeResponse,
    EnrolledEmployeeSummary,
    ThresholdEvaluationReport
)
from src.face_recognition.service import FaceRecognitionService
from src.utils.logging import app_logger

face_router = APIRouter(prefix="/api/v1/face", tags=["Biometric Face Recognition"])

face_service = FaceRecognitionService()


@face_router.post("/register", response_model=Dict[str, Any], status_code=201)
async def register_face(
    employee_code: Optional[str] = Form(None),
    sample_tag: str = Form("frontal"),
    file: Optional[UploadFile] = File(None),
    body: Optional[FaceRegisterRequest] = Body(None)
):
    """
    Enrolls a biometric face sample for an employee.
    Accepts multipart file upload or JSON with base64 image string.
    """
    try:
        target_code = employee_code or (body.employee_code if body else None)
        target_tag = sample_tag or (body.sample_tag if body else "frontal")

        if not target_code:
            raise HTTPException(status_code=400, detail="Missing required field: 'employee_code'.")

        image_data = None
        if file is not None:
            image_data = await file.read()
        elif body and body.image_base64:
            image_data = body.image_base64
        else:
            raise HTTPException(status_code=400, detail="Either 'file' or 'image_base64' must be provided.")

        response = face_service.register_face(
            employee_id_or_code=target_code,
            image_input=image_data,
            sample_tag=target_tag
        )
        return {"success": True, "data": response.model_dump()}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        app_logger.error(f"Error registering face: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@face_router.post("/recognize", response_model=Dict[str, Any])
async def recognize_face(
    threshold: float = Query(0.60, ge=0.0, le=1.0, description="Minimum cosine similarity matching threshold"),
    file: Optional[UploadFile] = File(None),
    image_base64: Optional[str] = Form(None)
):
    """
    Live face identification from camera frame.
    Performs 1:N vector search against enrolled gallery.
    If matched, automatically retrieves and attaches the complete Phase 3 Employee Profile.
    """
    try:
        image_data = None
        if file is not None:
            image_data = await file.read()
        elif image_base64:
            image_data = image_base64
        else:
            raise HTTPException(status_code=400, detail="Either 'file' or 'image_base64' is required.")

        result = face_service.recognize_face(image_input=image_data, threshold=threshold)
        return {"success": True, "data": result.model_dump()}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        app_logger.error(f"Error recognizing face: {e}")
        raise HTTPException(status_code=500, detail=f"Internal recognition error: {str(e)}")


@face_router.get("/enrolled", response_model=Dict[str, Any])
async def list_enrolled_employees():
    """Returns all employees who have registered biometric face profiles."""
    summaries = face_service.list_enrolled_employees()
    return {
        "success": True,
        "count": len(summaries),
        "enrolled_employees": [s.model_dump() for s in summaries]
    }


@face_router.delete("/{employee_id_or_code}", response_model=Dict[str, Any])
async def deactivate_face_biometrics(employee_id_or_code: str):
    """Deactivates enrolled face embeddings for an employee."""
    success = face_service.deactivate_employee_biometrics(employee_id_or_code)
    if not success:
        raise HTTPException(status_code=404, detail=f"No active biometric profile found for '{employee_id_or_code}'.")
    return {"success": True, "message": f"Biometric face data deactivated for '{employee_id_or_code}'."}


@face_router.post("/evaluate", response_model=Dict[str, Any])
async def evaluate_threshold(threshold: float = Query(0.60, ge=0.0, le=1.0)):
    """
    Runs benchmark accuracy evaluation over enrolled samples for thesis and research verification.
    """
    gallery = face_service.repository.get_all_active_embeddings()
    if len(gallery) < 2:
        return {
            "success": True,
            "message": "At least 2 enrolled embeddings required for threshold evaluation.",
            "data": None
        }

    # Construct genuine and impostor pairs from enrolled gallery
    genuine_pairs = []
    impostor_pairs = []
    for i in range(len(gallery)):
        for j in range(i + 1, len(gallery)):
            vec_a = gallery[i]["embedding"]
            vec_b = gallery[j]["embedding"]
            if gallery[i]["employee_id"] == gallery[j]["employee_id"]:
                genuine_pairs.append((vec_a, vec_b))
            else:
                impostor_pairs.append((vec_a, vec_b))

    report = face_service.evaluate_benchmark(genuine_pairs, impostor_pairs, threshold=threshold)
    return {"success": True, "data": report.model_dump()}
