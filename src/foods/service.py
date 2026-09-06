from pathlib import Path
from typing import Optional, List, Dict, Any

from src.foods.schemas import FoodItem, FoodCreate, FoodUpdate, FoodDetailResponse
from src.foods.repository import FoodRepository
from src.utils.logging import app_logger


class FoodService:
    """
    Business service layer for the Food Catalog domain.
    """

    def __init__(self, repository: Optional[FoodRepository] = None, db_path: Optional[Path] = None):
        self.repository = repository or FoodRepository(db_path=db_path)

    def list_foods(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Returns all food items."""
        return self.repository.get_all(active_only=active_only)

    def get_food(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a food item either by integer ID string or class_name.
        """
        if identifier.isdigit():
            return self.repository.get_by_id(int(identifier))
        return self.repository.get_by_class_name(identifier)

    def register_food(self, food_in: FoodCreate) -> Dict[str, Any]:
        """Registers a new food category."""
        existing = self.repository.get_by_class_name(food_in.class_name)
        if existing:
            app_logger.info(f"Food {food_in.class_name} already exists. Returning existing.")
            return existing
        return self.repository.create(food_in)

    def update_food(self, food_id: int, update_data: FoodUpdate) -> Optional[Dict[str, Any]]:
        """Updates food metadata."""
        return self.repository.update(food_id, update_data)

    def deactivate_food(self, food_id: int) -> bool:
        """Deactivates a food item."""
        return self.repository.delete(food_id)
