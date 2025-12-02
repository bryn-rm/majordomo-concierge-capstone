from __future__ import annotations

from typing import Dict, Any

from src.memory.state_cache import get_home_state as _get_home_state
from src.memory.state_cache import set_home_state as _set_home_state


async def get_home_state(user_id: str) -> Dict[str, Any]:
    """
    Simulated smart home 'get state' tool.

    In a real deployment this would call an external Home Assistant API.
    Here, it just returns the cached home state for the user.
    """
    return _get_home_state(user_id)


async def set_home_state(user_id: str, partial_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulated smart home 'set state' tool.

    Args:
        user_id: logical user id
        partial_state: e.g. {"lights": "off"} or {"doors_locked": "locked"}

    Behavior:
        - Merges partial_state into the existing home state
        - Returns the updated full state
    """
    _set_home_state(user_id, partial_state)
    return _get_home_state(user_id)
