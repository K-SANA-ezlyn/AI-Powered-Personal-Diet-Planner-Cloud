import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiError } from "../api/client";
import { ErrorBox } from "../components/Loading";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(form.email, form.password);
      navigate("/dashboard");
    } catch (err) {
      setError(apiError(err, "Login failed"));
    } finally {
      setBusy(false);
    }
  };

  const fillDemo = () => setForm({ email: "aasha@demo.com", password: "Demo@12345" });

  return (
    <div className="auth-page">
      <form className="card auth-card" onSubmit={submit}>
        <h2>Welcome back</h2>
        <ErrorBox message={error} />

        <label>Email</label>
        <input required type="email" value={form.email} onChange={set("email")} placeholder="you@example.com" />

        <label>Password</label>
        <input required type="password" value={form.password} onChange={set("password")} placeholder="••••••••" />

        <button className="btn btn-primary btn-block" disabled={busy}>
          {busy ? "Signing in…" : "Log in"}
        </button>

        <button type="button" className="btn btn-outline btn-block" onClick={fillDemo}>
          Use demo account (aasha@demo.com)
        </button>

        <p className="auth-switch">New here? <Link to="/register">Create an account</Link></p>
      </form>
    </div>
  );
}
