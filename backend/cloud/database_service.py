"""
database_service.py — CLOUD DATABASE service notes.

The SQLAlchemy engine in backend/database.py IS the cloud-database
abstraction: the same ORM models run against

    local mode : SQLite file on disk      (DATABASE_URL=sqlite:///./diet_planner.db)
    cloud mode : Supabase Postgres        (DATABASE_URL=postgresql+psycopg2://...)

Only the DATABASE_URL environment variable changes — the classic
"cloud database without vendor lock-in" demonstration.

This module additionally exposes a health probe used by /api/health/db.
"""

import logging

from sqlalchemy import text

from backend.database import engine

logger = logging.getLogger("diet.database")


def database_health() -> tuple[bool, str]:
    """Cheap readiness probe: run SELECT 1 against the configured database."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "database reachable"
    except Exception as exc:  # noqa: BLE001 — probe must never raise
        logger.error("Database health check failed: %s", exc)
        return False, f"database unreachable: {exc}"
