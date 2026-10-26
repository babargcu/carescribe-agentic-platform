"""Curated ICD-10-GM sample lookup with fuzzy matching.

This is a small hand-picked subset (common diagnoses/symptoms) for demo
purposes -- NOT the full German ICD-10-GM catalogue, which is a licensed
BfArM import. Swap this module out for a real catalogue lookup (e.g. a
Postgres table loaded from the official BfArM release) without touching
any calling code; the public surface is just `lookup_icd10gm`.
"""

from rapidfuzz import fuzz, process

# term -> (code, German display text)
ICD10GM_SAMPLE: dict[str, tuple[str, str]] = {
    "Migräne": ("G43.9", "Migräne, nicht näher bezeichnet"),
    "Grippe": ("J11.1", "Grippe mit sonstigen Manifestationen, Virus nicht nachgewiesen"),
    "Bronchitis": ("J20.9", "Akute Bronchitis, nicht näher bezeichnet"),
    "Diabetes mellitus Typ 2": ("E11.9", "Diabetes mellitus, Typ 2, ohne Komplikationen"),
    "Hypertonie": ("I10", "Essentielle (primäre) Hypertonie"),
    "Gastritis": ("K29.7", "Gastritis, nicht näher bezeichnet"),
    "Pneumonie": ("J18.9", "Pneumonie, nicht näher bezeichnet"),
    "COVID-19": ("U07.1", "COVID-19, Virus nachgewiesen"),
    "Angststörung": ("F41.9", "Angststörung, nicht näher bezeichnet"),
    "Kopfschmerzen": ("R51", "Kopfschmerz"),
    "Fieber": ("R50.9", "Fieber, nicht näher bezeichnet"),
    "Husten": ("R05", "Husten"),
    "Übelkeit": ("R11", "Übelkeit und Erbrechen"),
    "Schwindel": ("R42", "Schwindel und Taumel"),
    "Atemnot": ("R06.0", "Dyspnoe"),
    "Bauchschmerzen": ("R10.4", "Sonstige und nicht näher bezeichnete Bauchschmerzen"),
    "Müdigkeit": ("R53", "Unwohlsein und Ermüdung"),
    "Halsschmerzen": ("J02.9", "Akute Pharyngitis, nicht näher bezeichnet"),
}


def lookup_icd10gm(term: str, min_score: float = 70.0) -> tuple[str, str, float] | None:
    """Fuzzy-match a free-text clinical term to the sample ICD-10-GM table.

    Returns (code, display, score 0..1) or None if nothing scores above
    `min_score` (0..100 rapidfuzz scale).
    """
    if not term:
        return None
    match = process.extractOne(term, ICD10GM_SAMPLE.keys(), scorer=fuzz.WRatio)
    if match is None:
        return None
    matched_term, score, _ = match
    if score < min_score:
        return None
    code, display = ICD10GM_SAMPLE[matched_term]
    return code, display, round(score / 100.0, 3)
