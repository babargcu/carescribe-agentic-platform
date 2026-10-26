from app.agents.base import AgentStepResult, PipelineResult
from app.agents.coding_agent import CodingAgent
from app.agents.extraction_agent import ExtractionAgent
from app.agents.fhir_agent import FhirAgent
from app.agents.scribe_agent import ScribeAgent
from app.agents.validator_agent import ValidatorAgent


class PipelineOrchestrator:
    """Runs the full agent graph for one transcript:

        Scribe -> Extraction -> Coding -> FHIR -> Validator

    Each agent's `AgentStepResult` both feeds the next step's input and is
    collected into `PipelineResult.steps` for persistence as `AgentTrace`
    rows (and rendering as the frontend's agent timeline). The graph is
    intentionally linear/sequential here -- there's no branching or
    retries yet; see docs/ROADMAP.md for where that would extend.
    """

    def __init__(self) -> None:
        self.scribe = ScribeAgent()
        self.extraction = ExtractionAgent()
        self.coding = CodingAgent()
        self.fhir = FhirAgent()
        self.validator = ValidatorAgent()

    async def run(
        self,
        *,
        session_id: str,
        raw_text: str,
        language: str,
        patient_pseudonym: str,
        clinician_name: str,
    ) -> PipelineResult:
        steps: list[AgentStepResult] = []

        scribe_result = self.scribe.run(raw_text, language=language)
        steps.append(scribe_result)
        cleaned_text = scribe_result.output["cleaned_text"]

        extraction_result = await self.extraction.run(cleaned_text)
        steps.append(extraction_result)
        entities = extraction_result.output["entities"]

        coding_result = self.coding.run(entities)
        steps.append(coding_result)
        icd_codes = coding_result.output["icd_codes"]

        fhir_result = self.fhir.run(
            session_id, patient_pseudonym, clinician_name, entities, icd_codes
        )
        steps.append(fhir_result)
        fhir_bundle = fhir_result.output["fhir_bundle"]

        validator_result = self.validator.run(cleaned_text, entities, icd_codes)
        steps.append(validator_result)

        return PipelineResult(
            cleaned_text=cleaned_text,
            entities=entities,
            icd_codes=icd_codes,
            fhir_bundle=fhir_bundle,
            validator_flags=validator_result.output["validator_flags"],
            note_status=validator_result.output["note_status"],
            steps=steps,
        )
