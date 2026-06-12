# Analyst template

Answer questions about a small structured dataset (CSV, JSONL). Python computes the aggregation, the model narrates the result.

## Status

**Blocked** on the tools track — needs `file_read` and `data_query`. See `STATUS.md`.

## Why this architecture

Small local models are bad at arithmetic. The kit's discipline is: Python computes, the model narrates. This template is one of the two canonical examples of that pattern (briefer is the other).

## Run it (after unblock)

```bash
lak bot templates/analyst
```

Point it at a file:

> "Analyze ./sales.csv — what's the total revenue by region?"

The kit reads the file, runs the aggregation in Python, hands the result to the model as `[SYSTEM DATA]`, and the model describes what's there.

## Eval

Cases test the narrate-only contract: given a `[SYSTEM DATA]` block with computed numbers, the response may quote those numbers but may not invent new ones.
