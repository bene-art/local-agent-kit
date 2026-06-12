# STATUS — interviewer

**State:** blocked
**Blocker:** `FormFlow` primitive — a Python-driven form/interview state machine. Loads a YAML schema (questions, validation, follow-ups, output template), tracks current step, captures answers, writes a structured output file at completion.
**Owner:** kit
**Unblock condition:** `FormFlow` ships in `src/local_agent_kit/patterns/form_flow.py`. May share implementation with `StateFlow` (used by `study_buddy`).

## What is built
- `agent.yaml`, `identity/IDENTITY.md`, `README.md`, eval cases.
- IDENTITY enforces one-question-at-a-time and no-editorializing rules.

## What is NOT built
- `FormFlow` primitive.
- Schema parsing (YAML format for declaring questions).
- Output template rendering (turn captured answers into a structured markdown file).

## Acceptance criteria for unblock
- A `schema.yaml` with 5 questions can be loaded and `lak bot templates/interviewer` walks through them.
- Eval suite passes against `gemma4:e4b` on "one question at a time" and "no editorializing" cases.
- A completed interview writes a valid markdown file with all answers captured.
- The kit can detect when the user goes off-topic and gracefully redirect without breaking the flow.
