"""Interaktiver Einstiegspunkt: fragt Konzept/Richtung/Staerke/Kontext ab und nutzt
optional lokale LLMs fuer Begriffs-Vorschlag, Parameterschaetzung und Berichtstext.

Vor jedem LLM-Einsatz wird der Nutzer gefragt, ob er ihn nutzen moechte. Bei
Ablehnung (oder wenn kein Modellpfad konfiguriert ist) laeuft der Ablauf ohne
LLM weiter (manuelle Eingabe / Standardwerte / kein Bericht).

Modellpfade werden ueber Umgebungsvariablen konfiguriert (siehe README):
    KAUSAL_LLM_SYNONYM_MODEL_PATH   - kleines Modell (z.B. Llama 3B) fuer Begriffs-Vorschlaege
    KAUSAL_LLM_PARAM_MODEL_PATH     - Finanz-/Wirtschafts-Modell fuer Parameterschaetzung
    KAUSAL_LLM_REPORT_MODEL_PATH    - Modell fuer den abschliessenden Fliesstext-Bericht

Aufruf:
    python -m kausalrechner.interactive
"""
import os
import sys

from .cli import RICHTUNGEN, _drucke_ergebnis
from .data_loader import lade_alle, lade_dsge_modelle
from .dsge import DSGEKonvergenzFehler, loese_dsge
from .graph import KausalGraph, berechne_kausalkette
from .llm_client import LLMKonfiguration, LLMNichtVerfuegbar, erzeuge_generator
from .llm_parameters import schaetze_parameter
from .llm_report import erstelle_bericht
from .llm_synonyms import schlage_konzept_vor
from .parameters import parameter_werte
from .synonyms import baue_synonym_index, begriff_zu_id

MODELL_PFAD_SYNONYM = os.environ.get("KAUSAL_LLM_SYNONYM_MODEL_PATH", "")
MODELL_PFAD_PARAMETER = os.environ.get("KAUSAL_LLM_PARAM_MODEL_PATH", "")
MODELL_PFAD_BERICHT = os.environ.get("KAUSAL_LLM_REPORT_MODEL_PATH", "")


def _frage_ja_nein(text):
    antwort = input(f"{text} [j/n]: ").strip().lower()
    return antwort in ("j", "ja", "y", "yes")


def _hole_generator(modell_pfad, max_tokens=512):
    """Baut einen generiere()-Callable fuer den gegebenen Modellpfad, oder None,
    falls kein Pfad konfiguriert ist oder das Laden fehlschlaegt."""
    if not modell_pfad:
        print("  (kein Modellpfad konfiguriert - siehe README fuer die noetige Umgebungsvariable)")
        return None
    konfig = LLMKonfiguration(modell_pfad=modell_pfad, max_tokens=max_tokens)
    generator = erzeuge_generator(konfig)
    try:
        generator("PARAMETER: test=0\n</ende>")
    except LLMNichtVerfuegbar as exc:
        print(f"  Hinweis: {exc}")
        return None
    return generator


def _berechne_kausalkette(konzepte_raw, kausalkanten, start_id, richtung, staerke, parameter_werte_dict):
    richtung_key = richtung.strip().lower()
    anfangseffekt = RICHTUNGEN[richtung_key] * staerke
    graph = KausalGraph(kausalkanten)
    schritte, aggregiert = berechne_kausalkette(graph, start_id, anfangseffekt, parameter_werte_dict)
    _, id_zu_anzeigename = baue_synonym_index(konzepte_raw)
    return {
        "start_id": start_id,
        "id_zu_anzeigename": id_zu_anzeigename,
        "anfangseffekt": anfangseffekt,
        "schritte": schritte,
        "aggregiert": aggregiert,
    }


def _loese_dsge_fuer_konzept(konzept_id, konzepte_raw, richtung_key, staerke, parameter_werte_dict):
    """Falls das Konzept ein DSGE-Modell referenziert, loest dieses simultan und
    gibt (modell, werte, iterationen) zurueck, sonst None."""
    dsge_meta = konzepte_raw.get(konzept_id, {}).get("dsge")
    if not dsge_meta:
        return None

    modell = lade_dsge_modelle()[dsge_meta["modell"]]
    parameter = dict(parameter_werte_dict)
    schock_parameter = dsge_meta["schock_parameter"]
    richtung_vorzeichen = RICHTUNGEN[richtung_key]
    parameter[schock_parameter] = (
        parameter.get(schock_parameter, 0.0)
        + richtung_vorzeichen * staerke * dsge_meta.get("schock_skalierung", 1.0)
    )
    try:
        werte, iterationen = loese_dsge(modell, parameter)
    except DSGEKonvergenzFehler as exc:
        print(f"  DSGE-Modell konnte nicht geloest werden: {exc}")
        return None
    return modell, werte, iterationen


def main():
    print("=== Oekonomischer Kausalrechner (interaktiv) ===\n")

    konzepte_raw, kausalkanten, parameter_db = lade_alle()
    wort_zu_id, id_zu_anzeigename = baue_synonym_index(konzepte_raw)

    konzept_eingabe = input("Konzept (z.B. 'Unternehmenssteuer'): ").strip()
    start_id = begriff_zu_id(konzept_eingabe, wort_zu_id)

    while start_id is None:
        genutzt_llm_vorschlag = False
        if MODELL_PFAD_SYNONYM and _frage_ja_nein(
            f"Konzept '{konzept_eingabe}' nicht gefunden. LLM nach einem passenden bekannten Begriff fragen?"
        ):
            generator = _hole_generator(MODELL_PFAD_SYNONYM, max_tokens=64)
            vorschlag = schlage_konzept_vor(generator, konzept_eingabe, id_zu_anzeigename) if generator else None
            if vorschlag and _frage_ja_nein(f"Meintest du '{vorschlag}'?"):
                konzept_eingabe = vorschlag
                start_id = begriff_zu_id(konzept_eingabe, wort_zu_id)
                genutzt_llm_vorschlag = True
        if not genutzt_llm_vorschlag and start_id is None:
            konzept_eingabe = input("Bitte anderen Begriff eingeben: ").strip()
            start_id = begriff_zu_id(konzept_eingabe, wort_zu_id)

    richtung = input("Richtung (hoeher/geringer): ").strip().lower()
    if richtung not in RICHTUNGEN:
        print(f"Fehler: Unbekannte Richtung '{richtung}'.", file=sys.stderr)
        return 1
    staerke = float(input("Staerke der Ausgangsaenderung in Prozentpunkten: ").strip())
    kontext = input(
        "Zusaetzlicher Kontext (optional, z.B. 'Unternehmenssteuer wird von 25% auf 20% gesenkt'): "
    ).strip()

    aktive_parameter = dict(parameter_werte(parameter_db))

    if MODELL_PFAD_PARAMETER and _frage_ja_nein("LLM zur Schaetzung der Modellparameter aus dem Szenario nutzen?"):
        generator = _hole_generator(MODELL_PFAD_PARAMETER)
        if generator:
            ziel_parameter = list(parameter_db.keys())
            schaetzung = schaetze_parameter(
                generator, konzept_eingabe, richtung, staerke, kontext, parameter_db, ziel_parameter
            )
            for warnung in schaetzung.warnungen:
                print(f"  Warnung: {warnung}")
            aktive_parameter.update(schaetzung.werte)

            while True:
                print("\nVerwendete Parameter:")
                for name, wert in aktive_parameter.items():
                    print(f"  {name} = {wert}")
                if not _frage_ja_nein("\nParameter manuell anpassen und neu berechnen?"):
                    break
                name = input("  Parametername: ").strip()
                if name not in aktive_parameter:
                    print("  Unbekannter Parameter, wird ignoriert.")
                    continue
                try:
                    aktive_parameter[name] = float(input(f"  Neuer Wert fuer {name}: ").strip())
                except ValueError:
                    print("  Ungueltige Zahl, ignoriert.")

    ergebnis = _berechne_kausalkette(konzepte_raw, kausalkanten, start_id, richtung, staerke, aktive_parameter)
    print()
    _drucke_ergebnis(konzept_eingabe, richtung, staerke, ergebnis)

    dsge_text = ""
    dsge_ergebnis = _loese_dsge_fuer_konzept(start_id, konzepte_raw, richtung, staerke, aktive_parameter)
    if dsge_ergebnis:
        modell, werte, iterationen = dsge_ergebnis
        print(f"\nDSGE-Gleichgewicht ({modell.id}, {iterationen} Newton-Iterationen):")
        for name, wert in werte.items():
            print(f"  {name} = {wert:+.5f}")
        dsge_text = "\n".join(f"{n} = {w:+.5f}" for n, w in werte.items())

    if MODELL_PFAD_BERICHT and _frage_ja_nein("\nLLM-Bericht als Fliesstext erzeugen lassen?"):
        generator = _hole_generator(MODELL_PFAD_BERICHT)
        if generator:
            schritte_text = "\n".join(
                f"{s.von}->{s.nach}: {s.eingehender_effekt:+.3f} -> {s.ausgehender_effekt:+.3f}"
                for s in ergebnis["schritte"]
            )
            aggregiert_text = "\n".join(
                f"{id_zu_anzeigename.get(k, k)}: {v:+.3f}" for k, v in ergebnis["aggregiert"].items()
            )
            bericht = erstelle_bericht(
                generator, konzept_eingabe, richtung, staerke, schritte_text, aggregiert_text, dsge_text
            )
            print("\n=== Bericht ===")
            print(bericht)

    return 0


if __name__ == "__main__":
    sys.exit(main())
