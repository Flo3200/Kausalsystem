"""Laedt Konzepte, Kausalbeziehungen und Parameter aus dem paket-internen data/-Ordner."""
import json
from pathlib import Path

from .graph import Kausalkante

DATA_DIR = Path(__file__).parent / "data"

KONZEPTE_PATH = DATA_DIR / "konzepte.json"
KAUSALBEZIEHUNGEN_PATH = DATA_DIR / "kausalbeziehungen.json"
PARAMETER_PATH = DATA_DIR / "parameter.json"


def _lade_json(pfad):
    with pfad.open("r", encoding="utf-8") as f:
        return json.load(f)


def lade_konzepte():
    return _lade_json(KONZEPTE_PATH)


def lade_kausalkanten():
    rohdaten = _lade_json(KAUSALBEZIEHUNGEN_PATH)
    return [
        Kausalkante(von=eintrag["von"], nach=eintrag["nach"], formel=eintrag["formel"],
                    beschreibung=eintrag.get("beschreibung", ""))
        for eintrag in rohdaten
    ]


def lade_parameter_db():
    return _lade_json(PARAMETER_PATH)


def lade_alle():
    """Laedt die vollstaendige Datenbasis: (konzepte_raw, kausalkanten, parameter_db)."""
    return lade_konzepte(), lade_kausalkanten(), lade_parameter_db()
