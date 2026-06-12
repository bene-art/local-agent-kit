"""Memory — cross-session persistence for kit agents.

Templates with multi-session needs (journal, study_buddy) compose a
Memory implementation into their runner. The kit ships one default:
SQLiteMemory — small, local-only, no external deps. Other backends can
implement the Memory Protocol.

Conventions matched from patrick-agent's `conversation_memory.py`:
    - Per-thread storage keyed by `thread_id` (channel-defined).
    - Append a single (role, content) row at a time.
    - history() returns the last N rows oldest-first, as [{role, content}, ...].
    - Old entries are pruned per-thread to a max window (default 20).

This module is intentionally minimal. Encryption-at-rest, retrieval-by-
embedding, and full-text search are out of scope here; templates that
need them ship their own implementations of the Memory Protocol.
"""
from local_agent_kit.memory.base import Memory
from local_agent_kit.memory.quiz_progress import QuizProgress
from local_agent_kit.memory.sqlite_memory import SQLiteMemory

__all__ = ["Memory", "QuizProgress", "SQLiteMemory"]
