"""Agent — the core runtime that connects channels, search, and Ollama.

This is the main loop: listen for messages, detect tool needs,
fetch data, call the local LLM, respond.

Usage:
    agent = Agent.from_directory("./my-agent")
    await agent.run()
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import aiohttp
import yaml

from local_agent_kit.channels.base import Channel, Message
from local_agent_kit.search.base import SearchProvider

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Agent configuration loaded from agent.yaml."""
    name: str = "Agent"
    model: str = "gemma3:12b"
    temperature: float = 0.4
    max_tokens: int = 350
    system_prompt: str = ""
    ollama_host: str = "http://localhost:11434"
    search_provider: str = "none"
    channel: str = "cli"

    # Tool toggles
    web_search: bool = True
    memory_enabled: bool = True
    memory_max_history: int = 20


def load_config(agent_dir: Path) -> AgentConfig:
    """Load agent config from agent.yaml + IDENTITY.md."""
    config = AgentConfig()

    # Load agent.yaml
    yaml_path = agent_dir / "agent.yaml"
    if yaml_path.exists():
        data = yaml.safe_load(yaml_path.read_text()) or {}
        config.name = data.get("name", config.name)
        config.model = data.get("model", config.model)
        config.temperature = data.get("temperature", config.temperature)
        config.max_tokens = data.get("max_tokens", config.max_tokens)
        config.ollama_host = data.get("ollama_host", config.ollama_host)
        config.search_provider = data.get("search", {}).get("provider", "none") if isinstance(data.get("search"), dict) else data.get("search_provider", "none")
        config.channel = data.get("channel", config.channel)

        tools = data.get("tools", {})
        config.web_search = tools.get("web_search", config.web_search)

        mem = data.get("conversation_memory", {})
        config.memory_enabled = mem.get("enabled", config.memory_enabled)
        config.memory_max_history = mem.get("max_history", config.memory_max_history)

    # Load system prompt from IDENTITY.md
    identity_path = agent_dir / "identity" / "IDENTITY.md"
    if identity_path.exists():
        config.system_prompt = identity_path.read_text()

    # Load .env from agent dir
    env_path = agent_dir / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

    return config


class Agent:
    """The core agent runtime."""

    def __init__(
        self,
        config: AgentConfig,
        channel: Channel,
        search: SearchProvider | None = None,
    ):
        self.config = config
        self.channel = channel
        self.search = search
        self._session: aiohttp.ClientSession | None = None
        self._history: list[dict[str, str]] = []

    @classmethod
    def from_directory(cls, agent_dir: str | Path, channel: Channel | None = None, search: SearchProvider | None = None) -> "Agent":
        """Create an agent from a directory created by `lak init`."""
        agent_dir = Path(agent_dir)
        config = load_config(agent_dir)

        # Auto-select channel if not provided
        if channel is None:
            if config.channel == "telegram":
                from local_agent_kit.channels.telegram_channel import TelegramChannel
                channel = TelegramChannel()
            else:
                from local_agent_kit.channels.cli_channel import CLIChannel
                channel = CLIChannel(agent_name=config.name)

        # Auto-select search if not provided
        if search is None and config.web_search:
            gemini_key = os.environ.get("GEMINI_API_KEY")
            if gemini_key:
                from local_agent_kit.search.gemini_search import GeminiSearch
                search = GeminiSearch()
            else:
                from local_agent_kit.search.duckduckgo_search import DuckDuckGoSearch
                search = DuckDuckGoSearch()

        return cls(config=config, channel=channel, search=search)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _ollama_chat(self, user_msg: str) -> str:
        """Call Ollama's chat API."""
        session = await self._get_session()

        messages = []
        if self.config.system_prompt:
            messages.append({"role": "system", "content": self.config.system_prompt})

        # Add conversation history
        messages.extend(self._history[-self.config.memory_max_history:])

        # Add current message
        messages.append({"role": "user", "content": user_msg})

        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            },
        }

        try:
            async with session.post(
                f"{self.config.ollama_host}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                if resp.status != 200:
                    error = await resp.text()
                    return f"[LLM error: {error[:200]}]"
                data = await resp.json()
                return data.get("message", {}).get("content", "")
        except Exception as exc:
            logger.error("Ollama chat failed: %s", exc)
            return f"[LLM unavailable: {exc}]"

    async def _maybe_search(self, text: str) -> str:
        """Check if the message needs a web search and fetch results."""
        if not self.search:
            return ""

        # Simple heuristic: does this look like an external question?
        ml = text.lower()

        internal_keywords = {
            "identity", "soul", "system", "architecture",
            "config", "daemon", "briefing",
        }
        is_internal = any(kw in ml for kw in internal_keywords)

        is_question = any(ml.startswith(q) for q in [
            "what", "who", "where", "when", "how", "why", "is ",
            "are ", "did ", "does ", "can ", "tell", "show", "any ",
        ])

        if is_question and not is_internal and len(text) > 10:
            result = await self.search.search(text)
            if result and not result.startswith("["):
                return f"\n\n[SYSTEM DATA — web search results]\n{result}"

        return ""

    async def handle(self, text: str) -> str:
        """Handle a single message: search → inject → LLM → respond."""
        # Check for web search
        search_context = await self._maybe_search(text)

        # Build the full message with any tool context
        full_msg = text + search_context

        # Call the LLM
        response = await self._ollama_chat(full_msg)

        # Update conversation history
        self._history.append({"role": "user", "content": text})
        self._history.append({"role": "assistant", "content": response})

        # Trim history
        if len(self._history) > self.config.memory_max_history:
            self._history = self._history[-self.config.memory_max_history:]

        return response

    async def run(self) -> None:
        """Main loop: listen → handle → respond."""
        await self.channel.start()

        try:
            async for msg in self.channel.listen():
                try:
                    response = await self.handle(msg.text)
                    await self.channel.send(response, thread_id=msg.thread_id)
                except Exception as exc:
                    logger.error("Error handling message: %s", exc)
                    await self.channel.send(
                        f"Something went wrong. Error: {type(exc).__name__}",
                        thread_id=msg.thread_id,
                    )
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass
        finally:
            await self.channel.stop()
            if self._session and not self._session.closed:
                await self._session.close()
