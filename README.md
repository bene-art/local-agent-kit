# Local Agent Kit

Build a local-first AI agent in 5 minutes. No cloud account required.

```bash
pip install git+https://github.com/bene-art/local-agent-kit
lak init
lak bot ./my-agent
```

## What You Get

A conversational AI agent running on your hardware via [Ollama](https://ollama.com). It detects your system, recommends a model, scaffolds an agent directory, and starts chatting — in your terminal or on Telegram.

Web search is pluggable: DuckDuckGo (no API key) or Gemini (Google Search grounding, free tier). Add your own search provider by implementing one method.

## Quick Start

```bash
# 1. Install Ollama
brew install ollama        # macOS
# curl -fsSL https://ollama.com/install.sh | sh   # Linux

# 2. Install the kit
pip install git+https://github.com/bene-art/local-agent-kit

# 3. Run the setup wizard
lak init
```

The wizard:
1. Detects your hardware (chip, RAM, GPU)
2. Recommends and optionally pulls the best Ollama model for your system
3. Asks which communication channel (CLI or Telegram)
4. Asks which web search provider (DuckDuckGo or Gemini)
5. Scaffolds an agent directory with IDENTITY.md, agent.yaml, and .env

```bash
# 4. Check everything works
lak doctor --agent ./my-agent

# 5. Start chatting
lak bot ./my-agent
```

## Hardware Detection

```bash
lak hardware
```

The kit detects your system and recommends the best model:

| RAM | Model | Size (Q4) | Speed | Notes |
|-----|-------|-----------|-------|-------|
| 8 GB | gemma3:4b | 3.3 GB | ~30-40 tok/s | Minimal, good for testing |
| 16 GB | gemma3:12b | 8.1 GB | ~15-18 tok/s | Sweet spot |
| 24 GB | gemma3:12b | 8.1 GB | ~15-18 tok/s | Comfortable, room for more |
| 32 GB | gemma3:27b | 17 GB | ~8-12 tok/s | Higher quality |
| 64+ GB | llama3.3:70b | 43 GB | ~5-8 tok/s | Near cloud quality |

**Why these speeds:** LLM inference is memory-bandwidth bound. The GPU reads the entire model (~6 GB for 12b at Q4) for every token. On Apple M4 at ~120 GB/s, that's ~15 tokens/second. This is physics, not software.

## Pluggable Channels

Talk to your agent however you want:

| Channel | Setup | Status |
|---------|-------|--------|
| **CLI** | Zero config | ✅ Shipped |
| **Telegram** | Bot token + chat ID | ✅ Shipped |
| Discord | — | Planned |
| Slack | — | Planned |

**Add your own:**

```python
from local_agent_kit.channels.base import Channel, Message

class MyChannel(Channel):
    async def listen(self):
        # yield Message(text=...) for each incoming message
        ...

    async def send(self, text: str, thread_id: str = "") -> bool:
        # send the response back to the user
        ...
```

## Pluggable Search

Give your agent eyes on the world:

| Provider | API Key Required | Status |
|----------|-----------------|--------|
| **DuckDuckGo** | No | ✅ Shipped |
| **Gemini** | Yes (free tier) | ✅ Shipped |
| Brave Search | Yes (free tier) | Planned |
| SerpAPI | Yes | Planned |

**Add your own:**

```python
from local_agent_kit.search.base import SearchProvider

class MySearch(SearchProvider):
    async def search(self, query: str, max_results: int = 5) -> str:
        # return search results as text
        ...
```

## How It Works

```
User message
    ↓
Search check: does this need web data?
    ↓ yes                    ↓ no
Search provider              │
    ↓                        │
Inject [SYSTEM DATA]         │
    ↓                        │
Ollama (local LLM) ←────────┘
    ↓
Response sent via channel
```

The agent detects when a message needs external information, fetches it via your configured search provider, injects the results into the message, and lets the local LLM respond with real data.

**Key design decision:** Search results are injected **inline** into the user message, not as separate conversation history. Local models ignore data placed in earlier history turns. Inline injection makes the data impossible to miss.

## Agent Directory

`lak init` creates a directory like this:

```
my-agent/
├── identity/
│   └── IDENTITY.md    # Who the agent is (edit this!)
├── agent.yaml         # Model, channel, search config
└── .env               # API keys (gitignored)
```

**IDENTITY.md** is the system prompt. It defines who your agent is, what it knows, and how it behaves. This is the most important file — edit it to make the agent yours.

**agent.yaml** configures the model, channel, and search provider:

```yaml
name: my-agent
model: gemma3:12b
channel: cli          # or "telegram"

search:
  provider: duckduckgo  # or "gemini" or "none"

conversation_memory:
  enabled: true
  max_history: 20
```

## Why Local-First

**$0/month.** No API billing. The model runs on your GPU. Web search via DuckDuckGo is free. The only cost is the hardware you already own.

**Privacy by physics.** Core inference happens on your chip. Your conversations never leave the memory bus. (Web search queries do leave the machine — that's the trade-off for seeing the outside world.)

**Model-agnostic.** Swap models in agent.yaml. Any model Ollama supports works — Gemma, Llama, Mistral, Qwen, Phi. The kit doesn't care.

## Reference Implementation

[Patrick Agent](https://github.com/bene-art/patrick-agent) is the reference implementation built with this kit. He scores 0.9651 on a 518-entry eval corpus, has six tools, and runs on a Mac mini M4. See his [white paper](https://github.com/bene-art/patrick-agent/blob/main/docs/white_paper_v2.md) for the full technical analysis.

## License

MIT

## Author

Built by [Benjamin Easington](https://github.com/bene-art).
