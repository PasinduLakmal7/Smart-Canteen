"""
Meal Analysis Subsystem (Phase 2).
Integrates YOLO Detection -> Food Catalog -> Nutrition Assessment + Automated Billing.
"""
from src.meal_analysis.schemas import (
    DetectionItemInput,
    AnalyzedFoodItem,
    MealTotals,
    MealAnalysisResponse
)
from src.meal_analysis.service import MealAnalysisService

__all__ = [
    "DetectionItemInput",
    "AnalyzedFoodItem",
    "MealTotals",
    "MealAnalysisResponse",
    "MealAnalysisService"
]
