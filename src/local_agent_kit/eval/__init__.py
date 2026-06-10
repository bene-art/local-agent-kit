"""Eval harness — evaluate a local-agent-kit agent with promptfoo.

promptfoo (https://www.promptfoo.dev) is a local-first LLM eval runner. The
kit ships a custom provider that drives the full agent pipeline against local
Ollama, plus a scaffolder that writes a ready-to-run config into an agent dir.

Public surface:
    call_api      promptfoo Python-provider entry point
    scaffold_eval write eval/{provider.py, promptfooconfig.yaml} into an agent
"""
from local_agent_kit.eval.provider import call_api
from local_agent_kit.eval.scaffold import (
    CONFIG_NAME,
    EVAL_DIRNAME,
    scaffold_eval,
)

__all__ = ["call_api", "scaffold_eval", "EVAL_DIRNAME", "CONFIG_NAME"]
