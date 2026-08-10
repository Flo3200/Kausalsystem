"""Einstiegspunkt: laedt Daten, baut Indizes auf und demonstriert die Suche."""
from data_loader import lade_daten
from lookup import baue_synonym_index, baue_formelzeichen_werte, begriff_zu_id


def main():
    synonyme_raw, kausaldaten, formelzeichen_db = lade_daten()

    wort_zu_id, id_zu_anzeigename = baue_synonym_index(synonyme_raw)
    formelzeichen_werte = baue_formelzeichen_werte(formelzeichen_db)

    for begriff in ["Kraft", "Geschwindigkeit", "Unbekannt"]:
        begriff_zu_id(begriff, wort_zu_id, id_zu_anzeigename)

    print("Formelzeichen-Standardwerte:", formelzeichen_werte)
    print("Kausalbeziehungen:", kausaldaten)


if __name__ == "__main__":
    main()
