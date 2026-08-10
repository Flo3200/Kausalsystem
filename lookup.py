"""Indizes und Suchfunktionen fuer Begriffe und Formelzeichen."""


def baue_synonym_index(synonyme_raw):
    """Baut die Lookups Begriff->ID und ID->Anzeigename aus den Synonymdaten."""
    wort_zu_id = {}
    id_zu_anzeigename = {}

    for id_, eintrag in synonyme_raw.items():
        id_zu_anzeigename[id_] = eintrag["anzeigename"]
        for wort in eintrag["synonyme"]:
            wort_zu_id[wort.strip().lower()] = id_

    print(f"{len(wort_zu_id)} Synonyme indiziert.")
    return wort_zu_id, id_zu_anzeigename


def baue_formelzeichen_werte(formelzeichen_db):
    """Extrahiert die Standardwerte aller bekannten Formelzeichen."""
    return {symbol: eintrag["standardwert"] for symbol, eintrag in formelzeichen_db.items()}


def begriff_zu_id(suchbegriff, wort_zu_id, id_zu_anzeigename):
    """Exakte Suche in der Synonym-Tabelle. Gibt None zurueck, falls nicht gefunden."""
    key = suchbegriff.strip().lower()
    treffer_id = wort_zu_id.get(key)
    if treffer_id:
        print(f"   Gefunden: '{suchbegriff}' -> ID {treffer_id} ('{id_zu_anzeigename[treffer_id]}')")
    else:
        print(f"   Kein Treffer fuer '{suchbegriff}' in der Synonym-Tabelle.")
    return treffer_id
