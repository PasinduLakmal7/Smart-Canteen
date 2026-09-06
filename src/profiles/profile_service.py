from pathlib import Path
from typing import Optional, List, Dict, Any

from src.profiles.schemas import (
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileItem,
    FoodPreferenceSet,
    CompleteEmployeeProfile
)
from src.profiles.repository import ProfileRepository
from src.profiles.validators import ProfileValidator
from src.utils.logging import app_logger


class ProfileService:
    """
    Business Service Layer for User Nutrition Profiles & Food Preferences.
    """

    def __init__(self, repository: Optional[ProfileRepository] = None, db_path: Optional[Path] = None):
        self.repository = repository or ProfileRepository(db_path=db_path)
        self.validator = ProfileValidator()

    def get_profile(self, employee_id: int) -> Optional[UserProfileItem]:
        """
        Retrieves user profile with dynamically computed BMI and WHO category.
        """
        raw = self.repository.get_profile_by_employee_id(employee_id)
        if not raw:
            return None

        # Compute BMI dynamically
        bmi_res = self.validator.calculate_bmi(
            weight_kg=float(raw["weight_kg"]),
            height_cm=float(raw["height_cm"])
        )

        return UserProfileItem(
            id=raw["id"],
            employee_id=raw["employee_id"],
            age=raw["age"],
            height_cm=raw["height_cm"],
            weight_kg=raw["weight_kg"],
            daily_calorie_target=raw["daily_calorie_target"],
            diet_type=raw["diet_type"],
            health_goal=raw["health_goal"],
            notes=raw.get("notes") or "",
            bmi=bmi_res.bmi,
            bmi_category=bmi_res.category.value,
            created_at=str(raw["created_at"]) if raw.get("created_at") else None,
            updated_at=str(raw["updated_at"]) if raw.get("updated_at") else None
        )

    def create_or_update_profile(self, employee_id: int, profile_in: UserProfileCreate) -> UserProfileItem:
        """
        Initializes or replaces nutrition profile for an employee.
        """
        self.validator.validate_biometrics(
            age=profile_in.age,
            height_cm=profile_in.height_cm,
            weight_kg=profile_in.weight_kg,
            calorie_target=profile_in.daily_calorie_target
        )

        existing = self.repository.get_profile_by_employee_id(employee_id)
        if existing:
            self.repository.update_profile(
                employee_id,
                UserProfileUpdate(
                    age=profile_in.age,
                    height_cm=profile_in.height_cm,
                    weight_kg=profile_in.weight_kg,
                    daily_calorie_target=profile_in.daily_calorie_target,
                    diet_type=profile_in.diet_type,
                    health_goal=profile_in.health_goal,
                    notes=profile_in.notes
                )
            )
        else:
            self.repository.create_profile(employee_id, profile_in)

        return self.get_profile(employee_id)

    def update_profile(self, employee_id: int, update_in: UserProfileUpdate) -> Optional[UserProfileItem]:
        """Updates specific fields of an employee's nutrition profile."""
        existing = self.repository.get_profile_by_employee_id(employee_id)
        if not existing:
            return None

        # Validate updated biometrics against merged state
        merged_age = update_in.age if update_in.age is not None else existing["age"]
        merged_height = update_in.height_cm if update_in.height_cm is not None else existing["height_cm"]
        merged_weight = update_in.weight_kg if update_in.weight_kg is not None else existing["weight_kg"]
        merged_cal = update_in.daily_calorie_target if update_in.daily_calorie_target is not None else existing["daily_calorie_target"]

        self.validator.validate_biometrics(merged_age, merged_height, merged_weight, merged_cal)

        self.repository.update_profile(employee_id, update_in)
        return self.get_profile(employee_id)

    def get_preferences(self, employee_id: int) -> FoodPreferenceSet:
        """Retrieves food preferences."""
        raw_prefs = self.repository.get_preferences(employee_id)
        return FoodPreferenceSet(
            likes=raw_prefs.get("likes", []),
            dislikes=raw_prefs.get("dislikes", []),
            avoid=raw_prefs.get("avoid", [])
        )

    def set_preferences(self, employee_id: int, prefs: FoodPreferenceSet) -> FoodPreferenceSet:
        """Sets food preferences for an employee."""
        res = self.repository.set_preferences(employee_id, prefs)
        return FoodPreferenceSet(
            likes=res.get("likes", []),
            dislikes=res.get("dislikes", []),
            avoid=res.get("avoid", [])
        )

    def get_complete_profile(self, identifier: str) -> Optional[CompleteEmployeeProfile]:
        """
        Master method: Resolves employee by ID or Code and returns their full profile,
        computed BMI, and food preferences.
        """
        if identifier.isdigit():
            emp = self.repository.get_employee_by_id(int(identifier))
        else:
            emp = self.repository.get_employee_by_code(identifier)

        if not emp:
            return None

        emp_id = emp["id"]
        profile_item = self.get_profile(emp_id)
        preferences = self.get_preferences(emp_id)

        full_name = f"{emp['first_name']} {emp['last_name']}".strip()

        return CompleteEmployeeProfile(
            employee_id=emp_id,
            employee_code=emp["employee_code"],
            name=full_name,
            first_name=emp["first_name"],
            last_name=emp["last_name"],
            department=emp["department"],
            email=emp["email"],
            active=bool(emp["active"]),
            profile=profile_item,
            preferences=preferences
        )
