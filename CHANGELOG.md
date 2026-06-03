# Changelog

All notable changes to `local-agent-kit` are tracked here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the project uses
SemVer.

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
