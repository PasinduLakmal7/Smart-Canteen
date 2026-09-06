import pytest
import tempfile
from pathlib import Path

from database.connection import init_database
from database.seed.seed_runner import seed_database_if_empty
from src.profiles.employee_service import EmployeeService
from src.profiles.schemas import EmployeeCreate, EmployeeUpdate


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_p = Path(tmp_dir) / "test_canteen.db"
        init_database(db_p)
        seed_database_if_empty(db_path=db_p)
        yield db_p


def test_employee_service_create_and_get(temp_db):
    service = EmployeeService(db_path=temp_db)
    
    # 1. Create new employee
    emp_data = EmployeeCreate(
        employee_code="EMP100",
        first_name="Kamal",
        last_name="Perera",
        department="Logistics",
        email="kamal.perera@canteen.ai"
    )
    created = service.create_employee(emp_data)
    assert created["id"] is not None
    assert created["employee_code"] == "EMP100"
    assert created["first_name"] == "Kamal"

    # 2. Get by numeric ID
    fetched_by_id = service.get_employee(str(created["id"]))
    assert fetched_by_id["employee_code"] == "EMP100"

    # 3. Get by Employee Code (Phase 4 Face Recognition lookup compatibility)
    fetched_by_code = service.get_employee("EMP100")
    assert fetched_by_code["id"] == created["id"]


def test_employee_service_rejects_duplicate_code(temp_db):
    service = EmployeeService(db_path=temp_db)
    emp_data = EmployeeCreate(
        employee_code="EMP001",  # Already in seed data
        first_name="Duplicate",
        last_name="Test",
        department="IT",
        email="unique.email@canteen.ai"
    )
    with pytest.raises(ValueError, match="already exists"):
        service.create_employee(emp_data)


def test_employee_service_update_and_deactivate(temp_db):
    service = EmployeeService(db_path=temp_db)
    emp = service.get_employee("EMP001")
    emp_id = emp["id"]

    # Update
    updated = service.update_employee(emp_id, EmployeeUpdate(department="Executive IT"))
    assert updated["department"] == "Executive IT"

    # Deactivate
    deact_res = service.deactivate_employee(emp_id)
    assert deact_res is True

    # Active list should no longer include EMP001
    active_emps = service.list_employees(active_only=True)
    assert not any(e["id"] == emp_id for e in active_emps)
