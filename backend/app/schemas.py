"""Pydantic I/O schemas for the API layer (kept separate from DB models)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SessionCreate(BaseModel):
    patient_pseudonym: str = "synthetic-patient"
    clinician_name: str = "Dr. Demo"
    language: str = "de"


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_pseudonym: str
    clinician_name: str
    language: str
    status: str
    created_at: datetime
    updated_at: datetime


class TranscriptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    raw_text: str
    cleaned_text: str
    audio_duration_s: float | None
    asr_model: str
    asr_confidence: float | None


class EntityOut(BaseModel):
    text: str
    label: str
    start: int
    end: int
    confidence: float


class IcdCodeOut(BaseModel):
    entity_text: str
    code: str
    display: str
    confidence: float


class ValidatorFlagOut(BaseModel):
    field: str
    message: str
    severity: str  # info|warning|critical
    related_entity: str | None = None


class StructuredNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    entities: list[EntityOut]
    icd_codes: list[IcdCodeOut]
    fhir_bundle: dict
    validator_flags: list[ValidatorFlagOut]
    fhir_bundle_id: str | None


class AgentTraceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    step_index: int
    agent_name: str
    input_summary: str
    output_summary: str
    confidence: float | None
    latency_ms: float
    status: str


class ReviewDecision(BaseModel):
    decision: str  # "approve" | "reject"
    edited_entities: list[EntityOut] | None = None
    reviewer_note: str | None = None


class SessionDetail(BaseModel):
    session: SessionOut
    transcript: TranscriptOut | None
    note: StructuredNoteOut | None
    traces: list[AgentTraceOut]
