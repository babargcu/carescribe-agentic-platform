import time
from typing import Any

from app.agents.base import AgentStepResult

LOW_CONFIDENCE_THRESHOLD = 0.5


class ValidatorAgent:
    """QA gate: cross-checks every extracted claim against the transcript
    and flags anything a clinician should double-check before approval.

    - An entity whose text can't be located verbatim in the transcript
      (`start == -1`, set by ExtractionAgent._locate_spans) is a strong
      hallucination signal -> "critical".
    - Low-confidence extractions or ICD matches -> "warning".
    - An empty extraction result -> "info" (pipeline may have missed
      something, worth a human look).

    A clinician approval step is required before anything reaches FHIR
    storage regardless of flags -- flags only change *why* a reviewer
    should look closely, never whether review happens at all.
    """

    name = "validator"

    def run(
        self,
        cleaned_text: str,
        entities: list[dict[str, Any]],
        icd_codes: list[dict[str, Any]],
    ) -> AgentStepResult:
        start = time.perf_counter()
        flags: list[dict[str, Any]] = []

        for entity in entities:
            if entity["start"] == -1:
                flags.append(
                    {
                        "field": "entity",
                        "related_entity": entity["text"],
                        "message": (
                            f"'{entity['text']}' was extracted but not found verbatim in the "
                            "transcript -- possible hallucination."
                        ),
                        "severity": "critical",
                    }
                )
            elif entity["confidence"] < LOW_CONFIDENCE_THRESHOLD:
                flags.append(
                    {
                        "field": "entity",
                        "related_entity": entity["text"],
                        "message": f"Low extraction confidence ({entity['confidence']:.2f}).",
                        "severity": "warning",
                    }
                )

        for code in icd_codes:
            if code["confidence"] < LOW_CONFIDENCE_THRESHOLD:
                flags.append(
                    {
                        "field": "icd_code",
                        "related_entity": code["entity_text"],
                        "message": (
                            f"Low-confidence ICD-10-GM match ({code['confidence']:.2f}) for "
                            f"'{code['entity_text']}' -> {code['code']}."
                        ),
                        "severity": "warning",
                    }
                )

        if not entities:
            flags.append(
                {
                    "field": "pipeline",
                    "related_entity": None,
                    "message": "No clinical entities were extracted from this transcript.",
                    "severity": "info",
                }
            )

        has_critical = any(f["severity"] == "critical" for f in flags)

        latency_ms = (time.perf_counter() - start) * 1000
        return AgentStepResult(
            agent_name=self.name,
            output={"validator_flags": flags, "note_status": "needs_review"},
            confidence=0.0 if has_critical else (0.5 if flags else 1.0),
            latency_ms=latency_ms,
            input_summary=f"{len(entities)} entities, {len(icd_codes)} codes",
            output_summary=f"{len(flags)} flag(s)" + (" (critical)" if has_critical else ""),
            status="flagged" if flags else "ok",
        )
