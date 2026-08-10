"""Laedt die Rohdaten des Kausalsystems aus lokalen JSON-Dateien."""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

SYNONYME_PATH = DATA_DIR / "synonyme.json"
KAUSALDATEN_PATH = DATA_DIR / "kausaldaten.json"
FORMELZEICHEN_PATH = DATA_DIR / "formelzeichen.json"


def _lade_json(pfad, pflicht=True):
    try:
        with pfad.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        if pflicht:
            raise
        return {}


def lade_daten():
    """Laedt Synonyme, Kausaldaten und Formelzeichen und gibt sie als Tupel zurueck."""
    synonyme_raw = _lade_json(SYNONYME_PATH)
    kausaldaten = _lade_json(KAUSALDATEN_PATH)
    formelzeichen_db = _lade_json(FORMELZEICHEN_PATH, pflicht=False)

    print(f"{len(synonyme_raw)} Konzepte, {len(kausaldaten)} Kausalbeziehungen, "
          f"{len(formelzeichen_db)} Formelzeichen geladen.")

    return synonyme_raw, kausaldaten, formelzeichen_db
