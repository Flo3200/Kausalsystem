# Kausalsystem

Oekonomischer Kausalrechner: Ausgehend von einem oekonomischen Konzept (z.B.
"Unternehmenssteuer"), einer Richtung ("hoeher"/"geringer") und einer Staerke in
Prozentpunkten werden alle davon betroffenen Kausalketten in einem gerichteten Graphen
verfolgt. Jede Kausalkante hat eine frei definierbare Formel (kein fester "Staerke"-
Sonderfall), die beliebig viele oekonomische Parameter (Elastizitaeten, Daempfungsfaktoren,
Deckelungen, ...) referenzieren kann.

Konzepte koennen zusaetzlich ein **DSGE-Modell** referenzieren: statt (bzw. zusaetzlich zu)
der sequenziellen Kausalkette wird dann ein System simultaner Gleichungen numerisch geloest.
Optional koennen drei lokale, real existierende LLMs eingebunden werden, um (1) bei
unbekannten Suchbegriffen einen passenden bekannten Begriff vorzuschlagen, (2)
Modellparameter aus einer Szenario-Beschreibung zu schaetzen und (3) das Ergebnis in einen
lesbaren Text zu uebersetzen.

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
- `kausalrechner/data/` – siehe Abschnitt "Kausaldatenbank" unten.
- `kausalrechner/cli.py` – nicht-interaktiver CLI-Einstiegspunkt (nur Kausalkette, ohne LLMs).
- `kausalrechner/interactive.py` – **interaktiver Einstiegspunkt**, der Kausalkette,
  DSGE-Loeser und die drei LLM-Funktionen verbindet (siehe unten).
- `kausalrechner/llm_client.py` – austauschbarer Wrapper fuer lokale LLM-Inferenz, mit zwei
  Backends (`llama_cpp` fuer GGUF, `transformers` fuer Modelle ohne GGUF-Variante).
- `kausalrechner/llm_parameters.py` – Prompt-Vorlage und striktes Antwort-Parsing fuer die
  LLM-gestuetzte Parameterschaetzung.
- `kausalrechner/llm_report.py` – Prompt-Vorlage fuer den abschliessenden LLM-Berichtstext.
- `kausalrechner/llm_synonyms.py` – Prompt-Vorlage fuer den LLM-Begriffsvorschlag bei
  unbekannten Konzepten.
- `tests/` – pytest-Tests fuer Formelauswertung, Graph-Traversierung, Parameter-DB,
  DSGE-Solver, LLM-Backend-Dispatch, alle drei LLM-Prompt-Module (mit injizierbarem
  Stub-LLM, kein Modell-Download fuer die Tests noetig) und eine automatisierte
  **Datenkonsistenzpruefung** (`test_datenkonsistenz.py`) ueber die gesamte Kausaldatenbank.

## Kausaldatenbank

`kausalrechner/data/konzepte.json` enthaelt aktuell 21 Konzepte mit eindeutiger ID,
Anzeigename und Synonym-Liste. Jede Kausalkante in `kausalrechner/data/kausalbeziehungen.json`
referenziert Konzepte ausschliesslich ueber diese IDs - `test_datenkonsistenz.py` prueft
automatisch, dass jede Kante auf ein existierendes Konzept zeigt, jede Formel nur bekannte
Parameter verwendet und kein Synonym mehrdeutig zwei Konzepten zugeordnet ist.

Konzepte: Unternehmenssteuer, Investitionen, Beschaeftigung, Konsum, Steuereinnahmen,
Zinssatz, Inflation, Bruttoinlandsprodukt (BIP), Arbeitslosigkeit, Geldmenge,
Staatsausgaben, Wechselkurs, Exporte, Importe, Handelsbilanz, Loehne, Produktivitaet,
Verbrauchervertrauen, Aktienmarkt, Kreditvergabe, Sparquote.

Abgebildete Kausalkanaele (Auswahl, insgesamt 35 Kanten in `kausalbeziehungen.json`):

- **Geldpolitik:** Zinssatz -> Investitionen/Konsum/Wechselkurs/Kreditvergabe/Aktienmarkt;
  Geldmenge -> Inflation/Zinssatz.
- **Fiskalpolitik:** Staatsausgaben -> BIP/Beschaeftigung; Unternehmenssteuer ->
  Investitionen/Steuereinnahmen.
- **Arbeitsmarkt:** BIP -> Beschaeftigung -> Arbeitslosigkeit -> Loehne -> Konsum/Inflation
  (Lohn-Phillips-Kurve); Produktivitaet -> Loehne/BIP; Investitionen -> Produktivitaet.
- **Aussenhandel:** Wechselkurs -> Exporte/Importe -> Handelsbilanz -> BIP.
- **Nachfrageseite:** Konsum -> BIP; Verbrauchervertrauen/Aktienmarkt -> Konsum;
  Kreditvergabe -> Investitionen; Sparquote -> Konsum/Investitionen.
- Plus die urspruengliche Kette Unternehmenssteuer -> Investitionen -> Beschaeftigung ->
  Konsum -> Steuereinnahmen inkl. der bewussten Rueckkopplung Konsum -> Investitionen
  (zum Testen der Zyklenerkennung).

Jede Kante nutzt eine eigene, klar benannte Elastizitaet aus `kausalrechner/data/parameter.json`
(Namensschema `elastizitaet_<quelle>_<ziel>`), sodass jeder Kausalkanal einzeln kalibrierbar
ist. Eigene Szenarien: weitere Konzepte/Synonyme in `konzepte.json`, weitere Kanten (mit
beliebiger Formel) in `kausalbeziehungen.json` und neue Parameter in `parameter.json`
ergaenzen - oder programmatisch per `parameter_hinzufuegen(...)` aus
`kausalrechner/parameters.py`. Nach jeder Aenderung `python -m pytest tests/ -v` laufen
lassen, `test_datenkonsistenz.py` faengt die haeufigsten Fehler (Tippfehler in IDs,
verwaiste Parameter) sofort ab.

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
   python -m kausalrechner.cli "Zinssatz" hoeher 2 --max-tiefe 5
   ```
   Erwartete Ausgabe u.a.: pro Kausalschritt eine Zeile mit Tiefe, Quelle, Ziel, ein-/ausgehendem
   Effekt und verwendeter Formel, gefolgt vom aggregierten Gesamteffekt je betroffenem Konzept.
5. Sicherheit der Formelauswertung pruefen: `tests/test_formula_eval.py` zeigt, dass z.B.
   `__import__(...)`, `open(...)` oder Attributzugriffe (`x.__class__`) mit `FormelFehler`
   abgelehnt werden.

## DSGE-Modelle

Ein DSGE-Modell besteht aus benannten endogenen Variablen und ebenso vielen Residual-
Gleichungen (`linke_seite - rechte_seite`, soll = 0 werden), definiert in
`kausalrechner/data/dsge_modelle.json`. Aktuelles Modell `nk_5gleichungen`: statisches
5-Gleichungen-Neukeynesianisches Modell einer **offenen** Volkswirtschaft (IS-Kurve mit
Aussenhandelskanal, Phillips-Kurve, Taylor-Regel, ungedeckte Zinsparitaet fuer den
Wechselkurs, Okun'sches Gesetz fuer die Arbeitslosigkeit):

```json
{
  "nk_5gleichungen": {
    "variablen": ["produktionsluecke", "inflation", "zins", "wechselkurs", "arbeitslosigkeit"],
    "gleichungen": [
      "produktionsluecke - (y_erwartung - sigma * (zins - pi_erwartung - r_natuerlich) + gamma_nx * wechselkurs)",
      "inflation - (beta * pi_erwartung + kappa * produktionsluecke + kostendruck_schock)",
      "zins - (r_natuerlich + pi_erwartung + phi_pi * (inflation - pi_ziel) + phi_y * produktionsluecke + geldpolitischer_schock)",
      "wechselkurs - (uip_sensitivitaet * (auslaendischer_zins - zins) + erwartete_wechselkursaenderung)",
      "arbeitslosigkeit - (natuerliche_arbeitslosigkeit - okun_koeffizient * produktionsluecke)"
    ]
  }
}
```

Zwei Konzepte binden sich per `"dsge"`-Feld in `konzepte.json` an dieses Modell an (jeweils
mit eigenem Schock-Parameter und eigener Skalierung der Prozentpunkt-Staerke):

- `unternehmenssteuer` -> Kostendruckschock auf die Phillips-Kurve (`kostendruck_schock`).
- `zinssatz` -> direkter Schock auf die Taylor-Regel (`geldpolitischer_schock`).

```json
"zinssatz": {
  "dsge": {
    "modell": "nk_5gleichungen",
    "schock_parameter": "geldpolitischer_schock",
    "schock_skalierung": 0.005
  }
}
```

Geloest wird mit `kausalrechner.dsge.loese_dsge(modell, parameter)` per Newton-Raphson
(numerische Jacobi-Matrix, eigene Gauss-Elimination) - `test_datenkonsistenz.py` loest bei
jedem Testlauf alle referenzierten DSGE-Modelle mit den Standardparametern durch, um
verwaiste Referenzen oder unloesbare Modelle sofort zu erkennen. Weitere DSGE-Modelle koennen
als zusaetzliche Eintraege in `dsge_modelle.json` ergaenzt und ueber `konzepte.json` an ein
oder mehrere Konzepte angebunden werden - die Gleichungen duerfen dabei nur die in
`formula_eval` erlaubten Konstrukte verwenden.

## LLM-Integration (optional, mit real existierenden Modellen)

Alle drei LLM-Funktionen sind komplett optional, laufen lokal (kein Cloud-API-Call) und
werden erst nach expliziter Zustimmung (`[j/n]`-Abfrage) im interaktiven Modus aktiv. Die
Standardkonfiguration referenziert drei **tatsaechlich existierende, verifizierte**
Hugging-Face-Modelle:

| Baustein            | Standardmodell                                                                 | Backend        |
|----------------------|------------------------------------------------------------------------------------|----------------|
| Begriffs-Vorschlag   | [`bartowski/Llama-3.2-3B-Instruct-GGUF`](https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF) (Datei `Llama-3.2-3B-Instruct-Q4_K_M.gguf`, Quantisierung von `meta-llama/Llama-3.2-3B-Instruct`) | `llama_cpp` (automatischer Download via `Llama.from_pretrained`) |
| Parameterschaetzung  | [`DragonLLM/Llama-Open-Finance-8B`](https://huggingface.co/DragonLLM/Llama-Open-Finance-8B) (Llama-3.1-8B, feingetunt auf Finanzdaten in Englisch/Franzoesisch/Deutsch) | `transformers` |
| Abschlussbericht     | dasselbe Finanz-Modell wie oben (Wiederverwendung, ein Modell-Ladevorgang dank Caching) | `transformers` |

Jeder Baustein kann per Umgebungsvariable auf ein anderes Modell/Backend umgestellt werden,
ohne den Code zu aendern:

```bash
export KAUSAL_LLM_SYNONYM_BACKEND=llama_cpp
export KAUSAL_LLM_SYNONYM_REPO_ID=bartowski/Llama-3.2-3B-Instruct-GGUF
export KAUSAL_LLM_SYNONYM_DATEINAME=Llama-3.2-3B-Instruct-Q4_K_M.gguf
# oder eine bereits lokal vorhandene Datei:
export KAUSAL_LLM_SYNONYM_LOKALER_PFAD=/pfad/zu/modell.gguf

export KAUSAL_LLM_PARAM_BACKEND=transformers
export KAUSAL_LLM_PARAM_REPO_ID=DragonLLM/Llama-Open-Finance-8B

export KAUSAL_LLM_REPORT_BACKEND=transformers
export KAUSAL_LLM_REPORT_REPO_ID=DragonLLM/Llama-Open-Finance-8B
```

Ablauf im interaktiven Modus (`python -m kausalrechner.interactive`):

1. Konzept, Richtung, Staerke und optionaler Freitext-Kontext werden abgefragt (z.B. "Von 25%
   auf 20% gesenkt").
2. Wird das Konzept nicht gefunden, wird **zuerst gefragt**, ob das Synonym-LLM (Llama 3.2 3B)
   einen Vorschlag machen soll. Bei "ja" wird ein Vorschlag angezeigt und muss erneut bestaetigt
   werden; bei "nein" (in beiden Faellen) kann der Nutzer manuell einen anderen Begriff eingeben.
3. Optional schaetzt das Parameter-LLM (Llama Open Finance 8B) Werte fuer alle Modellparameter -
   der Prompt enthaelt *alle* eingegebenen Felder (Konzept, Richtung, Staerke,
   Freitext-Kontext) sowie Name, Beschreibung und Grenzen jedes Parameters. Die Antwort muss dem
   strikten Format `PARAMETER: <name>=<zahl>` folgen (eine Zeile pro Parameter); Werte
   ausserhalb der Grenzen werden geklemmt. Die verwendeten Parameter werden vollstaendig
   angezeigt und koennen beliebig oft manuell ueberschrieben werden - jede Aenderung fuehrt zu
   einer Neuberechnung von Kausalkette und (falls vorhanden) DSGE-Gleichgewicht.
4. Kausalkette und ggf. DSGE-Gleichgewicht werden berechnet und angezeigt.
5. Optional fasst dasselbe Llama-Open-Finance-8B-Modell die Zahlen (Kausalschritte,
   aggregierte Effekte, DSGE-Loesung) in einem kurzen deutschen Fliesstext zusammen, ohne neue
   Zahlen zu erfinden.

Fuer Unit-Tests wird in allen drei Prompt-Modulen (`llm_parameters.py`, `llm_report.py`,
`llm_synonyms.py`) eine `generiere(prompt: str) -> str` Funktion injiziert - die Tests nutzen
einfache Stub-Funktionen statt eines echten Modells (siehe `tests/test_llm_*.py`), sodass CI
ohne Modell-Download auskommt. `tests/test_llm_client.py` prueft zusaetzlich das
Backend-Dispatch von `llm_client.py` selbst (u.a. dass ein unbekanntes Backend sofort einen
klaren Fehler wirft).

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
Reine Kausalrechner-/DSGE-/Konsistenz-Tests (kein Modell-Download noetig):
```bash
!python -m pytest tests/ -v
```
```bash
!python -m kausalrechner.cli "Zinssatz" hoeher 2
```
Fuer die LLM-Funktionen: die Standardmodelle werden automatisch von Hugging Face geladen
(GPU-Laufzeit in Colab empfohlen: Laufzeit -> Laufzeittyp aendern -> GPU). Kein manueller
Download noetig, die Umgebungsvariablen muessen nur gesetzt werden, wenn ein **anderes**
Modell verwendet werden soll (siehe Tabelle oben fuer die Defaults). Danach den interaktiven
Modus starten:
```bash
!python -m kausalrechner.interactive
```
Der Befehl fragt interaktiv nach Konzept/Richtung/Staerke/Kontext sowie vor jedem LLM-Einsatz
einzeln nach Zustimmung; in Colab-Notebooks lassen sich `input()`-Aufrufe direkt in der Zelle
beantworten. Erwartetes Verhalten bei erstmaliger Zustimmung zur Parameterschaetzung: Download
von `DragonLLM/Llama-Open-Finance-8B` (~16 GB, einmalig, danach lokal gecacht).
