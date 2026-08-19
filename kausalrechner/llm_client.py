"""Generischer Wrapper fuer lokale LLM-Inferenz, gemeinsam genutzt von allen drei
LLM-gestuetzten Funktionen des Kausalrechners (Parameterschaetzung, Berichtstext,
Begriffs-Vorschlag). Alle Aufrufe laufen lokal, es gibt keinen Cloud-API-Call.

Unterstuetzt werden zwei austauschbare Backends:

- "llama_cpp": quantisierte GGUF-Modelle ueber `llama-cpp-python`. Das Modell wird
  entweder automatisch von Hugging Face geladen (`repo_id` + `dateiname`, ueber
  `Llama.from_pretrained`, mit lokalem Cache) oder aus einer bereits lokal
  vorhandenen Datei (`lokaler_pfad`).
- "transformers": volle/BF16-Modelle ueber die `transformers`-Bibliothek
  (`repo_id`), fuer Modelle, die (noch) nicht als GGUF vorliegen - z.B. das
  standardmaessig verwendete Finanz-Modell (siehe kausalrechner/interactive.py).

Fuer Tests kann unabhaengig von beiden Backends eine beliebige
`generiere(prompt: str) -> str` Funktion injiziert werden, siehe
kausalrechner.llm_parameters/llm_report/llm_synonyms.
"""
from dataclasses import dataclass
from functools import lru_cache
from typing import Callable

BACKEND_LLAMA_CPP = "llama_cpp"
BACKEND_TRANSFORMERS = "transformers"


@dataclass(frozen=True)
class LLMKonfiguration:
    backend: str                  # "llama_cpp" oder "transformers"
    repo_id: str = ""             # Hugging-Face-Repo, z.B. "DragonLLM/Llama-Open-Finance-8B"
    dateiname: str = ""           # nur llama_cpp: GGUF-Dateiname im Repo (fuer automatischen Download)
    lokaler_pfad: str = ""        # nur llama_cpp: alternativ direkter Pfad zu einer lokalen .gguf-Datei
    max_tokens: int = 512
    temperatur: float = 0.1
    kontext_groesse: int = 4096


class LLMNichtVerfuegbar(RuntimeError):
    """Wird geworfen, wenn das gewaehlte Backend nicht installiert ist, das Modell
    nicht geladen werden kann, oder die Konfiguration unvollstaendig/unbekannt ist."""


@lru_cache(maxsize=None)
def _lade_llama_cpp_modell(repo_id, dateiname, lokaler_pfad, kontext_groesse):
    try:
        from llama_cpp import Llama
    except ImportError as exc:
        raise LLMNichtVerfuegbar(
            "llama-cpp-python ist nicht installiert. `pip install llama-cpp-python` ausfuehren."
        ) from exc
    try:
        if lokaler_pfad:
            return Llama(model_path=lokaler_pfad, n_ctx=kontext_groesse, verbose=False)
        if repo_id and dateiname:
            return Llama.from_pretrained(
                repo_id=repo_id, filename=dateiname, n_ctx=kontext_groesse, verbose=False
            )
    except (OSError, ValueError) as exc:
        raise LLMNichtVerfuegbar(f"GGUF-Modell konnte nicht geladen werden: {exc}") from exc
    raise LLMNichtVerfuegbar(
        "llama_cpp-Backend braucht entweder 'lokaler_pfad' oder 'repo_id' + 'dateiname'."
    )


@lru_cache(maxsize=None)
def _lade_transformers_pipeline(repo_id):
    try:
        from transformers import pipeline
    except ImportError as exc:
        raise LLMNichtVerfuegbar(
            "transformers (und torch) sind nicht installiert. "
            "`pip install transformers torch accelerate` ausfuehren."
        ) from exc
    if not repo_id:
        raise LLMNichtVerfuegbar("transformers-Backend braucht 'repo_id'.")
    try:
        return pipeline("text-generation", model=repo_id, device_map="auto")
    except OSError as exc:
        raise LLMNichtVerfuegbar(f"Modell '{repo_id}' konnte nicht geladen werden: {exc}") from exc


def erzeuge_generator(konfig: LLMKonfiguration) -> Callable[[str], str]:
    """Baut eine generiere(prompt) -> text Funktion fuer die gegebene Konfiguration.

    Das Modell wird nicht sofort geladen, sondern erst beim ersten Aufruf von
    generiere() (verzoegertes Laden); Ladefehler werden dort als
    LLMNichtVerfuegbar sichtbar. Ein unbekanntes Backend wird dagegen sofort
    hier gemeldet, da es ein reiner Konfigurationsfehler ist.
    """
    if konfig.backend == BACKEND_LLAMA_CPP:
        def generiere(prompt: str) -> str:
            modell = _lade_llama_cpp_modell(
                konfig.repo_id, konfig.dateiname, konfig.lokaler_pfad, konfig.kontext_groesse
            )
            ausgabe = modell(
                prompt, max_tokens=konfig.max_tokens, temperature=konfig.temperatur, stop=["</ende>"]
            )
            return ausgabe["choices"][0]["text"].strip()
        return generiere

    if konfig.backend == BACKEND_TRANSFORMERS:
        def generiere(prompt: str) -> str:
            pipe = _lade_transformers_pipeline(konfig.repo_id)
            ausgabe = pipe(
                prompt,
                max_new_tokens=konfig.max_tokens,
                temperature=konfig.temperatur if konfig.temperatur > 0 else None,
                do_sample=konfig.temperatur > 0,
                return_full_text=False,
            )
            return ausgabe[0]["generated_text"].split("</ende>")[0].strip()
        return generiere

    raise LLMNichtVerfuegbar(f"Unbekanntes Backend: {konfig.backend!r} (erwartet 'llama_cpp' oder 'transformers')")
