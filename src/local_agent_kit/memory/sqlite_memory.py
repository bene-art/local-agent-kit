"""SQLiteMemory — the kit's default cross-session memory backend.

Pattern matched from patrick-agent's `conversation_memory.py`. Adapted:
    - Per-agent SQLite file (caller supplies the path) instead of a
      hardcoded ~/.patrick-agent location.
    - append(role, content) primitive, with add_exchange() as a
      conversation-style sugar that calls append twice.
    - Per-thread pruning to a configurable max_history window.

No third-party deps. Schema is created on first use.
"""
from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_MAX_HISTORY = 20
_MAX_CONTENT_CHARS = 4000     # soft cap per row to avoid runaway storage


class SQLiteMemory:
    """Local SQLite-backed memory, one DB file per agent."""

    def __init__(self, db_path: Path | str, max_history: int = DEFAULT_MAX_HISTORY):
        self.db_path = Path(db_path)
        self.max_history = max_history
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(str(self.db_path), timeout=5)

    def _ensure_schema(self) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    ts TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_thread_ts ON messages (thread_id, ts DESC)"
            )
            conn.commit()
        finally:
            conn.close()

    def append(self, thread_id: str, role: str, content: str) -> None:
        """Append one row under the given thread; prune to max_history."""
        if len(content) > _MAX_CONTENT_CHARS:
            content = content[:_MAX_CONTENT_CHARS] + " ...[truncated]"

        ts = datetime.now(timezone.utc).isoformat()
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO messages (thread_id, role, content, ts) VALUES (?, ?, ?, ?)",
                (thread_id, role, content, ts),
            )
            conn.execute(
                """
                DELETE FROM messages WHERE id NOT IN (
                    SELECT id FROM messages WHERE thread_id = ?
                    ORDER BY ts DESC, id DESC LIMIT ?
                ) AND thread_id = ?
                """,
                (thread_id, self.max_history, thread_id),
            )
            conn.commit()
        finally:
            conn.close()

    def add_exchange(self, thread_id: str, user_msg: str, assistant_msg: str) -> None:
        """Convenience: append a user/assistant pair (the conversation pattern)."""
        self.append(thread_id, "user", user_msg)
        self.append(thread_id, "assistant", assistant_msg)

    def history(self, thread_id: str, limit: int = DEFAULT_MAX_HISTORY) -> list[dict[str, str]]:
        """Return up to `limit` recent rows oldest-first."""
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT role, content FROM messages WHERE thread_id = ? "
                "ORDER BY ts ASC, id ASC LIMIT ?",
                (thread_id, limit),
            ).fetchall()
        finally:
            conn.close()
        return [{"role": r[0], "content": r[1]} for r in rows]

    def count(self, thread_id: str) -> int:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT COUNT(*) FROM messages WHERE thread_id = ?",
                (thread_id,),
            ).fetchone()
        finally:
            conn.close()
        return row[0] if row else 0

    def clear(self, thread_id: str) -> int:
        """Delete all rows for a thread. Returns the count removed."""
        conn = self._connect()
        try:
            cur = conn.execute(
                "DELETE FROM messages WHERE thread_id = ?", (thread_id,)
            )
            conn.commit()
            return cur.rowcount
        finally:
            conn.close()
