import time
from typing import Any

from app.agents.base import AgentStepResult
from app.agents.llm_client import LLMClient
from app.nlp.gazetteer import DIAGNOSES, MEDICATIONS, SYMPTOMS

EXTRACTION_SYSTEM_PROMPT = """You are a clinical information extraction assistant working on \
German or English doctor-patient transcripts.
Extract ONLY entities that are explicitly stated in the text -- never invent, infer, or assume \
anything not present. If you are unsure whether something is present, omit it.
Respond with ONLY JSON of this shape, no prose:
{"entities": [{"text": "<exact substring from the transcript>", \
"label": "symptom"|"medication"|"diagnosis"|"dosage"|"duration", "confidence": <0..1 float>}]}
"""


class ExtractionAgent:
    """Pulls clinical entities (symptoms, medications, diagnoses, dosages,
    durations) out of the cleaned transcript. Backed by an LLM in
    "ollama" mode (prompted for strict JSON) or a gazetteer keyword
    spotter in "mock" mode."""

    name = "extraction"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm = llm_client or LLMClient()

    async def run(self, cleaned_text: str) -> AgentStepResult:
        start = time.perf_counter()

        raw = await self.llm.complete_json(
            system_prompt=EXTRACTION_SYSTEM_PROMPT,
            user_prompt=cleaned_text,
            mock_fn=lambda: _mock_extract(cleaned_text),
        )
        entities = _locate_spans(cleaned_text, raw.get("entities", []))
        avg_confidence = (
            sum(e["confidence"] for e in entities) / len(entities) if entities else 0.0
        )

        latency_ms = (time.perf_counter() - start) * 1000
        return AgentStepResult(
            agent_name=self.name,
            output={"entities": entities},
            confidence=avg_confidence,
            latency_ms=latency_ms,
            input_summary=cleaned_text[:200],
            output_summary=f"{len(entities)} entities extracted",
            status="ok" if entities else "flagged",
        )


def _mock_extract(text: str) -> dict[str, Any]:
    lower = text.lower()
    entities: list[dict[str, Any]] = []
    gazetteers = ((SYMPTOMS, "symptom"), (MEDICATIONS, "medication"), (DIAGNOSES, "diagnosis"))
    for gazetteer, label in gazetteers:
        for term in gazetteer:
            if term.lower() in lower:
                entities.append({"text": term, "label": label, "confidence": 0.75})
    return {"entities": entities}


def _locate_spans(text: str, raw_entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Resolve each extracted entity's character span in the source
    transcript. An entity that can't be located (start == -1) is strong
    signal for the Validator Agent that it may be a hallucination."""
    lower_text = text.lower()
    out = []
    for e in raw_entities:
        entity_text = str(e.get("text", ""))
        start = lower_text.find(entity_text.lower())
        end = start + len(entity_text) if start != -1 else -1
        out.append(
            {
                "text": entity_text,
                "label": e.get("label", "unknown"),
                "start": start,
                "end": end,
                "confidence": float(e.get("confidence", 0.5)),
            }
        )
    return out
