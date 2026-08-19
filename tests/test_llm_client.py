"""Tests fuer den Backend-Dispatch in llm_client.py. Da llama-cpp-python bzw.
transformers in der CI nicht zwingend installiert sind, wird hier nur das
Fehlerverhalten (LLMNichtVerfuegbar) geprueft, nicht die eigentliche Inferenz -
letztere wird ueber die injizierbaren generiere()-Funktionen in den Modulen
llm_parameters/llm_report/llm_synonyms getestet (siehe dortige Tests)."""
import pytest

from kausalrechner.llm_client import (
    BACKEND_LLAMA_CPP,
    BACKEND_TRANSFORMERS,
    LLMKonfiguration,
    LLMNichtVerfuegbar,
    erzeuge_generator,
)


def test_unbekanntes_backend_wirft_sofort_beim_erzeugen():
    konfig = LLMKonfiguration(backend="kein_backend")
    with pytest.raises(LLMNichtVerfuegbar):
        erzeuge_generator(konfig)


def test_llama_cpp_backend_ohne_repo_oder_pfad_wirft_beim_ersten_aufruf():
    konfig = LLMKonfiguration(backend=BACKEND_LLAMA_CPP)
    generiere = erzeuge_generator(konfig)
    with pytest.raises(LLMNichtVerfuegbar):
        generiere("test")


def test_transformers_backend_ohne_repo_id_wirft_beim_ersten_aufruf():
    konfig = LLMKonfiguration(backend=BACKEND_TRANSFORMERS, repo_id="")
    generiere = erzeuge_generator(konfig)
    with pytest.raises(LLMNichtVerfuegbar):
        generiere("test")


def test_konfiguration_ist_unveraenderlich():
    konfig = LLMKonfiguration(backend=BACKEND_TRANSFORMERS, repo_id="DragonLLM/Llama-Open-Finance-8B")
    with pytest.raises(Exception):
        konfig.repo_id = "anderes-modell"
