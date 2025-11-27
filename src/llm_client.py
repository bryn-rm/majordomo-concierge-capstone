import os
import google.generativeai as genai

API_KEY_ENV = "GOOGLE_API_KEY"


class GeminiClient:
    """
    Simple wrapper around Google Generative AI (Gemini).

    - Reads API key from environment variable GOOGLE_API_KEY.
    - Exposes a single `generate(prompt: str) -> str` method.
    """

    def __init__(self, model_name: str = "gemini-1.5-flash"):
        api_key = os.getenv(API_KEY_ENV)
        if not api_key:
            raise RuntimeError(
                f"{API_KEY_ENV} is not set. "
                "Set it in your environment or in a .env file."
            )

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    async def generate(self, prompt: str) -> str:
        """
        Non-streaming text generation.
        ADK can call this under the hood as needed.
        """
        # google-generativeai is sync; we wrap it in an async-ish interface.
        response = self.model.generate_content(prompt)
        return response.text
