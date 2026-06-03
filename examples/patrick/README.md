# Example: Patrick (kit-only configuration)

This directory shows how the [Patrick reference agent](https://github.com/bene-art/patrick-agent) is configured using only `local-agent-kit` features — no custom tool router, no domain databases.

## What this example demonstrates

- `agent.yaml` — channel + search + memory configuration
- `identity/IDENTITY.md` — system prompt with tool-aware behavior
- Web search wired through Gemini Flash + Google Search grounding

## Run it

```bash
# From the local-agent-kit repo root
lak doctor --agent examples/patrick
lak bot examples/patrick
```

Set `GEMINI_API_KEY` in your environment for web search to work. Without it, search falls back to DuckDuckGo (change `search.provider` in `agent.yaml`).

## The full Patrick

This example only exercises the kit. The full Patrick adds:

- **Tool router** — pattern-matched dispatch to 6 tools (web, db, file read/write, shell exec, API call) with chaining
- **Eval harness** — Karpathy autoresearch pattern (immutable scorer + failure taxonomy + synonym-aware constraint checking)
- **Notification protocol** — Tier 2/Tier 3 Telegram message formatting with severity-based routing
- **Telemetry** — JSONL audit log that feeds production traffic back into the eval corpus

See https://github.com/bene-art/patrick-agent for the full implementation.
