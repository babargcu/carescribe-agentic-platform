import pytest

from app.agents.coding_agent import CodingAgent
from app.agents.orchestrator import PipelineOrchestrator
from app.agents.scribe_agent import ScribeAgent
from app.agents.validator_agent import ValidatorAgent


def test_scribe_agent_strips_filler_words_and_fixes_casing():
    agent = ScribeAgent()
    result = agent.run("also der patient hat äh fieber und, ähm, kopfschmerzen.", language="de")

    assert "äh" not in result.output["cleaned_text"].lower().split()
    assert result.output["cleaned_text"].startswith("Der patient")
    assert result.confidence == 1.0


def test_scribe_agent_flags_empty_output():
    agent = ScribeAgent()
    result = agent.run("", language="de")
    assert result.status == "flagged"
    assert result.confidence == 0.0


def test_coding_agent_matches_known_diagnosis():
    agent = CodingAgent()
    entities = [{"text": "Migräne", "label": "diagnosis", "confidence": 0.9, "start": 0, "end": 7}]
    result = agent.run(entities)

    codes = result.output["icd_codes"]
    assert len(codes) == 1
    assert codes[0]["code"] == "G43.9"


def test_coding_agent_ignores_medication_entities():
    agent = CodingAgent()
    entities = [
        {"text": "Ibuprofen", "label": "medication", "confidence": 0.9, "start": 0, "end": 9}
    ]
    result = agent.run(entities)
    assert result.output["icd_codes"] == []


def test_validator_flags_unlocatable_entity_as_critical():
    agent = ValidatorAgent()
    entities = [
        {"text": "Herzinfarkt", "label": "diagnosis", "confidence": 0.9, "start": -1, "end": -1}
    ]
    result = agent.run("Der Patient hat Kopfschmerzen.", entities, [])

    flags = result.output["validator_flags"]
    assert any(f["severity"] == "critical" for f in flags)
    assert result.status == "flagged"


def test_validator_passes_through_clean_entity_without_critical_flag():
    agent = ValidatorAgent()
    text = "Der Patient hat Kopfschmerzen."
    entities = [
        {"text": "Kopfschmerzen", "label": "symptom", "confidence": 0.9, "start": 17, "end": 30}
    ]
    result = agent.run(text, entities, [])
    flags = result.output["validator_flags"]
    assert not any(f["severity"] == "critical" for f in flags)


@pytest.mark.asyncio
async def test_orchestrator_runs_full_pipeline_end_to_end():
    orchestrator = PipelineOrchestrator()
    result = await orchestrator.run(
        session_id="test-session-1",
        raw_text="also der Patient klagt über Kopfschmerzen und Fieber, nimmt Ibuprofen.",
        language="de",
        patient_pseudonym="synthetic-patient",
        clinician_name="Dr. Test",
    )

    assert result.cleaned_text
    assert any(e["label"] == "symptom" for e in result.entities)
    assert any(c["code"] for c in result.icd_codes)
    assert result.fhir_bundle["resourceType"] == "Bundle"
    assert result.note_status == "needs_review"
    # scribe, extraction, coding, fhir, validator
    assert [s.agent_name for s in result.steps] == [
        "scribe",
        "extraction",
        "coding",
        "fhir",
        "validator",
    ]
