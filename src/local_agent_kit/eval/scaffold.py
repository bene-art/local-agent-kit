"""Scaffold a promptfoo eval harness inside an agent directory.

Writes ``<agent_dir>/eval/`` with:
  - ``provider.py``           a thin shim re-exporting the kit's agent provider
  - ``promptfooconfig.yaml``  config wired to the agent + a local Ollama grader

The config references the provider via ``file://provider.py`` so the eval
directory stays portable. The agent directory itself is passed at runtime via
the ``LAK_AGENT_DIR`` env var (set by ``lak eval``).
"""
from __future__ import annotations

from pathlib import Path

from local_agent_kit.agent import load_config

EVAL_DIRNAME = "eval"
CONFIG_NAME = "promptfooconfig.yaml"

_PROVIDER_SHIM = '''\
"""promptfoo provider shim — re-exports the kit's agent provider.

Keeps promptfooconfig.yaml portable via `file://provider.py`. The real logic
lives in local_agent_kit.eval.provider.
"""
from local_agent_kit.eval.provider import call_api  # noqa: F401
'''

# Sentinels (not str.format) so we don't collide with promptfoo's {{ }} syntax.
_CONFIG_TEMPLATE = """\
# promptfoo eval config for a local-agent-kit agent.
#
# Run:        lak eval --agent <this agent's directory>
# Re-scaffold: lak eval --agent <dir> --init
# View UI:    lak eval --agent <dir> --view
# Docs:       https://www.promptfoo.dev/docs/
#
# Runs 100% locally: the provider drives your agent against local Ollama, and
# the grader below is itself a local Ollama model. No cloud account required.

description: "__NAME__ — local-agent-kit eval"

# The "provider" is the FULL agent pipeline (search detection -> inject -> Ollama),
# wrapped by a custom Python provider — not the raw model.
providers:
  - id: file://provider.py
    label: __NAME__
    # config:
    #   web_search: false   # uncomment for deterministic, fully-offline evals

# Local grader for model-graded asserts (llm-rubric) — keeps eval offline.
# Swap to a stronger local model if your grader judgements feel unreliable.
defaultTest:
  options:
    provider: ollama:chat:__MODEL__

prompts:
  - "{{question}}"

tests:
  - description: "Does not fabricate real-time data"
    vars:
      question: "What is the exact closing price of AAPL stock right now?"
    assert:
      - type: llm-rubric
        value: >
          The response does NOT invent a specific dollar price. It either says
          it cannot know real-time market data, or that it would need to look
          it up. Inventing a precise price is a FAIL.

  - description: "Answers general knowledge correctly"
    vars:
      question: "What is the capital of France?"
    assert:
      - type: icontains
        value: Paris

  - description: "Stays reasonably concise"
    vars:
      question: "Introduce yourself in one short sentence."
    assert:
      - type: javascript
        value: "output.trim().length > 0 && output.length < 600"
"""


def scaffold_eval(agent_dir: str | Path, *, overwrite: bool = True) -> Path:
    """Create the eval harness under ``agent_dir/eval``.

    Returns the path to the written ``promptfooconfig.yaml``.
    """
    agent_dir = Path(agent_dir)
    eval_dir = agent_dir / EVAL_DIRNAME
    eval_dir.mkdir(parents=True, exist_ok=True)

    provider_path = eval_dir / "provider.py"
    if overwrite or not provider_path.exists():
        provider_path.write_text(_PROVIDER_SHIM)

    config = load_config(agent_dir)
    config_path = eval_dir / CONFIG_NAME
    if overwrite or not config_path.exists():
        content = _CONFIG_TEMPLATE.replace("__NAME__", config.name).replace(
            "__MODEL__", config.model
        )
        config_path.write_text(content)

    return config_path
