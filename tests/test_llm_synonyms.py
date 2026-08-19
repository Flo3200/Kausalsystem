from kausalrechner.llm_synonyms import baue_prompt, schlage_konzept_vor

ID_ZU_ANZEIGENAME = {"unternehmenssteuer": "Unternehmenssteuer", "konsum": "Konsum"}


def test_baue_prompt_enthaelt_begriff_und_konzeptliste():
    prompt = baue_prompt("Firmensteuer", list(ID_ZU_ANZEIGENAME.values()))
    assert "Firmensteuer" in prompt
    assert "Unternehmenssteuer" in prompt
    assert "Konsum" in prompt


def test_schlage_konzept_vor_mit_gueltigem_vorschlag():
    def stub(prompt):
        return "VORSCHLAG: Unternehmenssteuer\n</ende>"

    vorschlag = schlage_konzept_vor(stub, "Firmensteuer", ID_ZU_ANZEIGENAME)
    assert vorschlag == "Unternehmenssteuer"


def test_schlage_konzept_vor_mit_erfundenem_konzept_gibt_none():
    def stub(prompt):
        return "VORSCHLAG: Voellig erfundenes Konzept\n</ende>"

    vorschlag = schlage_konzept_vor(stub, "Firmensteuer", ID_ZU_ANZEIGENAME)
    assert vorschlag is None


def test_schlage_konzept_vor_mit_kein_vorschlag_gibt_none():
    def stub(prompt):
        return "VORSCHLAG: KEIN_VORSCHLAG\n</ende>"

    vorschlag = schlage_konzept_vor(stub, "Quantencomputer", ID_ZU_ANZEIGENAME)
    assert vorschlag is None
