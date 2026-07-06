"""
Factory for the LLM client + stage model names, switched by LLM_PROVIDER.

Stage 1 and Stage 2 only ever call get_llm_client() and use the returned
model names - they must not know or care whether they're talking to the
OpenAI API or a local Ollama server.
"""

from __future__ import annotations

import dataclasses
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

_OPENAI_STAGE1_MODEL = "gpt-5.4-mini"
_OPENAI_STAGE2_MODEL = "gpt-5.4"
_DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434/v1"

# Local requests fail fast (no silent retries) and time out instead of
# hanging forever if the Ollama server never responds.
_LOCAL_MAX_RETRIES = 0
_LOCAL_TIMEOUT_SECONDS = 10.0

_VALID_REPORT_LANGUAGES = {"ko", "en"}
_DEFAULT_REPORT_LANGUAGE = "ko"


class LLMConfigError(Exception):
    """Raised when the configured provider is missing required setup."""


@dataclasses.dataclass
class LLMConfig:
    client: OpenAI
    stage1_model: str
    stage2_model: str
    provider: str
    language: str


def get_llm_client() -> LLMConfig:
    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    language = _report_language()

    if provider == "openai":
        config = _openai_config()
    elif provider == "local":
        config = _local_config()
    else:
        raise LLMConfigError(
            f"Unknown LLM_PROVIDER '{provider}' (expected 'openai' or 'local')"
        )
    config.language = language
    return config


def _report_language() -> str:
    language = os.getenv("REPORT_LANGUAGE", _DEFAULT_REPORT_LANGUAGE).strip().lower()
    if language not in _VALID_REPORT_LANGUAGES:
        raise LLMConfigError(
            f"Unknown REPORT_LANGUAGE '{language}' (expected 'ko' or 'en')"
        )
    return language


def _openai_config() -> LLMConfig:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LLMConfigError(
            "OPENAI_API_KEY is not set. Add it to your .env file "
            "(see .env.example)."
        )
    return LLMConfig(
        client=OpenAI(api_key=api_key),
        stage1_model=_OPENAI_STAGE1_MODEL,
        stage2_model=_OPENAI_STAGE2_MODEL,
        provider="openai",
        language=_DEFAULT_REPORT_LANGUAGE,
    )


def _local_config() -> LLMConfig:
    stage1_model = os.getenv("LOCAL_STAGE1_MODEL")
    stage2_model = os.getenv("LOCAL_STAGE2_MODEL")
    if not stage1_model or not stage2_model:
        raise LLMConfigError(
            "LLM_PROVIDER=local requires LOCAL_STAGE1_MODEL and "
            "LOCAL_STAGE2_MODEL to be set in .env (see .env.example)."
        )
    base_url = os.getenv("OLLAMA_BASE_URL", _DEFAULT_OLLAMA_BASE_URL)
    client = OpenAI(
        api_key="ollama",  # unused by Ollama, but the SDK requires a value
        base_url=base_url,
        max_retries=_LOCAL_MAX_RETRIES,
        timeout=_LOCAL_TIMEOUT_SECONDS,
    )
    return LLMConfig(
        client=client,
        stage1_model=stage1_model,
        stage2_model=stage2_model,
        provider="local",
        language=_DEFAULT_REPORT_LANGUAGE,
    )
