import { useState } from "react";
import type { StructuredNoteOut } from "../types";

interface ReviewActionsProps {
  note: StructuredNoteOut;
  onReview: (decision: "approve" | "reject") => Promise<void>;
}

export function ReviewActions({ note, onReview }: ReviewActionsProps) {
  const [busy, setBusy] = useState(false);

  if (note.status === "submitted_to_fhir") {
    return (
      <section className="card review-actions">
        <p className="status-success">✅ Approved and submitted to FHIR server ({note.fhir_bundle_id}).</p>
      </section>
    );
  }
  if (note.status === "rejected") {
    return (
      <section className="card review-actions">
        <p className="status-rejected">🚫 Rejected by clinician. Not submitted to FHIR.</p>
      </section>
    );
  }

  const hasCritical = note.validator_flags.some((f) => f.severity === "critical");

  async function handle(decision: "approve" | "reject") {
    setBusy(true);
    try {
      await onReview(decision);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card review-actions">
      <h3>Clinician review</h3>
      {hasCritical && (
        <p className="status-warning">
          ⚠️ This note has critical validator flags. Review the highlighted entities carefully
          before approving.
        </p>
      )}
      <div className="review-buttons">
        <button className="btn btn-success" disabled={busy} onClick={() => handle("approve")}>
          ✅ Approve &amp; submit to FHIR
        </button>
        <button className="btn btn-danger" disabled={busy} onClick={() => handle("reject")}>
          🚫 Reject
        </button>
      </div>
    </section>
  );
}
