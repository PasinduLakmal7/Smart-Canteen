from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Body

from src.recommendations.schemas import (
    RecommendationRequest,
    PersonalizedRecommendationResponse
)
from src.recommendations.engine import RecommendationEngine

recommendation_router = APIRouter(prefix="/api/v1/recommendations", tags=["Phase 6: Personalized Recommendations"])

engine = RecommendationEngine()


@recommendation_router.post("/personalized-meal", response_model=PersonalizedRecommendationResponse)
async def get_personalized_recommendation(request: RecommendationRequest):
    """
    Phase 6: Personalized Recommendation Engine.
    Evaluates:
      1. User Profile (BMI, Goal, Dietary Preferences, Allergens)
      2. Today's Meal History (Consumed Calories & Macros)
      3. Current Scanned Plate Nutrition & Deficits
      4. Available Canteen Food Inventory & Pricing
    """
    try:
        scanned_dicts = [it.model_dump() for it in request.scanned_items] if request.scanned_items else None
        return engine.get_personalized_recommendations(
            employee_code=request.employee_code,
            scanned_items=scanned_dicts,
            time_of_day=request.time_of_day or "lunch"
        )
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation engine error: {str(e)}")


@recommendation_router.get("/suggestions/{employee_code}", response_model=PersonalizedRecommendationResponse)
async def get_suggestions_for_employee(
    employee_code: str,
    time_of_day: str = Query("lunch", description="Meal time (breakfast, lunch, dinner, snack)")
):
    """
    Fast lookup for personalized meal combos when an employee is recognized via Face Biometrics (Phase 4).
    """
    try:
        return engine.get_personalized_recommendations(
            employee_code=employee_code,
            scanned_items=None,
            time_of_day=time_of_day
        )
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation error: {str(e)}")
