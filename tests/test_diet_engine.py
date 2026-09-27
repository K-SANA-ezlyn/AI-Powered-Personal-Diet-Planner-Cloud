"""
test_diet_engine.py — rule-based engine rules + AI-API fallback logic.
"""

import pytest

from backend.ai_engine.diet_engine import get_diet_engine
from backend.ai_engine.rule_based_engine import UserPreferences


def _prefs(**overrides) -> UserPreferences:
    base = dict(
        user_id="test-user",
        age=28, height_cm=170, weight_kg=68,
        activity_level="moderate", dietary_preference="vegetarian",
        goal="weight_loss", allergies=["nuts"],
    )
    base.update(overrides)
    return UserPreferences(**base)


# ---------------------------------------------------------------------------
# Core generation
# ---------------------------------------------------------------------------
def test_generates_all_four_meals():
    result = get_diet_engine().generate(_prefs())
    assert result.breakfast and result.lunch and result.snack and result.dinner
    assert result.engine_used == "rule_based"
    assert result.nutrition_summary["calories_kcal"] > 0


def test_nutrition_summary_complete():
    summary = get_diet_engine().generate(_prefs()).nutrition_summary
    for key in ("calories_kcal", "protein_g", "carbs_g", "fat_g", "hydration_reminder"):
        assert key in summary


def test_vegan_plan_contains_no_non_vegan_pick():
    result = get_diet_engine().generate(_prefs(dietary_preference="vegan"))
    vegan_markers = ("paneer", "egg", "chicken", "fish", "curd", "yogurt", "cottage")
    for meal in (result.breakfast, result.lunch, result.snack, result.dinner):
        assert not any(marker in meal.lower() for marker in vegan_markers), meal


def test_non_vegetarian_plan_can_include_meat():
    result = get_diet_engine().generate(
        _prefs(dietary_preference="non_vegetarian", allergies=[])
    )
    assert result.dietary_preference == "non_vegetarian"


def test_allergy_hard_exclusion():
    """Dairy-allergic users must never receive a dairy item in any meal."""
    result = get_diet_engine().generate(_prefs(allergies=["dairy"]))
    dairy_markers = ("paneer", "curd", "yogurt", "cottage", "milk")
    for meal in (result.breakfast, result.lunch, result.snack, result.dinner):
        assert not any(marker in meal.lower() for marker in dairy_markers), meal


def test_variety_across_days():
    """Same user, different days -> not identical plans (seeded variety)."""
    from datetime import date, timedelta

    day1 = get_diet_engine().generate(_prefs(plan_date=date(2026, 1, 1)))
    day2 = get_diet_engine().generate(_prefs(plan_date=date(2026, 1, 2)))
    assert (day1.breakfast, day1.lunch, day1.dinner) != (day2.breakfast, day2.lunch, day2.dinner)


def test_plan_carries_disclaimer():
    result = get_diet_engine().generate(_prefs())
    assert "not medical" in result.to_dict()["disclaimer"]


# ---------------------------------------------------------------------------
# Goal differences
# ---------------------------------------------------------------------------
def test_weight_gain_lean_calorie_dense():
    gain = get_diet_engine().generate(_prefs(goal="weight_gain")).nutrition_summary
    loss = get_diet_engine().generate(_prefs(goal="weight_loss")).nutrition_summary
    assert gain["calories_kcal"] > loss["calories_kcal"]


# ---------------------------------------------------------------------------
# Fallback logic (the resilience contract)
# ---------------------------------------------------------------------------
class _ExplodingEngine:
    """Simulates a totally unavailable AI API."""

    name = "ai_api"

    def generate(self, prefs):
        raise RuntimeError("AI API down")


class _GarbageEngine:
    """Simulates an AI API returning structurally wrong output."""

    name = "ai_api"

    def generate(self, prefs):
        return {"unexpected": "shape"}


def _fallback_result(primary) -> object:
    from backend.ai_engine.diet_engine import _FallbackEngine

    return _FallbackEngine(primary).generate(_prefs())


def test_fallback_on_api_crash(monkeypatch):
    monkeypatch.setattr("backend.ai_engine.ai_api_engine.httpx.post",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    result = _fallback_result(_ExplodingEngine())
    assert result.engine_used == "rule_based"
    assert result.breakfast  # a usable plan came out anyway


def test_fallback_on_bad_schema():
    result = _fallback_result(_GarbageEngine())
    assert result.engine_used == "rule_based"


def test_factory_uses_rule_based_without_keys(monkeypatch):
    from backend.config import settings

    monkeypatch.setattr(settings, "AI_PROVIDER", "auto")
    monkeypatch.setattr(settings, "AI_API_KEY", "")
    engine = get_diet_engine()
    result = engine.generate(_prefs())
    assert result.engine_used == "rule_based"


def test_ai_api_rejects_malformed_json(monkeypatch):
    """The AI adapter itself must reject garbage instead of trusting it."""
    from backend.ai_engine.ai_api_engine import AIApiEngine

    class _FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": "this is not json"}}]}

    monkeypatch.setattr("backend.ai_engine.ai_api_engine.httpx.post", lambda *a, **k: _FakeResp())
    engine = AIApiEngine()
    with pytest.raises(RuntimeError):
        engine.generate(_prefs())
