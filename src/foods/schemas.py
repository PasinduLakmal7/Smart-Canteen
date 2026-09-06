from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class ServingType(str, Enum):
    PIECE = "piece"
    SERVING = "serving"
    PORTION = "portion"


class FoodBase(BaseModel):
    class_name: str = Field(..., description="Unique machine-readable YOLO class name (e.g. string_hoppers)")
    display_name: str = Field(..., description="Human-readable food title with bilingual support")
    serving_type: ServingType = Field(default=ServingType.PIECE, description="Serving unit type")
    standard_serving_g: float = Field(default=100.0, ge=1.0, description="Standard weight in grams per unit")
    active: bool = Field(default=True, description="Whether food is currently active in the canteen")

    @validator("class_name")
    def sanitize_class_name(cls, v):
        clean = v.strip().lower().replace(" ", "_").replace("-", "_")
        if not clean:
            raise ValueError("class_name cannot be empty")
        return clean


class FoodCreate(FoodBase):
    pass


class FoodUpdate(BaseModel):
    display_name: Optional[str] = None
    serving_type: Optional[ServingType] = None
    standard_serving_g: Optional[float] = Field(None, ge=1.0)
    active: Optional[bool] = None


class FoodItem(FoodBase):
    id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        orm_mode = True


class FoodDetailResponse(FoodItem):
    current_price: Optional[float] = None
    nutrition: Optional[Dict[str, Any]] = None
