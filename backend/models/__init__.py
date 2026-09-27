"""
models/__init__.py — ORM models for the diet planner.

Four tables (cloud database schema):

  users       — authentication principal (email unique, bcrypt hash)
  profiles    — 1:1 demo health profile (age, height, weight, goals...)
  diet_plans  — 1:N generated meal plans (owned by a user)
  user_files  — 1:N metadata rows for files stored in OBJECT STORAGE
                (bytes never live in the database — see docs/storage-design.md)

All primary keys are UUID strings; foreign keys are indexed because
"all rows for one user" is the hottest query pattern (user isolation).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    """Authentication principal. One row per registered account."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    profile: Mapped["Profile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    diet_plans: Mapped[list["DietPlan"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    files: Mapped[list["UserFile"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Profile(Base):
    """
    Demo wellness profile — 1:1 with a user.

    NOTE: this is self-reported demo data for an educational project.
    It is never used for medical diagnosis or clinical advice.
    """

    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    age: Mapped[int] = mapped_column(Integer)
    height_cm: Mapped[int] = mapped_column(Integer)
    weight_kg: Mapped[int] = mapped_column(Integer)
    activity_level: Mapped[str] = mapped_column(String(30))       # sedentary|light|moderate|active|athlete
    dietary_preference: Mapped[str] = mapped_column(String(30))   # vegetarian|vegan|non_vegetarian|eggetarian
    goal: Mapped[str] = mapped_column(String(30))                 # weight_loss|weight_gain|maintenance|fitness
    allergies: Mapped[str] = mapped_column(String(255), default="")  # comma separated: nuts,dairy,gluten,eggs
    meals_per_day: Mapped[int] = mapped_column(Integer, default=3)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    user: Mapped[User] = relationship(back_populates="profile")


class DietPlan(Base):
    """A generated meal plan saved by a user — 1:N with users."""

    __tablename__ = "diet_plans"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(160), default="My diet plan")
    breakfast: Mapped[str] = mapped_column(Text)
    lunch: Mapped[str] = mapped_column(Text)
    snack: Mapped[str] = mapped_column(Text)
    dinner: Mapped[str] = mapped_column(Text)
    nutrition_summary: Mapped[dict] = mapped_column(JSON)   # kcal, protein, carbs, fat, hydration
    engine_used: Mapped[str] = mapped_column(String(30))    # rule_based | ai_api
    goal: Mapped[str] = mapped_column(String(30))
    dietary_preference: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped[User] = relationship(back_populates="diet_plans")


class UserFile(Base):
    """
    Metadata for one object stored in CLOUD OBJECT STORAGE.

    Only the pointer (storage_path) lives here — the bytes live in the
    bucket / uploads folder. This separation is deliberate and is a
    classic cloud-architecture talking point (see docs/storage-design.md).
    """

    __tablename__ = "user_files"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    filename: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(500))
    content_type: Mapped[str] = mapped_column(String(100), default="application/octet-stream")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped[User] = relationship(back_populates="files")


__all__ = ["User", "Profile", "DietPlan", "UserFile"]
