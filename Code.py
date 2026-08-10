import requests, json

SYNONYME_URL = "https://raw.githubusercontent.com/DEIN_USER/DEIN_REPO/main/synonyme.json"
KAUSALDATEN_URL = "https://raw.githubusercontent.com/DEIN_USER/DEIN_REPO/main/kausaldaten.json"
FORMELZEICHEN_URL = "https://raw.githubusercontent.com/DEIN_USER/DEIN_REPO/main/formelzeichen.json"

synonyme_raw = requests.get(SYNONYME_URL).json()
kausaldaten = requests.get(KAUSALDATEN_URL).json()

try:
    formelzeichen_db = requests.get(FORMELZEICHEN_URL).json()
except Exception:
    formelzeichen_db = {}

print(f"{len(synonyme_raw)} Konzepte, {len(kausaldaten)} Kausalbeziehungen, "
      f"{len(formelzeichen_db)} Formelzeichen geladen.")

# ── Lookup: Begriff -> ID ────────────────────────────────
wort_zu_id = {}
id_zu_anzeigename = {}

for id_, eintrag in synonyme_raw.items():
    id_zu_anzeigename[id_] = eintrag["anzeigename"]
    for wort in eintrag["synonyme"]:
        wort_zu_id[wort.strip().lower()] = id_

print(f"{len(wort_zu_id)} Synonyme indiziert.")

# ── Lookup: Formelzeichen -> aktueller Zahlenwert ────────
formelzeichen_werte = {symbol: eintrag["standardwert"] for symbol, eintrag in formelzeichen_db.items()}


def begriff_zu_id(suchbegriff):
    """Exakte Suche in der Synonym-Tabelle. Gibt None zurueck, falls nicht gefunden."""
    key = suchbegriff.strip().lower()
    treffer_id = wort_zu_id.get(key)
    if treffer_id:
        print(f"   Gefunden: '{suchbegriff}' -> ID {treffer_id} ('{id_zu_anzeigename[treffer_id]}')")
    else:
        print(f"   Kein Treffer fuer '{suchbegriff}' in der Synonym-Tabelle.")
    return treffer_id
