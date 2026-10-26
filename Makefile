.PHONY: up down backend-test backend-lint frontend-dev frontend-build eval seed-data

up:
	docker compose up --build

down:
	docker compose down

backend-test:
	cd backend && pytest -q

backend-lint:
	cd backend && ruff check app tests && mypy app

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

eval:
	cd ml && python evaluation/evaluate_pipeline.py

seed-data:
	cd ml && python data/generate_synthetic_notes.py --count 20 --out data/synthetic_samples
