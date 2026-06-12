# STATUS — code_qa

**State:** blocked
**Blocker:** `file_read` tool (owned by the tools track).
**Owner:** tools track
**Unblock condition:** `file_read` ships as a kit tool with a sandboxed allowlist; agent.yaml `tools.file_read: true` becomes active.

## What is built
- `agent.yaml`, `identity/IDENTITY.md`, `README.md`, eval cases.
- Identity describes both inline-paste mode and file-read mode.

## What is NOT built
- The `file_read` tool itself (lives in the tools track).
- Path-allowlist enforcement (must be configurable per-agent for safety).

## Acceptance criteria for unblock
- `lak bot templates/code_qa` can read user-allowed paths via `file_read`.
- Eval suite passes against `gemma4:e4b` on the "explain a small file" and "write a regex" cases.
- "Refuse to invent API signatures" case has a high pass rate (>80%); if not, this is the trigger condition for the `ModelRouter` decision to escalate hard coding turns to a larger local model.
