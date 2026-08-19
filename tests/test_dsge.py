import pytest

from kausalrechner.dsge import DSGEKonvergenzFehler, DSGEModell, loese_dsge


def test_loest_lineares_system():
    # x + y = 4 ; x - y = 0  => x = 2, y = 2
    modell = DSGEModell(
        id="linear",
        variablen=["x", "y"],
        gleichungen=["x + y - 4", "x - y"],
        startwerte={"x": 0.0, "y": 0.0},
    )
    werte, _iterationen = loese_dsge(modell, parameter={})
    assert werte["x"] == pytest.approx(2.0, abs=1e-6)
    assert werte["y"] == pytest.approx(2.0, abs=1e-6)


def test_nichtlineares_system_konvergiert():
    # x^2 - a = 0  =>  x = sqrt(a)
    modell = DSGEModell(
        id="wurzel",
        variablen=["x"],
        gleichungen=["x * x - a"],
        startwerte={"x": 1.0},
    )
    werte, _iterationen = loese_dsge(modell, parameter={"a": 9.0})
    assert werte["x"] == pytest.approx(3.0, abs=1e-6)


def test_nk_3gleichungen_modell_konvergiert():
    modell = DSGEModell(
        id="nk_3gleichungen",
        variablen=["produktionsluecke", "inflation", "zins"],
        gleichungen=[
            "produktionsluecke - (y_erwartung - sigma * (zins - pi_erwartung - r_natuerlich))",
            "inflation - (beta * pi_erwartung + kappa * produktionsluecke + kostendruck_schock)",
            "zins - (r_natuerlich + pi_erwartung + phi_pi * (inflation - pi_ziel) + phi_y * produktionsluecke)",
        ],
        startwerte={"produktionsluecke": 0.0, "inflation": 0.02, "zins": 0.02},
    )
    parameter = dict(
        sigma=1.0, beta=0.99, kappa=0.3, phi_pi=1.5, phi_y=0.5,
        y_erwartung=0.0, pi_erwartung=0.02, pi_ziel=0.02, r_natuerlich=0.01,
        kostendruck_schock=0.01,
    )
    werte, _iterationen = loese_dsge(modell, parameter)
    for wert in werte.values():
        assert abs(wert) < 10

    # Positiver Kostendruckschock muss die Inflation gegenueber dem Fall ohne Schock erhoehen
    parameter_ohne_schock = dict(parameter, kostendruck_schock=0.0)
    werte_ohne_schock, _ = loese_dsge(modell, parameter_ohne_schock)
    assert werte["inflation"] > werte_ohne_schock["inflation"]


def test_singulaeres_system_wirft_dsge_konvergenzfehler():
    modell = DSGEModell(
        id="singulaer",
        variablen=["x", "y"],
        gleichungen=["x + y - 1", "2 * x + 2 * y - 2"],
        startwerte={"x": 0.0, "y": 0.0},
    )
    with pytest.raises(DSGEKonvergenzFehler):
        loese_dsge(modell, parameter={})
