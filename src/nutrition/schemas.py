from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class NutritionBasis(str, Enum):
    PER_UNIT = "per_unit"
    PER_100G = "per_100g"


class NutritionBase(BaseModel):
    basis_type: NutritionBasis = Field(default=NutritionBasis.PER_UNIT, description="Nutrient calculation basis")
    basis_amount: float = Field(default=1.0, ge=0.01, description="Amount of basis (e.g. 1.0 unit or 100.0g)")
    calories_kcal: float = Field(..., ge=0.0, description="Energy in kilocalories (kcal)")
    protein_g: float = Field(..., ge=0.0, description="Protein in grams")
    carbs_g: float = Field(..., ge=0.0, description="Carbohydrates in grams")
    fat_g: float = Field(..., ge=0.0, description="Total fat in grams")
    sugar_g: float = Field(default=0.0, ge=0.0, description="Free sugars in grams")
    fiber_g: float = Field(default=0.0, ge=0.0, description="Dietary fiber in grams")
    sodium_mg: float = Field(default=0.0, ge=0.0, description="Sodium content in milligrams")
    source_name: Optional[str] = Field(default="MRI Sri Lanka / USDA", description="Scientific data provenance")
    source_reference: Optional[str] = Field(default="Food Composition Tables, 2021", description="Academic citation")
    verified: bool = Field(default=True, description="Whether data has been peer/canteen verified")


class NutritionInfo(NutritionBase):
    id: int
    food_id: int


class NutritionUpdate(BaseModel):
    basis_type: Optional[NutritionBasis] = None
    basis_amount: Optional[float] = Field(None, ge=0.01)
    calories_kcal: Optional[float] = Field(None, ge=0.0)
    protein_g: Optional[float] = Field(None, ge=0.0)
    carbs_g: Optional[float] = Field(None, ge=0.0)
    fat_g: Optional[float] = Field(None, ge=0.0)
    sugar_g: Optional[float] = Field(None, ge=0.0)
    fiber_g: Optional[float] = Field(None, ge=0.0)
    sodium_mg: Optional[float] = Field(None, ge=0.0)
    source_name: Optional[str] = None
    source_reference: Optional[str] = None


class NutritionCalculationItem(BaseModel):
    food_name: str
    display_name: str
    quantity: int = Field(..., ge=1)
    serving_type: str = "piece"
    calories_kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float
    sugar_g: float = 0.0
    fiber_g: float = 0.0
    sodium_mg: float = 0.0
    source: Optional[str] = None


class MacroBreakdown(BaseModel):
    calories_kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float
    sugar_g: float = 0.0
    fiber_g: float = 0.0
    sodium_mg: float = 0.0
    protein_percentage: float = 0.0
    carbs_percentage: float = 0.0
    fat_percentage: float = 0.0


class NutritionCalculationResult(BaseModel):
    items: List[NutritionCalculationItem]
    totals: MacroBreakdown
    warnings: List[str] = []
