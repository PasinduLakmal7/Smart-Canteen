import pytest
import tempfile
from pathlib import Path

from database.connection import init_database
from database.seed.seed_runner import seed_database_if_empty
from src.foods.repository import FoodRepository
from src.foods.schemas import FoodCreate, FoodUpdate, ServingType


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_p = Path(tmp_dir) / "test_canteen.db"
        init_database(db_p)
        seed_database_if_empty(db_path=db_p)
        yield db_p


def test_food_repository_get_all(temp_db):
    repo = FoodRepository(db_path=temp_db)
    foods = repo.get_all(active_only=True)
    assert len(foods) >= 10
    classes = [f["class_name"] for f in foods]
    assert "string_hoppers" in classes
    assert "uludu_vade" in classes
    assert "samosa" in classes


def test_food_repository_get_by_class_name(temp_db):
    repo = FoodRepository(db_path=temp_db)
    food = repo.get_by_class_name("string_hoppers")
    assert food is not None
    assert food["class_name"] == "string_hoppers"
    assert food["serving_type"] == "piece"


def test_food_repository_create_and_update(temp_db):
    repo = FoodRepository(db_path=temp_db)
    new_food = FoodCreate(
        class_name="manioc_chips",
        display_name="Manioc Chips (මඤ්ඤොක්කා පෙති)",
        serving_type=ServingType.PORTION,
        standard_serving_g=80.0,
        active=True
    )
    created = repo.create(new_food)
    assert created["id"] is not None
    assert created["class_name"] == "manioc_chips"

    updated = repo.update(created["id"], FoodUpdate(display_name="Spicy Manioc Chips"))
    assert updated["display_name"] == "Spicy Manioc Chips"
