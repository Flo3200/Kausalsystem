"""DSGE-faehiger Gleichungssystem-Solver.

Ein DSGE-Modell besteht aus einer Menge endogener Variablen und ebenso vielen
Gleichungen der Form 0 = f(x1, ..., xn; parameter). Jede Gleichung wird als
String in Residualform (linke Seite minus rechte Seite) angegeben und mit
demselben sicheren Formel-Evaluator wie im Kausalgraphen ausgewertet
(kausalrechner.formula_eval.sichere_auswertung) - keine beliebigen
Python-Ausdruecke, kein Datei-/Netzwerkzugriff.

Geloest wird per Newton-Raphson mit numerisch approximierter Jacobi-Matrix und
Gauss-Elimination (reine Python-Standardbibliothek, keine Abhaengigkeit von
numpy/scipy noetig).
"""
from dataclasses import dataclass, field

from .formula_eval import sichere_auswertung


class DSGEKonvergenzFehler(RuntimeError):
    """Wird geworfen, wenn Newton-Raphson nicht innerhalb der Toleranz konvergiert
    oder die Jacobi-Matrix an einem Iterationspunkt singulaer ist."""


@dataclass
class DSGEModell:
    id: str
    variablen: list          # Namen der endogenen Variablen, in fester Reihenfolge
    gleichungen: list        # Residual-Formeln (0 = ...), gleiche Laenge wie variablen
    startwerte: dict = field(default_factory=dict)   # Variable -> Startwert fuer Newton
    beschreibung: str = ""

    def residuen(self, werte, parameter):
        variablen_namen = dict(zip(self.variablen, werte))
        namespace = {**parameter, **variablen_namen}
        return [sichere_auswertung(g, namespace) for g in self.gleichungen]


def _jacobi_numerisch(modell, werte, parameter, eps=1e-6):
    n = len(werte)
    basis = modell.residuen(werte, parameter)
    jac = [[0.0] * n for _ in range(n)]
    for j in range(n):
        gestoert = list(werte)
        h = eps * max(1.0, abs(werte[j]))
        gestoert[j] += h
        residuen_j = modell.residuen(gestoert, parameter)
        for i in range(n):
            jac[i][j] = (residuen_j[i] - basis[i]) / h
    return jac, basis


def _loese_linear(jac, rhs):
    """Gauss-Elimination mit Partial Pivoting fuer Jac @ dx = rhs."""
    n = len(jac)
    a = [row[:] + [rhs[i]] for i, row in enumerate(jac)]

    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(a[r][col]))
        if abs(a[pivot][col]) < 1e-14:
            raise DSGEKonvergenzFehler("Jacobi-Matrix singulaer - Modell an diesem Punkt nicht loesbar")
        a[col], a[pivot] = a[pivot], a[col]
        for r in range(col + 1, n):
            faktor = a[r][col] / a[col][col]
            for c in range(col, n + 1):
                a[r][c] -= faktor * a[col][c]

    x = [0.0] * n
    for i in reversed(range(n)):
        summe = sum(a[i][j] * x[j] for j in range(i + 1, n))
        x[i] = (a[i][n] - summe) / a[i][i]
    return x


def loese_dsge(modell, parameter, startwerte=None, max_iter=100, toleranz=1e-9):
    """Loest das DSGE-Gleichungssystem per Newton-Raphson.

    Gibt (werte, iterationen) zurueck, wobei werte ein {variable: wert} Dict ist.
    Wirft DSGEKonvergenzFehler, falls nach max_iter Iterationen keine Konvergenz
    erreicht wird oder die Jacobi-Matrix an einem Iterationspunkt singulaer ist.
    """
    start = startwerte or modell.startwerte
    werte = [start.get(v, 0.0) for v in modell.variablen]

    fehler = float("inf")
    for iteration in range(max_iter):
        jac, residuen = _jacobi_numerisch(modell, werte, parameter)
        fehler = max(abs(r) for r in residuen)
        if fehler < toleranz:
            return dict(zip(modell.variablen, werte)), iteration
        delta = _loese_linear(jac, [-r for r in residuen])
        werte = [w + d for w, d in zip(werte, delta)]

    raise DSGEKonvergenzFehler(f"Keine Konvergenz nach {max_iter} Iterationen (Restfehler {fehler:.3g})")
