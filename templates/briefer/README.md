# Briefer template

Scheduled deterministic briefings pushed to a channel. The agent fetches data on cron, formats it in Python, and the model only adds one sentence of framing.

## Status

**Blocked** on the `Scheduler` runtime — see `STATUS.md`.

The template files (IDENTITY, eval cases) are ready. The runtime piece is parked behind a dependency decision (`croniter`).

## What it will do

- A scheduled task fetches data (news, portfolio, calendar, custom).
- Python formats the result into a deterministic string.
- The kit wraps it as `[SYSTEM DATA]` and asks the model for one sentence of framing.
- The framed brief is sent through the configured channel (Telegram by default).

## Run it (after unblock)

```bash
lak bot templates/briefer
```

## Eval

The eval cases test the narrate-only contract: given a `[SYSTEM DATA]` block with specific numbers, the response may quote those numbers but may not invent new ones.
