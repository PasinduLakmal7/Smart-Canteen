import pytest
import tempfile
from pathlib import Path

from database.connection import init_database
from database.seed.seed_runner import seed_database_if_empty
from src.profiles.profile_service import ProfileService
from src.profiles.employee_service import EmployeeService
from src.profiles.schemas import (
    UserProfileCreate,
    UserProfileUpdate,
    DietType,
    HealthGoal,
    FoodPreferenceSet
)


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_p = Path(tmp_dir) / "test_canteen.db"
        init_database(db_p)
        seed_database_if_empty(db_path=db_p)
        yield db_p


def test_profile_service_get_and_dynamic_bmi(temp_db):
    profile_service = ProfileService(db_path=temp_db)
    emp_service = EmployeeService(db_path=temp_db)

    # EMP001: 172 cm, 74 kg -> BMI = 74 / (1.72^2) = 25.0 (Overweight)
    emp = emp_service.get_employee("EMP001")
    profile = profile_service.get_profile(emp["id"])

    assert profile is not None
    assert profile.age == 32
    assert profile.height_cm == 172.0
    assert profile.weight_kg == 74.0
    assert profile.bmi == 25.0
    assert "Overweight" in profile.bmi_category


def test_profile_service_create_or_update(temp_db):
    profile_service = ProfileService(db_path=temp_db)
    emp_service = EmployeeService(db_path=temp_db)

    emp = emp_service.get_employee("EMP001")
    emp_id = emp["id"]

    # Update weight to 68 kg -> BMI = 68 / (1.72^2) = 23.0 (Normal weight)
    updated = profile_service.create_or_update_profile(
        emp_id,
        UserProfileCreate(
            age=33,
            height_cm=172.0,
            weight_kg=68.0,
            daily_calorie_target=2100.0,
            diet_type=DietType.NORMAL,
            health_goal=HealthGoal.MAINTAIN,
            notes="Reduced weight to normal range."
        )
    )

    assert updated.weight_kg == 68.0
    assert updated.bmi == 23.0
    assert "Normal weight" in updated.bmi_category


def test_get_complete_profile_by_code(temp_db):
    profile_service = ProfileService(db_path=temp_db)
    full = profile_service.get_complete_profile("EMP001")

    assert full is not None
    assert full.employee_code == "EMP001"
    assert full.name == "Nimal Perera"
    assert full.profile is not None
    assert full.profile.daily_calorie_target == 2200.0
    assert "string_hoppers" in full.preferences.likes
    assert "noodles" in full.preferences.dislikes
