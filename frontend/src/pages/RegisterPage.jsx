import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiError } from "../api/client";
import { ErrorBox } from "../components/Loading";
import { useAuth } from "../context/AuthContext";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await register(form.name, form.email, form.password);
      navigate("/profile?welcome=1");
    } catch (err) {
      setError(apiError(err, "Registration failed"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-page">
      <form className="card auth-card" onSubmit={submit}>
        <h2>Create your account</h2>
        <ErrorBox message={error} />

        <label>Full name</label>
        <input required minLength={2} value={form.name} onChange={set("name")} placeholder="Aasha Kumar" />

        <label>Email</label>
        <input required type="email" value={form.email} onChange={set("email")} placeholder="you@example.com" />

        <label>Password <small>(8+ characters)</small></label>
        <input required minLength={8} type="password" value={form.password} onChange={set("password")} placeholder="••••••••" />

        <button className="btn btn-primary btn-block" disabled={busy}>
          {busy ? "Creating account…" : "Register"}
        </button>

        <p className="auth-switch">Already have an account? <Link to="/login">Log in</Link></p>
      </form>
    </div>
  );
}
