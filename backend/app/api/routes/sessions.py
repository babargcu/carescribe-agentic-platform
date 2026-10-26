import os
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import PipelineOrchestrator
from app.asr.whisper_service import get_whisper_service
from app.db.models import AgentTrace, ClinicalSession, StructuredNote, Transcript
from app.db.session import get_db
from app.fhir.client import FhirClient
from app.monitoring.metrics import (
    AGENT_CONFIDENCE,
    PIPELINE_LATENCY,
    PIPELINE_RUNS,
    VALIDATION_FLAGS,
)
from app.schemas import (
    AgentTraceOut,
    ReviewDecision,
    SessionCreate,
    SessionDetail,
    SessionOut,
    StructuredNoteOut,
    TranscriptOut,
)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])
orchestrator = PipelineOrchestrator()


class TextIngestPayload(BaseModel):
    text: str


async def _get_session_or_404(session_id: str, db: AsyncSession) -> ClinicalSession:
    session = await db.get(ClinicalSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


async def _to_detail(session: ClinicalSession, db: AsyncSession) -> SessionDetail:
    # Full refresh first: with aiosqlite (no RETURNING support), columns with
    # server-side `onupdate`/`default` (e.g. updated_at) are left "expired"
    # after a commit. Accessing an expired attribute outside an awaited
    # context raises MissingGreenlet, so refresh explicitly before Pydantic
    # (a sync call) touches the object.
    await db.refresh(session)
    await db.refresh(session, attribute_names=["transcript", "note", "traces"])
    return SessionDetail(
        session=SessionOut.model_validate(session),
        transcript=TranscriptOut.model_validate(session.transcript) if session.transcript else None,
        note=StructuredNoteOut.model_validate(session.note) if session.note else None,
        traces=[AgentTraceOut.model_validate(t) for t in session.traces],
    )


async def _run_pipeline_and_persist(
    session: ClinicalSession,
    raw_text: str,
    *,
    asr_model: str,
    asr_confidence: float | None,
    duration_s: float | None,
    db: AsyncSession,
) -> None:
    """Runs the agent pipeline and (re-)persists transcript/note/trace rows
    for this session. Clears any prior run's rows first so re-running the
    pipeline on a session (e.g. after fixing an ASR error) is idempotent."""
    await db.execute(delete(AgentTrace).where(AgentTrace.session_id == session.id))
    await db.execute(delete(Transcript).where(Transcript.session_id == session.id))
    await db.execute(delete(StructuredNote).where(StructuredNote.session_id == session.id))

    session.status = "processing"
    db.add(session)

    with PIPELINE_LATENCY.time():
        result = await orchestrator.run(
            session_id=session.id,
            raw_text=raw_text,
            language=session.language,
            patient_pseudonym=session.patient_pseudonym,
            clinician_name=session.clinician_name,
        )
    PIPELINE_RUNS.inc()

    db.add(
        Transcript(
            session_id=session.id,
            raw_text=raw_text,
            cleaned_text=result.cleaned_text,
            audio_duration_s=duration_s,
            asr_model=asr_model,
            asr_confidence=asr_confidence,
        )
    )
    db.add(
        StructuredNote(
            session_id=session.id,
            entities=result.entities,
            icd_codes=result.icd_codes,
            fhir_bundle=result.fhir_bundle,
            validator_flags=result.validator_flags,
            status=result.note_status,
        )
    )

    for i, step in enumerate(result.steps):
        AGENT_CONFIDENCE.labels(agent=step.agent_name).observe(step.confidence or 0.0)
        db.add(
            AgentTrace(
                session_id=session.id,
                step_index=i,
                agent_name=step.agent_name,
                input_summary=step.input_summary,
                output_summary=step.output_summary,
                confidence=step.confidence,
                latency_ms=step.latency_ms,
                status=step.status,
            )
        )

    VALIDATION_FLAGS.inc(len(result.validator_flags))
    session.status = result.note_status
    db.add(session)
    await db.commit()


@router.post("", response_model=SessionOut)
async def create_session(
    payload: SessionCreate, db: AsyncSession = Depends(get_db)
) -> ClinicalSession:
    session = ClinicalSession(**payload.model_dump())
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("", response_model=list[SessionOut])
async def list_sessions(db: AsyncSession = Depends(get_db)) -> list[ClinicalSession]:
    result = await db.execute(select(ClinicalSession).order_by(ClinicalSession.created_at.desc()))
    return list(result.scalars().all())


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)) -> SessionDetail:
    session = await _get_session_or_404(session_id, db)
    return await _to_detail(session, db)


@router.post("/{session_id}/transcript", response_model=SessionDetail)
async def ingest_text_transcript(
    session_id: str, payload: TextIngestPayload, db: AsyncSession = Depends(get_db)
) -> SessionDetail:
    """Ingest a transcript directly as text, bypassing ASR -- useful for
    demos, tests, and for text-only EHR integrations."""
    session = await _get_session_or_404(session_id, db)
    await _run_pipeline_and_persist(
        session,
        payload.text,
        asr_model="text-input",
        asr_confidence=1.0,
        duration_s=None,
        db=db,
    )
    return await _to_detail(session, db)


@router.post("/{session_id}/audio", response_model=SessionDetail)
async def ingest_audio(
    session_id: str, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
) -> SessionDetail:
    session = await _get_session_or_404(session_id, db)

    suffix = os.path.splitext(file.filename or "audio.wav")[1] or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        whisper = get_whisper_service()
        transcription = whisper.transcribe(tmp_path, language=session.language)
    finally:
        os.unlink(tmp_path)

    await _run_pipeline_and_persist(
        session,
        transcription.text,
        asr_model=transcription.model_name,
        asr_confidence=transcription.confidence,
        duration_s=transcription.duration_s,
        db=db,
    )
    return await _to_detail(session, db)


@router.post("/{session_id}/review", response_model=SessionDetail)
async def review_note(
    session_id: str, decision: ReviewDecision, db: AsyncSession = Depends(get_db)
) -> SessionDetail:
    """Clinician review gate: approve (-> submit to FHIR server) or reject.
    This is the only place a note's FHIR bundle is ever actually submitted --
    the agent pipeline only builds it."""
    session = await _get_session_or_404(session_id, db)
    await db.refresh(session, attribute_names=["note"])
    if session.note is None:
        raise HTTPException(status_code=400, detail="No structured note to review yet")

    if decision.decision == "approve":
        if decision.edited_entities is not None:
            session.note.entities = [e.model_dump() for e in decision.edited_entities]
        try:
            fhir_result = await FhirClient().submit_bundle(session.note.fhir_bundle)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"FHIR submission failed: {exc}") from exc
        session.note.fhir_bundle_id = fhir_result.get("id")
        session.note.status = "submitted_to_fhir"
        session.status = "submitted_to_fhir"
    elif decision.decision == "reject":
        session.note.status = "rejected"
        session.status = "rejected"
    else:
        raise HTTPException(status_code=400, detail="decision must be 'approve' or 'reject'")

    db.add(session.note)
    db.add(session)
    await db.commit()
    return await _to_detail(session, db)
