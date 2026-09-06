import pytest
from src.nutrition.calculator import NutritionCalculator


def test_scale_nutrient():
    calc = NutritionCalculator()
    # 70 kcal per 1 piece -> 4 pieces = 280 kcal
    assert calc.scale_nutrient(70.0, 1.0, 4) == 280.0
    # 150 kcal per 100g -> 250g = 375 kcal
    assert calc.scale_nutrient(150.0, 100.0, 250) == 375.0


def test_calculate_item_nutrition():
    calc = NutritionCalculator()
    mock_record = {
        "basis_amount": 1.0,
        "calories_kcal": 70.0,
        "protein_g": 2.1,
        "carbs_g": 14.5,
        "fat_g": 0.7,
        "sugar_g": 0.2,
        "fiber_g": 0.8,
        "sodium_mg": 18.0,
        "source_name": "MRI Sri Lanka"
    }

    item = calc.calculate_item_nutrition(
        food_name="string_hoppers",
        display_name="String Hoppers",
        quantity=4,
        nutr_record=mock_record,
        serving_type="piece"
    )

    assert item.food_name == "string_hoppers"
    assert item.quantity == 4
    assert item.calories_kcal == 280.0
    assert item.protein_g == 8.4
    assert item.carbs_g == 58.0
    assert item.fat_g == 2.8


def test_aggregate_nutrition():
    calc = NutritionCalculator()
    item1 = calc.calculate_item_nutrition(
        food_name="string_hoppers",
        display_name="String Hoppers",
        quantity=4,
        nutr_record={"basis_amount": 1.0, "calories_kcal": 70.0, "protein_g": 2.1, "carbs_g": 14.5, "fat_g": 0.7}
    )
    item2 = calc.calculate_item_nutrition(
        food_name="uludu_vade",
        display_name="Uludu Vade",
        quantity=1,
        nutr_record={"basis_amount": 1.0, "calories_kcal": 140.0, "protein_g": 4.2, "carbs_g": 16.5, "fat_g": 6.8}
    )

    totals = calc.aggregate_nutrition([item1, item2])
    assert totals.calories_kcal == 420.0
    assert totals.protein_g == 12.6
    assert totals.carbs_g == 74.5
    assert totals.fat_g == 9.6
    assert totals.protein_percentage > 0.0
    assert totals.carbs_percentage > 0.0
