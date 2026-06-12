"""Tools — sandboxed primitives the kit exposes to templates.

Each tool is a small async function returning a string. Errors are
returned as bracketed envelopes (e.g. `"[file not found: ...]"`) so the
model can read them like any other data block. The Agent never crashes
on a tool error — it surfaces the envelope.

Current tools:
    file_read   — read a file from a configured allowlist.
    list_files  — list a directory in the allowlist.
    data_query  — run a SELECT against a CSV/JSONL file loaded into
                  an in-memory SQLite table.

Conventions (matched from patrick-agent's tool suite):
    - async def tool_name(args, *, config_keyword_args) -> str
    - returns content on success
    - returns "[error: details]" on every failure (no exceptions across the seam)
    - hardcodes a universal blocklist for obvious-secret name patterns
    - takes config as keyword arguments — the kit's Agent passes them from agent.yaml
"""
from local_agent_kit.tools.data_query import data_query
from local_agent_kit.tools.file_read import file_read, list_files

__all__ = ["data_query", "file_read", "list_files"]
