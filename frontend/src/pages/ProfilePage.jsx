import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { apiError } from "../api/client";
import { ErrorBox, Loading, SuccessBox } from "../components/Loading";
import { profileService } from "../services/dietService";

const ACTIVITY = [
  ["sedentary", "Sedentary — little exercise"],
  ["light", "Light — 1–3 days/week"],
  ["moderate", "Moderate — 3–5 days/week"],
  ["active", "Active — 6–7 days/week"],
  ["athlete", "Athlete — intense training"],
];

const DIETS = [
  ["vegetarian", "🥬 Vegetarian"],
  ["vegan", "🌱 Vegan"],
  ["eggetarian", "🍳 Eggetarian"],
  ["non_vegetarian", "🍗 Non-vegetarian"],
];

const GOALS = [
  ["weight_loss", "⚖️ Weight-management (demo)"],
  ["weight_gain", "💪 Weight-gain (demo)"],
  ["maintenance", "🧘 Maintenance"],
  ["fitness", "🏋️ Fitness-oriented"],
];

const ALLERGY_OPTIONS = ["nuts", "dairy", "gluten", "eggs", "soy", "fish", "shellfish"];

const EMPTY = {
  age: 25, height_cm: 170, weight_kg: 65, activity_level: "moderate",
  dietary_preference: "vegetarian", goal: "maintenance",
  allergies: "", meals_per_day: 3,
};

export default function ProfilePage() {
  const [params] = useSearchParams();
  const [form, setForm] = useState(EMPTY);
  const [allergySet, setAllergySet] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    profileService.get()
      .then((p) => {
        const { user_id, updated_at, bmi_display, ...rest } = p;
        setForm({ ...EMPTY, ...rest });
        setAllergySet(new Set((rest.allergies || "").split(",").filter(Boolean)));
      })
      .catch(() => {/* first-time user: keep EMPTY */})
      .finally(() => setLoading(false));
  }, []);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const toggleAllergy = (tag) => {
    const next = new Set(allergySet);
    next.has(tag) ? next.delete(tag) : next.add(tag);
    setAllergySet(next);
  };

  const submit = async (e) => {
    e.preventDefault();
    setError(""); setSaved(""); setBusy(true);
    try {
      const payload = { ...form, allergies: [...allergySet].join(",") };
      await profileService.save(payload);
      setSaved("Profile saved! Head to Generate Plan →");
    } catch (err) {
      setError(apiError(err, "Could not save profile"));
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <Loading text="Loading profile…" />;

  return (
    <div className="page">
      <h2>Your profile</h2>
      {params.get("welcome") && (
        <SuccessBox message="🎉 Account created! Fill your profile to personalize your plans." />
      )}
      <ErrorBox message={error} />
      <SuccessBox message={saved} />

      <form className="card form-card" onSubmit={submit}>
        <div className="form-row">
          <div>
            <label>Age</label>
            <input required type="number" min="10" max="100" value={form.age} onChange={set("age")} />
          </div>
          <div>
            <label>Height (cm)</label>
            <input required type="number" min="100" max="250" value={form.height_cm} onChange={set("height_cm")} />
          </div>
          <div>
            <label>Weight (kg)</label>
            <input required type="number" min="25" max="300" value={form.weight_kg} onChange={set("weight_kg")} />
          </div>
        </div>

        <label>Activity level</label>
        <select value={form.activity_level} onChange={set("activity_level")}>
          {ACTIVITY.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>

        <label>Dietary preference</label>
        <div className="choice-row">
          {DIETS.map(([v, l]) => (
            <button type="button" key={v}
              className={`choice ${form.dietary_preference === v ? "selected" : ""}`}
              onClick={() => setForm({ ...form, dietary_preference: v })}>
              {l}
            </button>
          ))}
        </div>

        <label>Goal</label>
        <div className="choice-row">
          {GOALS.map(([v, l]) => (
            <button type="button" key={v}
              className={`choice ${form.goal === v ? "selected" : ""}`}
              onClick={() => setForm({ ...form, goal: v })}>
              {l}
            </button>
          ))}
        </div>

        <label>Allergies / exclusions <small>(optional, demo)</small></label>
        <div className="choice-row">
          {ALLERGY_OPTIONS.map((tag) => (
            <button type="button" key={tag}
              className={`choice small ${allergySet.has(tag) ? "selected" : ""}`}
              onClick={() => toggleAllergy(tag)}>
              {tag}
            </button>
          ))}
        </div>

        <button className="btn btn-primary" disabled={busy}>
          {busy ? "Saving…" : "Save profile"}
        </button>
        <p className="form-note">
          Self-reported demo values used only to personalize example meal plans —
          never used for medical assessment.
        </p>
      </form>
    </div>
  );
}
