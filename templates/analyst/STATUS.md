# STATUS — analyst

**State:** ready (peek-and-narrate); aggregation is direct-composition
**Last verified:** 2026-06-12

## What ships
- `agent.yaml` with `tools.file_read.roots: ["."]` and `data_peek_rows: 20`.
- IDENTITY enforces the narrate-only contract.
- `data_peek` (`local_agent_kit.tools.data_peek`) — a thin wrapper over
  `data_query` that returns the first N rows as a formatted table.
- `data_query` for direct user-authored aggregations.
- `_maybe_show_data` in `Agent.handle` — detects CSV/JSONL paths in
  user messages and auto-injects the head as `[SYSTEM DATA]`.
- Eval suite passes on `gemma4:e4b` for the narrate-only rubric.

## Run it

```bash
cd ~/your-project
lak bot templates/analyst
> What's in ./sales.csv?
```

The agent peeks the first 20 rows, sees column structure, and
narrates what it found without inventing values.

## What works vs what doesn't

**Works** — peek-and-narrate. Mention a `.csv` or `.jsonl` file under
the allowed roots; the agent gets a tabular head sample and describes
the columns + first rows accurately.

**Doesn't auto-work** — natural-language aggregation
("what's the total by region?"). gemma4:e4b cannot reliably generate
SQL against unknown schemas. For aggregation, compose `data_query`
directly:

```python
from local_agent_kit.tools.data_query import data_query
result = await data_query(
    "./sales.csv",
    "SELECT region, SUM(CAST(revenue AS INTEGER)) FROM data GROUP BY region",
    allowed_roots=["./"],
)
# Then pass `result` to Agent.handle, optionally via envelope().
```

The IDENTITY enforces no-fabrication-of-numbers, so even when the model
narrates the peek, it doesn't invent aggregations the data didn't include.

## Future unlock paths
- A larger local model (gemma4:12b+) generating reliable SQL would
  enable real NL→aggregation. Tracked as a `ModelRouter` trigger.
- A semantic schema cache (column types + sample values) injected as
  context would help even small models on a constrained subset of
  aggregations.
