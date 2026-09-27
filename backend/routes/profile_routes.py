"""
profile_routes.py — DEMO WELLNESS PROFILE endpoints.

GET /api/profile  returns the caller's profile (404 if not filled yet)
PUT /api/profile  create-or-update (upsert) the caller's profile

The profile is the input to the AI recommendation engine. Values are
validated at the API boundary (Pydantic ranges) and again before use.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Profile, User
from backend.schemas.schemas import ProfileOut, ProfileUpsert
from backend.utils.security import CurrentUser

logger = logging.getLogger("diet.profile")
router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=ProfileOut)
def get_profile(current: CurrentUser, db: Session = Depends(get_db)):
    """Return the caller's profile — users can only ever see their own."""
    profile = db.query(Profile).filter(Profile.user_id == current.id).first()
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Profile not created yet")
    return profile


@router.put("", response_model=ProfileOut)
def upsert_profile(payload: ProfileUpsert, current: CurrentUser, db: Session = Depends(get_db)):
    """Create or update the caller's profile (idempotent upsert)."""
    profile = db.query(Profile).filter(Profile.user_id == current.id).first()
    if profile is None:
        profile = Profile(user_id=current.id, **payload.model_dump())
        db.add(profile)
        logger.info("Profile created for user %s", current.id)
    else:
        for field, value in payload.model_dump().items():
            setattr(profile, field, value)
        logger.info("Profile updated for user %s", current.id)
    db.commit()
    db.refresh(profile)
    return profile
