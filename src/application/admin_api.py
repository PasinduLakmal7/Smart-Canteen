from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends

from src.foods.schemas import FoodItem, FoodCreate, FoodUpdate, FoodDetailResponse
from src.foods.service import FoodService
from src.nutrition.schemas import NutritionInfo, NutritionUpdate
from src.nutrition.service import NutritionService
from src.billing.schemas import PriceRecord, PriceUpdate
from src.billing.service import BillingService

admin_router = APIRouter(prefix="/api/v1/admin", tags=["Admin Food Management"])

# Dependency instances
food_service = FoodService()
nutrition_service = NutritionService()
billing_service = BillingService()


@admin_router.get("/foods", response_model=List[Dict[str, Any]])
async def list_admin_foods():
    """Returns all food items including inactive ones with price and nutrition."""
    foods = food_service.list_foods(active_only=False)
    results = []
    for f in foods:
        fid = f["id"]
        cname = f["class_name"]
        price_rec = billing_service.billing_repo.get_current_price_by_food_id(fid)
        nutr_rec = nutrition_service.nutrition_repo.get_by_food_id(fid)
        results.append({
            **f,
            "current_price": price_rec["price"] if price_rec else None,
            "nutrition": nutr_rec
        })
    return results


@admin_router.post("/foods", response_model=Dict[str, Any])
async def create_food(food_in: FoodCreate):
    """Registers a new food category."""
    try:
        return food_service.register_food(food_in)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@admin_router.put("/foods/{food_id}", response_model=Dict[str, Any])
async def update_food(food_id: int, update_in: FoodUpdate):
    """Updates food details (display name, serving type, active status)."""
    res = food_service.update_food(food_id, update_in)
    if not res:
        raise HTTPException(status_code=404, detail=f"Food item {food_id} not found")
    return res


@admin_router.put("/foods/{food_id}/price", response_model=Dict[str, Any])
async def update_food_price(food_id: int, price_in: PriceUpdate):
    """Updates canteen unit price for a food item (creates an audit price record)."""
    food = food_service.get_food(str(food_id))
    if not food:
        raise HTTPException(status_code=404, detail=f"Food item {food_id} not found")
    return billing_service.update_price(food_id, price_in)


@admin_router.put("/foods/{food_id}/nutrition", response_model=Dict[str, Any])
async def update_food_nutrition(food_id: int, nutr_in: NutritionUpdate):
    """Updates nutritional values for a food item."""
    food = food_service.get_food(str(food_id))
    if not food:
        raise HTTPException(status_code=404, detail=f"Food item {food_id} not found")
    res = nutrition_service.update_food_nutrition(food_id, nutr_in)
    if not res:
        raise HTTPException(status_code=400, detail="Failed to update nutrition record")
    return res


@admin_router.delete("/foods/{food_id}")
async def deactivate_food(food_id: int):
    """Deactivates a food item from the canteen menu."""
    success = food_service.deactivate_food(food_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Food item {food_id} not found")
    return {"success": True, "message": f"Food {food_id} deactivated successfully"}
