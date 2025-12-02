import pytest

from src.agents.sentinel import SentinelAgent
from src.tools import TOOL_REGISTRY
from tests.unit.conftest import DummyLLM


@pytest.mark.asyncio
async def test_sentinel_turns_lights_on_and_locks_door(monkeypatch):
    # Track smart home calls
    calls = {
        "set_state": [],
        "get_state": [],
        "approve": [],
    }

    async def fake_set_state(user_id: str, partial_state: dict):
        calls["set_state"].append((user_id, partial_state))
        # pretend current state is whatever we just set
        return {"user_id": user_id, **partial_state}

    async def fake_get_state(user_id: str):
        calls["get_state"].append(user_id)
        return {"user_id": user_id, "lights": "on", "doors_locked": "locked"}

    def fake_approve(message: str) -> bool:
        calls["approve"].append(message)
        return True

    monkeypatch.setitem(TOOL_REGISTRY, "smarthome.set_state", fake_set_state)
    monkeypatch.setitem(TOOL_REGISTRY, "smarthome.get_state", fake_get_state)
    monkeypatch.setitem(TOOL_REGISTRY, "human.approve", fake_approve)

    llm = DummyLLM(response_text="sentinel-narrative")
    sentinel = SentinelAgent(llm_client=llm)

    result = await sentinel.handle(
        user_id="bryn",
        user_message="Turn the lights on and lock the door.",
        ctx_text="",
    )

    # We expect an update with both lights + doors_locked
    assert result["approved"] is True
    assert result["state"]["lights"] == "on"
    assert result["state"]["doors_locked"] == "locked"
    assert result["narrative"] == "sentinel-narrative"

    # Check tools were actually used
    assert len(calls["approve"]) == 1
    assert len(calls["set_state"]) == 1
    user_id, partial_state = calls["set_state"][0]
    assert user_id == "bryn"
    assert partial_state["lights"] == "on"
    assert partial_state["doors_locked"] == "locked"
