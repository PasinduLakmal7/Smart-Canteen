import pytest
import tempfile
from pathlib import Path

from database.connection import init_database
from database.seed.seed_runner import seed_database_if_empty
from src.meal_analysis.service import MealAnalysisService


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_p = Path(tmp_dir) / "test_canteen.db"
        init_database(db_p)
        seed_database_if_empty(db_path=db_p)
        yield db_p


def test_meal_analysis_service(temp_db):
    service = MealAnalysisService(db_path=temp_db)

    raw_detections = [
        {"class_name": "string_hoppers", "confidence": 0.96},
        {"class_name": "string_hoppers", "confidence": 0.94},
        {"class_name": "string_hoppers", "confidence": 0.97},
        {"class_name": "string_hoppers", "confidence": 0.95},
        {"class_name": "uludu_vade", "confidence": 0.91}
    ]

    res = service.analyze_detections(raw_detections)

    assert res.success is True
    assert len(res.items) == 2

    # String Hoppers item check (4 x Rs. 25 = 100, 4 x 70 = 280 kcal)
    sh_item = next(it for it in res.items if it.food_name == "string_hoppers")
    assert sh_item.quantity == 4
    assert sh_item.unit_price == 25.00
    assert sh_item.total_price == 100.00
    assert sh_item.calories_kcal == 280.0
    assert sh_item.protein_g == 8.4

    # Uludu Vade item check (1 x Rs. 60 = 60, 1 x 140 = 140 kcal)
    uv_item = next(it for it in res.items if it.food_name == "uludu_vade")
    assert uv_item.quantity == 1
    assert uv_item.unit_price == 60.00
    assert uv_item.total_price == 60.00
    assert uv_item.calories_kcal == 140.0

    # Meal Grand Totals check
    totals = res.meal_totals
    assert totals.total_items_count == 5
    assert totals.total_bill_amount == 160.00
    assert totals.calories_kcal == 420.0
    assert totals.protein_g == 12.6


def test_meal_analysis_unknown_food_graceful(temp_db):
    service = MealAnalysisService(db_path=temp_db)
    raw_detections = [
        {"class_name": "unknown_future_snack", "confidence": 0.85},
        {"class_name": "samosa", "confidence": 0.92}
    ]

    res = service.analyze_detections(raw_detections)
    assert res.success is True
    assert len(res.items) == 1
    assert res.items[0].food_name == "samosa"
    assert any("unknown_future_snack" in w for w in res.warnings)
