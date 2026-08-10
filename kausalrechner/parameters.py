"""Verwaltung frei definierbarer Formel-Parameter (Elastizitaeten, Daempfungsfaktoren, ...)."""


def parameter_hinzufuegen(parameter_db, name, standardwert, beschreibung="", min_wert=None, max_wert=None):
    """Fuegt einen neuen Parameter zur Parameter-Datenbank hinzu (oder aktualisiert ihn).

    Gibt die (mutierte) parameter_db zurueck, damit Aufrufe verkettet werden koennen.
    """
    if min_wert is not None and max_wert is not None and min_wert > max_wert:
        raise ValueError(f"min_wert ({min_wert}) darf nicht groesser als max_wert ({max_wert}) sein")
    if min_wert is not None and standardwert < min_wert:
        raise ValueError(f"Standardwert {standardwert} unterschreitet min_wert {min_wert}")
    if max_wert is not None and standardwert > max_wert:
        raise ValueError(f"Standardwert {standardwert} ueberschreitet max_wert {max_wert}")

    parameter_db[name] = {
        "standardwert": standardwert,
        "beschreibung": beschreibung,
        "min": min_wert,
        "max": max_wert,
    }
    return parameter_db


def parameter_werte(parameter_db):
    """Extrahiert {parameter_name: standardwert} fuer die Formelauswertung."""
    return {name: eintrag["standardwert"] for name, eintrag in parameter_db.items()}
