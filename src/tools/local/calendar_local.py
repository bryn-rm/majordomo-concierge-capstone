# src/tools/local/calendar_local.py

from __future__ import annotations

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid

# Simple in-memory calendar storage keyed by user_id
_CALENDAR_STORE: dict[str, List[Dict[str, Any]]] = {}


def add_event(
    user_id: str,
    title: str,
    start_iso: str,
    end_iso: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Add a calendar event for the given user (local simulated calendar).

    Args:
        user_id: logical user id
        title: event summary/title
        start_iso: ISO8601 start time (e.g. "2025-12-02T18:00:00")
        end_iso: ISO8601 end time or None
        metadata: arbitrary extra info (location, source, tags, etc.)

    Returns:
        event_id (str)
    """
    event_id = str(uuid.uuid4())
    event = {
        "id": event_id,
        "user_id": user_id,
        "title": title,
        "start": start_iso,
        "end": end_iso,
        "metadata": metadata or {},
    }
    _CALENDAR_STORE.setdefault(user_id, []).append(event)
    return event_id


def list_upcoming_events(
    user_id: str,
    now_iso: Optional[str] = None,
    horizon_days: int = 7,
    max_events: int = 10,
) -> List[Dict[str, Any]]:
    """
    List upcoming events for a user in the next `horizon_days`.

    This is a local, in-memory implementation used for testing/demo.
    """
    events = _CALENDAR_STORE.get(user_id, [])
    if not events:
        return []

    if now_iso is None:
        now = datetime.utcnow()
    else:
        now = datetime.fromisoformat(now_iso)

    horizon = now + timedelta(days=horizon_days)

    def parse_start(ev: Dict[str, Any]) -> datetime:
        try:
            return datetime.fromisoformat(ev["start"])
        except Exception:
            return now

    upcoming = [
        ev for ev in events
        if now <= parse_start(ev) <= horizon
    ]

    upcoming_sorted = sorted(upcoming, key=parse_start)
    return upcoming_sorted[:max_events]
