"""QuizProgress — cross-session per-question score tracking.

Companion to `SQLiteMemory`. Where SQLiteMemory is append-only (chat
history), QuizProgress is key-update — per (quiz_id, step_id) it holds
the latest counts and timestamps, not every grading event.

Use case: study_buddy quiz mode. At quiz start the runner asks
`order_steps()` to put never-seen and recently-wrong questions first,
so each session focuses on weak spots.

Stdlib only. One SQLite file per agent (caller chooses the path).
"""
from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


class QuizProgress:
    """Per-question score tracking, keyed by (quiz_id, step_id)."""

    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(str(self.db_path), timeout=5)

    def _ensure_schema(self) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS quiz_progress (
                    quiz_id TEXT NOT NULL,
                    step_id TEXT NOT NULL,
                    correct_count INTEGER NOT NULL DEFAULT 0,
                    wrong_count INTEGER NOT NULL DEFAULT 0,
                    last_seen TEXT,
                    last_grade TEXT,
                    PRIMARY KEY (quiz_id, step_id)
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def record(self, quiz_id: str, step_id: str, *, correct: bool) -> None:
        """Increment the correct/wrong counter for (quiz_id, step_id)."""
        now = datetime.now(timezone.utc).isoformat()
        grade = "correct" if correct else "wrong"
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO quiz_progress (quiz_id, step_id, correct_count, wrong_count, last_seen, last_grade)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(quiz_id, step_id) DO UPDATE SET
                    correct_count = correct_count + excluded.correct_count,
                    wrong_count = wrong_count + excluded.wrong_count,
                    last_seen = excluded.last_seen,
                    last_grade = excluded.last_grade
                """,
                (
                    quiz_id,
                    step_id,
                    1 if correct else 0,
                    0 if correct else 1,
                    now,
                    grade,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def stats(self, quiz_id: str) -> dict[str, dict[str, object]]:
        """Per-step stats for a quiz."""
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT step_id, correct_count, wrong_count, last_seen, last_grade "
                "FROM quiz_progress WHERE quiz_id = ?",
                (quiz_id,),
            ).fetchall()
        finally:
            conn.close()
        return {
            r[0]: {
                "correct_count": r[1],
                "wrong_count": r[2],
                "last_seen": r[3],
                "last_grade": r[4],
            }
            for r in rows
        }

    def order_steps(self, quiz_id: str, step_ids: list[str]) -> list[str]:
        """Reorder a list of step_ids by priority.

        Priority (lowest = first):
            0  never-seen
            1  last graded wrong
            2  last graded correct, but seen at least once

        Stable within each tier — preserves the caller's input order so
        a deterministic quiz schema produces deterministic ordering when
        all steps share a tier.
        """
        stats = self.stats(quiz_id)

        def tier(sid: str) -> int:
            if sid not in stats:
                return 0
            return 1 if stats[sid].get("last_grade") == "wrong" else 2

        return sorted(step_ids, key=lambda sid: (tier(sid), step_ids.index(sid)))
