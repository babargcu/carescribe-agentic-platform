import time
from typing import Any

from app.agents.base import AgentStepResult
from app.nlp.icd10gm import lookup_icd10gm

CODABLE_LABELS = {"diagnosis", "symptom"}


class CodingAgent:
    """Maps extracted diagnosis/symptom entities to ICD-10-GM codes via
    fuzzy lookup against the curated sample catalogue."""

    name = "coding"

    def run(self, entities: list[dict[str, Any]]) -> AgentStepResult:
        start = time.perf_counter()

        codes = []
        for entity in entities:
            if entity.get("label") not in CODABLE_LABELS:
                continue
            match = lookup_icd10gm(entity["text"])
            if match is None:
                continue
            code, display, score = match
            codes.append(
                {
                    "entity_text": entity["text"],
                    "code": code,
                    "display": display,
                    "confidence": round(score * entity.get("confidence", 1.0), 3),
                }
            )

        avg_confidence = sum(c["confidence"] for c in codes) / len(codes) if codes else 0.0
        latency_ms = (time.perf_counter() - start) * 1000
        return AgentStepResult(
            agent_name=self.name,
            output={"icd_codes": codes},
            confidence=avg_confidence,
            latency_ms=latency_ms,
            input_summary=f"{len(entities)} entities considered",
            output_summary=f"{len(codes)} ICD-10-GM codes assigned",
            status="ok",
        )
