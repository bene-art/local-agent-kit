"""Promptfoo provider — runs an agent.yaml directory through Agent.handle().

Tests the full kit pipeline: load_config → search injection → Ollama. This
ensures promptfoo measures what the operator actually experiences, not raw
Ollama output stripped of the agent's IDENTITY and tool wiring.

Usage in promptfooconfig.yaml:

    providers:
      - id: python:src/local_agent_kit/eval/promptfoo_provider.py
        config:
          agent_dir: ../path/to/agent

The provider creates a fresh Agent per call, so no conversation history
bleeds between test cases. Override the model per provider with
`config.model`; override the system-wide default with the AGENT_MODEL env
var.
"""
from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def _get_loop():
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


async def _run_once(agent_dir: Path, prompt: str, model_override: str | None) -> str:
    from local_agent_kit.agent import Agent

    agent = Agent.from_directory(agent_dir)
    if model_override:
        agent.config.model = model_override

    try:
        return await agent.handle(prompt)
    finally:
        if agent._session and not agent._session.closed:
            await agent._session.close()


def call_api(prompt: str, options: dict, context: dict) -> dict:
    """Promptfoo calls this for each test case.

    Args:
        prompt: The rendered prompt (user message).
        options: Provider config from promptfooconfig.yaml. Expected keys:
            config.agent_dir  — path to the agent directory (required).
            config.model      — optional model override.
        context: Test context (vars, etc).

    Returns:
        {"output": "response text"} or {"error": "message"}
    """
    config = (options or {}).get("config", {}) or {}
    agent_dir_str = config.get("agent_dir")
    if not agent_dir_str:
        return {"error": "promptfoo provider config missing 'agent_dir'"}

    promptfoo_cwd = Path(os.environ.get("PROMPTFOO_CONFIG_DIR", ".")).resolve()
    agent_dir = (promptfoo_cwd / agent_dir_str).resolve()
    if not agent_dir.exists():
        return {"error": f"agent_dir not found: {agent_dir}"}

    model_override = config.get("model") or os.environ.get("AGENT_MODEL")

    try:
        loop = _get_loop()
        output = loop.run_until_complete(_run_once(agent_dir, prompt, model_override))
        return {"output": output}
    except Exception as exc:
        logger.exception("promptfoo provider call_api failed")
        return {"error": f"{type(exc).__name__}: {exc}"}
