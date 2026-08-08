"""
Reusable LLM client for Module 7.

Wraps the Google Gemini API (google-generativeai). The API key and model are
read from environment variables - never hard-coded. If no API key is
configured, the client raises a clear, catchable error so callers can decide
on a fallback behavior instead of crashing the whole request.
"""

from __future__ import annotations

import json
import os
import re
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash").strip()


class LLMError(Exception):
    """Raised when the LLM call fails or returns something unusable."""


class LLMNotConfiguredError(LLMError):
    """Raised when no API key is configured."""


def _strip_code_fences(text: str) -> str:
    """LLMs sometimes wrap JSON in ```json ... ``` fences. Strip those."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _extract_first_json_object(text: str) -> str:
    """Best-effort extraction of the first top-level JSON object in text."""
    start = text.find("{")
    if start == -1:
        raise LLMError("No JSON object found in LLM response.")
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    raise LLMError("Unbalanced JSON object in LLM response.")


class GeminiClient:
    """Thin, reusable wrapper around the Gemini generate_content API."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.model_name = model or GEMINI_MODEL
        self._model = None

    def _get_model(self):
        if not self.api_key:
            raise LLMNotConfiguredError(
                "GEMINI_API_KEY is not set. Configure it in your environment or .env file."
            )
        if self._model is None:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(self.model_name)
        return self._model

    def generate_json(self, prompt: str, max_output_tokens: int = 1024) -> dict:
        """Call the LLM and parse its response as a JSON object.

        Raises LLMError on any failure (network, parsing, empty response) so
        callers can apply a fallback strategy.
        """
        model = self._get_model()
        try:
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": max_output_tokens,
                    "response_mime_type": "application/json",
                },
            )
            raw_text = (response.text or "").strip()
        except Exception as exc:  # noqa: BLE001 - surfacing as LLMError deliberately
            raise LLMError(f"LLM call failed: {exc}") from exc

        if not raw_text:
            raise LLMError("LLM returned an empty response.")

        cleaned = _strip_code_fences(raw_text)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        try:
            candidate = _extract_first_json_object(cleaned)
            return json.loads(candidate)
        except (json.JSONDecodeError, LLMError) as exc:
            raise LLMError(f"Could not parse JSON from LLM response: {exc}") from exc


_default_client: Optional[GeminiClient] = None


def get_llm_client() -> GeminiClient:
    """Return a process-wide shared client instance."""
    global _default_client
    if _default_client is None:
        _default_client = GeminiClient()
    return _default_client
