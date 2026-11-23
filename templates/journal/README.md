# Journal template

A reflective companion that asks good questions and stays out of the way. Fully local, never touches the network.

## Status

**Blocked** on the memory track + a privacy audit. See `STATUS.md`.

The template files (IDENTITY, eval cases) are ready. Without persistent memory, the journal is single-session; the audit must verify nothing escapes the local machine.

## What it will do

- Listen across sessions (persistent local memory).
- Ask one short question at a time.
- Stay quiet when the user is writing.
- Never analyze, diagnose, or advise unless asked.

## Privacy posture

This template is the kit's strongest privacy story. Acceptance criteria for shipping include:
- Zero network calls during a session (verified by an audit script).
- All persistence is local, encrypted at rest.
- No log of journal content beyond what the user explicitly opts into.
- A "what touches disk" page in the docs, honest and complete.

## Run it (after unblock)

```bash
lak bot templates/journal
```

## Eval

Cases test the IDENTITY rules: does the model ask instead of tell, stay quiet when appropriate, avoid clinical language, refuse unprompted analysis.
