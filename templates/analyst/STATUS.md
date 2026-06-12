# STATUS — analyst

**State:** primitive ready; auto-injection runner pending
**Last verified:** 2026-06-12

## What ships
- `agent.yaml`, `identity/IDENTITY.md`, `README.md`, eval cases.
- IDENTITY enforces the narrate-only contract — Python computes,
  model narrates.
- `data_query` tool (`local_agent_kit.tools.data_query`) — loads a
  CSV or JSONL file into an in-memory SQLite table called `data`,
  runs validated SELECT queries, returns formatted rows. 9-test suite.
- `file_read` tool also available for inspecting raw files.
- `narrate_only.envelope()` for wrapping query results as `[SYSTEM DATA]`.

## What runs today

Compose `data_query` + `envelope()` + `Agent.handle()` directly:

```python
from local_agent_kit.agent import Agent
from local_agent_kit.tools.data_query import data_query
from local_agent_kit.patterns.narrate_only import envelope

agent = Agent.from_directory("templates/analyst")
result = await data_query(
    "./sales.csv",
    "SELECT region, SUM(CAST(revenue AS INTEGER)) FROM data GROUP BY region",
    allowed_roots=["./"],
)
prompt = "Describe these results." + envelope("sales by region", result)
response = await agent.handle(prompt)
```

The eval suite (`templates/analyst/eval/`) tests the IDENTITY rules
against pre-formatted [SYSTEM DATA] blocks — runs today.

## What is still pending

- A `run_analyst.py` runner that detects file references in user
  messages, calls `data_query`, and injects the result automatically.
  The current pattern requires the user to write Python.
- Auto-injection into `Agent.handle` based on detected file paths.

## Acceptance for full unblock
- `lak bot templates/analyst` accepts natural-language queries like
  "what's the total revenue by region in ./sales.csv?" and routes them
  through `data_query` automatically.
- Eval suite still passes against `gemma4:e4b` (no fabricated numbers —
  verifiable by `NarrationRubric`).
