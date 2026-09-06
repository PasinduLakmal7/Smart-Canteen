import pytest
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


def test_api_list_foods(client):
    res = client.get("/api/v1/foods")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["foods"]) >= 10
    classes = [f["class_name"] for f in data["foods"]]
    assert "string_hoppers" in classes


def test_api_get_single_food(client):
    res = client.get("/api/v1/foods/string_hoppers")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["food"]["class_name"] == "string_hoppers"
    assert data["price"]["price"] == 25.00
    assert data["nutrition"]["calories_kcal"] == 70.0


def test_api_calculate_nutrition(client):
    payload = [
        {"food_name": "string_hoppers", "quantity": 4},
        {"food_name": "uludu_vade", "quantity": 1}
    ]
    res = client.post("/api/v1/nutrition/calculate", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["totals"]["calories_kcal"] == 420.0
    assert data["totals"]["protein_g"] == 12.6


def test_api_calculate_billing(client):
    payload = [
        {"food_name": "string_hoppers", "quantity": 4},
        {"food_name": "uludu_vade", "quantity": 1}
    ]
    res = client.post("/api/v1/billing/calculate", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total_amount"] == 160.00
    assert data["item_count"] == 5


def test_admin_price_update(client):
    # Update price of uludu_vade to Rs. 65.00
    foods_res = client.get("/api/v1/foods/uludu_vade")
    food_id = foods_res.json()["food"]["id"]

    put_res = client.put(f"/api/v1/admin/foods/{food_id}/price", json={"price": 65.00})
    assert put_res.status_code == 200

    # Verify updated price in billing
    bill_res = client.post("/api/v1/billing/calculate", json=[{"food_name": "uludu_vade", "quantity": 2}])
    assert bill_res.json()["data"]["total_amount"] == 130.00

    # Reset price back to Rs. 60.00
    client.put(f"/api/v1/admin/foods/{food_id}/price", json={"price": 60.00})
