"""
dashboard_service.py — backend-for-frontend aggregation.

Builds the single dashboard payload: user, profile (with a display-only
BMI note), latest + recent plans, recent files and totals. Keeping this
logic in a service (not the route) keeps routes thin and the logic
unit-testable — an industry-style separation.
"""

from sqlalchemy.orm import Session

from backend.models import DietPlan, Profile, User, UserFile
from backend.schemas.schemas import DashboardOut, PlanOut, ProfileOut, UserOut
from backend.utils.validators import bmi_category, bmi_value


def build_dashboard(db: Session, user: User) -> DashboardOut:
    """Aggregate the caller's data into one dashboard response."""
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()

    plans = (
        db.query(DietPlan)
        .filter(DietPlan.user_id == user.id)
        .order_by(DietPlan.created_at.desc())
        .all()
    )
    files = (
        db.query(UserFile)
        .filter(UserFile.user_id == user.id)
        .order_by(UserFile.uploaded_at.desc())
        .limit(5)
        .all()
    )

    profile_out = None
    if profile is not None:
        profile_out = ProfileOut.model_validate(profile)
        # Educational, display-only BMI annotation (never a diagnosis).
        bmi = bmi_value(profile.height_cm, profile.weight_kg)
        profile_out.bmi_display = f"BMI {bmi} — {bmi_category(bmi)}"

    latest = plans[0] if plans else None
    return DashboardOut(
        user=UserOut.model_validate(user),
        profile=profile_out,
        latest_plan=PlanOut.model_validate(latest) if latest else None,
        total_plans=len(plans),
        total_files=db.query(UserFile).filter(UserFile.user_id == user.id).count(),
        recent_plans=[PlanOut.model_validate(p) for p in plans[:5]],
        recent_files=list(files),
    )
