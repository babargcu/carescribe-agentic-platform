// Mirrors backend/app/schemas.py -- kept in sync by hand for this project's
// size; a larger codebase would generate this from the OpenAPI schema.

export type SessionStatus =
  | "created"
  | "processing"
  | "needs_review"
  | "approved"
  | "rejected"
  | "submitted_to_fhir";

export interface SessionOut {
  id: string;
  patient_pseudonym: string;
  clinician_name: string;
  language: string;
  status: SessionStatus;
  created_at: string;
  updated_at: string;
}

export interface TranscriptOut {
  id: string;
  raw_text: string;
  cleaned_text: string;
  audio_duration_s: number | null;
  asr_model: string;
  asr_confidence: number | null;
}

export interface EntityOut {
  text: string;
  label: "symptom" | "medication" | "diagnosis" | "dosage" | "duration" | "unknown";
  start: number;
  end: number;
  confidence: number;
}

export interface IcdCodeOut {
  entity_text: string;
  code: string;
  display: string;
  confidence: number;
}

export type FlagSeverity = "info" | "warning" | "critical";

export interface ValidatorFlagOut {
  field: string;
  message: string;
  severity: FlagSeverity;
  related_entity: string | null;
}

export interface StructuredNoteOut {
  id: string;
  status: string;
  entities: EntityOut[];
  icd_codes: IcdCodeOut[];
  fhir_bundle: Record<string, unknown>;
  validator_flags: ValidatorFlagOut[];
  fhir_bundle_id: string | null;
}

export interface AgentTraceOut {
  step_index: number;
  agent_name: string;
  input_summary: string;
  output_summary: string;
  confidence: number | null;
  latency_ms: number;
  status: "ok" | "flagged" | "error";
}

export interface SessionDetail {
  session: SessionOut;
  transcript: TranscriptOut | null;
  note: StructuredNoteOut | null;
  traces: AgentTraceOut[];
}
