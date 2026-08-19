"""Generischer Wrapper fuer lokale LLM-Inferenz (llama.cpp / GGUF), gemeinsam
genutzt von allen drei LLM-gestuetzten Funktionen des Kausalrechners
(Parameterschaetzung, Berichtstext, Begriffs-Vorschlag).

Die eigentliche Modellinferenz ist austauschbar: standardmaessig wird
`llama_cpp.Llama` mit einer lokalen GGUF-Datei verwendet (keine Netzwerkzugriffe
zur Laufzeit ausserhalb des einmaligen Modell-Downloads). Fuer Tests kann eine
beliebige `generiere(prompt: str) -> str` Funktion injiziert werden, siehe
kausalrechner.llm_parameters/llm_report/llm_synonyms.
"""
from dataclasses import dataclass
from functools import lru_cache
from typing import Callable


@dataclass(frozen=True)
class LLMKonfiguration:
    modell_pfad: str
    max_tokens: int = 512
    temperatur: float = 0.1
    kontext_groesse: int = 4096


class LLMNichtVerfuegbar(RuntimeError):
    """Wird geworfen, wenn kein llama.cpp-Backend installiert ist oder die Modelldatei
    fehlt, und keine eigene generiere()-Funktion injiziert wurde."""


@lru_cache(maxsize=None)
def _lade_llama_cpp_modell(modell_pfad, kontext_groesse):
    try:
        from llama_cpp import Llama
    except ImportError as exc:
        raise LLMNichtVerfuegbar(
            "llama-cpp-python ist nicht installiert. `pip install llama-cpp-python` "
            "ausfuehren oder eine eigene generiere()-Funktion injizieren."
        ) from exc
    try:
        return Llama(model_path=modell_pfad, n_ctx=kontext_groesse, verbose=False)
    except (OSError, ValueError) as exc:
        raise LLMNichtVerfuegbar(f"Modell konnte nicht geladen werden: {modell_pfad} ({exc})") from exc


def erzeuge_generator(konfig: LLMKonfiguration) -> Callable[[str], str]:
    """Baut eine generiere(prompt) -> text Funktion fuer die gegebene Konfiguration.

    Wirft LLMNichtVerfuegbar erst beim ersten Aufruf von generiere(), nicht schon
    beim Erzeugen des Generators (verzoegertes Laden).
    """
    def generiere(prompt: str) -> str:
        modell = _lade_llama_cpp_modell(konfig.modell_pfad, konfig.kontext_groesse)
        ausgabe = modell(
            prompt,
            max_tokens=konfig.max_tokens,
            temperature=konfig.temperatur,
            stop=["</ende>"],
        )
        return ausgabe["choices"][0]["text"].strip()
    return generiere
