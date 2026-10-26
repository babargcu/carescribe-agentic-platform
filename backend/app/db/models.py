from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_uuid


class ClinicalSession(Base, TimestampMixin):
    """One doctor-patient encounter being documented.

    `patient_pseudonym` is a synthetic/pseudonymous label only -- this
    project never stores or expects real patient-identifiable data.
    """

    __tablename__ = "clinical_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    patient_pseudonym: Mapped[str] = mapped_column(String, default="synthetic-patient")
    clinician_name: Mapped[str] = mapped_column(String, default="Dr. Demo")
    language: Mapped[str] = mapped_column(String, default="de")
    status: Mapped[str] = mapped_column(String, default="created")
    # created -> transcribing -> processing -> needs_review -> approved|rejected
    # -> submitted_to_fhir

    transcript: Mapped["Transcript | None"] = relationship(
        back_populates="session", uselist=False, cascade="all, delete-orphan"
    )
    note: Mapped["StructuredNote | None"] = relationship(
        back_populates="session", uselist=False, cascade="all, delete-orphan"
    )
    traces: Mapped[list["AgentTrace"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="AgentTrace.step_index"
    )


class Transcript(Base, TimestampMixin):
    __tablename__ = "transcripts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    session_id: Mapped[str] = mapped_column(ForeignKey("clinical_sessions.id"), unique=True)

    raw_text: Mapped[str] = mapped_column(Text, default="")
    cleaned_text: Mapped[str] = mapped_column(Text, default="")
    audio_duration_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    asr_model: Mapped[str] = mapped_column(String, default="")
    asr_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    session: Mapped[ClinicalSession] = relationship(back_populates="transcript")


class StructuredNote(Base, TimestampMixin):
    __tablename__ = "structured_notes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    session_id: Mapped[str] = mapped_column(ForeignKey("clinical_sessions.id"), unique=True)

    entities: Mapped[list] = mapped_column(JSON, default=list)
    icd_codes: Mapped[list] = mapped_column(JSON, default=list)
    fhir_bundle: Mapped[dict] = mapped_column(JSON, default=dict)
    validator_flags: Mapped[list] = mapped_column(JSON, default=list)

    status: Mapped[str] = mapped_column(String, default="draft")
    # draft -> needs_review -> approved|rejected -> submitted_to_fhir
    fhir_bundle_id: Mapped[str | None] = mapped_column(String, nullable=True)

    session: Mapped[ClinicalSession] = relationship(back_populates="note")


class AgentTrace(Base, TimestampMixin):
    """One recorded step of the agent pipeline, for the UI timeline and evals."""

    __tablename__ = "agent_traces"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    session_id: Mapped[str] = mapped_column(ForeignKey("clinical_sessions.id"))

    step_index: Mapped[int] = mapped_column(Integer)
    agent_name: Mapped[str] = mapped_column(String)
    input_summary: Mapped[str] = mapped_column(Text, default="")
    output_summary: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String, default="ok")  # ok|flagged|error

    session: Mapped[ClinicalSession] = relationship(back_populates="traces")
