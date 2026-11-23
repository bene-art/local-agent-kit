# Local Agent Kit

[![CI](https://github.com/bene-art/local-agent-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/bene-art/local-agent-kit/actions/workflows/ci.yml)

> **Status:** Active. v0.4.0 (2026-07-13). Solo-maintained — no SLA on issues or PRs; security reports via [SECURITY.md](./SECURITY.md).

Build a local-first AI agent in 5 minutes. No cloud account, no API key, no telemetry.

## Why does this exist?

I run AI agents on my own hardware — for journaling, studying, and operational work I wouldn't send to a cloud API. Most agent frameworks assume the opposite: an API key, a hosted model, a Docker stack. This kit is the extracted, cleaned-up core of what I actually run: an agent loop on [Ollama](https://ollama.com), a handful of composable primitives, and nothing that phones home.

The rule that shaped v0.4.0: **if a feature needs a cloud account, it doesn't ship in the kit.** Inference is local. Search is opt-in DuckDuckGo (no key) or off. The journal template's zero-outbound promise is locked in by a test.

## Quick start

Templates live in the repo, so clone it:

```bash
# 1. Install Ollama
brew install ollama                     # macOS
# curl -fsSL https://ollama.com/install.sh | sh   # Linux

# 2. Clone + install the kit
git clone https://github.com/bene-art/local-agent-kit
cd local-agent-kit
pip install -e ".[schedule]"

# 3. Either scaffold your own agent...
lak init

# ...or run a bundled template
lak templates list
lak bot templates/writer
```

Using the kit as a library only (no templates)? `pip install git+https://github.com/bene-art/local-agent-kit` works too.

The `lak init` wizard detects your hardware, recommends and optionally pulls the best Ollama model for your RAM, asks whether you want web search (DuckDuckGo or fully offline), and scaffolds `IDENTITY.md` + `agent.yaml`. Then:

```bash
lak doctor --agent ./my-agent       # preflight check
lak bot ./my-agent                  # start chatting
```

## Templates

Three exemplars, one per primitive stack. Each ships a working `agent.yaml`, an `IDENTITY.md` tuned for `gemma4:e4b`, and an evaluated promptfoo suite.

| Template | What it demonstrates | Run |
|---|---|---|
| **writer** | The plain agent loop. Edit, draft, tone-shape prose. No tools, no network. | `lak bot templates/writer` |
| **journal** | Memory + privacy. Persistent local SQLite memory, verified zero-outbound (a test fails if any non-localhost request is attempted). | `python -m templates.journal.run_journal --agent-dir templates/journal` |
| **study_buddy** | Deterministic state machines. Explain mode + quiz mode over your own material; Python tracks the quiz state and score, the model only renders and grades. | `python -m templates.study_buddy.run_study --agent-dir templates/study_buddy --source <file> --quiz <yaml>` |

Each template's `STATUS.md` is honest about what works and what the model's actual ceiling is.

## Primitives

```
local_agent_kit/
├── agent.py              # Agent + load_config + handle pipeline
├── tools/
│   ├── file_read         # sandboxed file reader (allowlist + blocklist)
│   ├── data_query        # CSV/JSONL → SQLite SELECT (validated, SELECT-only)
│   └── data_peek         # first N rows of a CSV/JSONL as a table
├── memory/
│   ├── Memory            # Protocol every backend implements
│   ├── SQLiteMemory      # local SQLite, per-thread append + history
│   └── QuizProgress      # per-(quiz, step) score tracking
├── patterns/
│   ├── narrate_only      # envelope() + NarrationRubric — Python computes, model narrates
│   └── StateFlow         # Python-driven multi-step interaction state machine
├── scheduling/
│   ├── ScheduledTask     # declarative recurring task (cron + prompt + fetcher)
│   └── LocalScheduler    # asyncio runner; requires croniter (`.[schedule]` extra)
├── eval/
│   └── promptfoo_provider # wraps Agent.from_directory().handle() for eval suites
├── channels/             # CLI bundled; Channel ABC for your own
├── search/               # DuckDuckGo bundled; SearchProvider ABC for your own
└── hardware.py           # detection + model recommendation
```

The package ships `py.typed` — the API is fully annotated and mypy-clean.

## How it works

`Agent.handle()` runs three injection layers before the LLM call:

```
User message
    ↓
1. _maybe_search       → DuckDuckGo (if configured), injected as [SYSTEM DATA — web search]
2. _maybe_read_file    → file_read for text paths (.md, .py, .yaml, ...) mentioned in the message
3. _maybe_show_data    → data_peek for CSV/JSONL paths, formatted as a table
    ↓
Ollama (local LLM)     → think: configurable per template; empty responses are guarded
    ↓
Response sent via channel
```

**Key design decision:** all data — search results, file contents, computed aggregations — is injected **inline** into the user message, not as separate conversation history. Small local models ignore data placed in earlier turns. Inline injection makes the data impossible to miss.

**Per-template `think:` flag.** Reasoning models spend tokens on a hidden thinking phase before producing visible content. Templates with tight token budgets set `think: false` in `agent.yaml`. Default is on.

## Hardware detection

```bash
lak hardware
```

| RAM | Model | Size (Q4) | Speed | Notes |
|-----|-------|-----------|-------|-------|
| 8 GB | gemma4:e4b | 3.3 GB | ~30-40 tok/s | Default — what the bundled templates target |
| 16 GB | gemma4:12b | 7.6 GB | ~15-18 tok/s | Sweet spot for general use |
| 24 GB | gemma4:12b | 7.6 GB | ~15-18 tok/s | Headroom for longer contexts |
| 32 GB | gemma3:27b | 17 GB | ~8-12 tok/s | Higher quality |
| 48 GB | gemma3:27b | 17 GB | ~12-15 tok/s | 27B with headroom |
| 64 GB | llama3.3:70b | 43 GB | ~5-8 tok/s | Near cloud quality |
| 128 GB | llama3.3:70b | 43 GB | ~10-15 tok/s | 70B with full headroom |

**Why these speeds:** LLM inference is memory-bandwidth bound. The GPU reads the entire model for every token. On Apple M4 at ~120 GB/s, that's ~15 tokens/second for a 12B model at Q4. This is physics, not software.

## Extending

**Channels.** The CLI channel is bundled. For Telegram, Discord, Slack, iMessage — implement the two-method `Channel` ABC and pass an instance:

```python
from local_agent_kit.agent import Agent
from local_agent_kit.channels.base import Channel, Message

class MyChannel(Channel):
    async def listen(self):          # async generator of Message
        ...
    async def send(self, text: str, thread_id: str | None = None) -> bool:
        ...

agent = Agent.from_directory("./my-agent", channel=MyChannel())
```

**Search.** DuckDuckGo is bundled (no key). For Brave, SerpAPI, or a local SearXNG instance, implement `SearchProvider.search()` and pass it via `Agent.from_directory(search=...)`. In `agent.yaml`, `search.provider` is authoritative: `duckduckgo` or `none` — the environment never decides.

## Scheduling

Declare recurring tasks in `agent.yaml`. At fire time, the runner calls an optional Python fetcher, wraps its output as `[SYSTEM DATA]`, and runs the result through `Agent.handle()` — the "Python computes, model narrates" pattern. Results go out through the agent's channel.

```yaml
schedules:
  - name: morning_brief
    cron: "0 7 * * *"
    prompt: "Frame today's headlines in one or two sentences."
    fetcher: my_module:get_headlines
```

The parser works without `croniter`; the in-process scheduler requires the `schedule` extra.

## Eval

Every template ships a promptfoo suite under `templates/<name>/eval/`:

```bash
cd templates/writer/eval && promptfoo eval
```

The kit's `promptfoo_provider` wraps `Agent.from_directory(...).handle(prompt)` so each test exercises the full pipeline — config + IDENTITY + tools + LLM — not raw Ollama output. Tests stay deterministic where possible; semantic checks use `llm-rubric` with a larger local model as the grader.

## Agent directory

`lak init` creates:

```
my-agent/
├── identity/
│   └── IDENTITY.md    # The system prompt — edit this to make the agent yours
├── agent.yaml         # Model, search, tools, memory, schedules
└── .env               # Environment variables (gitignored)
```

A fuller `agent.yaml`:

```yaml
name: my-agent
model: gemma4:e4b
temperature: 0.4
max_tokens: 350
think: true                # reasoning phase on; flip to false for tight budgets

search:
  provider: duckduckgo     # or "none" — this field decides, not the environment

conversation_memory:
  enabled: true
  max_history: 20

tools:
  web_search: true
  file_read:
    roots: ["."]           # auto-inject file contents from these roots
    max_chars: 4000
    data_peek_rows: 20     # rows of CSV/JSONL to peek

schedules:
  - name: morning_brief
    cron: "0 7 * * *"
    prompt: "..."
    fetcher: my_module:get_data
```

## Why local-first

**$0/month.** No API billing. The model runs on your GPU. The only cost is the hardware you already own.

**Privacy by physics.** Inference happens on your chip. Your conversations never leave the memory bus. Web search queries do leave the machine when you enable a provider — that's the trade-off for seeing the outside world, and it's off with `provider: none`. The journal template ships a pytest and an `lsof` watcher that verify its zero-outbound claim.

**Model-agnostic.** Swap models in `agent.yaml`. Any model Ollama supports works — Gemma, Llama, Mistral, Qwen, Phi. The kit doesn't care.

## Reference implementation

[Patrick Agent](https://github.com/bene-art/patrick-agent) is the reference implementation built on this kit — the canonical worked example of a kit-style agent extended with a full custom tool router. See its [white paper](https://github.com/bene-art/patrick-agent/blob/main/docs/white_paper_v2.md), or [`examples/patrick/`](examples/patrick/) for the kit-only configuration.

## License

MIT

## Author

Built by [Benjamin Easington](https://github.com/bene-art).
