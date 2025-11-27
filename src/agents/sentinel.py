from typing import Dict, Any

from src.prompts.system_instructions import SENTINEL_BASE
from src.memory.state_cache import get_home_state, set_home_state
from src.tools import TOOL_REGISTRY


class SentinelAgent:
    """
    Sentinel agent.

    - Simulated smart home controller.
    - v1: only updates an in-memory state cache, with a simple approval gate.
    """

    def __init__(self, llm_client):
        self.llm = llm_client

    async def handle(
        self,
        user_id: str,
        user_message: str,
        ctx_text: str,
    ) -> Dict[str, Any]:
        lower = user_message.lower()
        new_state: Dict[str, Any] = {}

        # Very simple parsing for demo purposes
        if "lights" in lower and "off" in lower:
            new_state["lights"] = "off"
        elif "lights" in lower and "on" in lower:
            new_state["lights"] = "on"

        if "lock" in lower and "door" in lower:
            new_state["doors_locked"] = "locked"
        if "unlock" in lower and "door" in lower:
            new_state["doors_locked"] = "unlocked"

        approved = True
        if new_state:
            # For sensitive actions, ask human.approve (stubbed)
            approved = TOOL_REGISTRY["human.approve"](
                f"Update home state for user {user_id} to {new_state}"
            )
            if approved:
                set_home_state(user_id, new_state)

        state = get_home_state(user_id)

        prompt = f"""
{SENTINEL_BASE}

Previous context:
{ctx_text}

User request:
{user_message}

Action approval: {approved}
Resulting (simulated) home state:
{state}

Explain briefly what you did and what the state is now.
""".strip()

        narrative = await self.llm.generate(prompt)

        return {
            "state": state,
            "approved": approved,
            "narrative": narrative,
        }
