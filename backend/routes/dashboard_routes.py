"""
dashboard_routes.py — DASHBOARD endpoint.

GET /api/dashboard
    One aggregated call powering the whole dashboard screen:
    user + profile + latest plan + recent plans + recent files + counts.
    Fewer round-trips = snappier SPA and a clean "backend-for-frontend"
    pattern to talk about in reviews.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.schemas import DashboardOut
from backend.services.dashboard_service import build_dashboard
from backend.utils.security import CurrentUser

logger = logging.getLogger("diet.dashboard")
router = APIRouter(tags=["dashboard"])


@router.get("/api/dashboard", response_model=DashboardOut)
def dashboard(current: CurrentUser, db: Session = Depends(get_db)):
    """Aggregate everything the user's dashboard needs in one response."""
    return build_dashboard(db, current)
