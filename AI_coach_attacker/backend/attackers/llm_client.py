import os

from openai import OpenAI


def get_client() -> OpenAI:
    base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set")

    return OpenAI(base_url=base_url, api_key=api_key)


def get_model() -> str:
    return os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini")
