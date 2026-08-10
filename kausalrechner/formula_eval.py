"""Sichere Auswertung von Formel-Strings ohne Zugriff auf Dateisystem, Netzwerk oder Imports.

Erlaubt sind nur Grundrechenarten, Vergleiche, boolesche Verknuepfungen,
Bedingungsausdruecke (ternary) und ein festes Set an mathematischen
Funktionen. Alle Namen in der Formel muessen explizit als Variable
uebergeben werden (Parameter, 'effekt', 'tiefe').
"""
import ast

ERLAUBTE_FUNKTIONEN = {"min": min, "max": max, "abs": abs, "round": round}

_ERLAUBTE_KNOTEN = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Name, ast.Load,
    ast.Call, ast.IfExp, ast.Compare, ast.BoolOp, ast.And, ast.Or, ast.Not,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.FloorDiv,
    ast.USub, ast.UAdd,
    ast.Lt, ast.Gt, ast.LtE, ast.GtE, ast.Eq, ast.NotEq,
)


class FormelFehler(ValueError):
    """Wird geworfen, wenn eine Formel unerlaubte Konstrukte oder Namen enthaelt."""


def _pruefe_knoten(baum, bekannte_namen):
    for knoten in ast.walk(baum):
        if isinstance(knoten, ast.Call):
            if not (isinstance(knoten.func, ast.Name) and knoten.func.id in ERLAUBTE_FUNKTIONEN):
                raise FormelFehler(f"Funktionsaufruf nicht erlaubt: {ast.dump(knoten.func)}")
        elif isinstance(knoten, ast.Name):
            if knoten.id not in bekannte_namen and knoten.id not in ERLAUBTE_FUNKTIONEN:
                raise FormelFehler(f"Unbekannter Name in Formel: '{knoten.id}'")
        elif not isinstance(knoten, _ERLAUBTE_KNOTEN):
            raise FormelFehler(f"Nicht erlaubtes Konstrukt in Formel: {type(knoten).__name__}")


def sichere_auswertung(formel, variablen):
    """Wertet einen arithmetischen Formel-String sicher aus.

    variablen: dict mit z.B. 'effekt', 'tiefe' und allen Formel-Parametern.
    """
    try:
        baum = ast.parse(formel, mode="eval")
    except SyntaxError as exc:
        raise FormelFehler(f"Ungueltige Formel-Syntax: {formel!r}") from exc

    _pruefe_knoten(baum, set(variablen))

    namespace = dict(variablen)
    namespace.update(ERLAUBTE_FUNKTIONEN)
    code = compile(baum, "<formel>", "eval")
    return eval(code, {"__builtins__": {}}, namespace)  # noqa: S307 - durch _pruefe_knoten abgesichert
