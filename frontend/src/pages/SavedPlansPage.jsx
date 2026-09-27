import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiError } from "../api/client";
import { ErrorBox, Loading } from "../components/Loading";
import { planService } from "../services/dietService";

/** SavedPlansPage — every plan this user has saved in the cloud DB. */
export default function SavedPlansPage() {
  const [plans, setPlans] = useState(null);
  const [error, setError] = useState("");

  const load = () =>
    planService.list().then(setPlans).catch((err) => setError(apiError(err)));

  useEffect(() => { load(); }, []);

  const remove = async (id) => {
    if (!window.confirm("Delete this plan?")) return;
    await planService.delete(id);
    load();
  };

  if (error) return <div className="page"><ErrorBox message={error} /></div>;
  if (!plans) return <Loading text="Loading your plans…" />;

  return (
    <div className="page">
      <div className="page-head">
        <h2>Saved plans <span className="count-badge">{plans.length}</span></h2>
        <Link className="btn btn-primary" to="/generate">✨ New plan</Link>
      </div>

      {plans.length === 0 ? (
        <div className="empty-state card">
          <h3>No saved plans yet</h3>
          <p>Generate your first personalized plan — it takes seconds.</p>
          <Link className="btn btn-primary" to="/generate">Generate a plan</Link>
        </div>
      ) : (
        <div className="plan-grid">
          {plans.map((p) => (
            <div className="card plan-summary" key={p.id}>
              <div className="plan-head">
                <h3><Link to={`/plans/${p.id}`}>{p.title}</Link></h3>
                <span className={`badge engine-${p.engine_used}`}>
                  {p.engine_used === "ai_api" ? "AI API" : "Rule-based"}
                </span>
              </div>
              <p className="muted small-text">
                {p.goal.replace("_", " ")} · {p.dietary_preference.replace("_", " ")} ·{" "}
                {new Date(p.created_at).toLocaleDateString()}
              </p>
              <p className="muted small-text">
                ≈ {p.nutrition_summary?.calories_kcal ?? "?"} kcal/day
              </p>
              <div className="plan-actions">
                <Link className="btn btn-outline btn-sm" to={`/plans/${p.id}`}>View</Link>
                <button className="btn btn-danger btn-sm" onClick={() => remove(p.id)}>Delete</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
