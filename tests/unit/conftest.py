import pytest


class DummyLLM:
    """
    Very small stand-in for GeminiClient.

    It just records the last prompt and returns a fixed string.
    """

    def __init__(self, response_text: str = "DUMMY_RESPONSE"):
        self.response_text = response_text
        self.last_prompt = None

    async def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.response_text


@pytest.fixture
def dummy_llm():
    return DummyLLM()
