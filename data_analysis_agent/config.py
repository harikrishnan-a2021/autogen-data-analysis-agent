"""
LLM configuration for AutoGen agents.
Loads API keys from .env and builds the config_list AutoGen expects.

Provider priority:
  1. Ollama (local, free) — used when OLLAMA_MODEL is set or as default fallback
  2. Anthropic            — used when ANTHROPIC_API_KEY is set
  3. OpenAI               — used when OPENAI_API_KEY is set
"""
import os
from dotenv import load_dotenv

load_dotenv()


def get_llm_config(temperature: float = 0) -> dict:
    """Return the AutoGen-compatible LLM config dict."""
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key    = os.getenv("OPENAI_API_KEY")
    ollama_model  = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    use_ollama    = os.getenv("USE_OLLAMA", "true").lower() == "true"

    if use_ollama:
        return {
            "config_list": [
                {
                    "model": ollama_model,
                    "api_key": "ollama",          # placeholder — Ollama ignores this
                    "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
                    "api_type": "openai",          # Ollama exposes an OpenAI-compatible API
                }
            ],
            "temperature": temperature,
            "cache_seed": None,
        }

    if anthropic_key:
        return {
            "config_list": [
                {
                    "model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
                    "api_key": anthropic_key,
                    "api_type": "anthropic",
                }
            ],
            "temperature": temperature,
            "cache_seed": None,
        }

    if openai_key:
        return {
            "config_list": [
                {
                    "model": os.getenv("OPENAI_MODEL", "gpt-4o"),
                    "api_key": openai_key,
                }
            ],
            "temperature": temperature,
            "cache_seed": None,
        }

    raise EnvironmentError(
        "No LLM configured. Set USE_OLLAMA=true, ANTHROPIC_API_KEY, or OPENAI_API_KEY in .env"
    )
