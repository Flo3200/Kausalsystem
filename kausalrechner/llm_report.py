"""Erzeugt aus den numerischen Ergebnissen einer Kausalketten-/DSGE-Berechnung
einen sauberen, oekonomisch formulierten Fliesstext mittels lokalem LLM.

Das LLM bekommt ausschliesslich die bereits berechneten Zahlen als Kontext und
wird angewiesen, keine neuen Zahlen zu erfinden - es soll die vorhandenen
Ergebnisse nur in verstaendliche Sprache uebersetzen, nicht neu rechnen.
"""
from typing import Callable


def baue_prompt(konzept, richtung, staerke, schritte_text, aggregiert_text, dsge_text=""):
    zeilen = [
        "Du bist ein volkswirtschaftlicher Gutachter. Formuliere aus den folgenden "
        "Berechnungsergebnissen einen praezisen, gut lesbaren Fliesstext auf Deutsch "
        "(3-6 Saetze) fuer einen nicht-technischen Leser. Erfinde KEINE Zahlen, die "
        "nicht in den Daten unten stehen - runde hoechstens sinnvoll. Nenne Richtung "
        "und ungefaehre Groessenordnung der wichtigsten Effekte sowie etwaige "
        "Rueckkopplungen.",
        "",
        f"Szenario: {konzept} {richtung} um {staerke} Prozentpunkte",
        "",
        "Kausalkette (Rohdaten, Format Quelle->Ziel: eingehender_effekt -> ausgehender_effekt):",
        schritte_text or "(keine Kausalschritte)",
        "",
        "Aggregierte Effekte je betroffenem Konzept:",
        aggregiert_text or "(keine aggregierten Effekte)",
    ]
    if dsge_text:
        zeilen += ["", "Zusaetzliches DSGE-Gleichgewicht (simultan geloest):", dsge_text]
    zeilen += ["", "Gib ausschliesslich den Fliesstext zurueck, ohne Ueberschrift.", "</ende>"]
    return "\n".join(zeilen)


def erstelle_bericht(generiere: Callable[[str], str], konzept, richtung, staerke,
                      schritte_text, aggregiert_text, dsge_text="") -> str:
    """`generiere` ist eine prompt->text Funktion, siehe kausalrechner.llm_client."""
    prompt = baue_prompt(konzept, richtung, staerke, schritte_text, aggregiert_text, dsge_text)
    return generiere(prompt).strip()
