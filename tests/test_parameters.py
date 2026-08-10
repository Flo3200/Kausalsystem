import pytest

from kausalrechner.parameters import parameter_hinzufuegen, parameter_werte


def test_parameter_hinzufuegen_und_werte():
    db = {}
    parameter_hinzufuegen(db, "x", 0.5, beschreibung="Test", min_wert=0, max_wert=1)
    assert parameter_werte(db) == {"x": 0.5}


def test_standardwert_ausserhalb_grenzen():
    db = {}
    with pytest.raises(ValueError):
        parameter_hinzufuegen(db, "x", 5, min_wert=0, max_wert=1)


def test_min_groesser_max():
    db = {}
    with pytest.raises(ValueError):
        parameter_hinzufuegen(db, "x", 0.5, min_wert=1, max_wert=0)
