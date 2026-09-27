"""
diet_routes.py — AI PLAN GENERATION endpoint.

POST /api/diet/generate-plan
    Builds UserPreferences from the caller's saved profile (with optional
    per-request overrides), asks the engine factory for a plan (AI API with
    automatic rule-based fallback), and returns it as a PREVIEW.

    Nothing is persisted here — saving is an explicit POST /api/plans,
    which mirrors how the UI works (Generate -> review -> Save).
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.ai_engine.diet_engine import get_diet_engine
from backend.ai_engine.rule_based_engine import UserPreferences
from backend.database import get_db
from backend.models import Profile
from backend.schemas.schemas import GeneratePlanRequest, GeneratedPlan
from backend.utils.security import CurrentUser

logger = logging.getLogger("diet.routes")
router = APIRouter(prefix="/api/diet", tags=["diet"])


def _preferences_from(profile: Profile | None, user_id: str, payload: GeneratePlanRequest) -> UserPreferences:
    """Merge saved profile + request overrides into engine preferences."""
    allergies = set(
        a.strip().lower() for a in ((profile.allergies if profile else "") or "").split(",") if a.strip()
    )
    allergies |= set(a.strip().lower() for a in (payload.allergies or "").split(",") if a.strip())

    return UserPreferences(
        user_id=user_id,
        age=profile.age if profile else 25,
        height_cm=profile.height_cm if profile else 170,
        weight_kg=profile.weight_kg if profile else 65,
        activity_level=profile.activity_level if profile else "moderate",
        dietary_preference=payload.dietary_preference
        or (profile.dietary_preference if profile else "vegetarian"),
        goal=payload.goal or (profile.goal if profile else "maintenance"),
        allergies=sorted(allergies),
    )


@router.post("/generate-plan", response_model=GeneratedPlan)
def generate_plan(payload: GeneratePlanRequest, current: CurrentUser, db: Session = Depends(get_db)):
    """Generate (but don't save) a personalized one-day meal plan."""
    profile = db.query(Profile).filter(Profile.user_id == current.id).first()
    prefs = _preferences_from(profile, current.id, payload)

    engine = get_diet_engine()
    result = engine.generate(prefs)  # fallback handled inside the factory wrapper
    logger.info("Plan preview for user %s via %s", current.id, result.engine_used)
    return GeneratedPlan(**result.to_dict())
