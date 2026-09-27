import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiError } from "../api/client";
import { ErrorBox, Loading } from "../components/Loading";
import PlanCard from "../components/PlanCard";
import { useAuth } from "../context/AuthContext";
import { dashboardService } from "../services/dietService";

/** DashboardPage — the aggregated home screen (one GET /api/dashboard call). */
export default function DashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    dashboardService.get().then(setData).catch((err) => setError(apiError(err)));
  }, []);

  if (error) return <div className="page"><ErrorBox message={error} /></div>;
  if (!data) return <Loading text="Loading your dashboard…" />;

  const goal = data.profile?.goal?.replace("_", " ") || "not set";
  const diet = data.profile?.dietary_preference?.replace("_", " ") || "not set";

  return (
    <div className="page">
      <h2>Welcome, {user?.name?.split(" ")[0]} 👋</h2>

      <div className="stat-row">
        <div className="card stat">
          <span className="stat-label">Current goal</span>
          <strong>{goal}</strong>
        </div>
        <div className="card stat">
          <span className="stat-label">Diet preference</span>
          <strong>{diet}</strong>
        </div>
        <div className="card stat">
          <span className="stat-label">Saved plans</span>
          <strong>{data.total_plans}</strong>
        </div>
        <div className="card stat">
          <span className="stat-label">Cloud files</span>
          <strong>{data.total_files}</strong>
        </div>
      </div>

      {data.profile?.bmi_display && (
        <p className="muted small-text">
          📊 {data.profile.bmi_display} — informational only, not a diagnosis.
        </p>
      )}

      <div className="dashboard-section">
        <div className="page-head">
          <h3>Latest plan</h3>
          <Link className="btn btn-primary btn-sm" to="/generate">✨ Generate new plan</Link>
        </div>
        {data.latest_plan ? (
          <PlanCard plan={data.latest_plan} />
        ) : (
          <div className="empty-state card">
            <p>No plan yet — generate your first one!</p>
            <Link className="btn btn-primary" to="/generate">Generate plan</Link>
          </div>
        )}
      </div>

      <div className="dashboard-section">
        <div className="page-head">
          <h3>Previous plans</h3>
          <Link to="/plans">See all →</Link>
        </div>
        {data.recent_plans.length === 0 ? (
          <p className="muted">Nothing here yet.</p>
        ) : (
          <ul className="mini-list">
            {data.recent_plans.map((p) => (
              <li key={p.id}>
                <Link to={`/plans/${p.id}`}>{p.title}</Link>
                <span className="muted small-text">
                  {new Date(p.created_at).toLocaleDateString()} · ≈{p.nutrition_summary?.calories_kcal ?? "?"} kcal
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="dashboard-section">
        <div className="page-head">
          <h3>Uploaded files</h3>
          <Link to="/files">Manage →</Link>
        </div>
        {data.recent_files.length === 0 ? (
          <p className="muted">No files uploaded yet.</p>
        ) : (
          <ul className="mini-list">
            {data.recent_files.map((f) => (
              <li key={f.id}>
                <span>📄 {f.filename}</span>
                <span className="muted small-text">{new Date(f.uploaded_at).toLocaleDateString()}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
