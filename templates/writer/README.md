# Writer template

A local agent for drafting, editing, and shaping prose. Runs entirely offline — no web search, no external tools, no cloud account.

## What this template does

Paste in a passage and ask for an edit, a rewrite in a different tone, or a draft. The agent returns only the result. No preamble.

## Run it

```bash
lak bot templates/writer
```

Then paste text and ask for what you want:

- "Edit this for clarity: ..."
- "Rewrite this more formally: ..."
- "Draft a paragraph about ... — keep it under 100 words."

## What it won't do

- No web search.
- No external tools.
- No facts the user didn't provide.

The default model is `gemma4:e4b` — small enough to run on consumer hardware, focused enough for prose work. Swap to a larger model in `agent.yaml` if you have the headroom.

## Eval

```bash
cd templates/writer/eval && promptfoo eval
```

The eval suite is the template's contract. If you change `IDENTITY.md` or the model, re-run the eval before committing the change.
