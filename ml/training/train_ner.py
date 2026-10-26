"""Baseline entity-presence classifier, wired up with a train/val split and
MLflow logging.

This is intentionally NOT a real NER model -- it's a bag-of-character-
ngrams multi-label baseline ("does this sentence mention entity X") trained
on the synthetic data, so the training/evaluation/MLflow *harness* exists
and is exercised end-to-end. Swap in a real token-classification fine-tune
(e.g. HuggingFace `AutoModelForTokenClassification` on a clinical base
model) behind the same data-loading contract once there's enough
real/synthetic data volume to justify it -- see docs/ROADMAP.md.

Usage:
    python train_ner.py --samples ../data/synthetic_samples
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

import mlflow  # noqa: E402
import mlflow.sklearn  # noqa: E402
import numpy as np  # noqa: E402
from sklearn.feature_extraction.text import CountVectorizer  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import f1_score  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402
from sklearn.multiclass import OneVsRestClassifier  # noqa: E402

from app.nlp.gazetteer import DIAGNOSES, MEDICATIONS, SYMPTOMS  # noqa: E402

ALL_LABELS = sorted(set(SYMPTOMS) | set(MEDICATIONS) | set(DIAGNOSES))


def load_samples(samples_dir: Path) -> tuple[list[str], np.ndarray]:
    texts, labels = [], []
    for path in sorted(samples_dir.glob("*.json")):
        sample = json.loads(path.read_text(encoding="utf-8"))
        texts.append(sample["text"])
        present = {e["text"] for e in sample["gold_entities"]}
        labels.append([1 if term in present else 0 for term in ALL_LABELS])
    return texts, np.array(labels)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=str, default="../data/synthetic_samples")
    parser.add_argument("--test-size", type=float, default=0.3)
    args = parser.parse_args()

    texts, labels = load_samples(Path(args.samples))
    if len(texts) < 6:
        raise SystemExit(
            "Need at least ~6 samples for a train/val split -- run "
            "data/generate_synthetic_notes.py first (try --count 30)"
        )

    x_train, x_val, y_train, y_val = train_test_split(
        texts, labels, test_size=args.test_size, random_state=42
    )

    vectorizer = CountVectorizer(analyzer="char_wb", ngram_range=(2, 4))
    x_train_vec = vectorizer.fit_transform(x_train)
    x_val_vec = vectorizer.transform(x_val)

    model = OneVsRestClassifier(LogisticRegression(max_iter=1000))
    model.fit(x_train_vec, y_train)
    predictions = model.predict(x_val_vec)
    val_f1 = f1_score(y_val, predictions, average="micro", zero_division=0)

    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment("carescribe-ner-baseline")

    with mlflow.start_run(run_name="char-ngram-logreg-baseline"):
        mlflow.log_param("model", "char-ngram + one-vs-rest logreg (baseline, not a real NER model)")
        mlflow.log_param("num_train", len(x_train))
        mlflow.log_param("num_val", len(x_val))
        mlflow.log_metric("val_f1_micro", val_f1)
        mlflow.sklearn.log_model(model, artifact_path="model")

    print(f"Validation micro-F1: {val_f1:.3f}")


if __name__ == "__main__":
    main()
