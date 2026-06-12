# STATUS — analyst

**State:** blocked
**Blockers:**
  1. `file_read` tool (tools track).
  2. `data_query` tool — a new tool that runs Python aggregations on CSV/JSONL files and returns the computed result as text suitable for [SYSTEM DATA] injection.
**Owner:** tools track
**Unblock condition:** both tools ship; `narrate_only.envelope()` is implemented; agent.yaml `tools.{file_read,data_query}: true` becomes active.

## What is built
- `agent.yaml`, `identity/IDENTITY.md`, `README.md`, eval cases.
- IDENTITY enforces the narrate-only contract.

## What is NOT built
- `file_read` (tools track).
- `data_query` — new tool. Takes a file path + a query spec (groupby, agg, filter) and returns a formatted result string.
- `envelope()` in `local_agent_kit.patterns.narrate_only` (interface-only).

## Acceptance criteria for unblock
- `lak bot templates/analyst` can read a CSV and answer "what's the total of column X by category Y" without the model doing arithmetic.
- Eval suite passes against `gemma4:e4b` — every number in the response appears verbatim in [SYSTEM DATA].
- `NarrationRubric.evaluate()` returns True on every eval response.
