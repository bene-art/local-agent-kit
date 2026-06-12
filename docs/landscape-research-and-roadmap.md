# local-agent-kit — Landscape & Roadmap

Last updated: 2026-06-11

This doc consolidates the landscape research and the upgrade plan into one place.
Memory and tool-calling are owned by separate tracks; both surface here only as
integration points.

---

## North Star

Build the local-first agent kit whose wedge is **privacy + zero telemetry + zero
cloud account + `pip install` + Ollama** — none of the comparable nine projects
in the landscape offer all four. Every primitive ships as an **opt-in
module/hook**, never mandatory infrastructure. The moment the kit needs a Docker
stack, the wedge is lost.

## Underlying question this roadmap exists to answer

> How good can a local model on consumer hardware actually get, and where is the
> ceiling for Patrick's scope vs. the broader frontier-agent scope?

Roadmap items are sorted by how much they move the needle on that question.
Productization items (distribution, extensibility) sit behind a **measurement
gate** — we don't ship wrappers around a capability claim we haven't measured.

## Scope boundary (be honest about this)

- **Patrick's scope** — memory-grounded chat, search synthesis, briefings, tool
  calling, code Q&A on small surfaces. Local on consumer hardware is *already
  there or within ~6 months*. This is the bet the kit is sized for.
- **Frontier-general scope** — novel multi-file coding, long-horizon planning
  with self-correction, agentic loops that don't compound errors. Local is
  12–24 months behind cloud and the gap may not close. **Out of scope.**

The eval suite is what tells us when a use case has crossed from the first
category into the second.

---

## Tracks owned elsewhere (integration points only)

- **Tools / MCP / sandbox** — separate work track. The kit consumes the tool
  abstraction; we don't define it here.
- **Memory** — separate work track. `Retriever` / `DocStore` belongs here.

## Done this session

- **promptfoo eval harness** (`lak eval`) — `EvalProvider` wraps
  `Agent.handle()`. Establishes the "wrap the agent from outside" idiom that
  later phases build on.

---

## Phases

### Phase 0 — Reconcile (gate for everything else)

Make the repo match reality before adding anything.

- Integrate the separately-developed tools + memory tracks into the kit's main
  line, or confirm where they live and define the surface between them.
- Align the README with shipped code — the eval claim is now true; confirm
  tools/memory claims are too.
- **Honest scoping note:** if tools/memory developed independently, defining
  their surface to the kit is days, not hours. This is the gate; don't
  underestimate it.
- **Acceptance:** `lak doctor` + tests green; README describes only what's in
  the package.

### Phase 1 — Observability + the eval capture loop

The two primitives that turn the eval harness from synthetic to real-data-driven.
Highest leverage on the underlying question.

- **`Tracer` / `lak bot --trace`** — per-turn record: did search/a tool fire,
  context size, tokens, latency. Local-only, never telemetry. *(S)*
- **`EvalCase` capture loop** — `EvalCase.from_trace()` + `lak eval capture`:
  snapshot a real failing turn into the promptfoo suite. Closes the loop:
  run → observe → capture → regression-guard. *(M)*
- **Rubric authorship** (open question): assertions are not automatic. Two
  candidate flows:
  1. Capture → prompt for rubric (or `llm-rubric` template) → save.
  2. Capture → autoresearch proposes rubric → human accepts/edits → frozen
     into suite. Avoids grading against a drifting oracle.
  Default to flow 2 if autoresearch is available; fall back to 1 otherwise.
- **Acceptance:** a misbehaving turn can be captured and re-run as a promptfoo
  test in two commands plus one rubric review.

### Phase 2 — Measurement (no build; the missing phase)

**The decision-maker.** After Phase 1, run real Patrick traffic against the
suite for N weeks before building anything else. The output of this phase is
evidence, not code.

- Run Patrick (and any other agents on the kit) normally; capture failures via
  the Phase 1 loop as they occur.
- Track, per model: tool-call reliability, multi-turn coherence, search
  synthesis quality, code Q&A, briefing quality, latency, context efficiency.
- Define crossing thresholds *before* measuring (no moving goalposts):
  - Router trigger: E4B fails >X% of coding turns in suite (X to be set in
    this phase).
  - Model-swap trigger: E4B fails >Y% on Patrick scope overall.
  - Productization gate: capability is sufficient on Patrick scope → Phase 3+
    is justified. If not, Phase 3+ is premature regardless of how
    demo-worthy.
- **Acceptance:** a written measurement readout that says one of:
  (a) capability sufficient → proceed to productization;
  (b) capability insufficient → swap model / build router / narrow scope;
  (c) inconclusive → extend measurement period.

### Phase 3 — Productization (gated by Phase 2)

Only build these once Phase 2 says capability is sufficient. Order within is
driven by the win condition (see below).

- **`Schedule` / `Automation`** — `schedule:` block in `agent.yaml` running on
  cron, pushing via `Channel.send`. Local "morning briefing on Telegram,
  $0/month" — something Khoj does only via cloud. The most demo-worthy item
  and lands adopters. *(M)*
- **`Hook` / `HookManager`** — lifecycle events in `handle()`
  (`before_message`, `after_search`, `before_send`, `after_message`) so users
  redact/log/rewrite/inject without forking. Helps contributors extend.
  Borrow Cheshire's *design* only (GPL-3.0). *(M)*
- **Ordering depends on win condition:**
  - If win = adopters / demos / awesome-list listings → **Schedule first.**
  - If win = contributor extensibility / community PRs → **Hooks first.**
  - The win condition needs to be stated before this phase starts.

### Phase 4 — Reach & positioning (parallel, non-code)

Highest ROI per hour; can run alongside any phase.

- Lead with privacy, quantified: only project of the surveyed ten with
  local-default AND zero telemetry AND zero cloud account AND `pip install`.
  Headline + comparison table.
- Get listed: `janhq/awesome-local-ai` (~2k★), `msb-msb/awesome-local-ai`,
  `jim-schwoebel/awesome_ai_agents`.
- Use-case gallery mined from 500-AI-Agents, reframed "$0/month, offline."
- Docs polish: versioned docs, one-line installer, a "what we don't collect"
  page (the honest answer: nothing).

---

## Conditional / deferred

- **`ModelRouter`** — only when Phase 2 says E4B fails >X% of coding turns.
  Eval-driven decision, not a vibe. Trigger threshold defined in Phase 2.
- **`Retriever` / `DocStore`** — owned by the memory track. Listed for
  completeness, not built here.
- **More channels (Discord, Slack, …)** — when chasing users, not capability.
  Telegram stays the differentiator until reach demands more.
- **GUI** — large surface that fights minimalism. Defer; if ever built, make
  it a thin optional panel over the Phase 1 trace view.

---

## At a glance

| Phase | Build | Effort | Depends on | Verdict |
|---|---|---|---|---|
| 0 | Reconcile tools/memory/README | S–M | — | Required |
| 1 | `Tracer`, `EvalCase` capture | S+M | Phase 0 | **Build first** |
| 2 | **Measurement period (no build)** | — | Phase 1 | **Gate** |
| 3 | `Schedule`, `Hook`/`HookManager` | M each | Phase 2 verdict | Gated |
| 4 | Positioning / listings / docs | — | — | Parallel, high ROI |
| — | `ModelRouter` | M | Phase 2 trigger | Defer |
| — | `Retriever` | — | memory track | Hand off |
| — | Channels / GUI | S–L | demand | Defer |

**Critical path:** 0 → 1 → 2 → decide. Phase 3 only fires if Phase 2 clears
the capability gate. Phase 4 runs in parallel throughout.

## Open questions to resolve before Phase 3

1. **Win condition for the kit.** Stars? Demos at Chicago AI Tinkerers? Active
   pip installs? Contributor PRs? Drives Phase 3 ordering.
2. **Router trigger threshold.** What's the X% failure rate on coding turns
   that justifies escalating from E4B to a larger local model? Set during
   Phase 2.
3. **Scope creep guard.** If measurement shows a use case has crossed from
   Patrick scope into frontier-general scope, do we narrow back or accept
   cloud for that case? Default: narrow back.
