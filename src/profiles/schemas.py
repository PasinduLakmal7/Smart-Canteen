from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class DietType(str, Enum):
    NORMAL = "normal"
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    PESCATARIAN = "pescatarian"
    HALAL = "halal"
    DIABETIC = "diabetic"


class HealthGoal(str, Enum):
    MAINTAIN = "maintain"
    WEIGHT_LOSS = "weight_loss"
    WEIGHT_GAIN = "weight_gain"
    HIGH_PROTEIN = "high_protein"
    LOW_CARB = "low_carb"
    HEART_HEALTHY = "heart_healthy"


class PreferenceType(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    AVOID = "avoid"


class BMICategory(str, Enum):
    UNDERWEIGHT = "Underweight (< 18.5)"
    NORMAL = "Normal weight (18.5 - 24.9)"
    OVERWEIGHT = "Overweight (25.0 - 29.9)"
    OBESE = "Obese (>= 30.0)"


class BMICalculationResult(BaseModel):
    bmi: float
    category: BMICategory
    healthy_weight_range_kg: Dict[str, float]


# --- Employee Models ---
class EmployeeBase(BaseModel):
    employee_code: str = Field(..., description="Unique employee identifier (e.g. EMP001)")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    department: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=3, max_length=150)
    active: bool = Field(default=True)

    @field_validator("employee_code")
    @classmethod
    def sanitize_code(cls, v: str) -> str:
        clean = v.strip().upper()
        if not clean:
            raise ValueError("Employee code cannot be empty.")
        return clean

    @field_validator("email")
    @classmethod
    def sanitize_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if "@" not in clean or "." not in clean:
            raise ValueError("Invalid email format.")
        return clean


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    department: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = None
    active: Optional[bool] = None

    @field_validator("email")
    @classmethod
    def validate_opt_email(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip().lower()
            if "@" not in clean or "." not in clean:
                raise ValueError("Invalid email format.")
            return clean
        return v


class EmployeeItem(EmployeeBase):
    id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# --- User Profile Models ---
class UserProfileBase(BaseModel):
    age: int = Field(..., ge=16, le=100, description="Age in years (16 - 100)")
    height_cm: float = Field(..., ge=100.0, le=250.0, description="Height in centimeters (100.0 - 250.0)")
    weight_kg: float = Field(..., ge=30.0, le=300.0, description="Body weight in kg (30.0 - 300.0)")
    daily_calorie_target: float = Field(default=2000.0, ge=800.0, le=5000.0, description="Daily target calories in kcal")
    diet_type: DietType = Field(default=DietType.NORMAL)
    health_goal: HealthGoal = Field(default=HealthGoal.MAINTAIN)
    notes: Optional[str] = Field(default="", max_length=500)


class UserProfileCreate(UserProfileBase):
    pass


class UserProfileUpdate(BaseModel):
    age: Optional[int] = Field(None, ge=16, le=100)
    height_cm: Optional[float] = Field(None, ge=100.0, le=250.0)
    weight_kg: Optional[float] = Field(None, ge=30.0, le=300.0)
    daily_calorie_target: Optional[float] = Field(None, ge=800.0, le=5000.0)
    diet_type: Optional[DietType] = None
    health_goal: Optional[HealthGoal] = None
    notes: Optional[str] = Field(None, max_length=500)


class UserProfileItem(UserProfileBase):
    id: int
    employee_id: int
    bmi: Optional[float] = None
    bmi_category: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# --- Food Preference Models ---
class FoodPreferenceItem(BaseModel):
    food_name: str
    preference_type: PreferenceType


class FoodPreferenceSet(BaseModel):
    likes: List[str] = Field(default_factory=list, description="List of liked food class names")
    dislikes: List[str] = Field(default_factory=list, description="List of disliked food class names")
    avoid: List[str] = Field(default_factory=list, description="List of avoided/allergen food class names")


# --- Complete Unified Profile ---
class CompleteEmployeeProfile(BaseModel):
    employee_id: int
    employee_code: str
    name: str
    first_name: str
    last_name: str
    department: str
    email: str
    active: bool
    profile: Optional[UserProfileItem] = None
    preferences: FoodPreferenceSet = Field(default_factory=FoodPreferenceSet)
