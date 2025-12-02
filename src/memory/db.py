from __future__ import annotations

import os
import sqlite3
from typing import Callable, Any

# Path to SQLite DB file (relative to project root)
DB_PATH = os.path.join("data", "memory.db")


def get_connection() -> sqlite3.Connection:
    """
    Return a SQLite connection and ensure required tables exist.

    This is a simple, single-process setup:
    - Called per-operation.
    - Uses WAL mode for basic concurrency safety (optional).
    """
    first_time = not os.path.exists(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if first_time:
        _initialize_schema(conn)

    return conn


def _initialize_schema(conn: sqlite3.Connection) -> None:
    """
    Create tables if they do not exist.
    """
    cur = conn.cursor()

    # Journal entries: RAG-ready schema
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS journal_entries (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            raw_text TEXT NOT NULL,
            summary TEXT NOT NULL,
            tags TEXT,
            -- later: embedding BLOB or vector store key
            created_at TEXT NOT NULL
        );
        """
    )

    # You can add more tables later (e.g. home_state) using similar patterns.

    conn.commit()


def with_connection(fn: Callable[[sqlite3.Connection], Any]) -> Any:
    """
    Helper to run a callback with a connection.

    Example:
        def do_something(conn):
            ...

        result = with_connection(do_something)
    """
    conn = get_connection()
    try:
        return fn(conn)
    finally:
        conn.close()
