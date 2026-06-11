# Researcher template

Web search + grounded synthesis. The agent fetches results and answers from them — never from training data alone.

## Run it

```bash
lak bot templates/researcher
```

Ask external questions. The kit fetches results and injects them into the prompt as `[SYSTEM DATA]`; the model synthesizes from that.

## Search providers

- **DuckDuckGo** (default) — no API key required.
- **Gemini Search Grounding** — set `GEMINI_API_KEY` and change `search.provider` to `gemini` in `agent.yaml`. Higher-quality results.

## Eval

```bash
cd templates/researcher/eval && promptfoo eval
```

Cases test two things: that the model grounds claims in `[SYSTEM DATA]` when it is present, and that the model refuses to invent when it is not.

## Known limit (2026-06-11)

Last measured pass rate: **4/5 (80%)** on `gemma4:e4b` against live DuckDuckGo search.

The one failing case is a plausible-fictional-drug-name query: when a fictional name shape-matches a real drug class, the search returns content for the real class, and the model attributes that content to the fictional name. This is the small-local-model + real-search combination's ceiling on fuzzy-match cases. The IDENTITY explicitly forbids fuzzy-matching but `gemma4:e4b` is not reliable enough to honor it under search pressure.

Mitigations to consider when you build on this template:
- Swap to a larger local model (`gemma4:12b` and up tend to honor name-exactness better).
- Filter search results in Python before they reach the model (drop any result whose entity name doesn't match the user's query).
- Accept the limit and document it for end users.
