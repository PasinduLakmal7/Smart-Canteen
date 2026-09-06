"""
Profiles Domain Subsystem (Phase 3).
Manages employee records, biometric health metrics, daily calorie targets, diet types, and food preferences.
"""
from src.profiles.schemas import (
    DietType,
    HealthGoal,
    PreferenceType,
    BMICategory,
    BMICalculationResult,
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeItem,
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileItem,
    FoodPreferenceItem,
    FoodPreferenceSet,
    CompleteEmployeeProfile
)
from src.profiles.repository import ProfileRepository
from src.profiles.employee_service import EmployeeService
from src.profiles.profile_service import ProfileService

__all__ = [
    "DietType",
    "HealthGoal",
    "PreferenceType",
    "BMICategory",
    "BMICalculationResult",
    "EmployeeCreate",
    "EmployeeUpdate",
    "EmployeeItem",
    "UserProfileCreate",
    "UserProfileUpdate",
    "UserProfileItem",
    "FoodPreferenceItem",
    "FoodPreferenceSet",
    "CompleteEmployeeProfile",
    "ProfileRepository",
    "EmployeeService",
    "ProfileService"
]
