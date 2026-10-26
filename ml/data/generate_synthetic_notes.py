"""Generates synthetic German doctor-patient encounter transcripts with
gold entity/ICD annotations -- used to evaluate the extraction and coding
agents without ever touching real clinical data (see docs/ETHICS.md).

Usage:
    python generate_synthetic_notes.py --count 20 --out synthetic_samples
"""

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.nlp.gazetteer import DIAGNOSES, MEDICATIONS, SYMPTOMS  # noqa: E402
from app.nlp.icd10gm import ICD10GM_SAMPLE  # noqa: E402

TEMPLATES = [
    "Der Patient klagt über {symptom1} und {symptom2}. Er nimmt {medication}. Diagnose: {diagnosis}.",
    "Die Patientin berichtet seit drei Tagen über {symptom1}. Verordnet wurde {medication}. "
    "Verdacht auf {diagnosis}.",
    "Guten Tag, ich habe seit heute Morgen {symptom1} und {symptom2}. Arzt: Das klingt nach "
    "{diagnosis}. Nehmen Sie bitte {medication}.",
    "Patient: Mir ist seit gestern übel und ich habe {symptom1}. Arzt: Wir diagnostizieren "
    "{diagnosis} und verschreiben {medication}.",
]


def generate_sample(rng: random.Random) -> dict:
    symptom1, symptom2 = rng.sample(SYMPTOMS, 2)
    medication = rng.choice(MEDICATIONS)
    diagnosis = rng.choice(DIAGNOSES)
    template = rng.choice(TEMPLATES)
    text = template.format(
        symptom1=symptom1, symptom2=symptom2, medication=medication, diagnosis=diagnosis
    )

    candidate_entities = [
        {"text": symptom1, "label": "symptom"},
        {"text": symptom2, "label": "symptom"},
        {"text": medication, "label": "medication"},
        {"text": diagnosis, "label": "diagnosis"},
    ]
    # Keep only entities that actually made it into the rendered text.
    gold_entities = [e for e in candidate_entities if e["text"] in text]

    # CodingAgent codes both "diagnosis" and "symptom" entities (see
    # app/agents/coding_agent.py CODABLE_LABELS) -- gold labels must cover
    # the same scope, or precision looks artificially low during eval.
    gold_icd_codes = []
    for entity in gold_entities:
        if entity["label"] not in ("diagnosis", "symptom"):
            continue
        icd_entry = ICD10GM_SAMPLE.get(entity["text"])
        if icd_entry:
            code, display = icd_entry
            gold_icd_codes.append({"entity_text": entity["text"], "code": code, "display": display})

    return {
        "text": text,
        "language": "de",
        "gold_entities": gold_entities,
        "gold_icd_codes": gold_icd_codes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--out", type=str, default="synthetic_samples")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    for i in range(args.count):
        sample = generate_sample(rng)
        (out_dir / f"sample_{i:03d}.json").write_text(
            json.dumps(sample, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    print(f"Wrote {args.count} synthetic samples to {out_dir}")


if __name__ == "__main__":
    main()
