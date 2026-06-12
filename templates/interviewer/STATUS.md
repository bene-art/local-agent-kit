# STATUS — interviewer

**State:** ready
**Last verified:** 2026-06-12

## What ships
- `agent.yaml`, `identity/IDENTITY.md`, `README.md`.
- `schema.yaml` — example interview schema (project retrospective) using
  every StateFlow feature (capture toggle, follow-up prompts, linear flow).
- `run_interview.py` — driver that loads the schema, walks the flow,
  has the agent phrase each question warmly, captures user input, and
  writes a structured markdown output file at completion.
- Eval suite passes against `gemma4:e4b` on the IDENTITY rules
  (one-question-at-a-time, no editorializing).
- StateFlow primitive (`local_agent_kit.patterns.StateFlow`) with 12 tests.

## Run it

```bash
python -m templates.interviewer.run_interview \
    --agent-dir templates/interviewer \
    --schema  templates/interviewer/schema.yaml
```

Output goes to `./interview-YYYYMMDD-HHMMSS.md` by default.

## Customize

Swap `schema.yaml` for your own — see the file's inline comments. Any
list of `{id, prompt}` works; optional `capture`, `follow_up`, and `next`
fields enable richer flows.
