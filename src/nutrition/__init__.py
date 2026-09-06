"""
Nutrition Assessment Subsystem (Phase 2).
Calculates calories, macronutrients, and micronutrients scaled by item quantities.
"""
from src.nutrition.schemas import (
    NutritionBasis,
    NutritionInfo,
    NutritionUpdate,
    NutritionCalculationItem,
    NutritionCalculationResult,
    MacroBreakdown
)
from src.nutrition.repository import NutritionRepository
from src.nutrition.calculator import NutritionCalculator
from src.nutrition.service import NutritionService

__all__ = [
    "NutritionBasis",
    "NutritionInfo",
    "NutritionUpdate",
    "NutritionCalculationItem",
    "NutritionCalculationResult",
    "MacroBreakdown",
    "NutritionRepository",
    "NutritionCalculator",
    "NutritionService"
]
