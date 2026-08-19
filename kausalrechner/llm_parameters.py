"""LLM-gestuetzte Schaetzung von Kausalrechner-/DSGE-Parametern.

Nutzt ein lokales LLM (vorgesehen: ein "Llama Open Finance 8B"-artiges,
Finanz-/Wirtschafts-instruction-getuntes Modell als GGUF-Datei, Pfad ueber
KAUSAL_LLM_PARAM_MODEL_PATH konfigurierbar, siehe kausalrechner/interactive.py),
um Startwerte fuer die vom Nutzer noch nicht manuell gesetzten Formel-Parameter
zu schaetzen.

Das LLM bekommt eine praezise Aufgabenbeschreibung inkl. ALLER vom Nutzer
eingegebenen Kontextfelder (Konzept, Richtung, Staerke, sowie freier Zusatz-
Kontext wie z.B. "Unternehmenssteuer wird von 25% auf 20% gesenkt") und muss in
einem festen, zeilenbasierten Format antworten, das deterministisch geparst
wird (kein Freitext-Parsing, kein JSON-Raten). Werte ausserhalb der in
parameter.json definierten min/max-Grenzen werden auf die Grenze geklemmt, mit
einer entsprechenden Warnung.
"""
import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List

FORMAT_ANWEISUNG = (
    "Antworte AUSSCHLIESSLICH im folgenden Format, eine Zeile pro Parameter, "
    "kein Fliesstext, keine Erklaerung, keine Markdown-Formatierung:\n"
    "PARAMETER: <name>=<zahl>\n"
    "PARAMETER: <name>=<zahl>\n"
    "...\n"
    "</ende>"
)

ZEILEN_MUSTER = re.compile(r"^PARAMETER:\s*([A-Za-z0-9_]+)\s*=\s*(-?\d+(?:[.,]\d+)?)\s*$")


@dataclass
class ParameterSchaetzung:
    werte: Dict[str, float]
    warnungen: List[str] = field(default_factory=list)
    rohtext: str = ""


def baue_prompt(konzept, richtung, staerke, kontext, parameter_db, ziel_parameter):
    """Baut den Schaetzungs-Prompt inkl. aller Nutzereingaben und Parameterbeschreibungen."""
    zeilen = [
        "Du bist ein volkswirtschaftlicher Analyst. Schaetze plausible Werte fuer die "
        "folgenden Modellparameter eines Kausal-/DSGE-Modells, basierend auf dem unten "
        "beschriebenen konkreten Szenario. Nutze Standard-Literaturwerte als Anker, "
        "weiche aber gezielt davon ab, wenn das Szenario dafuer konkrete Hinweise liefert "
        "(z.B. Groesse und Richtung einer genannten Steuersatzaenderung). Bleibe innerhalb "
        "der angegebenen [min, max]-Grenzen.",
        "",
        f"Szenario-Konzept: {konzept}",
        f"Richtung der Ausgangsaenderung: {richtung}",
        f"Staerke der Ausgangsaenderung: {staerke} Prozentpunkte",
    ]
    if kontext:
        zeilen.append(f"Zusaetzlicher Kontext vom Nutzer (z.B. konkrete Von-Bis-Angaben): {kontext}")
    else:
        zeilen.append("Zusaetzlicher Kontext vom Nutzer: keiner")
    zeilen.append("")
    zeilen.append("Zu schaetzende Parameter (Name: Beschreibung [min, max], aktueller Standardwert):")
    for name in ziel_parameter:
        eintrag = parameter_db.get(name, {})
        beschreibung = eintrag.get("beschreibung", "")
        minw, maxw = eintrag.get("min"), eintrag.get("max")
        standard = eintrag.get("standardwert")
        zeilen.append(f"- {name}: {beschreibung} [{minw}, {maxw}], Standard={standard}")
    zeilen.append("")
    zeilen.append(FORMAT_ANWEISUNG)
    return "\n".join(zeilen)


def parse_antwort(text, ziel_parameter, parameter_db):
    """Parst die strikt formatierte LLM-Antwort. Liefert (werte, warnungen).

    Fehlende Parameter fallen auf den Standardwert aus parameter_db zurueck
    (mit Warnung), Werte ausserhalb [min, max] werden geklemmt (mit Warnung).
    """
    werte, warnungen = {}, []
    gefunden = set()
    for zeile in text.splitlines():
        treffer = ZEILEN_MUSTER.match(zeile.strip())
        if not treffer:
            continue
        name, wert_str = treffer.group(1), treffer.group(2).replace(",", ".")
        if name not in ziel_parameter:
            continue
        wert = float(wert_str)
        eintrag = parameter_db.get(name, {})
        minw, maxw = eintrag.get("min"), eintrag.get("max")
        if minw is not None and wert < minw:
            warnungen.append(f"{name}: geschaetzter Wert {wert} < min {minw}, auf {minw} geklemmt")
            wert = minw
        if maxw is not None and wert > maxw:
            warnungen.append(f"{name}: geschaetzter Wert {wert} > max {maxw}, auf {maxw} geklemmt")
            wert = maxw
        werte[name] = wert
        gefunden.add(name)

    for name in ziel_parameter:
        if name not in gefunden:
            warnungen.append(f"{name}: vom LLM nicht geliefert, Standardwert wird beibehalten")
            werte[name] = parameter_db.get(name, {}).get("standardwert")

    return werte, warnungen


def schaetze_parameter(generiere: Callable[[str], str], konzept, richtung, staerke,
                        kontext, parameter_db, ziel_parameter) -> ParameterSchaetzung:
    """Fuehrt eine LLM-Parameterschaetzung durch.

    `generiere` ist eine prompt->text Funktion, z.B. aus
    kausalrechner.llm_client.erzeuge_generator(...) oder ein Test-Stub.
    """
    prompt = baue_prompt(konzept, richtung, staerke, kontext, parameter_db, ziel_parameter)
    antwort = generiere(prompt)
    werte, warnungen = parse_antwort(antwort, ziel_parameter, parameter_db)
    return ParameterSchaetzung(werte=werte, warnungen=warnungen, rohtext=antwort)
