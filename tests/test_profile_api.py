import pytest
import uuid
from fastapi.testclient import TestClient
from src.application.app import app
from database.connection import init_database
from database.seed.seed_runner import seed_database_if_empty


@pytest.fixture(scope="module", autouse=True)
def setup_test_environment():
    init_database()
    seed_database_if_empty()


@pytest.fixture
def client():
    return TestClient(app)


def test_api_create_and_list_employees(client):
    # Use random employee code to guarantee idempotency across multiple test runs
    random_code = f"EMP{uuid.uuid4().hex[:5].upper()}"
    new_emp = {
        "employee_code": random_code,
        "first_name": "Saman",
        "last_name": "Kumara",
        "department": "Security",
        "email": f"saman.{random_code.lower()}@canteen.ai"
    }
    res = client.post("/api/v1/employees", json=new_emp)
    assert res.status_code == 201
    data = res.json()
    assert data["success"] is True
    assert data["employee"]["employee_code"] == random_code

    # 2. List Employees
    list_res = client.get("/api/v1/employees")
    assert list_res.status_code == 200
    emps = list_res.json()["employees"]
    assert any(e["employee_code"] == random_code for e in emps)


def test_api_get_employee_by_code(client):
    res = client.get("/api/v1/employees/EMP001")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["employee"]["first_name"] == "Nimal"


def test_api_update_and_get_profile(client):
    emp_res = client.get("/api/v1/employees/EMP001")
    emp_id = emp_res.json()["employee"]["id"]

    # Update profile
    profile_payload = {
        "age": 34,
        "height_cm": 172.0,
        "weight_kg": 72.0,
        "daily_calorie_target": 2150.0,
        "diet_type": "normal",
        "health_goal": "maintain",
        "notes": "Updated health goals"
    }
    put_res = client.put(f"/api/v1/employees/{emp_id}/profile", json=profile_payload)
    assert put_res.status_code == 200
    prof = put_res.json()["profile"]
    assert prof["weight_kg"] == 72.0
    assert prof["bmi"] == 24.3
    assert "Normal weight" in prof["bmi_category"]


def test_api_preferences_endpoints(client):
    emp_res = client.get("/api/v1/employees/EMP001")
    emp_id = emp_res.json()["employee"]["id"]

    # Get Preferences
    get_res = client.get(f"/api/v1/employees/{emp_id}/preferences")
    assert get_res.status_code == 200

    # Put Preferences
    prefs_payload = {
        "likes": ["string_hoppers", "samosa"],
        "dislikes": ["noodles"],
        "avoid": ["fish_curry"]
    }
    put_res = client.put(f"/api/v1/employees/{emp_id}/preferences", json=prefs_payload)
    assert put_res.status_code == 200
    saved = put_res.json()["preferences"]
    assert "fish_curry" in saved["avoid"]
    assert "string_hoppers" in saved["likes"]


def test_api_get_full_profile(client):
    res = client.get("/api/v1/employees/EMP001/full-profile")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["employee_code"] == "EMP001"
    assert data["name"] == "Nimal Perera"
    assert data["profile"] is not None
    assert data["preferences"] is not None


def test_api_unknown_employee_404(client):
    res = client.get("/api/v1/employees/UNKNOWN_999/full-profile")
    assert res.status_code == 404
