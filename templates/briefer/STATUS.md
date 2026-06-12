# STATUS — briefer

**State:** partially unblocked (runtime built; wiring + fetcher pending)
**Remaining blockers:**
  1. Agent.run integration — `Agent` doesn't yet call `load_schedules()` or wire a `LocalScheduler` into its main loop.
  2. No example fetcher — briefer needs at least one concrete data source (news headlines is the easy one) to be a meaningful template.
**Owner:** kit
**Unblock condition:** Agent loads the `schedules:` block at boot, starts a `LocalScheduler` that fires the declared tasks through `Agent.handle()`, output goes through `Channel.send()`. One example fetcher ships.

## What is built (2026-06-11)
- `agent.yaml`, `identity/IDENTITY.md`, `README.md`, eval cases.
- `croniter` approved as `[schedule]` optional dependency.
- `LocalScheduler` (asyncio-based, in-process) — `src/local_agent_kit/scheduling/local_scheduler.py`.
- `load_schedules()` parser.
- `narrate_only.envelope()` — the helper that wraps Python-computed strings as `[SYSTEM DATA]` for the model to narrate.

## What is NOT built
- `Agent.run` doesn't auto-start a scheduler from the `schedules:` block.
- No example data fetcher (news / calendar / portfolio) lives in the template.

## Acceptance criteria for full unblock
- `lak bot templates/briefer` runs and fires the declared schedule.
- Eval suite passes against `gemma4:e4b` (no fabrication of numbers — verified by `NarrationRubric`).
- One example fetcher (news headlines, RSS or similar) ships alongside the template.
