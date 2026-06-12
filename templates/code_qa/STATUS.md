# STATUS — code_qa

**State:** ready (basic), partial (file_read integration)
**Last verified:** 2026-06-12

## What ships
- `agent.yaml`, `identity/IDENTITY.md`, `README.md`, eval cases.
- IDENTITY handles both inline-paste mode (works today) and file_read
  mode (the tool exists; auto-injection into `Agent.handle` is not wired).
- The `file_read` tool (`local_agent_kit.tools.file_read`) is shipped
  with a 10-test suite. Path-allowlist, blocklist for secret name
  patterns, output cap.

## What works today

Inline paste — fully functional:

```bash
lak bot templates/code_qa
> Explain what this does:
> def chunks(seq, n): return [seq[i:i+n] for i in range(0, len(seq), n)]
```

## What requires a custom runner

Auto-reading files by path mention ("Explain `./script.py`") is not yet
auto-wired into `Agent.handle`. The tool exists; templates that want
file-by-path support ship their own runner that calls `file_read`
explicitly and injects the result as `[SYSTEM DATA]` before calling
`Agent.handle`. See `templates/interviewer/run_interview.py` for the
equivalent pattern with StateFlow.

## Acceptance criteria still open
- Auto-injection of file_read results when a user message references a
  file path that exists under the allowlist.
- A `runner.py` in this template demonstrating the inject-then-handle pattern.

These belong in a follow-up commit, not in this template's first ship.
