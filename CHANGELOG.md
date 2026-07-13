# Changelog

All notable changes to `local-agent-kit` are tracked here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the project uses
SemVer.

## [0.4.0] — 2026-07-13

Focus release: the kit is now local-first end to end. Everything that
required a cloud account is gone; the core runtime gained real test
coverage and a set of correctness fixes.

### Removed
- **BREAKING:** Gemini search provider. A cloud search API contradicted
  the zero-cloud-account premise. DuckDuckGo (no key, no account) is the
  bundled provider; custom providers implement `SearchProvider` and are
  passed to `Agent.from_directory(search=...)`.
- **BREAKING:** Telegram channel. The CLI channel is the only bundled
  surface; custom channels implement the `Channel` ABC and are passed to
  `Agent.from_directory(channel=...)`. The `channel:` key in agent.yaml
  and the `channel:` field on schedule entries are gone (both were
  parsed but never routed anything).
- **BREAKING:** researcher, briefer, code_qa, interviewer, and analyst
  templates. Three exemplars remain — writer (plain chat), journal
  (memory + verified zero-outbound), study_buddy (StateFlow +
  QuizProgress) — one per primitive stack.

### Fixed
- `SQLiteMemory.history(limit)` returned the *oldest* N rows instead of
  the newest — journal session restore was silently dropping the most
  recent turns.
- `search.provider` in agent.yaml was decorative: a `GEMINI_API_KEY` in
  the environment silently flipped agents to the cloud regardless of
  config, and `provider: none` did not disable search. The field is now
  authoritative; unknown values fail at boot.
- `conversation_memory.enabled: false` was ignored — stateless agents
  still accumulated history across turns.
- `data_query` keyword blocklist matched substrings, rejecting queries
  that touch columns like `created_at` or `last_updated`.
- Scheduled-task fetcher *resolution* failures escaped containment and
  silently killed the task in the scheduler loop.
- `Channel` ABC signatures (`listen` as async-generator-compatible `def`,
  `send` accepts `thread_id=None`) — conforming implementations no
  longer produce type errors, and third-party channels won't crash on
  scheduled-task sends.
- `lak doctor` counted RAM/chip failures as passing.
- `lak --version` reported a stale hardcoded version; `__version__` now
  derives from package metadata.

### Added
- Agent core test coverage: `handle`, `_ollama_chat` (success / HTTP
  error / connection failure), `_maybe_search` heuristics, scheduled
  fires, fetcher containment. 114 tests total.
- `py.typed` marker — the kit's annotations are visible to downstream
  mypy users.
- CI lint job: ruff, mypy, and the pre-commit privacy gate (secrets scan
  + internal-vocab scrub) now run on every push and PR. Test matrix
  extended to Python 3.14.

## [0.3.0] — 2026-06-12

### Added
- Templates: writer, researcher, briefer, code_qa, interviewer, journal,
  study_buddy, analyst — each with an evaluated promptfoo suite and
  STATUS.md.
- Tools: `file_read` + `list_files` (sandboxed, allowlist + blocklist),
  `data_query` (CSV/JSONL → in-memory SQLite SELECT), `data_peek`.
- Memory: `Memory` protocol, `SQLiteMemory` backend, `QuizProgress`.
- Patterns: `narrate_only` (envelope + NarrationRubric), `StateFlow`.
- Scheduling: declarative `schedules:` block, `LocalScheduler` runtime
  (optional `schedule` extra), fetcher dispatch.
- Agent: inline auto-injection for file paths and CSV/JSONL peeks,
  per-template `think:` flag, empty-response guard.
- Eval: promptfoo provider wrapping the full kit pipeline.
- `lak templates list`.

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
