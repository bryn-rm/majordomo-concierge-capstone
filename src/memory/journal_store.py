from typing import List, Dict, Any
from datetime import datetime
import uuid

# In-memory storage for now. You can swap this for SQLite / vector DB later.
_STORE: dict[str, List[Dict[str, Any]]] = {}


def save_entry(user_id: str, raw_text: str, summary: str, tags: list[str]) -> str:
    """
    Save a diary/journal entry for a user.
    """
    entry_id = str(uuid.uuid4())
    entry = {
        "id": entry_id,
        "timestamp": datetime.utcnow().isoformat(),
        "raw_text": raw_text,
        "summary": summary,
        "tags": tags,
    }
    _STORE.setdefault(user_id, []).append(entry)
    return entry_id


def get_recent_entries(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Return the most recent `limit` entries for a user, newest first.
    """
    entries = _STORE.get(user_id, [])
    return sorted(entries, key=lambda e: e["timestamp"], reverse=True)[:limit]


def search_entries(user_id: str, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Very simple keyword search over summary + raw_text.
    v1: not semantic; good enough to demo the flow.
    """
    entries = _STORE.get(user_id, [])
    q = query.lower()
    matches: List[Dict[str, Any]] = []

    for e in entries:
        text = (e["summary"] + " " + e["raw_text"]).lower()
        if q in text:
            matches.append(e)

    return matches[:top_k]
