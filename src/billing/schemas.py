from typing import Optional, List
from pydantic import BaseModel, Field


class PriceRecord(BaseModel):
    id: int
    food_id: int
    serving_type: str
    price: float = Field(..., ge=0.0, description="Unit price in LKR (Rs.)")
    active: bool = True
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None


class PriceUpdate(BaseModel):
    price: float = Field(..., ge=0.0, description="Updated unit price in LKR (Rs.)")
    serving_type: Optional[str] = None


class BillingItem(BaseModel):
    food_name: str
    display_name: str
    quantity: int = Field(..., ge=1)
    serving_type: str = "piece"
    unit_price: float = Field(..., ge=0.0)
    total_price: float = Field(..., ge=0.0)
    formatted_unit_price: str
    formatted_total_price: str


class BillingCalculationResult(BaseModel):
    items: List[BillingItem]
    item_count: int
    subtotal: float
    discount: float = 0.0
    tax: float = 0.0
    total_amount: float
    currency: str = "LKR"
    formatted_total: str
    warnings: List[str] = []
