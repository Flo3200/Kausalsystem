"""LLM-gestuetzter Begriffs-Vorschlag, wenn ein eingegebenes Konzept nicht in der
Synonym-Tabelle gefunden wird.

Vorgesehen fuer ein kleines, schnelles lokales Modell (Llama 3B), da hier nur
eine einfache Zuordnungsaufgabe geloest werden muss. Wird gemaess Vorgabe NUR
nach ausdruecklicher Zustimmung des Nutzers aufgerufen (siehe
kausalrechner/interactive.py: Frage vor jedem LLM-Einsatz, Vorschlag muss dann
per 'ja' bestaetigt werden, sonst kann der Nutzer selbst einen anderen Begriff
eingeben).
"""
from typing import Callable, List


def baue_prompt(unbekannter_begriff, bekannte_konzepte: List[str]):
    konzept_liste = ", ".join(bekannte_konzepte)
    return (
        "Ein Nutzer hat einen oekonomischen Begriff eingegeben, der in unserer "
        "Konzept-Datenbank nicht gefunden wurde. Schlage GENAU EIN bekanntes Konzept "
        "aus der folgenden Liste vor, das inhaltlich am ehesten dasselbe beschreibt "
        "wie der eingegebene Begriff. Antworte NUR mit dem exakten Konzeptnamen aus "
        "der Liste (Zeichen fuer Zeichen wie dort geschrieben), ohne weitere Erklaerung. "
        "Wenn kein Konzept aus der Liste thematisch passt, antworte mit KEIN_VORSCHLAG.\n\n"
        f"Eingegebener Begriff: '{unbekannter_begriff}'\n"
        f"Bekannte Konzepte: {konzept_liste}\n\n"
        "Antwortformat (genau eine Zeile):\nVORSCHLAG: <konzeptname oder KEIN_VORSCHLAG>\n</ende>"
    )


def schlage_konzept_vor(generiere: Callable[[str], str], unbekannter_begriff, id_zu_anzeigename: dict):
    """Gibt den vorgeschlagenen Anzeigenamen zurueck, oder None, falls kein gueltiger,
    in der Konzeptliste enthaltener Vorschlag geparst werden konnte."""
    anzeigenamen = list(id_zu_anzeigename.values())
    prompt = baue_prompt(unbekannter_begriff, anzeigenamen)
    antwort = generiere(prompt)
    for zeile in antwort.splitlines():
        zeile = zeile.strip()
        if zeile.upper().startswith("VORSCHLAG:"):
            vorschlag = zeile.split(":", 1)[1].strip()
            if vorschlag in anzeigenamen:
                return vorschlag
            return None
    return None
