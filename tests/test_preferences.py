import pytest
import tempfile
from pathlib import Path

from database.connection import init_database
from database.seed.seed_runner import seed_database_if_empty
from src.profiles.profile_service import ProfileService
from src.profiles.employee_service import EmployeeService
from src.profiles.schemas import FoodPreferenceSet, EmployeeCreate


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_p = Path(tmp_dir) / "test_canteen.db"
        init_database(db_p)
        seed_database_if_empty(db_path=db_p)
        yield db_p


def test_food_preferences_lifecycle(temp_db):
    profile_service = ProfileService(db_path=temp_db)
    emp_service = EmployeeService(db_path=temp_db)

    # 1. Create a distinct test employee
    new_emp = emp_service.create_employee(
        EmployeeCreate(
            employee_code="EMP_PREF_TEST",
            first_name="Test",
            last_name="Preferences",
            department="QA",
            email="test.prefs@canteen.ai"
        )
    )
    emp_id = new_emp["id"]

    # 2. Initial empty preferences
    initial_prefs = profile_service.get_preferences(emp_id)
    assert initial_prefs.likes == []
    assert initial_prefs.dislikes == []
    assert initial_prefs.avoid == []

    # 3. Set new preferences
    new_prefs = FoodPreferenceSet(
        likes=["samosa", "uludu_vade", "kiribath"],
        dislikes=["pastry"],
        avoid=["fish_curry"]
    )
    saved = profile_service.set_preferences(emp_id, new_prefs)

    assert set(saved.likes) == {"samosa", "uludu_vade", "kiribath"}
    assert saved.dislikes == ["pastry"]
    assert saved.avoid == ["fish_curry"]

    # 4. Re-verify persistence
    reloaded = profile_service.get_preferences(emp_id)
    assert set(reloaded.likes) == {"samosa", "uludu_vade", "kiribath"}
    assert reloaded.dislikes == ["pastry"]
    assert reloaded.avoid == ["fish_curry"]
