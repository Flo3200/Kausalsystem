"""Automatisierte Konsistenzpruefung der Datenbasis: stellt sicher, dass in
konzepte.json, kausalbeziehungen.json, parameter.json und dsge_modelle.json
durchgehend dieselben Konzept- und Parameternamen verwendet werden (keine
Tippfehler, keine verwaisten Referenzen, keine mehrdeutigen Synonyme)."""
import pytest

from kausalrechner.data_loader import lade_alle, lade_dsge_modelle
from kausalrechner.dsge import loese_dsge
from kausalrechner.formula_eval import sichere_auswertung
from kausalrechner.parameters import parameter_werte
from kausalrechner.synonyms import baue_synonym_index


def test_alle_kausalkanten_referenzieren_bekannte_konzepte():
    konzepte_raw, kausalkanten, _ = lade_alle()
    bekannte_ids = set(konzepte_raw.keys())
    for kante in kausalkanten:
        assert kante.von in bekannte_ids, f"Unbekanntes Quellkonzept in Kausalkante: '{kante.von}'"
        assert kante.nach in bekannte_ids, f"Unbekanntes Zielkonzept in Kausalkante: '{kante.nach}'"


def test_alle_kausalketten_formeln_sind_mit_bekannten_parametern_auswertbar():
    _konzepte_raw, kausalkanten, parameter_db = lade_alle()
    basiswerte = parameter_werte(parameter_db)
    for kante in kausalkanten:
        variablen = dict(basiswerte)
        variablen["effekt"] = 1.0
        variablen["tiefe"] = 0
        # Wirft FormelFehler, falls die Formel einen unbekannten Namen referenziert
        sichere_auswertung(kante.formel, variablen)


def test_jedes_dsge_verknuepfte_konzept_referenziert_existierendes_modell_und_parameter():
    konzepte_raw, _kausalkanten, parameter_db = lade_alle()
    dsge_modelle = lade_dsge_modelle()
    basiswerte = parameter_werte(parameter_db)

    gefundene_dsge_konzepte = 0
    for konzept_id, eintrag in konzepte_raw.items():
        dsge_meta = eintrag.get("dsge")
        if not dsge_meta:
            continue
        gefundene_dsge_konzepte += 1

        modell_id = dsge_meta["modell"]
        assert modell_id in dsge_modelle, f"{konzept_id}: unbekanntes DSGE-Modell '{modell_id}'"

        schock_parameter = dsge_meta["schock_parameter"]
        assert schock_parameter in parameter_db, (
            f"{konzept_id}: Schock-Parameter '{schock_parameter}' fehlt in parameter.json"
        )

        # Das Modell muss mit den Standardparametern (ohne Schock) loesbar sein
        modell = dsge_modelle[modell_id]
        loese_dsge(modell, basiswerte)

    assert gefundene_dsge_konzepte >= 2, "Es sollten mindestens zwei Konzepte an DSGE-Modelle angebunden sein"


def test_dsge_modell_gleichungen_referenzieren_nur_bekannte_parameter_und_variablen():
    _konzepte_raw, _kausalkanten, parameter_db = lade_alle()
    dsge_modelle = lade_dsge_modelle()
    basiswerte = parameter_werte(parameter_db)

    for modell in dsge_modelle.values():
        variablen = {name: 0.01 for name in modell.variablen}
        namespace = {**basiswerte, **variablen}
        for gleichung in modell.gleichungen:
            sichere_auswertung(gleichung, namespace)


def test_alle_synonyme_sind_eindeutig_genau_einem_konzept_zugeordnet():
    konzepte_raw, _kausalkanten, _parameter_db = lade_alle()
    wort_zu_id, _id_zu_anzeigename = baue_synonym_index(konzepte_raw)

    gesehen = {}
    for konzept_id, eintrag in konzepte_raw.items():
        for wort in eintrag["synonyme"]:
            schluessel = wort.strip().lower()
            if schluessel in gesehen and gesehen[schluessel] != konzept_id:
                pytest.fail(
                    f"Synonym '{wort}' ist sowohl '{gesehen[schluessel]}' als auch '{konzept_id}' zugeordnet"
                )
            gesehen[schluessel] = konzept_id

    # Stichprobe: die Synonym-Aufloesung muss fuer jedes Konzept konsistent auf sich selbst zeigen
    for konzept_id, eintrag in konzepte_raw.items():
        for wort in eintrag["synonyme"]:
            assert wort_zu_id[wort.strip().lower()] == konzept_id


def test_jedes_konzept_hat_mindestens_ein_synonym_und_einen_anzeigenamen():
    konzepte_raw, _kausalkanten, _parameter_db = lade_alle()
    for konzept_id, eintrag in konzepte_raw.items():
        assert eintrag.get("anzeigename"), f"{konzept_id}: kein Anzeigename gesetzt"
        assert eintrag.get("synonyme"), f"{konzept_id}: keine Synonyme gesetzt"
