from typing import Dict, Any

from src.prompts.system_instructions import SENTINEL_BASE
from src.tools import TOOL_REGISTRY
from src.memory.state_cache import get_home_state as fallback_get_home_state


class SentinelAgent:
    """
    Sentinel agent.

    - Simulated smart home controller.
    - Uses:
        - human.approve   for sensitive actions (HITL)
        - smarthome.set_state / smarthome.get_state tools
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

        # Approval tool (HITL)
        approve_fn = TOOL_REGISTRY.get("human.approve")
        approved = True

        if new_state and approve_fn is not None:
            approved = approve_fn(
                f"Update smart home state for user {user_id} with {new_state}"
            )

        # Smart home tool calls
        smarthome_set = TOOL_REGISTRY.get("smarthome.set_state")
        smarthome_get = TOOL_REGISTRY.get("smarthome.get_state")

        state: Dict[str, Any]

        if new_state and approved and smarthome_set is not None:
            try:
                # Call the MCP-style tool
                state = await smarthome_set(user_id=user_id, partial_state=new_state)  # type: ignore[call-arg]
            except Exception:
                # Fallback to whatever is in the local cache
                state = fallback_get_home_state(user_id)
        else:
            # No update requested or not approved: just read current state
            if smarthome_get is not None:
                try:
                    state = await smarthome_get(user_id=user_id)  # type: ignore[call-arg]
                except Exception:
                    state = fallback_get_home_state(user_id)
            else:
                state = fallback_get_home_state(user_id)

        prompt = f"""
{SENTINEL_BASE}

Previous context:
{ctx_text}

User request:
{user_message}

Action approval: {approved}
Resulting (simulated) home state:
{state}

Explain briefly what you did (if anything) and what the state is now.
""".strip()

        narrative = await self.llm.generate(prompt)

        return {
            "state": state,
            "approved": approved,
            "narrative": narrative,
        }
