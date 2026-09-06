import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from collections import defaultdict

from src.meal_analysis.schemas import (
    DetectionItemInput,
    AnalyzedFoodItem,
    MealTotals,
    MealAnalysisResponse
)
from src.nutrition.service import NutritionService
from src.billing.service import BillingService
from src.foods.service import FoodService
from src.billing.calculator import BillingCalculator
from src.utils.logging import app_logger


class MealAnalysisService:
    """
    Unified Master Adapter integrating YOLO Detections -> Food Catalog -> Nutrition Engine -> Billing Engine.
    """

    def __init__(
        self,
        nutrition_service: Optional[NutritionService] = None,
        billing_service: Optional[BillingService] = None,
        food_service: Optional[FoodService] = None,
        db_path: Optional[Path] = None
    ):
        self.nutrition_service = nutrition_service or NutritionService(db_path=db_path)
        self.billing_service = billing_service or BillingService(db_path=db_path)
        self.food_service = food_service or FoodService(db_path=db_path)

    def analyze_detections(
        self,
        raw_detections: List[Dict[str, Any]],
        annotated_image_base64: Optional[str] = None
    ) -> MealAnalysisResponse:
        """
        Takes raw YOLO detections (e.g. 4 individual bounding boxes of 'string_hoppers', 1 of 'uludu_vade'),
        clusters them by class_name, calculates itemized & total nutrition and price, and returns the response.
        """
        start_time = time.perf_counter()
        latencies: Dict[str, float] = {}

        # 1. Cluster detections by food class_name
        cluster_start = time.perf_counter()
        food_counts: Dict[str, int] = defaultdict(int)
        confidences: Dict[str, List[float]] = defaultdict(list)

        for det in raw_detections:
            # Handle variations in detection dictionary keys
            name = det.get("class_name") or det.get("food_name") or det.get("class") or det.get("name")
            if not name:
                continue
            
            # Skip non-food background detections
            if name.lower() in ["background", "natural", "negative", "none"]:
                continue

            clean_name = name.strip().lower().replace(" ", "_").replace("-", "_")
            qty = int(det.get("quantity", det.get("count", 1)))
            food_counts[clean_name] += max(1, qty)

            conf = det.get("confidence")
            if conf is not None:
                confidences[clean_name].append(float(conf))

        latencies["clustering_ms"] = round((time.perf_counter() - cluster_start) * 1000, 2)

        # 2. Process each clustered food item
        analyzed_items: List[AnalyzedFoodItem] = []
        warnings: List[str] = []

        calc_start = time.perf_counter()
        for food_name, qty in food_counts.items():
            # Get Nutrition
            nutr_item = self.nutrition_service.calculate_single(food_name, qty)
            # Get Billing
            bill_item = self.billing_service.calculate_single(food_name, qty)

            avg_conf = None
            if confidences.get(food_name):
                avg_conf = round(sum(confidences[food_name]) / len(confidences[food_name]), 3)

            if not nutr_item and not bill_item:
                warnings.append(f"Detected food '{food_name}' is not registered in active catalog.")
                continue

            display_name = (
                (nutr_item.display_name if nutr_item else None) or
                (bill_item.display_name if bill_item else None) or
                food_name.replace("_", " ").title()
            )
            serving_type = (
                (nutr_item.serving_type if nutr_item else None) or
                (bill_item.serving_type if bill_item else "piece")
            )
            unit_price = bill_item.unit_price if bill_item else 0.0
            total_price = bill_item.total_price if bill_item else 0.0
            fmt_unit_price = bill_item.formatted_unit_price if bill_item else BillingCalculator.format_currency(0.0)
            fmt_total_price = bill_item.formatted_total_price if bill_item else BillingCalculator.format_currency(0.0)

            calories_kcal = nutr_item.calories_kcal if nutr_item else 0.0
            protein_g = nutr_item.protein_g if nutr_item else 0.0
            carbs_g = nutr_item.carbs_g if nutr_item else 0.0
            fat_g = nutr_item.fat_g if nutr_item else 0.0
            sugar_g = nutr_item.sugar_g if nutr_item else 0.0
            fiber_g = nutr_item.fiber_g if nutr_item else 0.0
            sodium_mg = nutr_item.sodium_mg if nutr_item else 0.0
            source_ref = nutr_item.source if nutr_item else None

            if not nutr_item:
                warnings.append(f"No nutrition data available for '{food_name}'. Nutrition values set to 0.")
            if not bill_item:
                warnings.append(f"No active price found for '{food_name}'. Price set to Rs. 0.00.")

            analyzed_items.append(
                AnalyzedFoodItem(
                    food_name=food_name,
                    display_name=display_name,
                    quantity=qty,
                    serving_type=serving_type,
                    unit_price=unit_price,
                    total_price=total_price,
                    formatted_unit_price=fmt_unit_price,
                    formatted_total_price=fmt_total_price,
                    calories_kcal=calories_kcal,
                    protein_g=protein_g,
                    carbs_g=carbs_g,
                    fat_g=fat_g,
                    sugar_g=sugar_g,
                    fiber_g=fiber_g,
                    sodium_mg=sodium_mg,
                    confidence=avg_conf,
                    source_reference=source_ref
                )
            )

        latencies["nutrition_billing_calc_ms"] = round((time.perf_counter() - calc_start) * 1000, 2)

        # 3. Calculate Grand Totals
        agg_start = time.perf_counter()
        total_items_count = sum(it.quantity for it in analyzed_items)
        total_bill_amount = round(sum(it.total_price for it in analyzed_items), 2)
        total_cal = round(sum(it.calories_kcal for it in analyzed_items), 1)
        total_prot = round(sum(it.protein_g for it in analyzed_items), 1)
        total_carb = round(sum(it.carbs_g for it in analyzed_items), 1)
        total_fat = round(sum(it.fat_g for it in analyzed_items), 1)
        total_sug = round(sum(it.sugar_g for it in analyzed_items), 1)
        total_fib = round(sum(it.fiber_g for it in analyzed_items), 1)
        total_sod = round(sum(it.sodium_mg for it in analyzed_items), 1)

        # Macro Energy Ratios (4 kcal/g for protein/carb, 9 kcal/g for fat)
        p_cal = total_prot * 4.0
        c_cal = total_carb * 4.0
        f_cal = total_fat * 9.0
        macro_sum = p_cal + c_cal + f_cal

        if macro_sum > 0:
            p_pct = round((p_cal / macro_sum) * 100.0, 1)
            c_pct = round((c_cal / macro_sum) * 100.0, 1)
            f_pct = round((f_cal / macro_sum) * 100.0, 1)
        else:
            p_pct, c_pct, f_pct = 0.0, 0.0, 0.0

        meal_totals = MealTotals(
            total_items_count=total_items_count,
            total_bill_amount=total_bill_amount,
            formatted_total_bill=BillingCalculator.format_currency(total_bill_amount),
            currency="LKR",
            calories_kcal=total_cal,
            protein_g=total_prot,
            carbs_g=total_carb,
            fat_g=total_fat,
            sugar_g=total_sug,
            fiber_g=total_fib,
            sodium_mg=total_sod,
            protein_energy_pct=p_pct,
            carbs_energy_pct=c_pct,
            fat_energy_pct=f_pct
        )
        latencies["aggregation_ms"] = round((time.perf_counter() - agg_start) * 1000, 2)
        latencies["total_analysis_ms"] = round((time.perf_counter() - start_time) * 1000, 2)

        return MealAnalysisResponse(
            success=True,
            items=analyzed_items,
            meal_totals=meal_totals,
            warnings=warnings,
            annotated_image_base64=annotated_image_base64,
            execution_latencies_ms=latencies
        )
