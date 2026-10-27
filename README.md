# CareScribe

**Agentic ambient clinical documentation & FHIR coding platform.**

CareScribe turns a spoken doctor–patient encounter into a reviewed,
structured, FHIR-coded clinical note — end to end, with a multi-agent
pipeline, a human-in-the-loop review UI, and the MLOps scaffolding
(experiment tracking, monitoring, CI/CD) needed to run it safely in
production.

It brings together clinical NLP, multi-agent orchestration, FHIR
interoperability, and MLOps in a single platform, with a focus on the
German healthcare context (ICD-10-GM coding, German and English
encounters). The repository ships with synthetic audio/text samples
only — no real patient data.

> ⚠️ **Not a certified medical device.** CareScribe has not undergone
> clinical validation or regulatory clearance (MDR/CE). Do not use it on
> real patient data or to inform clinical decisions until those steps
> are complete.

## Motivation

Clinical documentation consumes a large share of clinicians' time, and
the output is often free text that downstream systems can't use.
CareScribe addresses both problems at once: it captures the encounter
ambiently, produces a structured and coded note, and delivers it as
standard FHIR resources — while keeping a clinician in control of every
note before it is stored.

## Architecture

```mermaid
flowchart LR
    subgraph Client["Frontend (React + TS)"]
        REC[Audio Recorder]
        REV[Review / Diff UI]
        TL[Agent Timeline]
    end

    subgraph API["Backend (FastAPI)"]
        EP[/REST + WebSocket API/]
        ORCH[Agent Orchestrator]
    end

    subgraph Agents["Agent Pipeline"]
        SCR[Scribe Agent\nASR cleanup]
        EXT[Extraction Agent\nclinical NER]
        COD[Coding Agent\nICD-10-GM / SNOMED]
        FHR[FHIR Agent\nresource builder]
        VAL[Validator Agent\nhallucination / confidence QA]
    end

    subgraph Infra["Data & MLOps"]
        PG[(PostgreSQL)]
        HAPI[(HAPI FHIR Server)]
        MLF[MLflow Tracking]
        LLM[Ollama LLM runtime]
        ASR[faster-whisper]
        PROM[Prometheus]
        GRAF[Grafana]
    end

    REC -- audio --> EP
    EP --> ORCH
    ORCH --> SCR --> EXT --> COD --> FHR --> VAL
    VAL -- needs_review --> REV
    REV -- approve/edit --> EP
    ORCH -. traces .-> TL
    SCR <-.-> ASR
    EXT <-.-> LLM
    COD <-.-> LLM
    FHR --> HAPI
    EP --> PG
    ORCH -. metrics .-> PROM --> GRAF
    EXT -. eval runs .-> MLF
```

**Pipeline, in words:** audio in → **Scribe Agent** transcribes
(faster-whisper) and cleans disfluencies → **Extraction Agent** pulls
clinical entities (symptoms, meds, diagnoses, dosages) via a local LLM
→ **Coding Agent** maps entities to ICD-10-GM codes → **FHIR Agent**
assembles a FHIR `Bundle` (Encounter, Condition, MedicationStatement,
Observation) and posts it to a HAPI FHIR server → **Validator Agent**
cross-checks extracted claims against the transcript, flags
low-confidence or unsupported statements, and routes anything
uncertain to a clinician review queue. Nothing reaches FHIR storage
without passing validation or explicit human approval.

Every agent run is logged as a structured trace (inputs, outputs,
confidence, latency) so the frontend can render a step-by-step
timeline, and so the same traces can be fed back into evaluation.

## Tech stack

| Layer | Choice |
|---|---|
| ASR | faster-whisper (local, CTranslate2) |
| LLM reasoning | Ollama (local models, e.g. `llama3.1`/`qwen2.5`) via OpenAI-compatible API, with a deterministic mock mode for CI/offline dev |
| Backend | FastAPI, SQLAlchemy (async), Pydantic v2, Alembic |
| Agent orchestration | Custom lightweight graph orchestrator (`backend/app/agents`) |
| Clinical coding | ICD-10-GM sample lookup table + fuzzy matching |
| FHIR | `fhir.resources` + HAPI FHIR (Docker) |
| Database | PostgreSQL |
| MLOps | MLflow (experiment tracking), evaluation harness with P/R/F1 against synthetic gold data |
| Monitoring | Prometheus + Grafana |
| Frontend | React 18 + TypeScript + Vite |
| CI/CD | GitHub Actions (lint, type-check, pytest, frontend build) |
| Packaging | Docker Compose (single-command local stack) |

## Repo layout

```
backend/     FastAPI app, agent pipeline, ASR, FHIR, DB, tests
frontend/    React + TS + Vite client
ml/          synthetic data generation, training, evaluation, MLflow
infra/       Prometheus/Grafana config
docs/        architecture notes, roadmap
.github/     CI workflows
docker-compose.yml   full local stack (one command)
```

## Quickstart

```bash
cp .env.example .env
docker compose up --build
```

This starts: `backend` (FastAPI, :8000), `frontend` (:5173), `postgres`,
`hapi-fhir` (:8080), `ollama` (:11434), `mlflow` (:5000), `prometheus`
(:9090), `grafana` (:3000).

On first run, pull a local LLM for the agents:

```bash
docker compose exec ollama ollama pull qwen2.5:7b-instruct
```

If you skip this, the backend automatically falls back to a
deterministic **mock LLM mode** (`LLM_MODE=mock` in `.env`) — the full
pipeline still runs end-to-end, with lower-quality extraction, which is
enough to exercise the API, UI, and tests without a GPU or model
download.

Run the backend test suite directly (no Docker):

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

Run the frontend directly:

```bash
cd frontend
npm install
npm run dev
```

## Project status / roadmap

CareScribe is at MVP stage and under active development. See
[`docs/ROADMAP.md`](docs/ROADMAP.md) for what's implemented, what's
stubbed, and what's next (model fine-tuning, real-time streaming ASR,
Kubernetes/Helm deployment, clinical trial-style evaluation).

## License

MIT — see [`LICENSE`](LICENSE). Synthetic data only; see
[`docs/ETHICS.md`](docs/ETHICS.md) for data-handling notes.
