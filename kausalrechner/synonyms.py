"""Aufloesung von Suchbegriffen zu eindeutigen Konzept-IDs ueber eine Synonym-Tabelle."""


def baue_synonym_index(konzepte_raw):
    """Baut Begriff->ID und ID->Anzeigename Lookups aus den Konzeptdaten."""
    wort_zu_id = {}
    id_zu_anzeigename = {}

    for id_, eintrag in konzepte_raw.items():
        id_zu_anzeigename[id_] = eintrag["anzeigename"]
        for wort in eintrag["synonyme"]:
            wort_zu_id[wort.strip().lower()] = id_

    return wort_zu_id, id_zu_anzeigename


def begriff_zu_id(suchbegriff, wort_zu_id):
    """Exakte Suche in der Synonym-Tabelle. Gibt None zurueck, falls nicht gefunden."""
    return wort_zu_id.get(suchbegriff.strip().lower())
