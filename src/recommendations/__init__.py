"""
Smart Canteen AI — Phase 6: Personalized Meal Recommendation Engine.
Integrates User Health Profiles, Today's Meal History, Current Plate Nutrition, and Available Canteen Foods.
"""
from src.recommendations.engine import RecommendationEngine
from src.recommendations.schemas import (
    RecommendationRequest,
    PersonalizedRecommendationResponse,
    MealCombo,
    PlateAddOnSuggestion,
    FoodRecommendationItem
)

__all__ = [
    "RecommendationEngine",
    "RecommendationRequest",
    "PersonalizedRecommendationResponse",
    "MealCombo",
    "PlateAddOnSuggestion",
    "FoodRecommendationItem"
]
