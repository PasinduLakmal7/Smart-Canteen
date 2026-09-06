from pathlib import Path
from typing import Optional, List, Dict, Any

from src.billing.schemas import BillingItem, BillingCalculationResult, PriceUpdate
from src.billing.repository import BillingRepository
from src.billing.calculator import BillingCalculator
from src.foods.repository import FoodRepository
from src.utils.logging import app_logger


class BillingService:
    """
    Service Layer for Canteen Automated Billing.
    """

    def __init__(
        self,
        billing_repo: Optional[BillingRepository] = None,
        food_repo: Optional[FoodRepository] = None,
        db_path: Optional[Path] = None
    ):
        self.billing_repo = billing_repo or BillingRepository(db_path=db_path)
        self.food_repo = food_repo or FoodRepository(db_path=db_path)
        self.calculator = BillingCalculator()

    def calculate_single(self, food_name: str, quantity: int = 1) -> Optional[BillingItem]:
        """Calculates billing for a single food item."""
        if quantity <= 0:
            quantity = 1

        price_record = self.billing_repo.get_current_price_by_class_name(food_name)
        if not price_record:
            app_logger.warning(f"No active price record found for food: '{food_name}'")
            return None

        display_name = price_record.get("display_name", food_name.replace("_", " ").title())
        unit_price = float(price_record.get("price", 0.0))
        serving_type = price_record.get("serving_type") or price_record.get("food_serving_type", "piece")

        return self.calculator.calculate_item_bill(
            food_name=food_name,
            display_name=display_name,
            quantity=quantity,
            unit_price=unit_price,
            serving_type=serving_type
        )

    def calculate_meal_bill(
        self,
        items_input: List[Dict[str, Any]],
        discount: float = 0.0,
        tax: float = 0.0
    ) -> BillingCalculationResult:
        """
        Calculates and aggregates bill for multiple detected items.
        Input format: [{"food_name": "string_hoppers", "quantity": 4}, ...]
        """
        billing_items: List[BillingItem] = []
        warnings: List[str] = []

        for req in items_input:
            food_name = req.get("food_name") or req.get("name") or req.get("food")
            if not food_name:
                continue

            qty = int(req.get("quantity", req.get("count", 1)))
            if qty <= 0:
                warnings.append(f"Invalid quantity {qty} for food '{food_name}'. Defaulted to 1.")
                qty = 1

            item_bill = self.calculate_single(food_name, qty)
            if item_bill:
                billing_items.append(item_bill)
            else:
                warnings.append(f"Detected food has no active price: '{food_name}'")

        result = self.calculator.aggregate_bill(billing_items, discount=discount, tax=tax)
        result.warnings = warnings
        return result

    def update_price(self, food_id: int, price_in: PriceUpdate) -> Dict[str, Any]:
        """Admin operation to update food price."""
        return self.billing_repo.set_price(food_id, price_in)
