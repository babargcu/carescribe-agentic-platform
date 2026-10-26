import time
from typing import Any

from app.agents.base import AgentStepResult
from app.fhir.builders import build_bundle


class FhirAgent:
    """Assembles the FHIR Bundle from extracted entities + coded diagnoses.

    Deliberately does NOT submit to the FHIR server -- that only happens
    from the API layer after a clinician approves the note (see
    `app/api/routes/notes.py`), keeping the pipeline side-effect-free and
    the human-approval gate enforceable in one place.
    """

    name = "fhir"

    def run(
        self,
        session_id: str,
        patient_pseudonym: str,
        clinician_name: str,
        entities: list[dict[str, Any]],
        icd_codes: list[dict[str, Any]],
    ) -> AgentStepResult:
        start = time.perf_counter()

        bundle = build_bundle(session_id, patient_pseudonym, clinician_name, entities, icd_codes)

        latency_ms = (time.perf_counter() - start) * 1000
        resource_count = len(bundle.get("entry", []))
        return AgentStepResult(
            agent_name=self.name,
            output={"fhir_bundle": bundle},
            confidence=1.0,
            latency_ms=latency_ms,
            input_summary=f"{len(entities)} entities, {len(icd_codes)} ICD codes",
            output_summary=f"Bundle assembled with {resource_count} resources (not yet submitted)",
            status="ok",
        )
