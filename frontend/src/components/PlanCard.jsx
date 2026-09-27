import DisclaimerBanner from "./DisclaimerBanner";

/**
 * PlanCard — renders a generated or saved plan (meals + nutrition).
 * Used by the result page, saved-plans page and the dashboard.
 */
export default function PlanCard({ plan, children }) {
  const n = plan.nutrition_summary || {};
  return (
    <div className="card plan-card">
      <div className="plan-head">
        <h3>{plan.title}</h3>
        <span className={`badge engine-${plan.engine_used}`}>
          {plan.engine_used === "ai_api" ? "AI API" : "Rule-based engine"}
        </span>
      </div>

      <div className="plan-meals">
        <div className="meal"><span className="meal-icon">🌅</span><div><h4>Breakfast</h4><p>{plan.breakfast}</p></div></div>
        <div className="meal"><span className="meal-icon">☀️</span><div><h4>Lunch</h4><p>{plan.lunch}</p></div></div>
        <div className="meal"><span className="meal-icon">🍎</span><div><h4>Snack</h4><p>{plan.snack}</p></div></div>
        <div className="meal"><span className="meal-icon">🌙</span><div><h4>Dinner</h4><p>{plan.dinner}</p></div></div>
      </div>

      {n.calories_kcal != null && (
        <div className="nutrition-grid">
          <div className="nutri"><strong>{n.calories_kcal}</strong><span>kcal</span></div>
          <div className="nutri"><strong>{n.protein_g}g</strong><span>protein</span></div>
          <div className="nutri"><strong>{n.carbs_g}g</strong><span>carbs</span></div>
          <div className="nutri"><strong>{n.fat_g}g</strong><span>fat</span></div>
        </div>
      )}

      {n.hydration_reminder && <p className="hydration">💧 {n.hydration_reminder}</p>}
      {n.goal_calorie_hint && <p className="hint">🎯 {n.goal_calorie_hint}</p>}

      <DisclaimerBanner compact />

      {children}
    </div>
  );
}
