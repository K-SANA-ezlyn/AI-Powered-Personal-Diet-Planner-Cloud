export function Loading({ text = "Loading…" }) {
  return <div className="loading">{text}</div>;
}

export function ErrorBox({ message }) {
  if (!message) return null;
  return <div className="error-box">{message}</div>;
}

export function SuccessBox({ message }) {
  if (!message) return null;
  return <div className="success-box">{message}</div>;
}
