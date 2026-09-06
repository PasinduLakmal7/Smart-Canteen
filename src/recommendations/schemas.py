from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ScannedFoodInput(BaseModel):
    food_name: str
    quantity: int = Field(1, ge=1)
    portion_size_g: Optional[float] = None


class RecommendationRequest(BaseModel):
    employee_code: str
    scanned_items: Optional[List[ScannedFoodInput]] = None
    time_of_day: Optional[str] = "lunch"  # breakfast, lunch, dinner, snack


class FoodRecommendationItem(BaseModel):
    id: int
    food_name: str
    display_name: str
    price_lkr: float
    portion_size: str
    calories_kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    category: str
    emoji: str
    reason: Optional[str] = None


class MealCombo(BaseModel):
    combo_id: str
    title: str
    description: str
    items: List[FoodRecommendationItem]
    total_calories: float
    total_price_lkr: float
    formatted_total_price: str
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    total_fiber_g: float
    match_score: int
    goal_alignment_tag: str


class PlateAddOnSuggestion(BaseModel):
    item: FoodRecommendationItem
    why_add: str
    benefit_type: str  # protein, fiber, low_cal, balance


class NutritionalBudgetStatus(BaseModel):
    daily_target_calories: float
    today_consumed_calories: float
    remaining_calories: float
    current_plate_calories: float
    projected_remaining_calories: float
    budget_status: str  # optimal, approaching_limit, exceeded


class PersonalizedRecommendationResponse(BaseModel):
    success: bool = True
    employee_code: str
    employee_name: str
    department: str
    health_goal: str
    diet_type: str
    bmi: float
    bmi_category: str
    dietary_restrictions: List[str]
    budget_status: NutritionalBudgetStatus
    recommended_combos: List[MealCombo]
    smart_add_ons: List[PlateAddOnSuggestion]
    warnings: List[str]
    health_nudge: str
