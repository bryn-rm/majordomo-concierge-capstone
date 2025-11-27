from typing import Dict, Any


def get_user_profile(user_id: str) -> Dict[str, Any]:
    """
    Long-term semantic profile for a user.

    v1: very simple, hard-coded stub.
    Later you can persist this to a DB or file.
    """
    return {
        "user_id": user_id,
        "summary": (
            f"User '{user_id}' is in the UK timezone and prefers concise, "
            "practical answers with clear steps."
        ),
    }
