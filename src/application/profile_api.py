from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Depends

from src.profiles.schemas import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeItem,
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileItem,
    FoodPreferenceSet,
    CompleteEmployeeProfile
)
from src.profiles.employee_service import EmployeeService
from src.profiles.profile_service import ProfileService

profile_router = APIRouter(prefix="/api/v1/employees", tags=["Employee Profiles & Health Goals"])

employee_service = EmployeeService()
profile_service = ProfileService()


# ==========================================
# 1. EMPLOYEE ENDPOINTS
# ==========================================
@profile_router.post("", response_model=Dict[str, Any], status_code=201)
async def create_employee(emp_in: EmployeeCreate):
    """Registers a new employee."""
    try:
        res = employee_service.create_employee(emp_in)
        return {"success": True, "employee": res}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@profile_router.get("", response_model=Dict[str, Any])
async def list_employees(active_only: bool = Query(True, description="Filter active employees only")):
    """Lists all registered employees."""
    employees = employee_service.list_employees(active_only=active_only)
    return {"success": True, "count": len(employees), "employees": employees}


@profile_router.get("/{id_or_code}", response_model=Dict[str, Any])
async def get_employee(id_or_code: str):
    """
    Looks up an employee by numeric ID or unique employee code (e.g. EMP001).
    Prepared for Phase 4 Face Recognition lookup.
    """
    emp = employee_service.get_employee(id_or_code)
    if not emp:
        raise HTTPException(status_code=404, detail=f"Employee '{id_or_code}' not found.")
    return {"success": True, "employee": emp}


@profile_router.put("/{employee_id}", response_model=Dict[str, Any])
async def update_employee(employee_id: int, update_in: EmployeeUpdate):
    """Updates basic employee information."""
    try:
        updated = employee_service.update_employee(employee_id, update_in)
        if not updated:
            raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found.")
        return {"success": True, "employee": updated}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@profile_router.delete("/{employee_id}", response_model=Dict[str, Any])
async def deactivate_employee(employee_id: int):
    """Deactivates an employee."""
    success = employee_service.deactivate_employee(employee_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found.")
    return {"success": True, "message": f"Employee {employee_id} deactivated."}


# ==========================================
# 2. USER PROFILE & NUTRITION GOAL ENDPOINTS
# ==========================================
@profile_router.post("/{employee_id}/profile", response_model=Dict[str, Any], status_code=201)
async def create_profile(employee_id: int, profile_in: UserProfileCreate):
    """Creates or initializes a nutrition and biometric profile for an employee."""
    emp = employee_service.get_employee(str(employee_id))
    if not emp:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found.")
    try:
        res = profile_service.create_or_update_profile(employee_id, profile_in)
        return {"success": True, "profile": res.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@profile_router.get("/{employee_id}/profile", response_model=Dict[str, Any])
async def get_profile(employee_id: int):
    """Retrieves an employee's nutrition profile with dynamically calculated BMI."""
    emp = employee_service.get_employee(str(employee_id))
    if not emp:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found.")

    profile = profile_service.get_profile(employee_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"No health profile found for employee {employee_id}.")
    return {"success": True, "profile": profile.model_dump()}


@profile_router.put("/{employee_id}/profile", response_model=Dict[str, Any])
async def update_profile(employee_id: int, update_in: UserProfileUpdate):
    """Updates biometric metrics, daily calorie targets, diet types, and health goals."""
    emp = employee_service.get_employee(str(employee_id))
    if not emp:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found.")
    try:
        updated = profile_service.update_profile(employee_id, update_in)
        if not updated:
            raise HTTPException(status_code=404, detail=f"No profile found for employee {employee_id} to update.")
        return {"success": True, "profile": updated.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# 3. FOOD PREFERENCES ENDPOINTS
# ==========================================
@profile_router.get("/{employee_id}/preferences", response_model=Dict[str, Any])
async def get_food_preferences(employee_id: int):
    """Retrieves liked, disliked, and avoided food preferences for an employee."""
    emp = employee_service.get_employee(str(employee_id))
    if not emp:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found.")

    prefs = profile_service.get_preferences(employee_id)
    return {"success": True, "preferences": prefs.model_dump()}


@profile_router.put("/{employee_id}/preferences", response_model=Dict[str, Any])
async def set_food_preferences(employee_id: int, prefs_in: FoodPreferenceSet):
    """Replaces or updates food preferences for an employee."""
    emp = employee_service.get_employee(str(employee_id))
    if not emp:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found.")

    saved_prefs = profile_service.set_preferences(employee_id, prefs_in)
    return {"success": True, "preferences": saved_prefs.model_dump()}


# ==========================================
# 4. MASTER UNIFIED FULL PROFILE ENDPOINT
# ==========================================
@profile_router.get("/{id_or_code}/full-profile", response_model=Dict[str, Any])
async def get_full_profile(id_or_code: str):
    """
    Master Endpoint for Phase 3, 4, 5, and 6:
    Returns complete employee record + nutrition biometrics (with BMI) + food preferences.
    """
    full_profile = profile_service.get_complete_profile(id_or_code)
    if not full_profile:
        raise HTTPException(status_code=404, detail=f"Employee '{id_or_code}' not found.")
    return {"success": True, "data": full_profile.model_dump()}
