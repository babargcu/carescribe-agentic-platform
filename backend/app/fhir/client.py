from typing import Any

import httpx

from app.core.config import get_settings


class FhirClient:
    """Minimal client for submitting a Bundle to a FHIR R4 server (HAPI FHIR
    in docker-compose). Only called from the review-approval API route --
    never from inside the agent pipeline itself, so nothing reaches FHIR
    storage without a clinician's explicit approval."""

    def __init__(self, base_url: str | None = None) -> None:
        settings = get_settings()
        self.base_url = base_url or settings.fhir_server_url

    @staticmethod
    def to_transaction(bundle: dict[str, Any]) -> dict[str, Any]:
        entries = []
        for entry in bundle.get("entry", []):
            resource = entry["resource"]
            entries.append(
                {
                    "fullUrl": f"urn:uuid:{resource['id']}",
                    "resource": resource,
                    "request": {
                        "method": "PUT",
                        "url": f"{resource['resourceType']}/{resource['id']}",
                    },
                }
            )
        return {"resourceType": "Bundle", "type": "transaction", "entry": entries}

    async def submit_bundle(self, bundle: dict[str, Any]) -> dict[str, Any]:
        transaction = self.to_transaction(bundle)
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            resp = await client.post(
                "/", json=transaction, headers={"Content-Type": "application/fhir+json"}
            )
            resp.raise_for_status()
            return resp.json()
