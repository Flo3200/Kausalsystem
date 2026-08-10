import pytest

from kausalrechner.formula_eval import FormelFehler, sichere_auswertung


def test_grundrechenarten():
    assert sichere_auswertung("effekt * 2 + tiefe", {"effekt": 3, "tiefe": 1}) == 7


def test_erlaubte_funktionen():
    assert sichere_auswertung("max(min(effekt, 5), -5)", {"effekt": 12}) == 5


def test_bedingter_ausdruck():
    assert sichere_auswertung("effekt if effekt > 0 else 0", {"effekt": -3}) == 0


def test_blockt_unbekannten_namen():
    with pytest.raises(FormelFehler):
        sichere_auswertung("geheim + 1", {"effekt": 1})


def test_blockt_import():
    with pytest.raises(FormelFehler):
        sichere_auswertung("__import__('os').system('echo hi')", {})


def test_blockt_nicht_freigegebene_funktion():
    with pytest.raises(FormelFehler):
        sichere_auswertung("open('x')", {})


def test_blockt_attributzugriff():
    with pytest.raises(FormelFehler):
        sichere_auswertung("effekt.__class__", {"effekt": 1})
