import type { StructuredNoteOut } from "../types";

interface StructuredNotePanelProps {
  note: StructuredNoteOut;
}

const SEVERITY_LABEL: Record<string, string> = {
  critical: "🔴 Critical",
  warning: "🟡 Warning",
  info: "🔵 Info",
};

export function StructuredNotePanel({ note }: StructuredNotePanelProps) {
  return (
    <section className="card">
      <h3>Structured note</h3>

      <h4>Entities</h4>
      {note.entities.length === 0 ? (
        <p className="muted">No entities extracted.</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Text</th>
              <th>Label</th>
              <th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {note.entities.map((entity, i) => (
              <tr key={i} className={entity.start === -1 ? "row-flagged" : undefined}>
                <td>{entity.text}</td>
                <td>
                  <span className={`pill pill-${entity.label}`}>{entity.label}</span>
                </td>
                <td>{(entity.confidence * 100).toFixed(0)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h4>ICD-10-GM codes</h4>
      {note.icd_codes.length === 0 ? (
        <p className="muted">No diagnoses coded yet.</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Term</th>
              <th>Code</th>
              <th>Display</th>
              <th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {note.icd_codes.map((code, i) => (
              <tr key={i}>
                <td>{code.entity_text}</td>
                <td>
                  <code>{code.code}</code>
                </td>
                <td>{code.display}</td>
                <td>{(code.confidence * 100).toFixed(0)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h4>Validator flags</h4>
      {note.validator_flags.length === 0 ? (
        <p className="muted">No flags raised.</p>
      ) : (
        <ul className="flag-list">
          {note.validator_flags.map((flag, i) => (
            <li key={i} className={`flag flag-${flag.severity}`}>
              <strong>{SEVERITY_LABEL[flag.severity] ?? flag.severity}</strong> {flag.message}
            </li>
          ))}
        </ul>
      )}

      <details>
        <summary>
          FHIR bundle ({(note.fhir_bundle.entry as unknown[] | undefined)?.length ?? 0} resources)
          {note.fhir_bundle_id && <> · submitted as {note.fhir_bundle_id}</>}
        </summary>
        <pre className="json-preview">{JSON.stringify(note.fhir_bundle, null, 2)}</pre>
      </details>
    </section>
  );
}
