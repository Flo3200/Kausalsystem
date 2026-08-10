"""Gerichteter Kausalgraph: Kanten mit Formeln, Traversierung mit Zyklenschutz."""
from collections import defaultdict
from dataclasses import dataclass

from .formula_eval import sichere_auswertung


@dataclass
class Kausalkante:
    von: str
    nach: str
    formel: str
    beschreibung: str = ""


@dataclass
class Kausalschritt:
    von: str
    nach: str
    tiefe: int
    eingehender_effekt: float
    ausgehender_effekt: float
    formel: str


class KausalGraph:
    def __init__(self, kanten):
        self.kanten = list(kanten)
        self._adjazenz = defaultdict(list)
        for kante in self.kanten:
            self._adjazenz[kante.von].append(kante)

    def ausgehende_kanten(self, konzept_id):
        return self._adjazenz.get(konzept_id, [])


def berechne_kausalkette(graph, start_id, anfangseffekt, parameter_werte, max_tiefe=10, min_effekt=1e-4):
    """Verfolgt alle Kausalketten ausgehend von start_id.

    Gibt (schritte, aggregierte_effekte) zurueck:
      - schritte: Liste aller durchlaufenen Kausalschritte (in Traversierungsreihenfolge)
      - aggregierte_effekte: {konzept_id: aufsummierter_effekt} ueber alle Pfade, die dieses
        Konzept erreichen

    Zyklen werden abgefangen, indem Knoten, die bereits im aktuellen Pfad liegen, nicht
    erneut betreten werden (max_tiefe ist zusaetzlich eine harte Obergrenze). Effekte, die
    unter min_effekt fallen, werden nicht weiterverfolgt.
    """
    schritte = []
    aggregiert = defaultdict(float)

    def _traversiere(konzept_id, effekt, tiefe, pfad):
        if tiefe >= max_tiefe or abs(effekt) < min_effekt:
            return
        for kante in graph.ausgehende_kanten(konzept_id):
            if kante.nach in pfad:
                continue  # Zyklus abgefangen: Ziel liegt bereits im aktuellen Pfad

            variablen = dict(parameter_werte)
            variablen["effekt"] = effekt
            variablen["tiefe"] = tiefe
            ausgehender_effekt = sichere_auswertung(kante.formel, variablen)

            schritte.append(Kausalschritt(
                von=kante.von, nach=kante.nach, tiefe=tiefe + 1,
                eingehender_effekt=effekt, ausgehender_effekt=ausgehender_effekt,
                formel=kante.formel,
            ))
            aggregiert[kante.nach] += ausgehender_effekt

            _traversiere(kante.nach, ausgehender_effekt, tiefe + 1, pfad | {kante.nach})

    _traversiere(start_id, anfangseffekt, 0, frozenset({start_id}))
    return schritte, dict(aggregiert)
