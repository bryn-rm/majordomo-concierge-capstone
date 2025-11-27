from typing import Dict, Any


def format_dynamic_context(ctx: Dict[str, Any]) -> str:
    """
    Turn structured memory context into a compact text block
    that can be prefixed into prompts.

    Expected keys in ctx:
    - "profile"
    - "recent_journal"
    - "journal_search_results"
    - "home_state"
    """
    parts: list[str] = []

    profile = ctx.get("profile")
    if profile:
        parts.append("USER PROFILE:\n" + profile.get("summary", ""))

    recent_journal = ctx.get("recent_journal") or []
    if recent_journal:
        snippets = [
            f"- {e['timestamp']}: {e['summary']}"
            for e in recent_journal[:5]
        ]
        parts.append("RECENT JOURNAL ENTRIES:\n" + "\n".join(snippets))

    journal_search = ctx.get("journal_search_results") or []
    if journal_search:
        snippets = [
            f"- {e['timestamp']}: {e['summary']}"
            for e in journal_search[:5]
        ]
        parts.append(
            "JOURNAL ENTRIES RELEVANT TO THIS REQUEST:\n" + "\n".join(snippets)
        )

    home_state = ctx.get("home_state")
    if home_state:
        parts.append("HOME STATE SNAPSHOT:\n" + str(home_state))

    return "\n\n".join(parts) if parts else ""
