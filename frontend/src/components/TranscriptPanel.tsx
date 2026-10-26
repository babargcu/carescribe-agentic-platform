import type { ReactNode } from "react";
import type { EntityOut, TranscriptOut } from "../types";

interface TranscriptPanelProps {
  transcript: TranscriptOut;
  entities: EntityOut[];
}

const LABEL_CLASS: Record<string, string> = {
  symptom: "highlight-symptom",
  medication: "highlight-medication",
  diagnosis: "highlight-diagnosis",
};

/** Renders the cleaned transcript with extracted entities highlighted
 * inline, so a clinician can see at a glance what the model picked up
 * and where. Entities with start === -1 (unlocatable -- see
 * ValidatorAgent) are skipped here since they have no valid span. */
function renderHighlighted(text: string, entities: EntityOut[]) {
  const spans = entities
    .filter((e) => e.start >= 0 && e.end > e.start)
    .sort((a, b) => a.start - b.start);

  const nodes: ReactNode[] = [];
  let cursor = 0;
  spans.forEach((entity, i) => {
    if (entity.start < cursor) return; // skip overlaps
    nodes.push(text.slice(cursor, entity.start));
    nodes.push(
      <mark key={i} className={LABEL_CLASS[entity.label] ?? "highlight-other"} title={entity.label}>
        {text.slice(entity.start, entity.end)}
      </mark>,
    );
    cursor = entity.end;
  });
  nodes.push(text.slice(cursor));
  return nodes;
}

export function TranscriptPanel({ transcript, entities }: TranscriptPanelProps) {
  return (
    <section className="card">
      <h3>Transcript</h3>
      <p className="meta-row">
        ASR model: <code>{transcript.asr_model}</code>
        {transcript.asr_confidence !== null && (
          <> · confidence {(transcript.asr_confidence * 100).toFixed(0)}%</>
        )}
        {transcript.audio_duration_s !== null && (
          <> · {transcript.audio_duration_s.toFixed(1)}s audio</>
        )}
      </p>
      <p className="transcript-text">{renderHighlighted(transcript.cleaned_text, entities)}</p>
      <details>
        <summary>Raw ASR output (before Scribe Agent cleanup)</summary>
        <p className="transcript-text transcript-raw">{transcript.raw_text}</p>
      </details>
    </section>
  );
}
