# Changelog

All notable changes to `local-agent-kit` are tracked here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the project uses
SemVer.

## [Unreleased]

### Added
- **Eval harness powered by [promptfoo](https://www.promptfoo.dev).** New `lak eval <agent>` command runs promptfoo against the *full agent pipeline* (search → inject → Ollama) via a custom Python provider — not just the raw model. Runs 100% locally: the grader is a local Ollama model, no cloud account.
  - `local_agent_kit.eval.provider.call_api` — promptfoo Python-provider entry point (wraps `Agent.handle` with a headless channel; fresh agent per case so memory never bleeds between tests).
  - `local_agent_kit.eval.scaffold.scaffold_eval` — writes `<agent>/eval/{provider.py, promptfooconfig.yaml}` with example assertions.
  - `lak eval --init` to (re)scaffold, `lak eval --view` to open the results viewer.
  - `lak init` now scaffolds the eval config; `lak doctor` reports promptfoo/Node availability (optional).
- promptfoo is a Node CLI invoked via `npx` on demand — the kit's pip footprint is unchanged.

## [0.2.0] — 2026-06

### Added
- Smoke test suite (`tests/test_hardware.py`, `test_agent.py`, `test_channels.py`).
- GitHub Actions CI workflow (`.github/workflows/ci.yml`) — runs syntax check + pytest on Python 3.11 / 3.12 / 3.13.
- `lak --version` flag.
- `examples/patrick/` — kit-only Patrick configuration showing agent.yaml + IDENTITY.md.

### Changed
- **BREAKING:** Telegram env vars renamed from `PAT_TG_BOT_TOKEN` / `PAT_TG_CHAT_ID` to `TG_BOT_TOKEN` / `TG_CHAT_ID`. The `PAT_` prefix was Patrick-specific branding in a generic kit. Update your `.env` files.
- `lak init` generates the new env var names in scaffolded agents.

### Fixed
- Generated `.env` no longer leaks Patrick-branded variable names.

## [0.1.0] — 2026-04

### Added
- Initial release.
- `lak` CLI: `init`, `doctor`, `bot`, `hardware`.
- Hardware detection (macOS / Linux) + Ollama model recommendation table.
- Pluggable channels: CLI, Telegram.
- Pluggable search providers: DuckDuckGo (no API key), Gemini Flash (grounding).
- `Agent` runtime with inline `[SYSTEM DATA]` injection.
