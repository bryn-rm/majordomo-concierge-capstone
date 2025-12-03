import pytest

from src.agents.oracle import OracleAgent, is_time_sensitive_query
from src.tools import TOOL_REGISTRY
from tests.unit.conftest import DummyLLM


@pytest.mark.parametrize(
    "text,expected",
    [
        ("What is the latest news on UK interest rates?", True),
        ("today's weather in London", True),
        ("covid updates 2025", True),
        ("Who won the NBA game last night?", True),
        ("What was the final score of Lakers vs Celtics?", True),
        ("Who was Ada Lovelace?", False),
        ("Explain quantum mechanics", False),
    ],
)
def test_is_time_sensitive_query(text, expected):
    assert is_time_sensitive_query(text) == expected


@pytest.mark.asyncio
async def test_oracle_uses_wikipedia_for_timeless(monkeypatch):
    calls = {"google": 0, "wiki": 0}

    async def fake_google_search(query: str, limit: int = 3):
        calls["google"] += 1
        return [{"title": "G", "description": "G desc", "url": "https://g"}]

    async def fake_wikipedia_search(query: str, limit: int = 3):
        calls["wiki"] += 1
        return [{"title": "W", "description": "W desc", "url": "https://w"}]

    monkeypatch.setitem(TOOL_REGISTRY, "search.google", fake_google_search)
    monkeypatch.setitem(TOOL_REGISTRY, "search.wikipedia", fake_wikipedia_search)

    llm = DummyLLM(response_text="oracle-answer")
    oracle = OracleAgent(llm_client=llm)

    result = await oracle.handle(
        user_message="Who was Ada Lovelace?",
        context_text="",
    )

    assert result["answer"] == "oracle-answer"
    assert result["tool_used"] == "search.wikipedia"
    assert calls["wiki"] == 1
    assert calls["google"] == 0


@pytest.mark.asyncio
async def test_oracle_uses_google_for_time_sensitive(monkeypatch):
    calls = {"google": 0, "wiki": 0}

    async def fake_google_search(query: str, limit: int = 3):
        calls["google"] += 1
        return [{"title": "G", "description": "G desc", "url": "https://g"}]

    async def fake_wikipedia_search(query: str, limit: int = 3):
        calls["wiki"] += 1
        return [{"title": "W", "description": "W desc", "url": "https://w"}]

    monkeypatch.setitem(TOOL_REGISTRY, "search.google", fake_google_search)
    monkeypatch.setitem(TOOL_REGISTRY, "search.wikipedia", fake_wikipedia_search)

    llm = DummyLLM(response_text="oracle-answer")
    oracle = OracleAgent(llm_client=llm)

    result = await oracle.handle(
        user_message="What is the latest news on UK interest rates this year?",
        context_text="",
    )

    assert result["answer"] == "oracle-answer"
    assert result["tool_used"] == "search.google"
    assert calls["google"] == 1
    # Wikipedia may still be called as fallback if google had returned nothing,
    # but in this test google returns a result so no fallback.
    assert calls["wiki"] == 0
