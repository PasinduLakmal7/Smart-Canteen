from typing import List, Dict, Any
from src.nutrition.schemas import (
    NutritionCalculationItem,
    MacroBreakdown,
    NutritionCalculationResult
)


class NutritionCalculator:
    """
    Pure mathematical calculator for scaling and aggregating nutrient values.
    """

    @staticmethod
    def scale_nutrient(base_value: float, basis_amount: float, quantity: float) -> float:
        """
        Scales a nutrient value based on quantity and basis amount.
        Formula: (base_value / basis_amount) * quantity
        """
        if basis_amount <= 0:
            basis_amount = 1.0
        return round((base_value / basis_amount) * quantity, 2)

    @classmethod
    def calculate_item_nutrition(
        cls,
        food_name: str,
        display_name: str,
        quantity: int,
        nutr_record: Dict[str, Any],
        serving_type: str = "piece"
    ) -> NutritionCalculationItem:
        """
        Computes the scaled nutrition values for a single food item with a given quantity.
        """
        basis_amount = float(nutr_record.get("basis_amount", 1.0))

        cal = cls.scale_nutrient(float(nutr_record.get("calories_kcal", 0.0)), basis_amount, quantity)
        prot = cls.scale_nutrient(float(nutr_record.get("protein_g", 0.0)), basis_amount, quantity)
        carb = cls.scale_nutrient(float(nutr_record.get("carbs_g", 0.0)), basis_amount, quantity)
        fat = cls.scale_nutrient(float(nutr_record.get("fat_g", 0.0)), basis_amount, quantity)
        sug = cls.scale_nutrient(float(nutr_record.get("sugar_g", 0.0)), basis_amount, quantity)
        fib = cls.scale_nutrient(float(nutr_record.get("fiber_g", 0.0)), basis_amount, quantity)
        sod = cls.scale_nutrient(float(nutr_record.get("sodium_mg", 0.0)), basis_amount, quantity)

        return NutritionCalculationItem(
            food_name=food_name,
            display_name=display_name,
            quantity=quantity,
            serving_type=serving_type,
            calories_kcal=round(cal, 1),
            protein_g=round(prot, 1),
            carbs_g=round(carb, 1),
            fat_g=round(fat, 1),
            sugar_g=round(sug, 1),
            fiber_g=round(fib, 1),
            sodium_mg=round(sod, 1),
            source=nutr_record.get("source_name")
        )

    @classmethod
    def aggregate_nutrition(cls, items: List[NutritionCalculationItem]) -> MacroBreakdown:
        """
        Aggregates individual nutrient items into a meal total with macro percentage distribution.
        """
        total_cal = sum(item.calories_kcal for item in items)
        total_prot = sum(item.protein_g for item in items)
        total_carb = sum(item.carbs_g for item in items)
        total_fat = sum(item.fat_g for item in items)
        total_sug = sum(item.sugar_g for item in items)
        total_fib = sum(item.fiber_g for item in items)
        total_sod = sum(item.sodium_mg for item in items)

        # Calculate macro energy percentages: Protein 4 kcal/g, Carbs 4 kcal/g, Fat 9 kcal/g
        p_cal = total_prot * 4.0
        c_cal = total_carb * 4.0
        f_cal = total_fat * 9.0
        macro_cal_sum = p_cal + c_cal + f_cal

        if macro_cal_sum > 0:
            p_pct = round((p_cal / macro_cal_sum) * 100.0, 1)
            c_pct = round((c_cal / macro_cal_sum) * 100.0, 1)
            f_pct = round((f_cal / macro_cal_sum) * 100.0, 1)
        else:
            p_pct, c_pct, f_pct = 0.0, 0.0, 0.0

        return MacroBreakdown(
            calories_kcal=round(total_cal, 1),
            protein_g=round(total_prot, 1),
            carbs_g=round(total_carb, 1),
            fat_g=round(total_fat, 1),
            sugar_g=round(total_sug, 1),
            fiber_g=round(total_fib, 1),
            sodium_mg=round(total_sod, 1),
            protein_percentage=p_pct,
            carbs_percentage=c_pct,
            fat_percentage=f_pct
        )
