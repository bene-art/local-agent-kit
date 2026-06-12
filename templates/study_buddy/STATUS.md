# STATUS — study_buddy

**State:** ready
**Last verified:** 2026-06-12

## What ships
- `agent.yaml`, `identity/IDENTITY.md`, `README.md`, eval cases.
- IDENTITY enforces one-question-at-a-time, short grades, grounded
  explanations.
- `run_study.py` — runner with two modes in one session:
    - **Explain** (default): user asks → source material injected as
      `[SYSTEM DATA]` → agent answers grounded in that source.
    - **Quiz**: user types `quiz` → runner loads a `StateFlow` schema,
      walks the user through questions one at a time, agent grades each
      answer in one short phrase, full transcript written to markdown
      at the end.
- Example source material (`sources/photosynthesis.md`) and quiz
  schema (`quizzes/photosynthesis.yaml`).
- Uses the StateFlow primitive (`local_agent_kit.patterns.StateFlow`)
  for the quiz loop and `narrate_only.envelope()` for source injection.

## Run it

```bash
python -m templates.study_buddy.run_study \
    --agent-dir templates/study_buddy \
    --source   templates/study_buddy/sources/photosynthesis.md \
    --quiz     templates/study_buddy/quizzes/photosynthesis.yaml
```

Then:

- Default mode — ask questions about the source.
- Type `quiz` — start a quiz; one question at a time.
- Type `quit` — exit.

Quiz transcripts (Q + your answer + agent's grade) get written to
`./quiz-YYYYMMDD-HHMMSS.md` in the output directory.

## Customize

Drop your own source file (markdown or text) — it's loaded once and
injected on every explain turn. Write your own quiz schema using the
same shape as `quizzes/photosynthesis.yaml` (a list of `{id, prompt}`
steps; `follow_up:` and `next:` are optional).

## Cross-session quiz progress

`run_study.py` writes a `QuizProgress` SQLite file (default
`./study_progress.db`) that tracks per-(quiz_id, step_id):

- `correct_count` / `wrong_count` lifetime
- `last_seen` timestamp
- `last_grade` (correct | wrong)

At quiz start, steps are reordered:

1. **Never-seen** questions first (tier 0).
2. **Last graded wrong** next (tier 1).
3. **Last graded correct** last (tier 2).

Stable within each tier so the schema's authored order is preserved
when nothing distinguishes steps. Each quiz session ends with a
lifetime score readout across all sessions.

Grading is parsed from the agent's response — the IDENTITY says graders
start with "Correct." or "Not quite." — so the heuristic is reliable
within the template's contract.

Pass `--progress-db ''` to disable cross-session tracking and run
quiz mode purely stateless.

## Notes
- `think: false` is set in `agent.yaml` because the IDENTITY caps
  explanations at two-or-three sentences; the reasoning phase would
  eat the token budget otherwise (same architecture as briefer).
