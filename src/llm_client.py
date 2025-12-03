import asyncio
import os
from pathlib import Path
from typing import Any

import google.generativeai as genai
from dotenv import load_dotenv

# Resolve project root (folder that contains .env and src/)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"

# Load .env explicitly from the project root
load_dotenv(dotenv_path=ENV_PATH)

API_KEY_ENV = "GEMINI_API_KEY"


class GeminiClient:
    """
    Simple wrapper around Google Generative AI (Gemini).

    - Reads API key from environment variable GEMINI_API_KEY.
    - Exposes a single `generate(prompt: str) -> str` method.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash"):
        api_key = os.getenv(API_KEY_ENV)
        if not api_key:
            raise RuntimeError(
                f"{API_KEY_ENV} is not set. "
                "Set it in your environment or in a .env file at {ENV_PATH}."
            )

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    async def generate(self, prompt: str) -> str:
        """
        Async-friendly text generation.

        Uses the async client if available; otherwise runs the sync call
        in a thread so callers can still await.
        """

        async def _async_call() -> Any:
            return await self.model.generate_content_async(prompt)

        def _sync_call() -> Any:
            return self.model.generate_content(prompt)

        try:
            if hasattr(self.model, "generate_content_async"):
                response = await _async_call()
            else:
                response = await asyncio.to_thread(_sync_call)
        except Exception as e:
            raise RuntimeError(f"Gemini generate failed: {e}") from e

        return self._extract_text(response)

    @staticmethod
    def _extract_text(response: Any) -> str:
        """
        Normalize Gemini responses to plain text.
        """
        if response is None:
            return ""

        # Preferred: response.text (provided by google-generativeai)
        text = getattr(response, "text", None)
        if text:
            return text

        # Fallback: look for the first candidate with content parts
        candidates = getattr(response, "candidates", None)
        if candidates:
            for cand in candidates:
                parts = getattr(cand, "content", None)
                if parts and hasattr(parts, "parts"):
                    return " ".join(str(p) for p in parts.parts if p)

        return str(response)
