from typing import Dict, Any, Optional
from src.profiles.schemas import BMICategory, BMICalculationResult


class ProfileValidator:
    """
    Validation and mathematical utility functions for employee biometrics and health goals.
    """

    @staticmethod
    def calculate_bmi(weight_kg: float, height_cm: float) -> BMICalculationResult:
        """
        Computes Body Mass Index (BMI) dynamically on-the-fly from weight and height.
        Formula: BMI = weight_kg / (height_m ^ 2)
        """
        if height_cm <= 0 or weight_kg <= 0:
            raise ValueError("Height and weight must be strictly positive numbers.")

        height_m = height_cm / 100.0
        bmi_val = round(weight_kg / (height_m ** 2), 1)

        if bmi_val < 18.5:
            category = BMICategory.UNDERWEIGHT
        elif 18.5 <= bmi_val < 25.0:
            category = BMICategory.NORMAL
        elif 25.0 <= bmi_val < 30.0:
            category = BMICategory.OVERWEIGHT
        else:
            category = BMICategory.OBESE

        # Healthy weight range (BMI 18.5 - 24.9) for this height
        min_healthy_kg = round(18.5 * (height_m ** 2), 1)
        max_healthy_kg = round(24.9 * (height_m ** 2), 1)

        return BMICalculationResult(
            bmi=bmi_val,
            category=category,
            healthy_weight_range_kg={
                "min_kg": min_healthy_kg,
                "max_kg": max_healthy_kg
            }
        )

    @staticmethod
    def validate_biometrics(age: int, height_cm: float, weight_kg: float, calorie_target: float) -> None:
        """Validates that biometric metrics are within realistic human ranges."""
        if not (16 <= age <= 100):
            raise ValueError(f"Age {age} is invalid. Must be between 16 and 100 years.")
        if not (100.0 <= height_cm <= 250.0):
            raise ValueError(f"Height {height_cm} cm is invalid. Must be between 100.0 cm and 250.0 cm.")
        if not (30.0 <= weight_kg <= 300.0):
            raise ValueError(f"Weight {weight_kg} kg is invalid. Must be between 30.0 kg and 300.0 kg.")
        if not (800.0 <= calorie_target <= 5000.0):
            raise ValueError(f"Daily calorie target {calorie_target} kcal is invalid. Must be between 800 and 5000 kcal.")
