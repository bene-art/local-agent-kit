"""data_query — run SELECT queries against a CSV or JSONL file.

Loads a file from the allowlist into an in-memory SQLite table called
`data`, executes the user's SELECT, formats rows as text. Stdlib only
(`sqlite3`, `csv`, `json`) — no new deps.

This is the canonical "Python computes, model narrates" tool: the
aggregation runs in code (deterministic, accurate); the model's job is
only to describe the result.

Query safety: matches patrick-agent/db_query.py — SELECT only, hardcoded
blocklist for DDL/PRAGMA keywords. The same allowlist + blocked-name
pattern as `file_read` applies to the file path itself.

Usage:

    from local_agent_kit.tools.data_query import data_query
    result = await data_query(
        "./sales.csv",
        "SELECT region, SUM(revenue) FROM data GROUP BY region",
        allowed_roots=["./reports"],
    )
"""
from __future__ import annotations

import csv
import json
import logging
import sqlite3
from pathlib import Path

from local_agent_kit.tools.file_read import _is_safe, _resolve_roots

logger = logging.getLogger(__name__)


_BLOCKED_KEYWORDS = {
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE",
    "ATTACH", "DETACH", "PRAGMA", "VACUUM", "REINDEX",
}

DEFAULT_MAX_ROWS = 20


def _is_safe_sql(sql: str) -> bool:
    normalized = sql.strip().upper()
    if not normalized.startswith("SELECT"):
        return False
    return not any(kw in normalized for kw in _BLOCKED_KEYWORDS)


def _load_csv(conn: sqlite3.Connection, path: Path) -> None:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            raise ValueError("CSV is empty")
        columns = [_safe_col(h) for h in headers]
        placeholders = ", ".join("?" for _ in columns)
        col_defs = ", ".join(f'"{c}" TEXT' for c in columns)
        conn.execute(f"CREATE TABLE data ({col_defs})")
        for row in reader:
            if len(row) != len(columns):
                continue
            conn.execute(f"INSERT INTO data VALUES ({placeholders})", row)


def _load_jsonl(conn: sqlite3.Connection, path: Path) -> None:
    # Two-pass: peek the first record to determine columns, then ingest.
    columns: list[str] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if not isinstance(obj, dict):
                raise ValueError("JSONL rows must be JSON objects")
            columns = [_safe_col(k) for k in obj.keys()]
            break
    if not columns:
        raise ValueError("JSONL is empty")
    col_defs = ", ".join(f'"{c}" TEXT' for c in columns)
    placeholders = ", ".join("?" for _ in columns)
    conn.execute(f"CREATE TABLE data ({col_defs})")
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            row = [_stringify(obj.get(c)) for c in columns]
            conn.execute(f"INSERT INTO data VALUES ({placeholders})", row)


def _safe_col(name: str) -> str:
    # SQLite identifiers — strip anything weird so the SQL stays safe to interpolate.
    cleaned = "".join(c if c.isalnum() or c == "_" else "_" for c in name)
    return cleaned or "col"


def _stringify(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    return str(value)


async def data_peek(
    file_path: str,
    *,
    allowed_roots: list[Path | str],
    n_rows: int = 20,
) -> str:
    """Return the first N rows of a CSV/JSONL file as a formatted table.

    A thin wrapper around `data_query` with `SELECT * LIMIT N`. Intended
    for "show me this data" UX: small local models can't reliably author
    aggregation SQL, but they CAN narrate a head sample.
    """
    return await data_query(
        file_path,
        f"SELECT * FROM data LIMIT {n_rows}",
        allowed_roots=allowed_roots,
        max_rows=n_rows,
    )


async def data_query(
    file_path: str,
    sql: str,
    *,
    allowed_roots: list[Path | str],
    max_rows: int = DEFAULT_MAX_ROWS,
) -> str:
    """Load `file_path` (CSV or JSONL) into a SQLite table named `data`,
    run `sql`, return formatted rows.

    Args:
        file_path: Path to a CSV or JSONL file (~ expanded).
        sql: A SELECT query. Must reference table name `data`.
        allowed_roots: Directories the tool may read from.
        max_rows: Cap on rows returned.

    Returns:
        Formatted table on success, or a bracketed error envelope.
    """
    if not allowed_roots:
        return "[data_query disabled: no allowed_roots configured]"

    roots = _resolve_roots(allowed_roots)
    target = Path(file_path).expanduser()

    if not target.exists():
        return f"[file not found: {file_path}]"
    if not _is_safe(target, roots):
        return f"[access denied: {file_path} is outside allowed_roots]"
    if not _is_safe_sql(sql):
        return "[query blocked — SELECT only, no DDL/PRAGMA]"

    suffix = target.suffix.lower()
    if suffix not in {".csv", ".jsonl", ".json"}:
        return f"[unsupported file type: {suffix} — use .csv or .jsonl]"

    try:
        conn = sqlite3.connect(":memory:")
        conn.execute("PRAGMA query_only = OFF")  # we INSERT during load
        if suffix == ".csv":
            _load_csv(conn, target)
        else:
            _load_jsonl(conn, target)
        conn.execute("PRAGMA query_only = ON")
        cursor = conn.execute(sql)
        columns = [d[0] for d in cursor.description] if cursor.description else []
        rows = cursor.fetchmany(max_rows)
        conn.close()
    except Exception as exc:
        logger.warning("data_query failed: %s", exc)
        return f"[data_query error: {exc}]"

    if not rows:
        return "[no results]"

    header = " | ".join(columns)
    lines = [header, "-" * len(header)]
    for row in rows:
        lines.append(" | ".join(_stringify(v) for v in row))
    if len(rows) == max_rows:
        lines.append(f"... (capped at {max_rows} rows)")
    return "\n".join(lines)
