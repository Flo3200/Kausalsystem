"""Laedt Konzepte, Kausalbeziehungen, Parameter und DSGE-Modelle aus dem
paket-internen data/-Ordner."""
import json
from pathlib import Path

from .dsge import DSGEModell
from .graph import Kausalkante

DATA_DIR = Path(__file__).parent / "data"

KONZEPTE_PATH = DATA_DIR / "konzepte.json"
KAUSALBEZIEHUNGEN_PATH = DATA_DIR / "kausalbeziehungen.json"
PARAMETER_PATH = DATA_DIR / "parameter.json"
DSGE_MODELLE_PATH = DATA_DIR / "dsge_modelle.json"


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


def lade_dsge_modelle():
    """Laedt alle DSGE-Modelldefinitionen aus dsge_modelle.json als {id: DSGEModell}."""
    rohdaten = _lade_json(DSGE_MODELLE_PATH)
    return {
        modell_id: DSGEModell(
            id=modell_id,
            variablen=eintrag["variablen"],
            gleichungen=eintrag["gleichungen"],
            startwerte=eintrag.get("startwerte", {}),
            beschreibung=eintrag.get("beschreibung", ""),
        )
        for modell_id, eintrag in rohdaten.items()
    }


def lade_alle():
    """Laedt die vollstaendige Datenbasis: (konzepte_raw, kausalkanten, parameter_db)."""
    return lade_konzepte(), lade_kausalkanten(), lade_parameter_db()
