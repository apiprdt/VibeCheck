"""SQLite-based concept memory system.

Tracks which concepts the developer has learned so explanations
can be progressively shortened: full → reminder → skipped.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_DIR = Path.home() / ".vibecheck"
DB_PATH = DB_DIR / "knowledge.db"


def _get_connection() -> sqlite3.Connection:
    """Get a connection to the knowledge database."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the learned_concepts table if it doesn't exist."""
    conn = _get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS learned_concepts (
                concept_name TEXT PRIMARY KEY,
                first_seen   TEXT NOT NULL,
                times_seen   INTEGER DEFAULT 1,
                last_file    TEXT
            )
        """)
        conn.commit()
    finally:
        conn.close()


def get_concept(name: str) -> dict | None:
    """Look up a single concept by name.

    Returns:
        Dict with concept data, or None if not found.
    """
    init_db()
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM learned_concepts WHERE concept_name = ?",
            (name,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def record_concept(name: str, file_path: str) -> str:
    """Record that a concept was encountered. Returns its status.

    Returns:
        "new" — concept was just inserted (first time ever)
        "reminder" — concept seen once before, now bumped to 2
        "learned" — concept already seen 2+ times
    """
    init_db()
    conn = _get_connection()
    try:
        existing = conn.execute(
            "SELECT times_seen FROM learned_concepts WHERE concept_name = ?",
            (name,),
        ).fetchone()

        now = datetime.now(timezone.utc).isoformat()

        if existing is None:
            conn.execute(
                "INSERT INTO learned_concepts (concept_name, first_seen, times_seen, last_file) "
                "VALUES (?, ?, 1, ?)",
                (name, now, file_path),
            )
            conn.commit()
            return "new"
        else:
            new_count = existing["times_seen"] + 1
            conn.execute(
                "UPDATE learned_concepts SET times_seen = ?, last_file = ? "
                "WHERE concept_name = ?",
                (new_count, file_path, name),
            )
            conn.commit()
            if existing["times_seen"] == 1:
                return "reminder"
            return "learned"
    finally:
        conn.close()


def get_concept_status(name: str) -> str:
    """Get the learning status of a concept without modifying it.

    Returns:
        "new" — never seen before
        "reminder" — seen once
        "learned" — seen 2+ times
    """
    concept = get_concept(name)
    if concept is None:
        return "new"
    if concept["times_seen"] == 1:
        return "reminder"
    return "learned"


def get_all_concepts() -> list[dict]:
    """Get all learned concepts, ordered by times_seen descending."""
    init_db()
    conn = _get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM learned_concepts ORDER BY times_seen DESC"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def reset_memory() -> int:
    """Clear all learned concepts.

    Returns:
        Number of concepts that were deleted.
    """
    init_db()
    conn = _get_connection()
    try:
        count = conn.execute("SELECT COUNT(*) FROM learned_concepts").fetchone()[0]
        conn.execute("DELETE FROM learned_concepts")
        conn.commit()
        return count
    finally:
        conn.close()


def get_memory_context(concepts: list[str]) -> dict[str, str]:
    """Get memory status for a list of concepts.

    Args:
        concepts: List of concept names to check.

    Returns:
        Dict mapping concept_name → status ("new", "reminder", "learned").
    """
    return {concept: get_concept_status(concept) for concept in concepts}
