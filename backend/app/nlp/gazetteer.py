"""Small curated term lists (German-first) used by the mock extraction
backend and by synthetic data generation. Not exhaustive -- a real system
would use a trained NER model (see docs/ROADMAP.md) instead of lists."""

SYMPTOMS = [
    "Kopfschmerzen",
    "Fieber",
    "Husten",
    "Übelkeit",
    "Schwindel",
    "Atemnot",
    "Bauchschmerzen",
    "Müdigkeit",
    "Schüttelfrost",
    "Halsschmerzen",
]

MEDICATIONS = [
    "Ibuprofen",
    "Paracetamol",
    "Metformin",
    "Amoxicillin",
    "Omeprazol",
    "Ramipril",
    "Metoprolol",
    "Insulin",
]

DIAGNOSES = [
    "Migräne",
    "Grippe",
    "Bronchitis",
    "Diabetes mellitus Typ 2",
    "Hypertonie",
    "Gastritis",
    "Pneumonie",
    "COVID-19",
    "Angststörung",
]
