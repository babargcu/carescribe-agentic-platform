"""Hand-built FHIR R4 resource dicts.

Deliberately not using the `fhir.resources` pydantic library here: for a
curated, small resource surface (Encounter/Condition/MedicationStatement
wrapped in a Bundle) plain dict builders are easier to read, easier to
unit-test, and avoid pinning to one FHIR sub-version (R4 vs R4B vs R5)
that library enforces. Swap-in point for a stricter validated builder if
the resource surface grows.
"""

import uuid
from typing import Any

FHIR_ICD10GM_SYSTEM = "http://fhir.de/CodeSystem/bfarm/icd-10-gm"
AI_CONFIDENCE_EXTENSION_URL = "https://carescribe.example/fhir/StructureDefinition/ai-confidence"


def _confidence_extension(confidence: float | None) -> list[dict[str, Any]]:
    if confidence is None:
        return []
    return [{"url": AI_CONFIDENCE_EXTENSION_URL, "valueDecimal": round(confidence, 3)}]


def build_encounter(session_id: str, patient_pseudonym: str, clinician_name: str) -> dict[str, Any]:
    return {
        "resourceType": "Encounter",
        "id": f"encounter-{session_id}",
        "status": "finished",
        "class": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                        "code": "AMB",
                        "display": "ambulatory",
                    }
                ]
            }
        ],
        "subject": {"display": patient_pseudonym},
        "participant": [{"individual": {"display": clinician_name}}],
    }


def build_condition(session_id: str, icd_code: dict[str, Any]) -> dict[str, Any]:
    return {
        "resourceType": "Condition",
        "id": f"condition-{uuid.uuid4().hex[:8]}",
        "clinicalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "active",
                }
            ]
        },
        "code": {
            "coding": [
                {
                    "system": FHIR_ICD10GM_SYSTEM,
                    "code": icd_code["code"],
                    "display": icd_code["display"],
                }
            ],
            "text": icd_code["entity_text"],
        },
        "encounter": {"reference": f"Encounter/encounter-{session_id}"},
        "extension": _confidence_extension(icd_code.get("confidence")),
    }


def build_medication_statement(session_id: str, entity: dict[str, Any]) -> dict[str, Any]:
    return {
        "resourceType": "MedicationStatement",
        "id": f"medstatement-{uuid.uuid4().hex[:8]}",
        "status": "active",
        "medicationCodeableConcept": {"text": entity["text"]},
        "context": {"reference": f"Encounter/encounter-{session_id}"},
        "extension": _confidence_extension(entity.get("confidence")),
    }


def build_bundle(
    session_id: str,
    patient_pseudonym: str,
    clinician_name: str,
    entities: list[dict[str, Any]],
    icd_codes: list[dict[str, Any]],
) -> dict[str, Any]:
    """Assemble the full FHIR Bundle for one encounter. Returned as a
    `collection` bundle -- `FhirClient.to_transaction` converts it to a
    `transaction` bundle only at actual submission time."""
    encounter = build_encounter(session_id, patient_pseudonym, clinician_name)
    conditions = [build_condition(session_id, code) for code in icd_codes]
    medications = [
        build_medication_statement(session_id, e)
        for e in entities
        if e.get("label") == "medication"
    ]

    resources = [encounter, *conditions, *medications]
    return {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [{"resource": r} for r in resources],
    }
