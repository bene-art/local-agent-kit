# STATUS — briefer

**State:** ready
**Last verified:** 2026-06-12

## What ships
- `agent.yaml` with a declared schedule and a Hacker News RSS fetcher.
- `fetch_news.py` — example fetcher (httpx + stdlib XML, no extra deps).
- IDENTITY enforces the narrate-only contract (model adds at most three
  sentences of framing, never invents numbers, refuses on empty data).
- Eval suite passes 4/4 on `gemma4:e4b`.
- End-to-end live fire verified: fetcher → `envelope()` → `Agent.handle()` →
  channel.send, with the model correctly narrating real RSS headlines and
  flagging what the data did not cover.

## Run it

```bash
lak bot templates/briefer
```

The declared schedule (`0 7 * * *`) fires daily at 7am, fetches headlines,
and posts to the configured channel. Override the RSS feed with the
`BRIEFER_RSS_URL` env var.

## Notes on extending

- Swap `fetch_news.py` for a custom fetcher by changing the `fetcher:` dotted
  path in `agent.yaml`. Any callable returning a string works — it gets
  wrapped in `[SYSTEM DATA]` automatically.
- Reasoning is OFF for this template (`think: false`) — narrate-only at a
  250-token budget doesn't have room for the reasoning phase. Bump
  `max_tokens` and flip `think` back on if you want the model to plan
  before narrating.
- Channel defaults to `cli` for local testing. Set `TG_BOT_TOKEN` +
  `TG_CHAT_ID` and switch `channel: telegram` to push to Telegram.
