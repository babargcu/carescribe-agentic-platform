"""Evaluates the extraction + coding agents against synthetic gold-labeled
samples and logs precision/recall/F1 to MLflow.

Usage:
    python evaluate_pipeline.py --samples ../data/synthetic_samples
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
os.environ.setdefault("LLM_MODE", "mock")

import mlflow  # noqa: E402

from app.agents.coding_agent import CodingAgent  # noqa: E402
from app.agents.extraction_agent import ExtractionAgent  # noqa: E402
from app.agents.scribe_agent import ScribeAgent  # noqa: E402


def _entity_set(entities: list[dict], text_key: str = "text") -> set[tuple[str, str]]:
    return {(str(e[text_key]).lower(), e.get("label")) for e in entities}


def precision_recall_f1(predicted: set, gold: set) -> tuple[float, float, float]:
    if not predicted and not gold:
        return 1.0, 1.0, 1.0
    true_positives = len(predicted & gold)
    precision = true_positives / len(predicted) if predicted else 0.0
    recall = true_positives / len(gold) if gold else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return precision, recall, f1


async def evaluate(samples_dir: Path) -> dict:
    scribe = ScribeAgent()
    extraction = ExtractionAgent()
    coding = CodingAgent()

    entity_scores: list[tuple[float, float, float]] = []
    icd_scores: list[tuple[float, float, float]] = []

    sample_paths = sorted(samples_dir.glob("*.json"))
    if not sample_paths:
        raise SystemExit(
            f"No synthetic samples found in {samples_dir} -- run "
            "data/generate_synthetic_notes.py first"
        )

    for path in sample_paths:
        sample = json.loads(path.read_text(encoding="utf-8"))

        scribe_result = scribe.run(sample["text"], language=sample.get("language", "de"))
        cleaned_text = scribe_result.output["cleaned_text"]

        extraction_result = await extraction.run(cleaned_text)
        entities = extraction_result.output["entities"]
        coding_result = coding.run(entities)
        codes = coding_result.output["icd_codes"]

        entity_scores.append(
            precision_recall_f1(_entity_set(entities), _entity_set(sample["gold_entities"]))
        )

        predicted_codes = {c["code"] for c in codes}
        gold_codes = {c["code"] for c in sample["gold_icd_codes"] if c.get("code")}
        icd_scores.append(precision_recall_f1(predicted_codes, gold_codes))

    def avg(values: list[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    entity_p, entity_r, entity_f1 = zip(*entity_scores) if entity_scores else ([], [], [])
    icd_p, icd_r, icd_f1 = zip(*icd_scores) if icd_scores else ([], [], [])

    return {
        "num_samples": len(sample_paths),
        "entity_precision": avg(list(entity_p)),
        "entity_recall": avg(list(entity_r)),
        "entity_f1": avg(list(entity_f1)),
        "icd_precision": avg(list(icd_p)),
        "icd_recall": avg(list(icd_r)),
        "icd_f1": avg(list(icd_f1)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=str, default="../data/synthetic_samples")
    args = parser.parse_args()

    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment("carescribe-extraction-eval")

    metrics = asyncio.run(evaluate(Path(args.samples)))

    with mlflow.start_run(run_name=f"eval-{os.environ.get('LLM_MODE', 'mock')}"):
        mlflow.log_param("llm_mode", os.environ.get("LLM_MODE", "mock"))
        mlflow.log_param("num_samples", metrics["num_samples"])
        for key, value in metrics.items():
            if key != "num_samples":
                mlflow.log_metric(key, value)

    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
