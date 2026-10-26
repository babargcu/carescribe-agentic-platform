from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentStepResult:
    """Uniform result shape every pipeline agent returns.

    This is what gets persisted as an `AgentTrace` row and rendered as a
    step in the frontend's agent timeline, so every agent -- however it
    works internally -- reports the same fields.
    """

    agent_name: str
    output: dict[str, Any]
    confidence: float | None
    latency_ms: float
    input_summary: str
    output_summary: str
    status: str = "ok"  # ok | flagged | error


@dataclass
class PipelineResult:
    """Final output of running the full agent pipeline once."""

    cleaned_text: str
    entities: list[dict]
    icd_codes: list[dict]
    fhir_bundle: dict
    validator_flags: list[dict]
    note_status: str
    steps: list[AgentStepResult] = field(default_factory=list)
