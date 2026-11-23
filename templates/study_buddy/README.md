# Study Buddy template

Explain, quiz, and reinforce on supplied source material.

## Status

**Blocked** on the memory track (for source material persistence) and a new `StateFlow` primitive (for quiz state). See `STATUS.md`.

## What it will do

- Load a user-supplied source (chapter, notes, paper) into local memory.
- Explain concepts from that material in plain language.
- Quiz the user one question at a time, deterministic Python tracks score, model only renders + grades.
- Refuse to import outside facts unless the user invokes well-known ones.

## Why state-machine architecture

Small local models lose the thread on multi-step interactions by turn 4–5. The quiz loop is driven by Python — current question, expected answer, score, next-question logic. The model is called only inside bounded steps: render the question, grade the answer. Same discipline as `lak init`.

## Run it (after unblock)

```bash
lak bot templates/study_buddy
```

## Eval

Cases test: explanations stay grounded in supplied material, quiz responses are one question at a time, grading is short and not lecture-y, the model refuses to invent facts.
