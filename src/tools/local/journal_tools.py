# src/tools/local/journal_tools.py

from typing import List, Dict, Any

from src.memory.journal_store import get_recent_entries, search_entries


def recent_journal_entries(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Tool wrapper: get the most recent journal entries for a user.
    """
    return get_recent_entries(user_id=user_id, limit=limit)


def search_journal_entries(
    user_id: str,
    query: str,
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    """
    Tool wrapper: keyword search over the user's journal entries.
    """
    return search_entries(user_id=user_id, query=query, top_k=top_k)
