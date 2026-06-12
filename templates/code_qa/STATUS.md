# STATUS — code_qa

**State:** ready
**Last verified:** 2026-06-12

## What ships
- `agent.yaml` with `tools.file_read.roots: ["."]` — the agent
  auto-reads any file the user mentions under the working directory.
- `identity/IDENTITY.md`, `README.md`, eval cases.
- The `file_read` tool with path allowlist, name-pattern blocklist
  (api_key, secret, token, .env, ...), prefix-collision guard, and
  output cap. 10-test suite.
- Auto-injection into `Agent.handle` — detects file paths in user
  messages, reads them, wraps as `[SYSTEM DATA]` before the LLM call.
  6-test suite covering the injection path.

## Run it

```bash
cd ~/your-project
lak bot templates/code_qa
> Explain ./script.py
> What does main() do in ./src/cli.py?
> Suggest a fix for the bug in ./tests/test_thing.py
```

The agent reads the referenced file (must exist under `.`, must not be
a secret-shaped filename) and injects up to 4000 chars before responding.

## How it works
- `_PATH_RE` in `agent.py` matches paths starting with `./`, `../`, `~/`,
  or `/` that end in a recognized content extension.
- At most one file per turn is injected — keeps context bounded.
- Denials never reach the LLM as data — they're silently dropped so the
  model just sees the original question.

## Customize

Edit `tools.file_read.roots` in `agent.yaml`:

```yaml
tools:
  file_read:
    roots:
      - ~/code
      - ./project
    max_chars: 6000
```
