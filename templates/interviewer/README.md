# Interviewer template

Conduct a structured Q&A (intake form, retrospective, decision log) and produce a markdown output file.

## Status

**Blocked** on the `FormFlow` primitive. See `STATUS.md`.

## What it will do

- Load a question schema (YAML) declaring the questions, validation, optional follow-ups, and output template.
- Python drives the question sequence; the model renders the current question warmly and the user's answer is captured to disk.
- At completion, write a structured markdown file with all answers.

## Why this template is the kit's deterministic-harness showcase

Small local models lose the thread on multi-step interactions. The interview loop is fully deterministic — Python knows which question is current, which answers have been captured, when the interview is done. The model is called only inside two bounded steps: render the question, optionally ask a follow-up.

This is the same architecture as `lak init`. The template doubles as a template for that pattern.

## Run it (after unblock)

```bash
lak bot templates/interviewer
```

## Eval

Cases test: model asks one question at a time, does not editorialize on answers, does not invent questions outside the schema, signals completion correctly.
