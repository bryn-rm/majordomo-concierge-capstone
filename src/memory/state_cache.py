from typing import Dict, Any

# Per-user simulated smart home state
_STATE: dict[str, Dict[str, Any]] = {}


def get_home_state(user_id: str) -> Dict[str, Any]:
    """
    Return current simulated home state for a user.
    """
    return _STATE.get(
        user_id,
        {
            "lights": "unknown",
            "doors_locked": "unknown",
        },
    )


def set_home_state(user_id: str, new_state: Dict[str, Any]) -> None:
    """
    Merge in an update to the home state.
    """
    current = get_home_state(user_id)
    current.update(new_state)
    _STATE[user_id] = current
