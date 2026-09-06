from pathlib import Path
from typing import Optional, List, Dict, Any, Union

from src.nutrition.schemas import (
    NutritionCalculationItem,
    MacroBreakdown,
    NutritionCalculationResult,
    NutritionUpdate
)
from src.nutrition.repository import NutritionRepository
from src.nutrition.calculator import NutritionCalculator
from src.foods.repository import FoodRepository
from src.utils.logging import app_logger


class NutritionService:
    """
    Service Layer for Nutrition assessment and calculation.
    """

    def __init__(
        self,
        nutrition_repo: Optional[NutritionRepository] = None,
        food_repo: Optional[FoodRepository] = None,
        db_path: Optional[Path] = None
    ):
        self.nutrition_repo = nutrition_repo or NutritionRepository(db_path=db_path)
        self.food_repo = food_repo or FoodRepository(db_path=db_path)
        self.calculator = NutritionCalculator()

    def calculate_single(self, food_name: str, quantity: int = 1) -> Optional[NutritionCalculationItem]:
        """
        Calculates nutrition for a single food item and quantity.
        """
        if quantity <= 0:
            quantity = 1

        nutr_record = self.nutrition_repo.get_by_class_name(food_name)
        if not nutr_record:
            app_logger.warning(f"No active nutrition record found for food: '{food_name}'")
            return None

        display_name = nutr_record.get("display_name", food_name.replace("_", " ").title())
        serving_type = nutr_record.get("serving_type", "piece")

        return self.calculator.calculate_item_nutrition(
            food_name=food_name,
            display_name=display_name,
            quantity=quantity,
            nutr_record=nutr_record,
            serving_type=serving_type
        )

    def calculate_meal_nutrition(self, items_input: List[Dict[str, Any]]) -> NutritionCalculationResult:
        """
        Calculates and aggregates nutrition for a list of detected food items.
        Input format: [{"food_name": "string_hoppers", "quantity": 4}, ...]
        """
        calculated_items: List[NutritionCalculationItem] = []
        warnings: List[str] = []

        for req in items_input:
            food_name = req.get("food_name") or req.get("name") or req.get("food")
            if not food_name:
                continue

            qty = int(req.get("quantity", req.get("count", 1)))
            if qty <= 0:
                warnings.append(f"Invalid quantity {qty} for food '{food_name}'. Defaulted to 1.")
                qty = 1

            item_nutr = self.calculate_single(food_name, qty)
            if item_nutr:
                calculated_items.append(item_nutr)
            else:
                warnings.append(f"Detected food has no nutrition record: '{food_name}'")

        totals = self.calculator.aggregate_nutrition(calculated_items)
        return NutritionCalculationResult(
            items=calculated_items,
            totals=totals,
            warnings=warnings
        )

    def update_food_nutrition(self, food_id: int, update_data: NutritionUpdate) -> Optional[Dict[str, Any]]:
        """Updates nutrition values for admin operations."""
        return self.nutrition_repo.update_nutrition(food_id, update_data)
