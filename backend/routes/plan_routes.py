"""
plan_routes.py — SAVED DIET PLAN endpoints (cloud database rows).

POST   /api/plans       save a generated plan (from the preview screen)
GET    /api/plans       list MY saved plans (newest first)
GET    /api/plans/{id}  fetch one of MY plans
DELETE /api/plans/{id}  delete one of MY plans

USER ISOLATION: every query is filtered by the JWT-derived user id, and
foreign plan ids return 404 (not 403) so the API never confirms the
existence of another user's data.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import DietPlan, User
from backend.schemas.schemas import PlanOut, PlanSaveRequest
from backend.utils.security import CurrentUser

logger = logging.getLogger("diet.plans")
router = APIRouter(prefix="/api/plans", tags=["plans"])


@router.post("", response_model=PlanOut, status_code=status.HTTP_201_CREATED)
def save_plan(payload: PlanSaveRequest, current: CurrentUser, db: Session = Depends(get_db)):
    """Persist a generated plan to the cloud database, owned by the caller."""
    plan = DietPlan(
        user_id=current.id,
        title=(payload.title or payload.plan.title or "My diet plan").strip()[:160],
        breakfast=payload.plan.breakfast,
        lunch=payload.plan.lunch,
        snack=payload.plan.snack,
        dinner=payload.plan.dinner,
        nutrition_summary=payload.plan.nutrition_summary.model_dump(),
        engine_used=payload.plan.engine_used,
        goal=payload.plan.goal,
        dietary_preference=payload.plan.dietary_preference,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    logger.info("Saved plan %s for user %s", plan.id, current.id)
    return plan


@router.get("", response_model=list[PlanOut])
def list_plans(current: CurrentUser, db: Session = Depends(get_db)):
    """List the caller's saved plans, newest first."""
    return (
        db.query(DietPlan)
        .filter(DietPlan.user_id == current.id)
        .order_by(DietPlan.created_at.desc())
        .all()
    )


@router.get("/{plan_id}", response_model=PlanOut)
def get_plan(plan_id: str, current: CurrentUser, db: Session = Depends(get_db)):
    """Fetch one plan — 404 unless it belongs to the caller."""
    plan = (
        db.query(DietPlan)
        .filter(DietPlan.id == plan_id, DietPlan.user_id == current.id)
        .first()
    )
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan not found")
    return plan


@router.delete("/{plan_id}")
def delete_plan(plan_id: str, current: CurrentUser, db: Session = Depends(get_db)):
    """Delete one plan — 404 unless it belongs to the caller."""
    plan = (
        db.query(DietPlan)
        .filter(DietPlan.id == plan_id, DietPlan.user_id == current.id)
        .first()
    )
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan not found")
    db.delete(plan)
    db.commit()
    logger.info("Deleted plan %s for user %s", plan_id, current.id)
    return {"detail": "Plan deleted", "id": plan_id}
