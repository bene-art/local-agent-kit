"""Agent — the core runtime that connects channels, search, and Ollama.

This is the main loop: listen for messages, detect tool needs,
fetch data, call the local LLM, respond.

Usage:
    agent = Agent.from_directory("./my-agent")
    await agent.run()
"""
from __future__ import annotations

import asyncio
import inspect
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import aiohttp
import yaml

from local_agent_kit.channels.base import Channel, Message
from local_agent_kit.patterns.narrate_only import envelope
from local_agent_kit.scheduling.schedule import ScheduledTask, load_schedules
from local_agent_kit.search.base import SearchProvider

logger = logging.getLogger(__name__)


def _resolve_dotted(path: str) -> Any:
    """Import a callable from a dotted path like 'pkg.mod:fn' or 'pkg.mod.fn'."""
    import importlib

    if ":" in path:
        mod_path, attr = path.split(":", 1)
    else:
        mod_path, _, attr = path.rpartition(".")
    if not mod_path or not attr:
        raise ValueError(f"invalid dotted path: {path!r}")
    return getattr(importlib.import_module(mod_path), attr)


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

    # Tool toggles
    web_search: bool = True
    memory_enabled: bool = True
    memory_max_history: int = 20

    # Disable Ollama's reasoning-token phase. Default True (kept on) because
    # most templates benefit from it. Templates with tight num_predict budgets
    # (briefer, anything narrate-only) should set this to False — otherwise
    # the thinking phase can eat the entire token budget before any visible
    # content is generated.
    think: bool = True

    # file_read tool config. If `roots` is non-empty, Agent.handle auto-
    # injects file contents for paths it detects in user messages.
    file_read_roots: list[str] = field(default_factory=list)
    file_read_max_chars: int = 3000
    # Number of rows to peek when a CSV/JSONL path is mentioned (the
    # data_peek auto-injection path). Set to 0 to disable peek and fall
    # back to raw file_read for data files.
    data_peek_rows: int = 20

    # Schedules — parsed from the `schedules:` block in agent.yaml.
    # Empty list if no schedules are declared. The LocalScheduler runtime
    # (croniter dep) is only loaded when this list is non-empty.
    schedules: list[ScheduledTask] = field(default_factory=list)


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

        tools = data.get("tools", {})
        config.web_search = tools.get("web_search", config.web_search) if not isinstance(tools.get("web_search"), dict) else config.web_search

        # file_read config: tools.file_read can be a bool (legacy / disable)
        # or a mapping with roots + max_chars + data_peek_rows.
        fr = tools.get("file_read")
        if isinstance(fr, dict):
            roots = fr.get("roots") or []
            if isinstance(roots, list):
                config.file_read_roots = [str(r) for r in roots]
            config.file_read_max_chars = int(fr.get("max_chars", config.file_read_max_chars))
            config.data_peek_rows = int(fr.get("data_peek_rows", config.data_peek_rows))

        mem = data.get("conversation_memory", {})
        config.memory_enabled = mem.get("enabled", config.memory_enabled)
        config.memory_max_history = mem.get("max_history", config.memory_max_history)

        if "think" in data:
            config.think = bool(data["think"])

        config.schedules = load_schedules(data)

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

        # Default to the CLI channel; pass a Channel instance for anything else.
        if channel is None:
            from local_agent_kit.channels.cli_channel import CLIChannel
            channel = CLIChannel(agent_name=config.name)

        # Search is config-driven: `search.provider` in agent.yaml decides,
        # never the environment. 'none' means no outbound search requests
        # even when tools.web_search is left on.
        if search is None and config.web_search:
            if config.search_provider == "duckduckgo":
                from local_agent_kit.search.duckduckgo_search import DuckDuckGoSearch
                search = DuckDuckGoSearch()
            elif config.search_provider != "none":
                raise ValueError(
                    f"unknown search.provider {config.search_provider!r} — "
                    "use 'duckduckgo', 'none', or pass a SearchProvider instance "
                    "to Agent.from_directory(search=...)"
                )

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

        # Add conversation history (unless the agent is configured stateless)
        if self.config.memory_enabled:
            messages.extend(self._history[-self.config.memory_max_history:])

        # Add current message
        messages.append({"role": "user", "content": user_msg})

        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
            # Templates with tight num_predict budgets must set think:false
            # in agent.yaml — otherwise the model's reasoning phase can eat
            # the entire token budget before any visible content is generated.
            "think": self.config.think,
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

    # Match local file paths users actually type. Anchored on a clear
    # path prefix (./, ../, ~/, or /) followed by at least one path
    # component, ending in a common content extension. Conservative on
    # purpose — false positives become unwanted disk reads.
    #
    # Two regexes: text files get raw file_read; data files get a
    # tabular peek via data_query so the model sees structure, not raw bytes.
    _DATA_PATH_RE = re.compile(r"(?:\.\.?/|~/|/)[\w\-./]+\.(?:csv|jsonl)\b")
    _TEXT_PATH_RE = re.compile(
        r"(?:\.\.?/|~/|/)[\w\-./]+\.(?:md|txt|py|js|ts|tsx|json|yaml|yml|html|css|sh|rs|go|toml|ini|conf|sql)\b"
    )

    async def _maybe_read_file(self, text: str) -> str:
        """If the message mentions a non-data file inside an allowed root,
        read it and return a [SYSTEM DATA] envelope. Otherwise empty."""
        if not self.config.file_read_roots:
            return ""

        matches = self._TEXT_PATH_RE.findall(text)
        if not matches:
            return ""

        from local_agent_kit.tools.file_read import file_read

        # Read at most one file per turn — keeps the context bounded and
        # the behavior predictable.
        path = matches[0]
        content = await file_read(
            path,
            allowed_roots=self.config.file_read_roots,
            max_chars=self.config.file_read_max_chars,
        )
        # Don't inject denial envelopes — they're not data, they're noise.
        if content.startswith("[") and content.endswith("]"):
            return ""
        return f"\n\n[SYSTEM DATA — file_read {path}]\n{content}"

    async def _maybe_show_data(self, text: str) -> str:
        """If the message mentions a CSV/JSONL file inside an allowed root,
        peek the first N rows and return a [SYSTEM DATA] envelope.

        Distinct from _maybe_read_file because data files look better as
        a formatted table than as raw bytes. Set data_peek_rows: 0 in
        agent.yaml to disable this and route data files through raw file_read.
        """
        if not self.config.file_read_roots or self.config.data_peek_rows <= 0:
            return ""

        matches = self._DATA_PATH_RE.findall(text)
        if not matches:
            return ""

        from local_agent_kit.tools.data_query import data_peek

        path = matches[0]
        content = await data_peek(
            path,
            allowed_roots=self.config.file_read_roots,
            n_rows=self.config.data_peek_rows,
        )
        if content.startswith("[") and content.endswith("]"):
            return ""
        return f"\n\n[SYSTEM DATA — head of {path}]\n{content}"

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

        # Check for file_read auto-injection (paths in the message)
        file_context = await self._maybe_read_file(text)

        # Check for data peek (CSV/JSONL paths)
        data_context = await self._maybe_show_data(text)

        # Build the full message with any tool context
        full_msg = text + search_context + file_context + data_context

        # Call the LLM
        response = await self._ollama_chat(full_msg)

        # Empty-response guard — small local models sometimes return whitespace
        # when they have nothing useful to say. Replace with an explicit refusal
        # so the user never sees silence.
        if not response or not response.strip():
            response = "I do not have data on that right now."

        # Update conversation history (skipped entirely for stateless agents,
        # so one turn's output can never leak into the next)
        if self.config.memory_enabled:
            self._history.append({"role": "user", "content": text})
            self._history.append({"role": "assistant", "content": response})
            if len(self._history) > self.config.memory_max_history:
                self._history = self._history[-self.config.memory_max_history:]

        return response

    async def _run_scheduled_task(self, task: ScheduledTask) -> None:
        """Fire one ScheduledTask through Agent.handle + the agent's channel.

        If the task names a fetcher, call it first, wrap its output as
        [SYSTEM DATA], and append to the task's prompt — the "Python computes,
        model narrates" pattern.
        """
        full_prompt = task.prompt
        if task.fetcher:
            # Resolution failures (bad dotted path, module not importable)
            # must be contained here like call failures — otherwise they
            # escape to the scheduler loop and the task dies silently.
            try:
                fn = _resolve_dotted(task.fetcher)
                data = await fn() if inspect.iscoroutinefunction(fn) else fn()
            except Exception:
                logger.exception("fetcher %s failed for task %s", task.fetcher, task.name)
                return
            if not isinstance(data, str):
                data = str(data)
            full_prompt = task.prompt + envelope(task.name, data)

        response = await self.handle(full_prompt)
        await self.channel.send(response, thread_id=None)

    async def run(self) -> None:
        """Main loop: listen → handle → respond. Drives the scheduler too."""
        scheduler = None
        if self.config.schedules:
            try:
                from local_agent_kit.scheduling.local_scheduler import LocalScheduler
            except ImportError as exc:
                raise RuntimeError(
                    "agent.yaml declares schedules but croniter is not installed. "
                    "Install with: pip install local-agent-kit[schedule]"
                ) from exc
            scheduler = LocalScheduler(runner=self._run_scheduled_task)
            for task in self.config.schedules:
                await scheduler.add(task)
            await scheduler.start()

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
            if scheduler is not None:
                await scheduler.stop()
            await self.channel.stop()
            if self._session and not self._session.closed:
                await self._session.close()
