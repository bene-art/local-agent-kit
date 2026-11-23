"""Memory Protocol — the contract every memory backend implements."""
from __future__ import annotations

from typing import Protocol


class Memory(Protocol):
    """Cross-session memory backend contract.

    Implementations:
        SQLiteMemory   — local SQLite file, default for the kit.
        (future)       — encrypted, FTS-indexed, or external store
                         backends can implement this protocol.

    Thread keying: implementations key all rows by a caller-supplied
    `thread_id` string. Channels are responsible for choosing a stable
    thread identifier (CLI may use a fixed value; a chat channel would
    use its conversation id).
    """

    def append(self, thread_id: str, role: str, content: str) -> None:
        """Append one (role, content) row under the given thread."""

    def history(self, thread_id: str, limit: int = 20) -> list[dict[str, str]]:
        """Return up to `limit` recent rows oldest-first as [{role, content}, ...]."""

    def count(self, thread_id: str) -> int:
        """Total rows currently stored for the thread."""
