"""
schemas.py — Pydantic request/response contracts.

Every API input and output is validated here BEFORE it touches the
database or the AI engine. This is input validation at the API boundary
(a core cloud-security control).
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# ----- Allowed enum-ish values (kept as literals for clear 422 errors) -----
ActivityLevel = Literal["sedentary", "light", "moderate", "active", "athlete"]
DietaryPreference = Literal["vegetarian", "vegan", "non_vegetarian", "eggetarian"]
Goal = Literal["weight_loss", "weight_gain", "maintenance", "fitness"]

KNOWN_ALLERGIES = {"nuts", "dairy", "gluten", "eggs", "soy", "fish", "shellfish"}


# =========================================================================
# Auth
# =========================================================================
class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128, description="8+ characters")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: EmailStr
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# =========================================================================
# Profile
# =========================================================================
class ProfileUpsert(BaseModel):
    age: int = Field(ge=10, le=100)
    height_cm: int = Field(ge=100, le=250)
    weight_kg: int = Field(ge=25, le=300)
    activity_level: ActivityLevel
    dietary_preference: DietaryPreference
    goal: Goal
    allergies: str = Field(default="", max_length=255)
    meals_per_day: int = Field(default=3, ge=1, le=6)

    @field_validator("allergies")
    @classmethod
    def _clean_allergies(cls, v: str) -> str:
        """Keep only known allergy tags, lowercase, comma separated."""
        if not v:
            return ""
        tags = [t.strip().lower() for t in v.split(",") if t.strip()]
        unknown = [t for t in tags if t not in KNOWN_ALLERGIES]
        if unknown:
            raise ValueError(f"Unknown allergy tag(s): {', '.join(unknown)}. "
                             f"Allowed: {', '.join(sorted(KNOWN_ALLERGIES))}")
        return ",".join(tags)


class ProfileOut(ProfileUpsert):
    model_config = ConfigDict(from_attributes=True)
    user_id: str
    updated_at: datetime
    bmi_display: str | None = None  # educational, display-only annotation


# =========================================================================
# Diet plan
# =========================================================================
class GeneratePlanRequest(BaseModel):
    """Optional overrides — defaults come from the saved profile."""
    goal: Goal | None = None
    dietary_preference: DietaryPreference | None = None
    allergies: str = Field(default="", max_length=255)


class NutritionSummary(BaseModel):
    calories_kcal: int
    protein_g: int
    carbs_g: int
    fat_g: int
    hydration_reminder: str


class GeneratedPlan(BaseModel):
    """The AI engine's output — previewed in the UI, saved on request."""
    title: str
    breakfast: str
    lunch: str
    snack: str
    dinner: str
    nutrition_summary: NutritionSummary
    engine_used: str
    goal: str
    dietary_preference: str
    disclaimer: str = (
        "Educational/general wellness example — not medical or clinical nutrition advice."
    )


class PlanSaveRequest(BaseModel):
    plan: GeneratedPlan
    title: str | None = Field(default=None, max_length=160)


class PlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    title: str
    breakfast: str
    lunch: str
    snack: str
    dinner: str
    nutrition_summary: dict[str, Any]
    engine_used: str
    goal: str
    dietary_preference: str
    created_at: datetime


# =========================================================================
# Files (object storage metadata)
# =========================================================================
class FileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    storage_path: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime


# =========================================================================
# Dashboard
# =========================================================================
class DashboardOut(BaseModel):
    user: UserOut
    profile: ProfileOut | None
    latest_plan: PlanOut | None
    total_plans: int
    total_files: int
    recent_plans: list[PlanOut]
    recent_files: list[FileOut]
