# Kausalsystem

Ein kleines System zur Verwaltung von Begriffen, ihren Synonymen, Kausalbeziehungen zwischen ihnen und zugehoerigen Formelzeichen.

## Aufbau

- `data_loader.py` – laedt die drei JSON-Datenquellen aus dem `data/`-Ordner.
- `lookup.py` – baut die Suchindizes auf (Begriff -> ID, ID -> Anzeigename, Formelzeichen -> Standardwert) und stellt die Suchfunktion `begriff_zu_id` bereit.
- `main.py` – Einstiegspunkt, der alles zusammenfuehrt und eine Beispielsuche ausfuehrt.
- `data/synonyme.json` – Begriffe mit ihren Synonymen (aktuell minimaler Platzhalterinhalt).
- `data/kausaldaten.json` – Kausalbeziehungen zwischen Begriffen (aktuell minimaler Platzhalterinhalt).
- `data/formelzeichen.json` – Formelzeichen mit Bedeutung, Einheit und Standardwert (aktuell minimaler Platzhalterinhalt).

Die drei JSON-Dateien enthalten bewusst nur minimale Beispieldaten. Sie sollen spaeter durch ein einfaches Modell befuellt bzw. erzeugt werden.

## Testen

1. Repository klonen:
   ```bash
   git clone https://github.com/Flo3200/Kausalsystem.git
   cd Kausalsystem
   ```
2. Skript ausfuehren (keine externen Abhaengigkeiten noetig, da die Daten jetzt lokal aus `data/` geladen werden):
   ```bash
   python main.py
   ```
3. Erwartete Ausgabe u.a.:
   ```
   2 Konzepte, 1 Kausalbeziehungen, 2 Formelzeichen geladen.
   4 Synonyme indiziert.
      Gefunden: 'Kraft' -> ID kraft ('Kraft')
      Gefunden: 'Geschwindigkeit' -> ID geschwindigkeit ('Geschwindigkeit')
      Kein Treffer fuer 'Unbekannt' in der Synonym-Tabelle.
   Formelzeichen-Standardwerte: {'F': 0, 'v': 0}
   Kausalbeziehungen: {...}
   ```
4. Eigene Begriffe testen: in `main.py` die Liste in der `for begriff in [...]`-Schleife anpassen oder `data/synonyme.json` um weitere Eintraege ergaenzen.
