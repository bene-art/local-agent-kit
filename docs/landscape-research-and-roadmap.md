# Local-First Agent Landscape — Research & Upgrade Paths

> **Status:** Research snapshot, 2026-06-10. Reference document, not a commitment.
> **Purpose:** A map of the local-first agent ecosystem and a menu of upgrade
> paths for `local-agent-kit`, so the maintainer can compare *what is actually
> built on the machine* against *what the research identifies as gaps* — and
> pick what's worth doing.
>
> **How to read this:** Sections 1–2 are the landscape. Section 3 is an honest
> read of the kit's current code. Section 4 is what shipped this session.
> Section 5 is the borrow analysis (the meat). Section 6 is a dependency-ordered
> roadmap. Section 7 is guardrails. Treat star counts and dates as approximate
> (gathered via live web reads; exact figures drift).

---

## 1. The ten repositories

Two research rounds, one agent per repo (direct README/repo + corroborating
search), with flagged-claim verification.

**Round 1 — the four named repos:**
`ashishpatel26/500-AI-Agents-Projects`, `mudler/LocalAGI`,
`damianvtran/local-operator`, `msb-msb/awesome-local-ai`.

**Round 2 — closest peers in the niche:**
`khoj-ai/khoj`, `cheshire-cat-ai/core`, `letta-ai/letta` (MemGPT),
`openinterpreter/open-interpreter`, `huggingface/smolagents`, `block/goose`.

### Consolidated comparison

| Project | ★ (approx) | Category | Local posture | Phones home? | Best-in-class at |
|---|---|---|---|---|---|
| **open-interpreter** | ~64k | Code-exec agent | `--local` optional; **cloud default** | **Telemetry ON (opt-out)** | Code-exec + human-in-loop confirmation |
| **goose** (Block→AAIF) | ~mid-40k | On-machine agent (Rust) | Ollama 1 of 15+; **cloud-led** | Telemetry opt-out | **MCP extensibility** (70+ extensions) |
| **Khoj** | ~34k | Personal-AI product | Ollama first-class | **Telemetry ON (opt-out)** | RAG over personal docs + automations |
| **500-AI-Agents-Projects** | ~32k | Catalog (no runtime) | N/A (links mostly cloud) | — | Use-case content marketing |
| **smolagents** (HF) | ~28k | Minimal agent library | Local optional; **cloud-default quickstart** | Telemetry opt-in | "Code-agents" + sandboxed exec + GAIA eval |
| **Letta / MemGPT** | ~23k | Stateful-agent platform | Ollama/vLLM, **cloud-steered** | Unverified | Self-editing memory hierarchy |
| **Cheshire Cat** | ~3k | Agent microservice | **Local first-class** (`local-cat`) | Unverified | Plugin system (hooks/tools/forms) + 3-tier memory |
| **LocalAGI** (mudler) | ~1.8k | Self-host agent platform | **Local by default** | No (default) | No-code UI + 6 connectors + RAG + sandbox |
| **local-operator** | ~204 | Autonomous operator | Local supported; **Radient cloud steered** | Unverified | AI safety-review gate before code-exec |
| **awesome-local-ai** (msb-msb) | ~115 | Directory (no runtime) | N/A (curates local tools) | — | Discoverability / ecosystem taxonomy |
| **local-agent-kit** (this) | — | **Local agent builder** | **Local-only by design, zero cloud account** | **No — nothing** | 5-min onboarding + hardware-fit + truly-local |

### Per-repo, one paragraph each

- **open-interpreter** — Natural-language code interpreter; runs code locally. Note: default branch is now `oix` (a Rust rewrite, "coding agent for low-cost models"); the classic Python product was handed to a community fork (`endolith/open-interpreter`). Cloud GPT-4o is the steered default; `--local` works but is lower-reliability. **Telemetry to PostHog ON by default** (opt-out), possibly even in local mode. *Category peer of local-operator, not of this kit.*
- **goose** — General on-machine agent in Rust; desktop + CLI + embeddable API. As of Apr 2026 governed by the Linux Foundation's Agentic AI Foundation. **Abandoned its bespoke Python plugins for MCP** (70+ extensions). Ollama is one of 15+ providers but cloud-led. Opt-out telemetry. *The clearest signal in the whole set: standardize on MCP.*
- **Khoj** — "AI second brain" personal assistant; strong RAG over docs (PDF/Markdown/Notion), automations, many clients (web/desktop/Obsidian/Emacs/mobile/WhatsApp — **no Telegram**). Ollama first-class but hosted SaaS is pushed. **Default-on PostHog telemetry** (opt-out via `KHOJ_TELEMETRY_DISABLE`). AGPL-3.0.
- **500-AI-Agents-Projects** — ~32k-star *catalog* of agent use-cases linking to 500+ third-party repos (mostly cloud-default). Ships nothing runnable. Value to us: use-case inspiration + comparison-table + star-growth playbook.
- **smolagents** — HuggingFace's minimal (~1k-LoC core) agent library. Differentiator: **CodeAgent** writes actions as Python instead of JSON tool-calls. Model-agnostic; local possible but quickstart defaults to HF Inference API. First-class sandboxing (E2B/Docker/Modal). Public GAIA benchmark (~55%). Apache-2.0.
- **Letta / MemGPT** — Stateful agents whose entire thesis is **self-editing memory** (core/recall/archival hierarchy, agent-managed via tool calls). Python; server + ADE GUI + SDKs. Local via Ollama/vLLM but cloud-steered and **fragile on weak/quantized local models** (their own docs warn ≥Q6, native tool-calling required). Apache-2.0, $10M seed. *Most relevant to the separate memory track.*
- **Cheshire Cat** — Production-oriented agent *microservice* (Docker, REST/WS). Standout **plugin system ("Mad Hatter"): hooks + tools + forms**, and a **three-tier vector memory**. Fully-local path is first-class (`local-cat`: Cat + Ollama + FastEmbed + Qdrant). Active through mid-2025, cadence slowed since. **GPL-3.0 — borrow patterns, not code.**
- **LocalAGI** — mudler's (LocalAI author) self-hostable **no-code agent platform** in Go + React. Multi-agent teaming, RAG, scheduler, ~20 tools, **6 connectors** (Discord/Slack/Telegram/GitHub/IRC/Email), MCP, sandboxed code-exec (SSHBox). **Local by default**; 4-service Docker stack. MIT. *Closest "platform-altitude" peer; the heavyweight foil to our minimalism.*
- **local-operator** — Python autonomous **operator** that writes & executes code via chat, with an **independent AI safety-review + confirmation gate**. Runs local via Ollama but marketing/onboarding steer to **Radient** (author's commercial cloud). Activity cooled in Q2 2026. **License confirmed MIT** (Medium's GPL-3.0 claim is stale).
- **awesome-local-ai** (msb-msb) — Small (~115★, 8 commits, CC0, solo) curated list of local-AI tools with an AI Agents section. Not a competitor — a **listing opportunity**. The bigger prize is `janhq/awesome-local-ai` (~2k★).

---

## 2. Where local-agent-kit sits in the landscape

**The wedge is real and rare.** Of every *runnable* peer, only LocalAGI and
Cheshire Cat match "local-by-default." **None** match the full posture:
*local-by-default AND zero cloud account AND zero telemetry AND
hardware-detection onboarding.* Khoj, Open Interpreter, and Goose all ship
default-on or opt-out telemetry. Letta, local-operator, smolagents, and Open
Interpreter all *steer* users to cloud. This is a defensible, quantifiable
differentiator — and it is currently under-claimed.

**The debt is capability depth.** The kit trails the field on tools, memory
persistence, an extensibility standard, and a GUI — and (until this session)
its "eval-driven" claim had no code behind it.

---

## 3. Honest read of the current codebase (the "what's actually built" baseline)

Grounded in a direct read of `src/local_agent_kit/`:

- **`eval/`, `tools/`, `providers/` were 0-line stubs.** The "eval-driven"
  scorer and tools described in the README actually live in the *Patrick
  reference agent*, not the kit. (`eval/` is now populated — see §4.)
- **Memory is a flat in-memory trailing window.** `self._history[-max:]`
  (`agent.py:143,215`); an in-process list that does not survive a restart.
  No persistence, summarization, or self-editing. *This is the separate track.*
- **Tool use is a single hardcoded heuristic.** `_maybe_search` decides whether
  to web-search by checking if the message starts with "what/who/how…" and
  lacks "identity/soul/system" keywords (`agent.py:178-192`). English-only,
  single-tool, brittle. There is no general tool-calling — search results are
  string-concatenated onto the user message (`agent.py:205`).
- **Clean, swappable seams already exist.** `Channel` (ABC: `listen`/`send`/
  `start`/`stop`) and `SearchProvider` (one method) are good abstractions. The
  config flows `agent.yaml → AgentConfig`. These are the surfaces to build on.
- **CLI:** `init`, `doctor`, `bot`, `hardware` — and now `eval`.

**Takeaway for the maintainer's comparison:** the gap between README claims and
shipped code (eval, tools) is the first thing to reconcile against your machine.
If your local copy has more than this, the roadmap below shifts accordingly.

---

## 4. What shipped this session — promptfoo eval harness

Done, committed, pushed to `claude/local-ai-agents-eval-nb6h80`.

- **`lak eval <agent>`** runs [promptfoo](https://www.promptfoo.dev) against the
  **full agent pipeline** (search → inject → Ollama) via a custom Python
  provider — not the raw model.
- `eval/provider.py` — promptfoo `call_api()` wrapping `Agent.handle` with a
  headless channel; fresh agent per case (no memory bleed).
- `eval/scaffold.py` — writes `<agent>/eval/{provider.py, promptfooconfig.yaml}`
  with a **local Ollama grader** and example assertions.
- `lak init` scaffolds it; `lak doctor` reports Node/promptfoo availability.
- **100% local** (local grader, nothing phones home). promptfoo runs via `npx`
  on demand → pip footprint unchanged. Requires Node 18+.
- Verified end-to-end: promptfoo loaded the provider and drove `Agent.handle`
  3× (failures were only the absent sandbox Ollama, handled gracefully).

**Caveats:** small local graders (e.g. `gemma3:4b`) are weak judges — lean on
deterministic asserts (`icontains`/`javascript`) and bump the grader model for
`llm-rubric`. promptfoo's site shows "part of OpenAI" branding but the CLI runs
fully offline for local use.

---

## 5. Borrow analysis — capability by capability

> Memory excluded (separate track). Eval done (§4). Ordered by dependency: the
> tool-calling refactor unblocks most of the rest.

### 5.1 Keystone — real tool-calling (from smolagents, Goose, LocalAGI)
- **Today:** `_maybe_search` keyword heuristic; single tool; string concat.
- **Take:** Ollama's native function-calling (`tools` param on `/api/chat`).
  From smolagents, the *abstraction* (Tool = name + JSON schema + callable) —
  not their write-code-as-actions trick. From Goose, the strategic lesson:
  **adopt MCP rather than inventing a plugin protocol** (they deleted theirs
  and gained 70+ integrations).
- **Fit:** Generalize the `SearchProvider` pattern into a `Tool` base; register
  tools in `_ollama_chat`'s payload; run a tool-call loop. DuckDuckGo/Gemini
  search becomes *one tool*; `_maybe_search` guesswork disappears. An `MCPTool`
  adapter then exposes any MCP server through the same interface.
- **Why first:** every capability below becomes a tool, not a core change.
- **Avoid:** smolagents' in-process executor (no sandbox); start as MCP *client*
  only, skip server hosting.

### 5.2 Code execution + safety gate (from Open Interpreter, local-operator, smolagents)
- **Take three patterns, combined:** approve-before-run default + `-y` opt-out
  (Open Interpreter); independent AI safety-review pass (local-operator);
  pluggable sandbox backends — Docker/subprocess jail (smolagents).
- **Fit:** a `CodeTool.run()` that (a) optional safety-review verdict, (b)
  channel-prompted confirmation, (c) sandboxed execution. Confirmation rides
  your existing `Channel.send`/`listen` loop (a Telegram "approve? y/n").
- **Why:** biggest capability jump; turns talker into actor.
- **Avoid — sharply:** Open Interpreter *documented* container isolation while
  shipping only a Semgrep scan + "no guarantees" disclaimer. **Ship real
  isolation or label it experimental.** A broken security promise is worse than
  no feature for a privacy-branded tool.

### 5.3 Lifecycle hooks (from Cheshire Cat)
- **Take:** named pipeline interception points (`before_message`, `after_search`,
  `before_send`) — the "hooks" third of their hooks/tools/forms model.
- **Fit:** `handle()` is a closed linear pipeline today (`agent.py:199-218`).
  A few hook callouts let users redact/log/rewrite/inject without forking —
  the same swappability your `Channel`/`SearchProvider` already give. (The eval
  provider we built is this pattern applied from *outside*; hooks bring it in.)
- **Why:** community contributes behavior without you merging everything to core.
- **Avoid:** Cheshire is **GPL-3.0** — design only, never source. Skip "forms".

### 5.4 Channels expansion (from LocalAGI)
- **Take:** Discord/Slack/IRC/Email/GitHub connectors — each ~one file on your
  `Channel` ABC. Plus a registry/entry-point pattern so third-party channels
  install as separate packages and self-register (vs. hardcoding in
  `from_directory`, `agent.py:108-115`).
- **Reality check:** widens reach, not capability. Do it when chasing users.
  Keep **Telegram as a differentiator** — Khoj and Goose lack it.

### 5.5 Observability + optional GUI (from Letta ADE, Goose, Khoj, Cheshire)
- **Tier 1 (cheap, on-brand):** runtime introspection — a `--trace` flag on
  `lak bot` showing which tools fired, context size, tokens/turn. Makes
  "eval-driven" felt every turn; pairs with the tool-calling work.
- **Tier 2 (defer):** thin optional web panel for config + trace. Copyable
  detail from Goose: auto-populated dropdown of installed Ollama models.
- **Avoid:** Khoj/Goose/OI tie observability to **telemetry**. Keep yours
  local-only, on-demand — the contrast is a marketing asset.

### 5.6 Automations & multi-model routing (from Khoj, LocalAGI, local-operator)
- **Scheduled tasks** (Khoj/LocalAGI): a `schedule:` block in `agent.yaml` +
  small loop; pushes a morning briefing via `Channel.send`. Patrick already does
  briefing-style work.
- **Multi-model routing** (local-operator): small model for easy turns, big for
  hard — local-operator funnels this to *cloud* (Radient); **you'd do it fully
  local** (two Ollama models + cheap classifier), directly serving your
  hardware-bound audience. Differentiator *because* it's cloud-free.

### 5.7 RAG over documents (from Khoj, Cheshire) — FLAGGED memory-adjacent
- Khoj's biggest draw; Cheshire's fully-local blueprint = **FastEmbed + embedded
  Qdrant**, no external service. Once tool-calling exists, it's a `DocSearchTool`.
  *Flagged because archival doc-retrieval blurs into the separate memory track —
  maintainer's call where it belongs.*

### 5.8 Distribution & positioning (highest ROI/hour; not code)
- **Lead with privacy — now quantified:** you are the *only* one of ten that's
  local-default AND zero-telemetry AND zero-cloud-account. Make "nothing phones
  home, ever" a headline; back it with a comparison table (format borrowed from
  janhq / 500-AI-Agents).
- **Get listed:** `janhq/awesome-local-ai` (~2k★, Agents), `msb-msb/awesome-local-ai`,
  `jim-schwoebel/awesome_ai_agents`.
- **Use-case gallery** mined from 500-AI-Agents, reframed "$0/month, offline".
- **Crisp tagline** (Open Interpreter style); **docs polish** (Goose: versioned
  docs + one-line installer + a "what we don't collect" page — which reads
  stronger for us because the answer is *nothing*).

---

## 6. Suggested upgrade sequence (by dependency, not flash)

1. **Reconcile README claims vs. shipped code** (eval ✓ done; decide on tools).
2. **Tool-calling refactor** — replace `_maybe_search`; unblocks everything.
3. **MCP client adapter** — instant tool ecosystem on top of #2.
4. **Runtime introspection / `--trace`** — cheap, reinforces eval identity.
5. **Lifecycle hooks** — extensibility without core bloat.
6. **Code-exec tool + safety gate + real sandbox** — biggest jump; do it right
   or label experimental.
7. **Then** reach/polish: channels, scheduling, routing, GUI, RAG, listings.

---

## 7. Guardrails — what NOT to do

- **Don't become LocalAGI/Khoj.** Their weakness (4-service Docker stacks,
  Postgres, heavy installs) is your wedge: `pip install` + Ollama. Add
  everything as **opt-in modules/tools/hooks**, never mandatory infrastructure.
- **Don't chase code-exec autonomy as identity.** That's the saturated
  Open-Interpreter / local-operator lane. You're a *conversational assistant
  builder*; code-exec is a tool, not the product.
- **Don't add telemetry.** It would forfeit your single most defensible claim.
- **Don't promise safety you don't ship** (the Open Interpreter lesson).
- **Respect licenses:** Cheshire (GPL-3.0) and Khoj (AGPL-3.0) — borrow design,
  never source.

---

## Appendix — selected sources

- LocalAGI: github.com/mudler/LocalAGI · deepwiki.com/mudler/LocalAGI
- local-operator: github.com/damianvtran/local-operator · local-operator.com · radienthq.com
- 500-AI-Agents-Projects: github.com/ashishpatel26/500-AI-Agents-Projects
- awesome-local-ai: github.com/msb-msb/awesome-local-ai · github.com/janhq/awesome-local-ai
- Khoj: github.com/khoj-ai/khoj · docs.khoj.dev
- Cheshire Cat: github.com/cheshire-cat-ai/core · cheshirecat.ai
- Letta/MemGPT: github.com/letta-ai/letta · docs.letta.com
- Open Interpreter: github.com/openinterpreter/open-interpreter · docs.openinterpreter.com
- smolagents: github.com/huggingface/smolagents · huggingface.co/docs/smolagents
- goose: github.com/block/goose · goose-docs.ai
- promptfoo: promptfoo.dev/docs

*Star counts and dates approximate as of 2026-06-10; verify against the live
repos before citing externally.*
