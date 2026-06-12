# STATUS — study_buddy

**State:** blocked
**Blockers:**
  1. Memory track — needs persistent storage of source material across sessions.
  2. `StateFlow` primitive — Python-driven multi-step interaction (current step, expected output, transitions). Powers the quiz loop. Also used by `interviewer` template.
**Owner:** memory track + kit
**Unblock condition:** memory layer supports loading + querying a user-supplied source; `StateFlow` ships in `src/local_agent_kit/patterns/state_flow.py`.

## What is built
- `agent.yaml`, `identity/IDENTITY.md`, `README.md`, eval cases.
- IDENTITY enforces one-question-at-a-time and grounded-in-material rules.

## What is NOT built
- The `StateFlow` primitive.
- The memory-track integration that loads source material into [SYSTEM DATA].

## Acceptance criteria for unblock
- `lak bot templates/study_buddy` can ingest a source file and quiz from it.
- Eval suite passes against `gemma4:e4b` on "one question at a time" and "grading is short" cases.
- A 10-question quiz run completes without the model losing track (multi-turn coherence check — the trigger threshold for whether `gemma4:e4b` carries the state-machine load or whether `ModelRouter` escalation is needed for this template).
