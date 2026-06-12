# Code Q&A template

Small-surface coding help — explain a file, suggest a fix, write a regex, answer a syntax question.

## Status

**Blocked** on the tools track — needs `file_read`. See `STATUS.md`.

The template files (IDENTITY, eval cases) are ready. Without `file_read`, the user has to paste code inline; the template still works in that mode, but the eval suite is gated until reading-from-disk lands.

## Run it (after unblock)

```bash
lak bot templates/code_qa
```

## Why this template tests the local-model ceiling

Coding is where small models hit their hardest limits — the eval suite for this template doubles as the input to the future `ModelRouter` decision (escalate from `gemma4:e4b` to a bigger local model on hard turns).

## Eval

Cases test: explain a small file, suggest a fix for a specific bug, write a small regex, answer a syntax question, refuse to invent unknown API signatures.
