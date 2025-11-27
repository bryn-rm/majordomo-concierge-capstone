from typing import Dict, Any, Literal

from .profile_store import get_user_profile
from .journal_store import get_recent_entries, search_entries
from .state_cache import get_home_state

IntentType = Literal["knowledge", "diary_capture", "diary_reflection", "smart_home"]


def get_dynamic_context(
    user_id: str,
    intent: IntentType,
    query: str | None = None,
) -> Dict[str, Any]:
    """
    Central facade to gather relevant memory for a request.

    Returns a structured dict:
    {
      "profile": {...},
      "recent_journal": [...],
      "journal_search_results": [...],
      "home_state": {...},
    }
    """
    ctx: Dict[str, Any] = {
        "profile": get_user_profile(user_id),
    }

    if intent in ("diary_capture", "diary_reflection"):
        ctx["recent_journal"] = get_recent_entries(user_id)
        if intent == "diary_reflection" and query:
            ctx["journal_search_results"] = search_entries(user_id, query=query)

    if intent == "smart_home":
        ctx["home_state"] = get_home_state(user_id)

    return ctx
