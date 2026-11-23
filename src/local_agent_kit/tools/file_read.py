"""file_read — sandboxed file reader for kit agents.

Read-only access to files within an explicit allowlist. Universal name-
pattern blocklist (api_key, secret, token, .env, ...) is applied on top.
Output is capped to prevent context blowout.

Pattern matched from patrick-agent's `file_read.py`. Adapted for the kit:
    - allowed_roots passed as a keyword arg (no hardcoded paths)
    - returns the same "[error envelope]" string format on every failure
    - both file_read and list_files share the same allowlist logic

Direct usage:

    from local_agent_kit.tools.file_read import file_read
    contents = await file_read("~/notes/today.md", allowed_roots=["~/notes"])

Agent integration — paths mentioned in user messages are auto-injected
when roots are configured in agent.yaml:

    tools:
      file_read:
        roots: [~/notes, ./docs]
        max_chars: 3000
"""
from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path

logger = logging.getLogger(__name__)


# Universal name-pattern blocklist — never returned regardless of allowlist.
# Match patrick-agent's set so the two stay aligned.
_BLOCKED_PATTERNS = {
    "api_key",
    "secret",
    "credential",
    "token",
    ".env",
    "password",
    "auth.yaml",
}

DEFAULT_MAX_CHARS = 3000


def _resolve_roots(roots: Sequence[Path | str]) -> list[Path]:
    return [Path(r).expanduser().resolve() for r in roots]


def _is_safe(path: Path, allowed_roots: list[Path]) -> bool:
    """True if path resolves under one of allowed_roots AND its name isn't blocked."""
    resolved = path.resolve()

    name_lower = resolved.name.lower()
    if any(b in name_lower for b in _BLOCKED_PATTERNS):
        return False

    for root in allowed_roots:
        if resolved == root:
            return True
        # Compare path components, not raw string prefix — avoids
        # /foo matching /foobar by accident.
        try:
            resolved.relative_to(root)
            return True
        except ValueError:
            continue
    return False


async def file_read(
    path: str,
    *,
    allowed_roots: Sequence[Path | str],
    max_chars: int = DEFAULT_MAX_CHARS,
) -> str:
    """Read a file from an allowed location.

    Args:
        path: File path (relative or absolute; ~ is expanded).
        allowed_roots: Directories the tool may read from. An empty list
            disables the tool entirely.
        max_chars: Truncate file content at this size. Default 3000.

    Returns:
        File content (capped) on success, or a bracketed error envelope.
    """
    if not allowed_roots:
        return "[file_read disabled: no allowed_roots configured]"

    roots = _resolve_roots(allowed_roots)
    target = Path(path).expanduser()

    if not target.exists():
        return f"[file not found: {path}]"

    if not _is_safe(target, roots):
        return f"[access denied: {path} is outside allowed_roots]"

    try:
        content = target.read_text(errors="replace")
    except Exception as exc:
        logger.warning("file_read failed: %s", exc)
        return f"[file read error: {exc}]"

    if len(content) > max_chars:
        content = content[:max_chars] + f"\n\n... (truncated at {max_chars} chars)"

    logger.info("file_read: path=%s, chars=%d", target.resolve(), len(content))
    return content


async def list_files(
    directory: str,
    *,
    allowed_roots: Sequence[Path | str],
    max_entries: int = 20,
) -> str:
    """List files in an allowed directory, most-recent first.

    Args:
        directory: Directory path (~ is expanded).
        allowed_roots: Directories the tool may list. Same allowlist as file_read.
        max_entries: Cap the visible listing.

    Returns:
        Newline-separated file names, or a bracketed error envelope.
    """
    if not allowed_roots:
        return "[list_files disabled: no allowed_roots configured]"

    roots = _resolve_roots(allowed_roots)
    target = Path(directory).expanduser()

    if not target.is_dir():
        return f"[directory not found: {directory}]"
    if not _is_safe(target, roots):
        return f"[access denied: {directory} is outside allowed_roots]"

    try:
        entries = sorted(target.iterdir(), key=lambda f: f.stat().st_mtime, reverse=True)
    except Exception as exc:
        return f"[list error: {exc}]"

    lines = [f.name for f in entries[:max_entries]]
    if len(entries) > max_entries:
        lines.append(f"... ({len(entries)} total)")
    return "\n".join(lines)
