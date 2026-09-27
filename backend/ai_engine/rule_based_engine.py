"""
rule_based_engine.py — VERSION A: RULE-BASED RECOMMENDATION ENGINE.

A deterministic "AI simulation": given a user's demo profile it
  1. filters the food dataset by dietary preference,
  2. removes anything matching the user's allergy tags,
  3. scores remaining foods against the goal
       weight_loss   -> lean, lower-calorie, protein-forward picks
       weight_gain   -> calorie-dense picks + an extra snack push
       maintenance   -> balanced mid-range picks
       fitness       -> highest-protein picks
  4. picks one item per meal slot (breakfast / lunch / snack / dinner)
     with variety seeded by user-id + date so two users (or the same
     user on different days) don't always get identical plans,
  5. sums an approximate nutrition summary + a general hydration note.

Fully offline, zero cost, sub-millisecond — the fallback that keeps the
Demo alive when the optional AI API is unreachable.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import date
from pathlib import Path

from backend.utils.validators import bmi_value

logger = logging.getLogger("diet.rule_engine")

_DATA_PATH = Path(__file__).with_name("food_data.json")

# Approximate calorie targets per goal (educational demo values, not clinical).
_GOAL_CALORIE_HINTS = {
    "weight_loss": "~1,600–1,800 kcal/day (demo target)",
    "weight_gain": "~2,500–2,800 kcal/day (demo target)",
    "maintenance": "~2,000–2,400 kcal/day (demo target)",
    "fitness": "~2,200–2,500 kcal/day, protein-focused (demo target)",
}


def _load_foods() -> list[dict]:
    with open(_DATA_PATH, encoding="utf-8") as fh:
        data = json.load(fh)
    return data["foods"]


FOODS: list[dict] = _load_foods()


class UserPreferences:
    """Everything the engine needs, decoupled from HTTP/database layers."""

    __slots__ = ("user_id", "age", "height_cm", "weight_kg", "activity_level",
                 "dietary_preference", "goal", "allergies", "plan_date")

    def __init__(
        self,
        user_id: str,
        age: int = 25,
        height_cm: int = 170,
        weight_kg: int = 65,
        activity_level: str = "moderate",
        dietary_preference: str = "vegetarian",
        goal: str = "maintenance",
        allergies: list[str] | None = None,
        plan_date: date | None = None,
    ) -> None:
        self.user_id = user_id
        self.age = age
        self.height_cm = height_cm
        self.weight_kg = weight_kg
        self.activity_level = activity_level
        self.dietary_preference = dietary_preference
        self.goal = goal
        self.allergies = [a.strip().lower() for a in (allergies or []) if a.strip()]
        self.plan_date = plan_date or date.today()


def _variety_seed(prefs: UserPreferences, slot: str) -> int:
    """Stable pseudo-random seed: same user+day -> same plan, different across days."""
    raw = f"{prefs.user_id}:{prefs.plan_date.isoformat()}:{slot}"
    return int(hashlib.sha256(raw.encode()).hexdigest()[:8], 16)


def _eligible_foods(prefs: UserPreferences, slot: str) -> list[dict]:
    """Apply dietary-preference and allergy filters, then goal-aware scoring."""
    eligible: list[tuple[int, dict]] = []
    for food in FOODS:
        # ---- rule 1: meal slot must match ----
        if slot not in food["meal_slots"]:
            continue
        # ---- rule 2: dietary preference ----
        if prefs.dietary_preference not in food["diets"]:
            continue
        # ---- rule 3: allergies are a HARD exclusion ----
        if any(a in food["allergens"] for a in prefs.allergies):
            continue

        kcal = food["calories_kcal"]
        protein = food["protein_g"]

        # ---- rule 4: goal-aware scoring (higher = better fit) ----
        score = 1
        if prefs.goal == "weight_loss":
            score += (3 if kcal <= 400 else 0) + (2 if protein >= 15 else 0) - (2 if kcal >= 550 else 0)
        elif prefs.goal == "weight_gain":
            score += (3 if kcal >= 500 else 0) + (1 if kcal >= 400 else 0) + (2 if protein >= 18 else 0)
        elif prefs.goal == "fitness":
            score += (3 if protein >= 20 else 0) + (2 if kcal >= 350 else 0) + (1 if kcal <= 550 else 0)
        else:  # maintenance
            score += (2 if 300 <= kcal <= 550 else 0) + (1 if 10 <= protein <= 30 else 0)

        # ---- rule 5: activity bump — active users get denser meals ----
        if prefs.activity_level in {"active", "athlete"} and kcal >= 450:
            score += 1
        if prefs.activity_level == "sedentary" and kcal >= 550:
            score -= 1

        eligible.append((max(score, 1), food))

    eligible.sort(key=lambda pair: (-pair[0], pair[1]["id"]))
    return [food for _, food in eligible]


def _pick(prefs: UserPreferences, slot: str) -> dict:
    """Pick a food for the slot using deterministic seeded variety."""
    candidates = _eligible_foods(prefs, slot)
    if not candidates:
        # Dataset guarantee: never happens for supported preference+goal
        # combos, but guard anyway so the engine can always answer.
        candidates = [f for f in FOODS if slot in f["meal_slots"]]
        if not candidates:
            raise ValueError(f"No foods available for slot '{slot}'")
    seed = _variety_seed(prefs, slot)
    # Take the top-scoring third and rotate through it for variety.
    pool = candidates[: max(3, len(candidates) // 3)]
    return pool[seed % len(pool)]


def _summarize(picks: dict[str, dict], prefs: UserPreferences) -> dict:
    """Approximate nutrition totals + hydration reminder (demo values)."""
    totals = {"calories_kcal": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}
    for food in picks.values():
        for key in totals:
            totals[key] += food[f"{key.split('_')[0]}_g" if key != "calories_kcal" else "calories_kcal"]

    hydration = "Drink about 2.5–3 L of water through the day (general wellness guidance, adjust to your body and climate)."
    if prefs.activity_level in {"active", "athlete"}:
        hydration = "You log high activity — keep water handy and sip regularly; ~3 L/day is a fair demo target (general guidance only)."

    totals["hydration_reminder"] = hydration
    totals["goal_calorie_hint"] = _GOAL_CALORIE_HINTS.get(prefs.goal, _GOAL_CALORIE_HINTS["maintenance"])
    totals["estimated_bmi_display_only"] = bmi_value(prefs.height_cm, prefs.weight_kg)
    return totals


class RuleBasedEngine:
    """Deterministic recommendation engine over the food dataset."""

    name = "rule_based"

    def generate(self, prefs: UserPreferences) -> DietPlanResult:
        from backend.ai_engine.diet_engine import DietPlanResult

        picks = {slot: _pick(prefs, slot) for slot in ("breakfast", "lunch", "snack", "dinner")}
        nutrition = _summarize(picks, prefs)

        goal_label = prefs.goal.replace("_", " ").title()
        title = f"{goal_label} · {prefs.dietary_preference.replace('_', ' ').title()} Plan"

        result = DietPlanResult(
            title=title,
            breakfast=f"{picks['breakfast']['name']} (~{picks['breakfast']['calories_kcal']} kcal)",
            lunch=f"{picks['lunch']['name']} (~{picks['lunch']['calories_kcal']} kcal)",
            snack=f"{picks['snack']['name']} (~{picks['snack']['calories_kcal']} kcal)",
            dinner=f"{picks['dinner']['name']} (~{picks['dinner']['calories_kcal']} kcal)",
            nutrition_summary=nutrition,
            engine_used=self.name,
            goal=prefs.goal,
            dietary_preference=prefs.dietary_preference,
        )
        logger.info(
            "Rule-based plan ready for user=%s goal=%s diet=%s allergies=%s",
            prefs.user_id, prefs.goal, prefs.dietary_preference, prefs.allergies or "none",
        )
        return result
