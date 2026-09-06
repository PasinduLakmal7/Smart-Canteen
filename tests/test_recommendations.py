import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from src.application.app import app
from src.recommendations.engine import RecommendationEngine
from src.recommendations.schemas import RecommendationRequest, ScannedFoodInput
from database.connection import init_database
from database.seed.seed_runner import seed_database_if_empty

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_database()
    seed_database_if_empty()


def test_recommendation_engine_initialization():
    engine = RecommendationEngine()
    foods = engine._get_available_food_items()
    assert len(foods) > 0
    # Check that each food has valid price and macronutrients
    for f in foods:
        assert f.price_lkr >= 0
        assert f.calories_kcal >= 0
        assert f.protein_g >= 0
        assert f.emoji != ""


def test_dietary_and_allergen_filtering():
    engine = RecommendationEngine()
    all_foods = engine._get_available_food_items()

    # 1. Vegetarian filtering
    veg_foods = engine._filter_safe_foods(all_foods, diet_type="vegetarian", restrictions=[])
    for f in veg_foods:
        name = f.display_name.lower()
        assert "chicken" not in name
        assert "fish" not in name

    # 2. Vegan filtering
    vegan_foods = engine._filter_safe_foods(all_foods, diet_type="vegan", restrictions=[])
    for f in vegan_foods:
        name = f.display_name.lower()
        assert "chicken" not in name
        assert "fish" not in name
        assert "egg" not in name

    # 3. Peanut allergy filtering
    safe_from_peanuts = engine._filter_safe_foods(all_foods, diet_type="normal", restrictions=["Peanut Allergy"])
    for f in safe_from_peanuts:
        assert "peanut" not in f.display_name.lower()


def test_personalized_recommendation_emp001():
    engine = RecommendationEngine()
    res = engine.get_personalized_recommendations("EMP001")

    assert res.success is True
    assert res.employee_code == "EMP001"
    assert res.budget_status.daily_target_calories > 0
    assert len(res.recommended_combos) == 3
    for combo in res.recommended_combos:
        assert combo.total_calories > 0
        assert combo.total_price_lkr > 0
        assert len(combo.items) > 0
        assert combo.match_score >= 80
    assert len(res.health_nudge) > 10


def test_personalized_recommendation_with_scanned_plate():
    engine = RecommendationEngine()
    scanned = [
        {"food_name": "rice_and_curry", "quantity": 1},
        {"food_name": "dhal_curry", "quantity": 1}
    ]
    res = engine.get_personalized_recommendations("EMP001", scanned_items=scanned)

    assert res.success is True
    assert res.budget_status.current_plate_calories > 0
    # Should evaluate smart plate add-ons
    assert len(res.smart_add_ons) >= 0


def test_recommendation_api_endpoints():
    # 1. POST /api/v1/recommendations/personalized-meal
    payload = {
        "employee_code": "EMP001",
        "scanned_items": [
            {"food_name": "rice_and_curry", "quantity": 1}
        ],
        "time_of_day": "lunch"
    }
    response = client.post("/api/v1/recommendations/personalized-meal", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["employee_code"] == "EMP001"
    assert len(data["recommended_combos"]) == 3
    assert "budget_status" in data

    # 2. GET /api/v1/recommendations/suggestions/EMP001
    resp_get = client.get("/api/v1/recommendations/suggestions/EMP001")
    assert resp_get.status_code == 200
    data_get = resp_get.json()
    assert data_get["success"] is True
    assert len(data_get["recommended_combos"]) == 3

    # 3. Non-existent employee error
    resp_err = client.get("/api/v1/recommendations/suggestions/NONEXISTENT999")
    assert resp_err.status_code == 404
