import { useEffect, useRef, useState } from "react";
import { apiError } from "../api/client";
import { ErrorBox, Loading, SuccessBox } from "../components/Loading";
import { fileService } from "../services/dietService";

const MAX_MB = 5;
const ACCEPT = ".jpg,.jpeg,.png,.gif,.webp,.pdf,.txt,.csv";

function prettySize(bytes) {
  if (bytes > 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  return `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

/**
 * CloudFilesPage — the object-storage demo: upload meal photos/food logs,
 * list metadata, download bytes, delete. All owner-scoped by the API.
 */
export default function CloudFilesPage() {
  const [files, setFiles] = useState(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const inputRef = useRef(null);

  const load = () =>
    fileService.list().then(setFiles).catch((err) => setError(apiError(err)));

  useEffect(() => { load(); }, []);

  const upload = async (e) => {
    e.preventDefault();
    const file = inputRef.current?.files?.[0];
    if (!file) { setError("Choose a file first"); return; }
    if (file.size > MAX_MB * 1024 * 1024) {
      setError(`File too large (max ${MAX_MB} MB)`); return;
    }
    setError(""); setNotice(""); setBusy(true);
    try {
      const meta = await fileService.upload(file);
      setNotice(`Uploaded "${meta.filename}" to cloud storage ✔`);
      inputRef.current.value = "";
      load();
    } catch (err) {
      setError(apiError(err, "Upload failed"));
    } finally {
      setBusy(false);
    }
  };

  const remove = async (id, name) => {
    if (!window.confirm(`Delete "${name}" from cloud storage?`)) return;
    await fileService.delete(id);
    load();
  };

  if (!files && !error) return <Loading text="Loading cloud files…" />;

  return (
    <div className="page">
      <h2>Cloud files</h2>
      <p className="muted">Meal photos & food logs stored in object storage — metadata in the cloud database.</p>
      <ErrorBox message={error} />
      <SuccessBox message={notice} />

      <form className="card upload-card" onSubmit={upload}>
        <input ref={inputRef} type="file" accept={ACCEPT} />
        <button className="btn btn-primary" disabled={busy}>
          {busy ? "Uploading…" : "☁️ Upload to cloud"}
        </button>
        <span className="muted small-text">Images, PDF, TXT, CSV · max {MAX_MB} MB</span>
      </form>

      {files && files.length === 0 && (
        <div className="empty-state card">
          <h3>No files yet</h3>
          <p>Upload a meal photo or a food-log CSV to see object storage in action.</p>
        </div>
      )}

      {files && files.length > 0 && (
        <table className="table">
          <thead>
            <tr><th>File</th><th>Size</th><th>Uploaded</th><th>Actions</th></tr>
          </thead>
          <tbody>
            {files.map((f) => (
              <tr key={f.id}>
                <td className="file-cell">📄 {f.filename}</td>
                <td>{prettySize(f.size_bytes)}</td>
                <td>{new Date(f.uploaded_at).toLocaleString()}</td>
                <td className="actions-cell">
                  <a className="btn btn-outline btn-sm" href={fileService.downloadUrl(f.id)} target="_blank" rel="noreferrer">
                    ⬇️ Download
                  </a>
                  <button className="btn btn-danger btn-sm" onClick={() => remove(f.id, f.filename)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
