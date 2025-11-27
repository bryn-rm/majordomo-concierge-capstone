"""
Human-in-the-loop approval tool.

v1: always 'approves' the action.
Later this can be wired to a real UI confirmation.
"""


def request_approval(action_description: str) -> bool:
    """
    Ask for approval for a sensitive action.

    v1: Just log/describe the action and return True.
    """
    # In a real system, you'd send this to a UI or notification.
    print(f"[HITL] Requesting approval for action: {action_description}")
    return True
