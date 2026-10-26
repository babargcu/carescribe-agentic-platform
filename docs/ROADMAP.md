# Roadmap & status

Honest snapshot of what's real vs. stubbed, so this doubles as an
engineering log as well as a project plan.

## Done (MVP)

- [x] FastAPI backend with async SQLAlchemy models (Session, Transcript,
      StructuredNote, AgentTrace)
- [x] Agent pipeline: Scribe → Extraction → Coding → FHIR → Validator,
      with a graph orchestrator and structured per-step tracing
- [x] LLM client abstraction: Ollama (OpenAI-compatible) + deterministic
      mock mode for offline/CI runs
- [x] faster-whisper ASR service wrapper
- [x] ICD-10-GM sample lookup/fuzzy-match coding table (small curated
      subset, not the full catalogue)
- [x] FHIR `Bundle` builder (Encounter/Condition/MedicationStatement/
      Observation) + HAPI FHIR client
- [x] REST API: create session, upload audio, run pipeline, fetch
      transcript/note/trace, approve/edit/reject note
- [x] Prometheus metrics (pipeline latency, per-agent confidence,
      validation flag rate)
- [x] Synthetic data generator (fake doctor–patient dialogues + gold
      entity/ICD annotations, German + English)
- [x] Evaluation harness: precision/recall/F1 of extraction vs. gold
      data, logged to MLflow
- [x] React + TS frontend: recorder, transcript view, structured note
      review/diff, agent timeline, session dashboard
- [x] Docker Compose stack wiring every service together
- [x] GitHub Actions CI (backend lint/type-check/pytest, frontend
      build)

## Explicitly stubbed / simplified (by design, for MVP scope)

- ICD-10-GM table covers a curated sample of common codes, not the full
  German catalogue (full catalogue is a licensed BfArM import — swap-in
  point is `backend/app/nlp/icd10gm.py`)
- No real-time streaming ASR yet — audio is uploaded as a complete
  clip and transcribed in one pass (streaming is a natural extension of
  `whisper_service.py`)
- No authentication/authorization layer (would be required before any
  non-local deployment — see "Next" below)
- Validator agent uses heuristic + LLM-judge confidence scoring, not a
  trained classifier
- No fine-tuned domain model yet — extraction runs on a general
  instruction-tuned LLM via prompting; `ml/training/` has the scaffold
  for fine-tuning a smaller encoder (e.g. a token-classification head)
  once enough synthetic/eval data exists to justify it

## Next

- [ ] AuthN/Z (OIDC) + audit logging for any multi-user deployment
- [ ] Fine-tune a compact clinical NER model and compare against the
      LLM-prompting baseline in the MLflow evaluation harness
- [ ] Streaming ASR (chunked websocket transcription) for true ambient
      capture
- [ ] Expand ICD-10-GM coverage + add SNOMED CT cross-walk
- [ ] Helm chart for Kubernetes deployment (mirrors the Docker Compose
      topology)
- [ ] Model/data versioning via DVC or MLflow Model Registry
- [ ] Load-test the pipeline and publish latency/throughput numbers
