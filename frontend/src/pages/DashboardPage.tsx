import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { createSession, listSessions } from "../api/client";
import type { SessionOut } from "../types";

export function DashboardPage() {
  const [sessions, setSessions] = useState<SessionOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    listSessions()
      .then(setSessions)
      .catch((err) => setError(String(err)))
      .finally(() => setLoading(false));
  }, []);

  async function handleCreate() {
    setCreating(true);
    try {
      const session = await createSession({
        patient_pseudonym: "synthetic-patient",
        clinician_name: "Dr. Demo",
        language: "de",
      });
      navigate(`/sessions/${session.id}`);
    } catch (err) {
      setError(String(err));
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="page">
      <header className="page-header">
        <h1>CareScribe</h1>
        <p className="subtitle">Agentic ambient clinical documentation &amp; FHIR coding -- demo</p>
      </header>

      <button className="btn btn-primary" onClick={handleCreate} disabled={creating}>
        + New encounter session
      </button>

      {error && <p className="field-error">{error}</p>}
      {loading ? (
        <p className="muted">Loading sessions…</p>
      ) : sessions.length === 0 ? (
        <p className="muted">No sessions yet -- create one to try the pipeline.</p>
      ) : (
        <table className="data-table session-table">
          <thead>
            <tr>
              <th>Patient</th>
              <th>Clinician</th>
              <th>Status</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {sessions.map((session) => (
              <tr key={session.id} onClick={() => navigate(`/sessions/${session.id}`)}>
                <td>{session.patient_pseudonym}</td>
                <td>{session.clinician_name}</td>
                <td>
                  <span className={`pill pill-status-${session.status}`}>{session.status}</span>
                </td>
                <td>{new Date(session.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
