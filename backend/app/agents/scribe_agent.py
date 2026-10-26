import re
import time

from app.agents.base import AgentStepResult

FILLER_WORDS = {
    "de": ["äh", "ähm", "also", "halt", "sozusagen", "quasi"],
    "en": ["um", "uh", "like", "you know", "i mean"],
}


class ScribeAgent:
    """Cleans raw ASR output: strips filler words/disfluencies, normalizes
    whitespace, fixes sentence casing. Deliberately rule-based (not an LLM
    call) -- it's cheap, deterministic, and fast enough to run on every
    utterance without adding pipeline latency."""

    name = "scribe"

    def run(self, raw_text: str, language: str = "de") -> AgentStepResult:
        start = time.perf_counter()

        text = raw_text
        for filler in FILLER_WORDS.get(language, FILLER_WORDS["de"]):
            text = re.sub(rf"\b{re.escape(filler)}\b", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s+", " ", text).strip()
        text = _fix_sentence_casing(text)

        latency_ms = (time.perf_counter() - start) * 1000
        return AgentStepResult(
            agent_name=self.name,
            output={"cleaned_text": text},
            confidence=1.0 if text else 0.0,
            latency_ms=latency_ms,
            input_summary=raw_text[:200],
            output_summary=text[:200],
            status="ok" if text else "flagged",
        )


def _fix_sentence_casing(text: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return " ".join(s[:1].upper() + s[1:] if s else s for s in sentences).strip()
