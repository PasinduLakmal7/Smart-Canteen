from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DetectionItemInput(BaseModel):
    food_name: str = Field(..., description="YOLO detected class name")
    quantity: int = Field(default=1, ge=1, description="Quantity / portion count")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Detection confidence score")
    bbox: Optional[List[float]] = Field(default=None, description="Bounding box [x1, y1, x2, y2]")


class AnalyzedFoodItem(BaseModel):
    food_name: str
    display_name: str
    quantity: int
    serving_type: str
    unit_price: float
    total_price: float
    formatted_unit_price: str
    formatted_total_price: str
    calories_kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float
    sugar_g: float = 0.0
    fiber_g: float = 0.0
    sodium_mg: float = 0.0
    confidence: Optional[float] = None
    source_reference: Optional[str] = None


class MealTotals(BaseModel):
    total_items_count: int
    total_bill_amount: float
    formatted_total_bill: str
    currency: str = "LKR"
    calories_kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float
    sugar_g: float = 0.0
    fiber_g: float = 0.0
    sodium_mg: float = 0.0
    protein_energy_pct: float = 0.0
    carbs_energy_pct: float = 0.0
    fat_energy_pct: float = 0.0


class MealAnalysisResponse(BaseModel):
    success: bool = True
    items: List[AnalyzedFoodItem]
    meal_totals: MealTotals
    warnings: List[str] = []
    annotated_image_base64: Optional[str] = None
    execution_latencies_ms: Dict[str, float] = {}
