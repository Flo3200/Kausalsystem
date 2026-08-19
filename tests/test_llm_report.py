from kausalrechner.llm_report import baue_prompt, erstelle_bericht


def test_baue_prompt_enthaelt_szenario_und_ergebnisdaten():
    prompt = baue_prompt("Unternehmenssteuer", "geringer", 5.0, "unternehmenssteuer->investitionen: +5.000 -> -10.000",
                          "Investitionen: -10.000", dsge_text="inflation = +0.02500")
    assert "Unternehmenssteuer" in prompt
    assert "unternehmenssteuer->investitionen" in prompt
    assert "Investitionen: -10.000" in prompt
    assert "inflation = +0.02500" in prompt


def test_erstelle_bericht_ruft_generator_mit_prompt_auf_und_trimmt_ausgabe():
    empfangene_prompts = []

    def stub(prompt):
        empfangene_prompts.append(prompt)
        return "  Ein kurzer, sachlicher Testbericht.  "

    bericht = erstelle_bericht(stub, "Unternehmenssteuer", "geringer", 5.0, "x->y: +1.0 -> +1.0", "y: +1.0")
    assert bericht == "Ein kurzer, sachlicher Testbericht."
    assert len(empfangene_prompts) == 1
