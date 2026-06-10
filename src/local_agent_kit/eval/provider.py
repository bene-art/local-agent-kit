"""promptfoo custom provider — evaluates the full local-agent-kit pipeline.

promptfoo calls ``call_api(prompt, options, context)`` once per test case. We
wrap :meth:`Agent.handle` so evals exercise the *real* pipeline
(search detection → inject → Ollama), not just the raw model.

Everything runs locally: the agent talks to your local Ollama, and the grader
in ``promptfooconfig.yaml`` is itself a local Ollama model. No cloud account.

The agent directory is resolved in priority order:
  1. ``options["config"]["agent_dir"]``   (set in promptfooconfig.yaml)
  2. ``LAK_AGENT_DIR`` environment variable (set by ``lak eval``)
  3. the current working directory
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any, AsyncIterator

from local_agent_kit.agent import Agent
from local_agent_kit.channels.base import Channel, Message


class _NullChannel(Channel):
    """Headless channel for eval — never listens or sends.

    Lets us load an agent whose configured channel is Telegram without
    needing bot credentials; ``Agent.handle`` never touches the channel.
    """

    async def listen(self) -> AsyncIterator[Message]:  # pragma: no cover
        return
        yield  # noqa: unreachable — makes this an async generator

    async def send(self, text: str, thread_id: str = "") -> bool:
        return True


def _resolve_agent_dir(options: dict[str, Any]) -> Path:
    config = (options or {}).get("config") or {}
    agent_dir = config.get("agent_dir") or os.environ.get("LAK_AGENT_DIR") or "."
    return Path(agent_dir).expanduser().resolve()


def _build_agent(options: dict[str, Any]) -> Agent:
    """Construct a fresh agent for a single eval call."""
    config = (options or {}).get("config") or {}
    agent = Agent.from_directory(
        _resolve_agent_dir(options),
        channel=_NullChannel(),
    )
    # Opt-in: force web search off for deterministic, fully-offline evals.
    if config.get("web_search") is False:
        agent.search = None
    return agent


async def _run_once(agent: Agent, prompt: str) -> str:
    try:
        return await agent.handle(prompt)
    finally:
        if agent._session and not agent._session.closed:
            await agent._session.close()


def call_api(
    prompt: str,
    options: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Entry point promptfoo invokes for each test case.

    A fresh agent is built per call so conversation memory never bleeds
    between test cases — each eval row is independent.
    """
    options = options or {}
    try:
        agent = _build_agent(options)
        output = asyncio.run(_run_once(agent, prompt))
        return {"output": output}
    except Exception as exc:  # promptfoo expects failures in the return dict
        return {"error": f"{type(exc).__name__}: {exc}"}
