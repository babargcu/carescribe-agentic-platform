import type { FormEvent } from "react";
import { useState } from "react";

interface TextIngestFormProps {
  onSubmit: (text: string) => void;
  disabled?: boolean;
}

const EXAMPLE_TEXT =
  "Die Patientin klagt seit drei Tagen über Kopfschmerzen und Fieber. " +
  "Sie nimmt bereits Ibuprofen. Verdacht auf Grippe.";

export function TextIngestForm({ onSubmit, disabled }: TextIngestFormProps) {
  const [text, setText] = useState("");

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (text.trim()) onSubmit(text.trim());
  }

  return (
    <form className="text-ingest-form" onSubmit={handleSubmit}>
      <textarea
        value={text}
        onChange={(event) => setText(event.target.value)}
        placeholder="Or paste/type a transcript directly…"
        rows={4}
        disabled={disabled}
      />
      <div className="text-ingest-actions">
        <button
          type="button"
          className="btn btn-ghost"
          disabled={disabled}
          onClick={() => setText(EXAMPLE_TEXT)}
        >
          Fill example
        </button>
        <button type="submit" className="btn btn-primary" disabled={disabled || !text.trim()}>
          Run pipeline on text
        </button>
      </div>
    </form>
  );
}
