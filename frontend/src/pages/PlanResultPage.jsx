import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { apiError } from "../api/client";
import { ErrorBox, Loading } from "../components/Loading";
import PlanCard from "../components/PlanCard";
import { planService } from "../services/dietService";

/** PlanResultPage — one saved plan in detail, with delete. */
export default function PlanResultPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [plan, setPlan] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    planService.get(id).then(setPlan).catch((err) =>
      setError(apiError(err, "Plan not found"))
    );
  }, [id]);

  const remove = async () => {
    if (!window.confirm("Delete this saved plan?")) return;
    await planService.delete(id);
    navigate("/plans");
  };

  if (error) return <div className="page"><ErrorBox message={error} /><Link to="/plans">← Back to saved plans</Link></div>;
  if (!plan) return <Loading text="Loading plan…" />;

  return (
    <div className="page">
      <div className="page-head">
        <h2>{plan.title}</h2>
        <button className="btn btn-danger" onClick={remove}>🗑 Delete plan</button>
      </div>
      <p className="muted">Saved {new Date(plan.created_at).toLocaleString()} · engine: {plan.engine_used}</p>
      <PlanCard plan={plan} />
      <Link to="/plans">← All saved plans</Link>
    </div>
  );
}
