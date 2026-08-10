# Kausalsystem

## Oekonomischer Kausalrechner (`kausalrechner/`, aktiv)

Ausgehend von einem oekonomischen Konzept (z.B. "Unternehmenssteuer"), einer Richtung
("hoeher"/"geringer") und einer Staerke in Prozentpunkten werden alle davon betroffenen
Kausalketten in einem gerichteten Graphen verfolgt. Jede Kausalkante hat eine frei
definierbare Formel (kein fester "Staerke"-Sonderfall), die beliebig viele oekonomische
Parameter (Elastizitaeten, Daempfungsfaktoren, Deckelungen, ...) referenzieren kann.

### Aufbau

- `kausalrechner/formula_eval.py` – sichere Formelauswertung auf Basis von `ast` (nur
  Grundrechenarten, Vergleiche, `min`/`max`/`abs`/`round`; kein Datei-/Netzwerk-/Import-Zugriff).
- `kausalrechner/graph.py` – `KausalGraph`, `Kausalkante`, `Kausalschritt` und
  `berechne_kausalkette`: Traversierung mit Zyklenerkennung (Knoten im aktuellen Pfad werden
  nicht erneut betreten) und `max_tiefe` als zusaetzliche Sicherheitsgrenze. `effekt` und
  `tiefe` stehen in jeder Formel zur Verfuegung.
- `kausalrechner/parameters.py` – Parameter-Datenbank; `parameter_hinzufuegen(...)` fuegt neue
  Parameter mit Standardwert, optionaler Beschreibung und Grenzen (`min_wert`/`max_wert`) hinzu.
- `kausalrechner/synonyms.py` – Aufloesung von Suchbegriffen zu eindeutigen Konzept-IDs ueber
  eine Synonym-Tabelle.
- `kausalrechner/data_loader.py` – laedt Konzepte, Kausalbeziehungen und Parameter aus
  `kausalrechner/data/*.json`.
- `kausalrechner/data/` – Beispieldaten: `konzepte.json`, `kausalbeziehungen.json`,
  `parameter.json` (Kette Unternehmenssteuer -> Investitionen -> Beschaeftigung -> Konsum ->
  Steuereinnahmen, inkl. einer bewussten Rueckkopplung Konsum -> Investitionen zum Testen der
  Zyklenerkennung).
- `kausalrechner/cli.py` – CLI-Einstiegspunkt.
- `tests/` – pytest-Tests fuer Formelauswertung, Graph-Traversierung und Parameter-DB.

### Testen

1. Repository klonen und ins Verzeichnis wechseln:
   ```bash
   git clone https://github.com/Flo3200/Kausalsystem.git
   cd Kausalsystem
   ```
2. Keine externen Abhaengigkeiten fuer den Kausalrechner selbst noetig (nur Standardbibliothek).
   Fuer die Tests: `pip install pytest`.
3. Unit-Tests ausfuehren:
   ```bash
   python -m pytest tests/ -v
   ```
4. CLI mit den mitgelieferten Beispieldaten ausprobieren:
   ```bash
   python -m kausalrechner.cli "Unternehmenssteuer" hoeher 10
   python -m kausalrechner.cli "Unternehmenssteuer" geringer 10 --max-tiefe 5
   ```
   Erwartete Ausgabe u.a.: pro Kausalschritt eine Zeile mit Tiefe, Quelle, Ziel, ein-/ausgehendem
   Effekt und verwendeter Formel, gefolgt vom aggregierten Gesamteffekt je betroffenem Konzept.
5. Eigene Szenarien testen: weitere Konzepte/Synonyme in `kausalrechner/data/konzepte.json`,
   weitere Kausalkanten (mit beliebiger Formel) in `kausalrechner/data/kausalbeziehungen.json`
   und neue Parameter in `kausalrechner/data/parameter.json` ergaenzen – oder programmatisch per
   `parameter_hinzufuegen(...)` aus `kausalrechner/parameters.py`.
6. Sicherheit der Formelauswertung pruefen: `tests/test_formula_eval.py` zeigt, dass z.B.
   `__import__(...)`, `open(...)` oder Attributzugriffe (`x.__class__`) mit `FormelFehler`
   abgelehnt werden.

## Alte Struktur (`Platzhalter`, nicht mehr aktiv gepflegt)

`data_loader.py`, `lookup.py`, `main.py` und `data/synonyme.json`, `data/kausaldaten.json`,
`data/formelzeichen.json` im Root-Verzeichnis stammen aus einer fruehen Vorversion (Synonym-
Lookup + Formelzeichen-Standardwerte ohne Graph/Formeln pro Kante) und wurden bewusst als
Platzhalter im Repo belassen. Sie werden vom neuen `kausalrechner`-Paket nicht verwendet.
