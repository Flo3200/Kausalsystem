from kausalrechner.llm_parameters import baue_prompt, parse_antwort, schaetze_parameter

PARAMETER_DB = {
    "sigma": {"standardwert": 1.0, "beschreibung": "Testparameter sigma", "min": 0, "max": 5},
    "kappa": {"standardwert": 0.3, "beschreibung": "Testparameter kappa", "min": 0, "max": 2},
}


def test_baue_prompt_enthaelt_alle_nutzereingaben():
    prompt = baue_prompt(
        "Unternehmenssteuer", "geringer", 5.0, "von 25% auf 20% gesenkt", PARAMETER_DB, ["sigma", "kappa"]
    )
    assert "Unternehmenssteuer" in prompt
    assert "geringer" in prompt
    assert "5.0" in prompt
    assert "von 25% auf 20% gesenkt" in prompt
    assert "sigma" in prompt and "kappa" in prompt
    assert "PARAMETER: <name>=<zahl>" in prompt


def test_parse_antwort_klemmt_werte_ausserhalb_der_grenzen():
    text = "PARAMETER: sigma=99\nPARAMETER: kappa=0.1\n</ende>"
    werte, warnungen = parse_antwort(text, ["sigma", "kappa"], PARAMETER_DB)
    assert werte["sigma"] == 5
    assert werte["kappa"] == 0.1
    assert any("geklemmt" in w for w in warnungen)


def test_parse_antwort_fehlender_parameter_faellt_auf_standard_zurueck():
    text = "PARAMETER: sigma=2.0\n</ende>"
    werte, warnungen = parse_antwort(text, ["sigma", "kappa"], PARAMETER_DB)
    assert werte["sigma"] == 2.0
    assert werte["kappa"] == 0.3
    assert any("nicht geliefert" in w for w in warnungen)


def test_parse_antwort_ignoriert_muell_und_kommazahlen():
    text = "Hier ist meine Schaetzung:\nPARAMETER: sigma=1,5\nirrelevante Zeile\nPARAMETER: kappa=0.4\n</ende>"
    werte, warnungen = parse_antwort(text, ["sigma", "kappa"], PARAMETER_DB)
    assert werte == {"sigma": 1.5, "kappa": 0.4}
    assert warnungen == []


def test_schaetze_parameter_mit_stub_llm():
    def stub(prompt):
        assert "Unternehmenssteuer" in prompt
        return "PARAMETER: sigma=1.5\nPARAMETER: kappa=0.4\n</ende>"

    schaetzung = schaetze_parameter(
        stub, "Unternehmenssteuer", "geringer", 5.0, "", PARAMETER_DB, ["sigma", "kappa"]
    )
    assert schaetzung.werte == {"sigma": 1.5, "kappa": 0.4}
    assert schaetzung.warnungen == []
