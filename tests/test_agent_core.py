"""Tests for the Agent runtime core: handle, _ollama_chat, _maybe_search,
and scheduled-task fires.

Ollama is never called — the HTTP layer is mocked at aiohttp.ClientSession
(same approach as test_journal_privacy) or _ollama_chat is stubbed directly.
"""
from __future__ import annotations

import aiohttp

from local_agent_kit.agent import Agent, AgentConfig
from local_agent_kit.channels.base import Channel, Message
from local_agent_kit.scheduling.schedule import ScheduledTask
from local_agent_kit.search.base import SearchProvider


class RecordingChannel(Channel):
    """Channel stub that records sends — also exercises ABC conformance."""

    def __init__(self):
        self.sent: list[tuple[str, str | None]] = []

    async def listen(self):
        return
        yield Message(text="")  # pragma: no cover — makes this an async generator

    async def send(self, text: str, thread_id: str | None = None) -> bool:
        self.sent.append((text, thread_id))
        return True


class FakeSearch(SearchProvider):
    def __init__(self, result: str = "Result: the sky is blue."):
        self.result = result
        self.queries: list[str] = []

    async def search(self, query: str, max_results: int = 5) -> str:
        self.queries.append(query)
        return self.result


def make_agent(**config_kwargs) -> Agent:
    return Agent(
        config=AgentConfig(**config_kwargs),
        channel=RecordingChannel(),
    )


class _MockResponse:
    def __init__(self, payload: dict | None = None, status: int = 200, body: str = ""):
        self._payload = payload or {}
        self.status = status
        self._body = body

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    async def json(self):
        return self._payload

    async def text(self):
        return self._body


# --- _ollama_chat -----------------------------------------------------------


async def test_ollama_chat_returns_message_content(monkeypatch):
    agent = make_agent(system_prompt="You are a test.")
    captured: dict = {}

    def fake_post(self, url, **kwargs):
        captured["url"] = url
        captured["payload"] = kwargs["json"]
        return _MockResponse({"message": {"content": "hello back"}})

    monkeypatch.setattr(aiohttp.ClientSession, "post", fake_post)
    out = await agent._ollama_chat("hello")
    assert out == "hello back"
    assert captured["url"].endswith("/api/chat")
    roles = [m["role"] for m in captured["payload"]["messages"]]
    assert roles == ["system", "user"]


async def test_ollama_chat_non_200_returns_error_envelope(monkeypatch):
    agent = make_agent()

    def fake_post(self, url, **kwargs):
        return _MockResponse(status=500, body="model exploded")

    monkeypatch.setattr(aiohttp.ClientSession, "post", fake_post)
    out = await agent._ollama_chat("hello")
    assert out.startswith("[LLM error:")
    assert "model exploded" in out


async def test_ollama_chat_connection_failure_returns_unavailable(monkeypatch):
    agent = make_agent()

    def fake_post(self, url, **kwargs):
        raise aiohttp.ClientConnectionError("connection refused")

    monkeypatch.setattr(aiohttp.ClientSession, "post", fake_post)
    out = await agent._ollama_chat("hello")
    assert out.startswith("[LLM unavailable:")


# --- _maybe_search ----------------------------------------------------------


async def test_search_fires_on_external_question():
    agent = make_agent()
    agent.search = FakeSearch()
    out = await agent._maybe_search("What is the tallest mountain on Earth?")
    assert "[SYSTEM DATA — web search results]" in out
    assert "the sky is blue" in out


async def test_search_skipped_for_internal_keywords():
    agent = make_agent()
    agent.search = FakeSearch()
    out = await agent._maybe_search("What does your identity say about tools?")
    assert out == ""
    assert agent.search.queries == []


async def test_search_skipped_for_non_questions():
    agent = make_agent()
    agent.search = FakeSearch()
    out = await agent._maybe_search("Please write me a haiku about autumn.")
    assert out == ""


async def test_search_error_envelope_not_injected():
    agent = make_agent()
    agent.search = FakeSearch(result="[search error: timeout]")
    out = await agent._maybe_search("What is the capital of France?")
    assert out == ""


async def test_no_search_provider_means_no_search():
    agent = make_agent()
    assert agent.search is None
    out = await agent._maybe_search("What is the capital of France?")
    assert out == ""


# --- handle -----------------------------------------------------------------


async def test_handle_injects_search_context_into_llm_call(monkeypatch):
    agent = make_agent()
    agent.search = FakeSearch(result="Result: 8,849 meters.")
    seen: list[str] = []

    async def fake_chat(msg: str) -> str:
        seen.append(msg)
        return "It is 8,849 meters tall."

    monkeypatch.setattr(agent, "_ollama_chat", fake_chat)
    out = await agent.handle("How tall is Mount Everest?")
    assert out == "It is 8,849 meters tall."
    assert len(seen) == 1
    assert "How tall is Mount Everest?" in seen[0]
    assert "[SYSTEM DATA — web search results]" in seen[0]
    # History stores the user's original text, not the augmented prompt.
    assert agent._history[0] == {"role": "user", "content": "How tall is Mount Everest?"}


async def test_handle_replaces_empty_response(monkeypatch):
    agent = make_agent()

    async def fake_chat(msg: str) -> str:
        return "   "

    monkeypatch.setattr(agent, "_ollama_chat", fake_chat)
    out = await agent.handle("hello")
    assert out == "I do not have data on that right now."


async def test_handle_trims_history_to_max(monkeypatch):
    agent = make_agent(memory_max_history=4)

    async def fake_chat(msg: str) -> str:
        return "ok"

    monkeypatch.setattr(agent, "_ollama_chat", fake_chat)
    for i in range(5):
        await agent.handle(f"msg{i}")
    assert len(agent._history) == 4
    # The newest exchange survives the trim.
    assert agent._history[-2]["content"] == "msg4"


# --- _run_scheduled_task ----------------------------------------------------


def sample_fetcher() -> str:
    return "42 events processed"


async def test_scheduled_task_sends_through_channel(monkeypatch):
    agent = make_agent()

    async def fake_chat(msg: str) -> str:
        return "brief text"

    monkeypatch.setattr(agent, "_ollama_chat", fake_chat)
    task = ScheduledTask(name="brief", cron="0 7 * * *", prompt="Brief me.")
    await agent._run_scheduled_task(task)
    assert agent.channel.sent == [("brief text", None)]


async def test_scheduled_task_fetcher_output_wrapped_as_system_data(monkeypatch):
    agent = make_agent()
    seen: list[str] = []

    async def fake_chat(msg: str) -> str:
        seen.append(msg)
        return "done"

    monkeypatch.setattr(agent, "_ollama_chat", fake_chat)
    task = ScheduledTask(
        name="brief",
        cron="0 7 * * *",
        prompt="Narrate this.",
        fetcher=f"{__name__}:sample_fetcher",
    )
    await agent._run_scheduled_task(task)
    assert "42 events processed" in seen[0]
    assert "[SYSTEM DATA" in seen[0]


async def test_scheduled_task_bad_fetcher_is_contained(monkeypatch):
    # A fetcher pointing at a module that doesn't exist must be logged and
    # swallowed, not escape to the scheduler loop (which would silently
    # kill the task forever).
    agent = make_agent()
    called: list[str] = []

    async def fake_handle(text: str) -> str:
        called.append(text)
        return "never"

    monkeypatch.setattr(agent, "handle", fake_handle)
    task = ScheduledTask(
        name="brief",
        cron="0 7 * * *",
        prompt="Narrate this.",
        fetcher="no_such_module.nowhere:fn",
    )
    await agent._run_scheduled_task(task)   # must not raise
    assert called == []
    assert agent.channel.sent == []
