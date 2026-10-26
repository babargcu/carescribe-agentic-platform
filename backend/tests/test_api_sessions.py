import pytest

from app.fhir.client import FhirClient


@pytest.mark.asyncio
async def test_create_and_fetch_session(client):
    resp = await client.post("/api/sessions", json={"patient_pseudonym": "patient-1"})
    assert resp.status_code == 200
    session = resp.json()
    assert session["status"] == "created"

    resp = await client.get(f"/api/sessions/{session['id']}")
    assert resp.status_code == 200
    assert resp.json()["session"]["id"] == session["id"]


@pytest.mark.asyncio
async def test_404_for_missing_session(client):
    resp = await client.get("/api/sessions/does-not-exist")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_text_ingest_runs_pipeline_and_produces_note(client):
    create = await client.post("/api/sessions", json={"patient_pseudonym": "patient-2"})
    session_id = create.json()["id"]

    resp = await client.post(
        f"/api/sessions/{session_id}/transcript",
        json={"text": "Die Patientin hat Fieber und Husten."},
    )
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["note"] is not None
    assert detail["note"]["status"] == "needs_review"
    assert len(detail["traces"]) == 5


@pytest.mark.asyncio
async def test_review_reject_does_not_touch_fhir(client):
    create = await client.post("/api/sessions", json={"patient_pseudonym": "patient-3"})
    session_id = create.json()["id"]
    await client.post(
        f"/api/sessions/{session_id}/transcript", json={"text": "Der Patient hat Kopfschmerzen."}
    )

    resp = await client.post(f"/api/sessions/{session_id}/review", json={"decision": "reject"})
    assert resp.status_code == 200
    assert resp.json()["note"]["status"] == "rejected"


@pytest.mark.asyncio
async def test_review_approve_submits_bundle(client, monkeypatch):
    async def fake_submit_bundle(self, bundle):
        assert bundle["resourceType"] == "Bundle"
        return {"id": "fake-bundle-123"}

    monkeypatch.setattr(FhirClient, "submit_bundle", fake_submit_bundle)

    create = await client.post("/api/sessions", json={"patient_pseudonym": "patient-4"})
    session_id = create.json()["id"]
    await client.post(
        f"/api/sessions/{session_id}/transcript",
        json={"text": "Die Patientin hat Migräne und nimmt Ibuprofen."},
    )

    resp = await client.post(f"/api/sessions/{session_id}/review", json={"decision": "approve"})
    assert resp.status_code == 200
    note = resp.json()["note"]
    assert note["status"] == "submitted_to_fhir"
    assert note["fhir_bundle_id"] == "fake-bundle-123"
