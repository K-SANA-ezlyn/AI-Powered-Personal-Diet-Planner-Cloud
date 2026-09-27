"""
ai_api_engine.py — VERSION B: OPTIONAL EXTERNAL AI API ADAPTER.

Sends a structured prompt (profile + constraints) to any OpenAI-style
chat-completions endpoint and expects STRICT JSON back:

    {"title": ..., "breakfast": ..., "lunch": ..., "snack": ...,
     "dinner": ..., "nutrition_summary": {"calories_kcal": ..., ...}}

Safety and resilience rules enforced here:
  * the API key comes from environment variables ONLY (AI_API_KEY)
  * hard timeout (AI_API_TIMEOUT_SECONDS) so the request never hangs
  * response is schema-validated; anything malformed is rejected
  * EVERY exception propagates to _FallbackEngine -> rule-based plan,
    so the product never breaks when the third-party API does
  * prompt explicitly forbids medical claims in the output
"""

import json
import logging

import httpx

from backend.ai_engine.rule_based_engine import UserPreferences
from backend.config import settings

logger = logging.getLogger("diet.ai_api")


class AIApiEngine:
    """Adapter for an OpenAI-compatible chat-completions endpoint."""

    name = "ai_api"

    SYSTEM_PROMPT = (
        "You are a general wellness meal-planning assistant for an educational "
        "cloud-computing demo. You create simple one-day meal plans from the "
        "user's stated food preferences. You NEVER provide medical, clinical, "
        "or diagnostic advice and you never mention medications or conditions. "
        "Reply with STRICT JSON only — no markdown, no commentary — matching: "
        '{"title": str, "breakfast": str, "lunch": str, "snack": str, '
        '"dinner": str, "nutrition_summary": {"calories_kcal": int, '
        '"protein_g": int, "carbs_g": int, "fat_g": int}}'
    )

    REQUIRED_KEYS = {"title", "breakfast", "lunch", "snack", "dinner", "nutrition_summary"}
    REQUIRED_NUTRITION = {"calories_kcal", "protein_g", "carbs_g", "fat_g"}

    def __init__(self) -> None:
        self._timeout = float(settings.AI_API_TIMEOUT_SECONDS)

    def is_ready(self) -> bool:
        """Cheap readiness check used by the factory at startup."""
        return bool(settings.AI_API_KEY and settings.AI_API_URL)

    def _build_user_prompt(self, prefs: UserPreferences) -> str:
        allergies = ", ".join(prefs.allergies) if prefs.allergies else "none"
        return (
            "Create a one-day meal plan with exactly one breakfast, one lunch, "
            "one snack and one dinner.\n"
            f"Age: {prefs.age}\n"
            f"Height cm: {prefs.height_cm}\n"
            f"Weight kg: {prefs.weight_kg}\n"
            f"Activity level: {prefs.activity_level}\n"
            f"Dietary preference: {prefs.dietary_preference}\n"
            f"Goal: {prefs.goal}\n"
            f"Allergies (must be excluded): {allergies}\n"
            "Use widely available everyday foods and modest portion sizes."
        )

    def _validate(self, data: dict) -> dict:
        """Schema-validate the AI response; raise on any deviation."""
        if not isinstance(data, dict):
            raise ValueError("AI response is not a JSON object")
        missing = self.REQUIRED_KEYS - data.keys()
        if missing:
            raise ValueError(f"AI response missing keys: {sorted(missing)}")
        nutrition = data["nutrition_summary"]
        if not isinstance(nutrition, dict) or self.REQUIRED_NUTRITION - nutrition.keys():
            raise ValueError("AI response nutrition_summary is incomplete")
        for key in self.REQUIRED_NUTRITION:
            if not isinstance(nutrition[key], int) or nutrition[key] < 0:
                raise ValueError(f"AI nutrition field '{key}' must be a non-negative int")
        for key in ("title", "breakfast", "lunch", "snack", "dinner"):
            if not isinstance(data[key], str) or not data[key].strip():
                raise ValueError(f"AI field '{key}' must be a non-empty string")
        return data

    def generate(self, prefs: UserPreferences):
        """Call the AI API; any failure raises -> rule-based fallback kicks in."""
        from backend.ai_engine.diet_engine import DietPlanResult

        payload = {
            "model": settings.AI_API_MODEL,
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": self._build_user_prompt(prefs)},
            ],
            "temperature": 0.7,
            "response_format": {"type": "json_object"},
        }

        try:
            resp = httpx.post(
                settings.AI_API_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {settings.AI_API_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=self._timeout,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("AI API request failed: %s", exc)
            raise RuntimeError(f"AI API request failed: {exc}") from exc

        try:
            body = resp.json()
            content = body["choices"][0]["message"]["content"]
            data = json.loads(content)
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            logger.warning("AI API response malformed: %s", exc)
            raise RuntimeError(f"AI API response malformed: {exc}") from exc

        data = self._validate(data)
        data["nutrition_summary"]["hydration_reminder"] = (
            "Drink about 2.5–3 L of water through the day (general wellness guidance)."
        )

        result = DietPlanResult(
            title=data["title"].strip()[:160],
            breakfast=data["breakfast"].strip(),
            lunch=data["lunch"].strip(),
            snack=data["snack"].strip(),
            dinner=data["dinner"].strip(),
            nutrition_summary=data["nutrition_summary"],
            engine_used=self.name,
            goal=prefs.goal,
            dietary_preference=prefs.dietary_preference,
        )
        logger.info("AI API plan generated for user=%s", prefs.user_id)
        return result
