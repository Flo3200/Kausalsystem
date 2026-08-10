"""CLI-Einstiegspunkt: Konzept + Richtung + Staerke -> Kausalketten + Gesamteffekt.

Aufruf:
    python -m kausalrechner.cli "Unternehmenssteuer" hoeher 10
    python -m kausalrechner.cli "Unternehmenssteuer" geringer 10 --max-tiefe 5
"""
import argparse
import sys

from .data_loader import lade_alle
from .graph import KausalGraph, berechne_kausalkette
from .parameters import parameter_werte
from .synonyms import baue_synonym_index, begriff_zu_id

RICHTUNGEN = {
    "hoeher": 1, "höher": 1, "steigend": 1, "mehr": 1,
    "geringer": -1, "niedriger": -1, "weniger": -1, "sinkend": -1,
}


def berechne(konzept, richtung, staerke, max_tiefe=10):
    """Fuehrt eine vollstaendige Berechnung durch und gibt ein Ergebnis-Dict zurueck."""
    richtung_key = richtung.strip().lower()
    if richtung_key not in RICHTUNGEN:
        raise ValueError(f"Unbekannte Richtung '{richtung}'. Erlaubt: {sorted(set(RICHTUNGEN))}")

    konzepte_raw, kausalkanten, parameter_db = lade_alle()
    wort_zu_id, id_zu_anzeigename = baue_synonym_index(konzepte_raw)

    start_id = begriff_zu_id(konzept, wort_zu_id)
    if start_id is None:
        raise ValueError(f"Unbekanntes Konzept: '{konzept}'")

    anfangseffekt = RICHTUNGEN[richtung_key] * staerke
    graph = KausalGraph(kausalkanten)
    schritte, aggregiert = berechne_kausalkette(
        graph, start_id, anfangseffekt, parameter_werte(parameter_db), max_tiefe=max_tiefe,
    )

    return {
        "start_id": start_id,
        "id_zu_anzeigename": id_zu_anzeigename,
        "anfangseffekt": anfangseffekt,
        "schritte": schritte,
        "aggregiert": aggregiert,
    }


def _drucke_ergebnis(konzept, richtung, staerke, ergebnis):
    name = lambda id_: ergebnis["id_zu_anzeigename"].get(id_, id_)  # noqa: E731

    print(f"Ausgangspunkt: {name(ergebnis['start_id'])} ({richtung}, {staerke:+.1f} Prozentpunkte)\n")

    if not ergebnis["schritte"]:
        print("Keine ausgehenden Kausalbeziehungen gefunden.")
        return

    for schritt in ergebnis["schritte"]:
        print(f"[Tiefe {schritt.tiefe}] {name(schritt.von)} -> {name(schritt.nach)}: "
              f"{schritt.eingehender_effekt:+.3f} -> {schritt.ausgehender_effekt:+.3f} "
              f"(Formel: {schritt.formel})")

    print("\nAggregierter Gesamteffekt je betroffenem Konzept:")
    for konzept_id, effekt in ergebnis["aggregiert"].items():
        print(f"  {name(konzept_id)}: {effekt:+.3f}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Oekonomischer Kausalrechner")
    parser.add_argument("konzept", help="z.B. 'Unternehmenssteuer'")
    parser.add_argument("richtung", choices=sorted(set(RICHTUNGEN)), help="Richtung der Ausgangsaenderung")
    parser.add_argument("staerke", type=float, help="Staerke der Ausgangsaenderung in Prozentpunkten")
    parser.add_argument("--max-tiefe", type=int, default=10, help="Maximale Kettentiefe (Sicherheitsgrenze)")
    args = parser.parse_args(argv)

    try:
        ergebnis = berechne(args.konzept, args.richtung, args.staerke, max_tiefe=args.max_tiefe)
    except ValueError as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 1

    _drucke_ergebnis(args.konzept, args.richtung, args.staerke, ergebnis)
    return 0


if __name__ == "__main__":
    sys.exit(main())
