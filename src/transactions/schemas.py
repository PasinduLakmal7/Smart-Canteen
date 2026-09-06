from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class PaymentStatus(str, Enum):
    COMPLETED = "completed"
    PENDING = "pending"
    PAYROLL_DEDUCTED = "payroll_deducted"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    PAYROLL = "payroll"
    NFC = "nfc"
    CASH = "cash"
    QR = "qr"


class TransactionItemInput(BaseModel):
    food_name: Optional[str] = Field(None, description="Food class name (e.g. 'chicken_curry' or 'rice_and_curry')")
    food_id: Optional[int] = Field(None, description="Database food ID")
    quantity: int = Field(default=1, ge=1, description="Portion / count (minimum 1)")
    portion_size_g: Optional[float] = Field(None, ge=1.0, description="Custom portion weight in grams")


class TransactionCreateRequest(BaseModel):
    employee_id: Optional[int] = Field(None, description="Employee numeric database ID")
    employee_code: Optional[str] = Field(None, description="Employee identifier (e.g. 'EMP001' or 'EMP2026')")
    items: List[TransactionItemInput] = Field(..., min_length=1, description="List of food items inside the meal")
    payment_method: PaymentMethod = Field(default=PaymentMethod.PAYROLL)
    payment_status: PaymentStatus = Field(default=PaymentStatus.COMPLETED)
    notes: Optional[str] = Field(None, max_length=255)

    @field_validator("items")
    @classmethod
    def validate_items_present(cls, v: List[TransactionItemInput]) -> List[TransactionItemInput]:
        if not v:
            raise ValueError("A transaction must contain at least one food item.")
        for item in v:
            if not item.food_name and not item.food_id:
                raise ValueError("Each item must have either a 'food_name' or a 'food_id'.")
        return v


class TransactionItemResponse(BaseModel):
    id: int
    transaction_id: int
    food_id: Optional[int] = None
    food_name: str
    display_name: str
    quantity: int
    serving_size_g: float
    calories: float
    protein: float
    carbs: float
    fat: float
    sugar: float = 0.0
    fiber: float = 0.0
    sodium_mg: float = 0.0
    unit_price: float
    subtotal: float


class TransactionResponse(BaseModel):
    id: int
    transaction_code: str
    employee_id: int
    employee_code: str
    employee_name: str
    department: str
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fat: float
    total_sugar: float = 0.0
    total_fiber: float = 0.0
    total_sodium_mg: float = 0.0
    total_amount: float
    formatted_total_amount: str
    payment_status: str
    payment_method: str
    transaction_date: str
    created_at: str
    items: List[TransactionItemResponse] = []


class MealHistoryItem(BaseModel):
    transaction_id: int
    transaction_code: str
    foods: List[str]
    items_detail: List[Dict[str, Any]] = []
    calories: float
    amount: float
    formatted_amount: str
    date: str
    time: str
    timestamp: str
    macros: Dict[str, float]


class EmployeeMealHistoryResponse(BaseModel):
    employee_id: int
    employee_code: str
    employee_name: str
    department: str
    total_meals: int
    total_calories: float
    total_spent_lkr: float
    formatted_total_spent: str
    meals: List[MealHistoryItem]


class MonthlySummaryResponse(BaseModel):
    employee_id: int
    employee_code: str
    employee_name: str
    month: str
    total_meals: int
    total_calories: float
    total_spent: float
    formatted_total_spent: str
    avg_daily_calories: float
    avg_meal_cost: float
    macro_distribution_pct: Dict[str, float]


class CanteenAnalyticsSummary(BaseModel):
    total_transactions: int
    total_revenue_lkr: float
    formatted_total_revenue: str
    today_transactions: int
    today_revenue_lkr: float
    formatted_today_revenue: str
    total_calories_served: float
    top_dishes: List[Dict[str, Any]] = []
