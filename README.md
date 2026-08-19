# Kausalsystem

Oekonomischer Kausalrechner: Ausgehend von einem oekonomischen Konzept (z.B.
"Unternehmenssteuer"), einer Richtung ("hoeher"/"geringer") und einer Staerke in
Prozentpunkten werden alle davon betroffenen Kausalketten in einem gerichteten Graphen
verfolgt. Jede Kausalkante hat eine frei definierbare Formel (kein fester "Staerke"-
Sonderfall), die beliebig viele oekonomische Parameter (Elastizitaeten, Daempfungsfaktoren,
Deckelungen, ...) referenzieren kann.

Konzepte koennen zusaetzlich ein **DSGE-Modell** referenzieren: statt (bzw. zusaetzlich zu)
der sequenziellen Kausalkette wird dann ein System simultaner Gleichungen numerisch geloest.
Optional koennen drei lokale LLMs eingebunden werden, um (1) bei unbekannten Suchbegriffen
einen passenden bekannten Begriff vorzuschlagen, (2) Modellparameter aus einer Szenario-
Beschreibung zu schaetzen und (3) das Ergebnis in einen lesbaren Text zu uebersetzen.

## Aufbau

- `kausalrechner/formula_eval.py` – sichere Formelauswertung auf Basis von `ast` (nur
  Grundrechenarten, Vergleiche, `min`/`max`/`abs`/`round`; kein Datei-/Netzwerk-/Import-Zugriff).
  Wird sowohl von der Kausalkette als auch vom DSGE-Solver genutzt.
- `kausalrechner/graph.py` – `KausalGraph`, `Kausalkante`, `Kausalschritt` und
  `berechne_kausalkette`: Traversierung mit Zyklenerkennung (Knoten im aktuellen Pfad werden
  nicht erneut betreten) und `max_tiefe` als zusaetzliche Sicherheitsgrenze. `effekt` und
  `tiefe` stehen in jeder Formel zur Verfuegung.
- `kausalrechner/dsge.py` – **DSGE-Solver**: `DSGEModell` (Variablen + Residual-Gleichungen)
  und `loese_dsge(...)`, ein Newton-Raphson-Verfahren mit numerisch approximierter
  Jacobi-Matrix und eigener Gauss-Elimination (reine Standardbibliothek, keine
  numpy/scipy-Abhaengigkeit). Jede Gleichung ist eine Residual-Formel (`0 = ...`), die mit
  `formula_eval.sichere_auswertung` ausgewertet wird - also derselben Sandbox wie die
  Kausalkanten.
- `kausalrechner/parameters.py` – Parameter-Datenbank; `parameter_hinzufuegen(...)` fuegt neue
  Parameter mit Standardwert, optionaler Beschreibung und Grenzen (`min_wert`/`max_wert`) hinzu.
- `kausalrechner/synonyms.py` – Aufloesung von Suchbegriffen zu eindeutigen Konzept-IDs ueber
  eine Synonym-Tabelle.
- `kausalrechner/data_loader.py` – laedt Konzepte, Kausalbeziehungen, Parameter und
  DSGE-Modelle aus `kausalrechner/data/*.json`.
- `kausalrechner/data/` – Beispieldaten: `konzepte.json`, `kausalbeziehungen.json`,
  `parameter.json` (Kette Unternehmenssteuer -> Investitionen -> Beschaeftigung -> Konsum ->
  Steuereinnahmen, inkl. einer bewussten Rueckkopplung Konsum -> Investitionen zum Testen der
  Zyklenerkennung) sowie `dsge_modelle.json` (Beispiel: statisches 3-Gleichungen-
  Neukeynesianisches Modell aus IS-Kurve, Phillips-Kurve und Taylor-Regel; die Unternehmenssteuer
  ist in `konzepte.json` ueber das Feld `"dsge"` als Kostendruckschock auf die Phillips-Kurve
  daran angebunden).
- `kausalrechner/cli.py` – nicht-interaktiver CLI-Einstiegspunkt (nur Kausalkette, ohne LLMs).
- `kausalrechner/interactive.py` – **interaktiver Einstiegspunkt**, der Kausalkette,
  DSGE-Loeser und die drei LLM-Funktionen verbindet (siehe unten).
- `kausalrechner/llm_client.py` – austauschbarer Wrapper fuer lokale LLM-Inferenz
  (`llama-cpp-python` / GGUF-Dateien).
- `kausalrechner/llm_parameters.py` – Prompt-Vorlage und striktes Antwort-Parsing fuer die
  LLM-gestuetzte Parameterschaetzung.
- `kausalrechner/llm_report.py` – Prompt-Vorlage fuer den abschliessenden LLM-Berichtstext.
- `kausalrechner/llm_synonyms.py` – Prompt-Vorlage fuer den LLM-Begriffsvorschlag bei
  unbekannten Konzepten.
- `tests/` – pytest-Tests fuer Formelauswertung, Graph-Traversierung, Parameter-DB,
  DSGE-Solver und alle drei LLM-Module (mit injizierbarem Stub-LLM, kein Modell-Download
  fuer die Tests noetig).

## Testen (ohne LLMs, reine Standardbibliothek)

1. Repository klonen und ins Verzeichnis wechseln:
   ```bash
   git clone https://github.com/Flo3200/Kausalsystem.git
   cd Kausalsystem
   ```
2. Keine externen Abhaengigkeiten fuer Kausalrechner und DSGE-Solver noetig (nur
   Standardbibliothek). Fuer die Tests: `pip install pytest`.
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

## DSGE-Modelle

Ein DSGE-Modell besteht aus benannten endogenen Variablen und ebenso vielen Residual-
Gleichungen (`linke_seite - rechte_seite`, soll = 0 werden), definiert in
`kausalrechner/data/dsge_modelle.json`. Beispiel `nk_3gleichungen` (statisches
3-Gleichungen-Neukeynesianisches Modell):

```json
{
  "nk_3gleichungen": {
    "variablen": ["produktionsluecke", "inflation", "zins"],
    "gleichungen": [
      "produktionsluecke - (y_erwartung - sigma * (zins - pi_erwartung - r_natuerlich))",
      "inflation - (beta * pi_erwartung + kappa * produktionsluecke + kostendruck_schock)",
      "zins - (r_natuerlich + pi_erwartung + phi_pi * (inflation - pi_ziel) + phi_y * produktionsluecke)"
    ],
    "startwerte": {"produktionsluecke": 0.0, "inflation": 0.02, "zins": 0.02}
  }
}
```

Ein Konzept bindet sich per `"dsge"`-Feld in `konzepte.json` an ein Modell an, inkl. welcher
Parameter als Schock genutzt wird und wie die Prozentpunkt-Staerke der Nutzereingabe in die
Schock-Groesse umgerechnet wird (`schock_skalierung`):

```json
"unternehmenssteuer": {
  "dsge": {
    "modell": "nk_3gleichungen",
    "schock_parameter": "kostendruck_schock",
    "schock_skalierung": 0.005
  }
}
```

Geloest wird mit `kausalrechner.dsge.loese_dsge(modell, parameter)` per Newton-Raphson
(numerische Jacobi-Matrix, eigene Gauss-Elimination). Weitere DSGE-Modelle koennen als
zusaetzliche Eintraege in `dsge_modelle.json` ergaenzt und ueber `konzepte.json` an ein
oder mehrere Konzepte angebunden werden - die Gleichungen duerfen dabei nur die in
`formula_eval` erlaubten Konstrukte verwenden (siehe oben).

## LLM-Integration (optional)

Alle drei LLM-Funktionen sind komplett optional, laufen lokal (kein Cloud-API-Call) und
greifen auf `llama-cpp-python` mit GGUF-Modelldateien zurueck. Sie werden erst aktiv, wenn
die passende Umgebungsvariable auf eine vorhandene `.gguf`-Datei zeigt, und selbst dann nur
nach expliziter Zustimmung (`[j/n]`-Abfrage) im interaktiven Modus:

| Umgebungsvariable                 | Zweck                                   | Vorgesehene Modellgroesse |
|------------------------------------|------------------------------------------|----------------------------|
| `KAUSAL_LLM_SYNONYM_MODEL_PATH`    | Begriffs-Vorschlag bei unbekanntem Konzept | klein, z.B. Llama 3B |
| `KAUSAL_LLM_PARAM_MODEL_PATH`      | Parameterschaetzung aus dem Szenario     | Finanz-/Wirtschafts-instruction-getuntes 8B-Modell |
| `KAUSAL_LLM_REPORT_MODEL_PATH`     | Fliesstext-Bericht aus den Ergebnissen   | 8B (kann dasselbe Modell wie oben sein) |

**Hinweis zur Modellwahl:** Der genaue Hugging-Face-Repo-Name fuer ein Modell namens
"Llama Open Finance 8B" konnte hier nicht verifiziert werden. Setze `KAUSAL_LLM_PARAM_MODEL_PATH`
auf ein beliebiges lokal vorliegendes, finanz-/wirtschafts-instruction-getuntes 8B-Llama-GGUF
(oder ein generisches Instruct-Modell, falls keines verfuegbar ist) - der Code selbst ist
modellagnostisch und funktioniert mit jedem GGUF-Chat-/Instruct-Modell, das dem im Prompt
verlangten Zeilenformat folgen kann.

Ablauf im interaktiven Modus (`python -m kausalrechner.interactive`):

1. Konzept, Richtung, Staerke und optionaler Freitext-Kontext werden abgefragt (z.B. "Von 25%
   auf 20% gesenkt").
2. Wird das Konzept nicht gefunden, wird **zuerst gefragt**, ob das (kleine) Synonym-LLM
   einen Vorschlag machen soll. Bei "ja" wird ein Vorschlag angezeigt und muss erneut bestaetigt
   werden; bei "nein" (in beiden Faellen) kann der Nutzer manuell einen anderen Begriff eingeben.
3. Optional schaetzt das Parameter-LLM Werte fuer alle Modellparameter - der Prompt enthaelt
   *alle* eingegebenen Felder (Konzept, Richtung, Staerke, Freitext-Kontext) sowie Name,
   Beschreibung und Grenzen jedes Parameters. Die Antwort muss dem strikten Format
   `PARAMETER: <name>=<zahl>` folgen (eine Zeile pro Parameter); Werte ausserhalb der Grenzen
   werden geklemmt. Die verwendeten Parameter werden vollstaendig angezeigt und koennen beliebig
   oft manuell ueberschrieben werden - jede Aenderung fuehrt zu einer Neuberechnung von
   Kausalkette und (falls vorhanden) DSGE-Gleichgewicht.
4. Kausalkette und ggf. DSGE-Gleichgewicht werden berechnet und angezeigt.
5. Optional fasst das Bericht-LLM die Zahlen (Kausalschritte, aggregierte Effekte,
   DSGE-Loesung) in einem kurzen deutschen Fliesstext zusammen, ohne neue Zahlen zu erfinden.

Fuer Unit-Tests wird in allen drei Modulen (`llm_parameters.py`, `llm_report.py`,
`llm_synonyms.py`) eine `generiere(prompt: str) -> str` Funktion injiziert - die Tests nutzen
einfache Stub-Funktionen statt eines echten Modells, siehe `tests/test_llm_*.py`.

## Google Colab testen

```bash
!git clone https://github.com/Flo3200/Kausalsystem.git
```
```bash
%cd Kausalsystem
```
```bash
!git checkout feature/dsge-llm
```
```bash
!pip install -q -r requirements-llm.txt
```
Reine Kausalrechner-/DSGE-Tests (kein Modell-Download noetig):
```bash
!python -m pytest tests/ -v
```
```bash
!python -m kausalrechner.cli "Unternehmenssteuer" geringer 10
```
Fuer die LLM-Funktionen: eigene GGUF-Modelldateien hochladen bzw. per `huggingface_hub`
herunterladen (Repo-/Dateinamen an das tatsaechlich verfuegbare Modell anpassen) und die
Umgebungsvariablen setzen, bevor der interaktive Modus gestartet wird:
```bash
!python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='<HF-REPO-FUER-LLAMA-3B-INSTRUCT-GGUF>', filename='<DATEINAME>.gguf', local_dir='models')"
```
```bash
!python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='<HF-REPO-FUER-FINANZ-8B-GGUF>', filename='<DATEINAME>.gguf', local_dir='models')"
```
```bash
import os
os.environ["KAUSAL_LLM_SYNONYM_MODEL_PATH"] = "models/<DATEINAME-3B>.gguf"
os.environ["KAUSAL_LLM_PARAM_MODEL_PATH"] = "models/<DATEINAME-8B>.gguf"
os.environ["KAUSAL_LLM_REPORT_MODEL_PATH"] = "models/<DATEINAME-8B>.gguf"
```
```bash
!python -m kausalrechner.interactive
```
Der letzte Befehl fragt interaktiv nach Konzept/Richtung/Staerke/Kontext; in Colab-Notebooks
lassen sich `input()`-Aufrufe direkt in der Zelle beantworten.
