# Local Agent Kit

[![CI](https://github.com/bene-art/local-agent-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/bene-art/local-agent-kit/actions/workflows/ci.yml)

Build a local-first AI agent in 5 minutes. No cloud account required.

```bash
pip install git+https://github.com/bene-art/local-agent-kit
lak init                          # scaffold an agent from scratch
# — or —
lak templates list                # pick a pre-built template
lak bot templates/writer          # run it
```

## What You Get

- A conversational AI agent running on your hardware via [Ollama](https://ollama.com).
- **Eight starter templates** for common shapes — writer, researcher, briefer, code Q&A, journal, study buddy, interviewer, analyst.
- **Composable primitives** the templates use and you can too: tools, memory, patterns, scheduling, eval.
- Pluggable channels (CLI, Telegram), pluggable search (DuckDuckGo, Gemini), and a stable Agent contract.

Inference is local. Web search is optional and pluggable. The only cost is the hardware you already own.

## Quick Start

```bash
# 1. Install Ollama
brew install ollama                     # macOS
# curl -fsSL https://ollama.com/install.sh | sh   # Linux

# 2. Install the kit
pip install git+https://github.com/bene-art/local-agent-kit

# 3. Either scaffold from the wizard...
lak init

# ...or run a bundled template
lak templates list
lak bot templates/writer
```

The wizard:
1. Detects your hardware (chip, RAM, GPU)
2. Recommends and optionally pulls the best Ollama model for your system
3. Asks which communication channel (CLI or Telegram)
4. Asks which web search provider (DuckDuckGo or Gemini)
5. Scaffolds an agent directory with `IDENTITY.md`, `agent.yaml`, and `.env`

Then:

```bash
lak doctor --agent ./my-agent       # preflight check
lak bot ./my-agent                  # start chatting
```

## Templates

`lak templates list` surfaces eight starter shapes. Each ships with a working `agent.yaml`, an `IDENTITY.md` tuned for `gemma4:e4b`, an evaluated promptfoo suite, and (where applicable) a runner script.

| Template | What it does | Run |
|---|---|---|
| **writer** | Edit, draft, tone-shape prose. No tools, no network. | `lak bot templates/writer` |
| **researcher** | Web search + grounded synthesis with name-exactness enforcement. | `lak bot templates/researcher` |
| **briefer** | Scheduled deterministic briefings pushed to a channel. Ships a Hacker News RSS fetcher as the example. | `lak bot templates/briefer` |
| **code_qa** | Auto-injects file contents when a path is mentioned. | `cd ~/project && lak bot templates/code_qa` |
| **journal** | Reflective companion. Persistent local memory, verified zero-outbound. | `python -m templates.journal.run_journal --agent-dir templates/journal` |
| **study_buddy** | Explain mode + spaced-repetition quiz mode over your own source material. | `python -m templates.study_buddy.run_study --agent-dir templates/study_buddy --source <file> --quiz <yaml>` |
| **interviewer** | Schema-driven structured Q&A; writes captured answers to markdown. | `python -m templates.interviewer.run_interview --agent-dir templates/interviewer --schema templates/interviewer/schema.yaml` |
| **analyst** | Auto-injects a tabular head when a CSV/JSONL is mentioned. Aggregation is direct-composition via `data_query`. | `cd ~/data && lak bot templates/analyst` |

Each template's `STATUS.md` is honest about what works, what's still pending, and what the model's actual ceiling is.

## Primitives

The kit's eight templates compose from a small set of shared primitives. Build your own templates by composing them too.

```
local_agent_kit/
├── agent.py              # Agent + load_config + handle pipeline
├── tools/
│   ├── file_read         # sandboxed file reader (allowlist + blocklist)
│   ├── data_query        # CSV/JSONL → SQLite SELECT (validated)
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
│   └── LocalScheduler    # asyncio runner; requires croniter (`pip install .[schedule]`)
├── eval/
│   └── promptfoo_provider # wraps Agent.from_directory().handle() for per-template eval suites
├── channels/             # CLI, Telegram (Discord, Slack planned)
├── search/               # DuckDuckGo, Gemini Search Grounding
└── hardware.py           # detection + model recommendation
```

## How It Works

`Agent.handle()` runs four injection layers before the LLM call:

```
User message
    ↓
1. _maybe_search       → DuckDuckGo / Gemini, injected as [SYSTEM DATA — web search]
2. _maybe_read_file    → file_read for text paths (.md, .py, .yaml, ...) mentioned in the message
3. _maybe_show_data    → data_peek for CSV/JSONL paths, formatted as a table
4. Ollama (local LLM)  → think: configurable per template; empty responses are guarded
    ↓
Response sent via channel
```

**Key design decision:** all data — search results, file contents, computed aggregations — is injected **inline** into the user message, not as separate conversation history. Small local models ignore data placed in earlier turns. Inline injection makes the data impossible to miss.

**Per-template `think:` flag.** Reasoning models (gemma4:e4b, etc.) spend tokens on a hidden thinking phase before producing visible content. Templates with tight token budgets (briefer, study_buddy) set `think: false` in `agent.yaml`. Default is on.

## Hardware Detection

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

## Pluggable Channels

| Channel | Setup | Status |
|---------|-------|--------|
| **CLI** | Zero config | ✅ Shipped |
| **Telegram** | Bot token + chat ID | ✅ Shipped |
| Discord | — | Planned |
| Slack | — | Planned |

Implement `local_agent_kit.channels.base.Channel` for your own.

## Pluggable Search

| Provider | API Key Required | Status |
|----------|-----------------|--------|
| **DuckDuckGo** | No | ✅ Shipped |
| **Gemini Search Grounding** | Yes (free tier) | ✅ Shipped |

Implement `local_agent_kit.search.base.SearchProvider` for your own.

## Scheduling

Declare recurring tasks in `agent.yaml`. At fire time, the runner calls an optional Python fetcher, wraps its output as `[SYSTEM DATA]`, and runs the result through `Agent.handle()`:

```yaml
schedules:
  - name: morning_brief
    cron: "0 7 * * *"
    prompt: "Frame today's headlines in one or two sentences."
    channel: cli
    fetcher: templates.briefer.fetch_news:get_headlines
```

Install with the optional extra to enable the runtime:

```bash
pip install git+https://github.com/bene-art/local-agent-kit#egg=local-agent-kit[schedule]
```

The parser works without `croniter`; the in-process scheduler requires it.

## Eval

Every template ships a promptfoo suite under `templates/<name>/eval/`. Run from the template's eval directory:

```bash
cd templates/writer/eval && promptfoo eval
```

The kit's `promptfoo_provider` (`src/local_agent_kit/eval/promptfoo_provider.py`) wraps `Agent.from_directory(...).handle(prompt)` so each test exercises the full kit pipeline — config + IDENTITY + search + tools + LLM — not raw Ollama output. Tests stay deterministic where possible (`icontains`, `not-icontains`, length checks); semantic checks use `llm-rubric` with a larger local model as the grader when needed.

## Agent Directory

`lak init` creates:

```
my-agent/
├── identity/
│   └── IDENTITY.md    # The system prompt — edit this to make the agent yours
├── agent.yaml         # Model, channel, search, tools, schedules config
└── .env               # API keys (gitignored)
```

A fuller `agent.yaml`:

```yaml
name: my-agent
model: gemma4:e4b
channel: cli
temperature: 0.4
max_tokens: 350
think: true                # reasoning phase on; flip to false for tight budgets

search:
  provider: duckduckgo     # or "gemini" or "none"

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
    channel: cli
    fetcher: my_module:get_data
```

## Why Local-First

**$0/month.** No API billing. The model runs on your GPU. Web search via DuckDuckGo is free. The only cost is the hardware you already own.

**Privacy by physics.** Core inference happens on your chip. Your conversations never leave the memory bus. (Web search queries do leave the machine when you enable a search provider — that's the trade-off for seeing the outside world. The journal template ships with both a pytest and an `lsof` watcher to verify the zero-outbound claim for templates that don't need search.)

**Model-agnostic.** Swap models in `agent.yaml`. Any model Ollama supports works — Gemma, Llama, Mistral, Qwen, Phi. The kit doesn't care.

## Reference Implementation

[Patrick Agent](https://github.com/bene-art/patrick-agent) is the reference implementation built on this kit. It's the canonical worked example of a kit-style agent extended with a full custom tool router. See its [white paper](https://github.com/bene-art/patrick-agent/blob/main/docs/white_paper_v2.md) for the technical analysis, or [`examples/patrick/`](examples/patrick/) for the kit-only configuration.

## License

MIT

## Author

Built by [Benjamin Easington](https://github.com/bene-art).
