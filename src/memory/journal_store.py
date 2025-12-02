from __future__ import annotations

from typing import List, Dict, Any
from datetime import datetime
import uuid
import json
import sqlite3

from src.memory.db import with_connection


def save_entry(user_id: str, raw_text: str, summary: str, tags: list[str]) -> str:
    """
    Save a diary/journal entry for a user into SQLite.

    Schema (journal_entries):
    - id TEXT PRIMARY KEY
    - user_id TEXT
    - timestamp TEXT (ISO)
    - raw_text TEXT
    - summary TEXT
    - tags TEXT (JSON-encoded list)
    - created_at TEXT (ISO)
    """
    entry_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    created_at = timestamp
    tags_json = json.dumps(tags)

    def _insert(conn: sqlite3.Connection):
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO journal_entries (
                id, user_id, timestamp, raw_text, summary, tags, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (entry_id, user_id, timestamp, raw_text, summary, tags_json, created_at),
        )
        conn.commit()

    with_connection(_insert)
    return entry_id


def _row_to_entry(row: sqlite3.Row) -> Dict[str, Any]:
    """
    Convert a SQLite row to a dict that matches the previous in-memory format.
    """
    tags = []
    if row["tags"]:
        try:
            tags = json.loads(row["tags"])
        except Exception:
            tags = []

    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "timestamp": row["timestamp"],
        "raw_text": row["raw_text"],
        "summary": row["summary"],
        "tags": tags,
    }


def get_recent_entries(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Return the most recent `limit` entries for a user, newest first.
    """

    def _query(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, user_id, timestamp, raw_text, summary, tags
            FROM journal_entries
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?;
            """,
            (user_id, limit),
        )
        rows = cur.fetchall()
        return [_row_to_entry(r) for r in rows]

    return with_connection(_query)


def search_entries(
    user_id: str,
    query: str,
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    """
    Simple keyword search over summary + raw_text using LIKE.

    v1: not semantic; good enough to demo a "RAG-like" memory tool.
    Later you can replace this with a vector search / embeddings.
    """

    pattern = f"%{query.lower()}%"

    def _query(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, user_id, timestamp, raw_text, summary, tags
            FROM journal_entries
            WHERE user_id = ?
              AND LOWER(summary || ' ' || raw_text) LIKE ?
            ORDER BY timestamp DESC
            LIMIT ?;
            """,
            (user_id, pattern, top_k),
        )
        rows = cur.fetchall()
        return [_row_to_entry(r) for r in rows]

    return with_connection(_query)
