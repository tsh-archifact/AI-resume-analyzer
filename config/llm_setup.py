import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()


def get_llm_provider() -> str:
    return (os.getenv("LLM_PROVIDER") or "groq").lower()


def get_llm_model() -> str:
    """Resolve the model in one place so services stay provider-agnostic."""
    provider = get_llm_provider()
    default_models = {
        "groq": "groq/compound-mini",
        "openai": "gpt-4o-mini",
    }
    env_name = f"{provider.upper()}_MODEL"
    return os.getenv("LLM_MODEL") or os.getenv(env_name) or default_models.get(provider, "groq/compound-mini")


def get_llm_api_key() -> str | None:
    provider = get_llm_provider()
    if provider == "groq":
        return os.getenv("GROQ_API_KEY") or os.getenv("LLM_API_KEY")
    if provider == "openai":
        return os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
    return os.getenv("LLM_API_KEY")


def get_llm_client() -> Any:
    provider = get_llm_provider()
    api_key = get_llm_api_key()
    if not api_key:
        raise ValueError(f"No API key configured for provider: {provider}")

    if provider == "groq":
        from groq import Groq

        return Groq(api_key=api_key)

    if provider == "openai":
        from openai import OpenAI

        return OpenAI(api_key=api_key)

    raise ValueError(f"Unsupported LLM provider: {provider}")
