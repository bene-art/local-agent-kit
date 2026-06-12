"""Locks in the journal template's "zero outbound, non-localhost" promise.

Monkeypatches aiohttp.ClientSession._request so any request to a
non-localhost host raises. Mocks the Ollama call (so the test runs in
CI without a running model). Drives one journal turn through Agent.handle
and asserts no non-localhost request was attempted.

This catches:
    - A future code change that accidentally hits a CDN, telemetry,
      or third-party API from the journal codepath.
    - Search/Telegram channels accidentally being enabled in the
      journal's agent.yaml.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import aiohttp
import pytest

LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1", "[::1]"}


class _MockResponse:
    def __init__(self, payload: dict, status: int = 200):
        self._payload = payload
        self.status = status

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    async def json(self):
        return self._payload

    async def text(self):
        return ""


def _is_local(url: str) -> bool:
    return any(h in url for h in LOCAL_HOSTS)


@pytest.mark.asyncio
async def test_journal_turn_makes_no_non_localhost_requests(monkeypatch):
    """One Agent.handle() call from the journal template must only touch
    localhost (Ollama). Anything else is a privacy regression."""
    from local_agent_kit.agent import Agent
    from local_agent_kit.channels.cli_channel import CLIChannel

    seen_urls: list[str] = []

    def fake_post(self, url, **kwargs):
        seen_urls.append(str(url))
        if not _is_local(str(url)):
            raise AssertionError(
                f"Journal made a non-localhost request: {url}"
            )
        return _MockResponse({"message": {"content": "What made it feel heavy?"}})

    monkeypatch.setattr(aiohttp.ClientSession, "post", fake_post)

    template = Path(__file__).resolve().parents[1] / "templates" / "journal"
    agent = Agent.from_directory(template, channel=CLIChannel(agent_name="Journal"))
    out = await agent.handle("Today felt heavy.")

    assert out == "What made it feel heavy?"
    assert len(seen_urls) >= 1, "expected at least the Ollama call"
    assert all(_is_local(u) for u in seen_urls), (
        f"non-local URLs reached aiohttp: {[u for u in seen_urls if not _is_local(u)]}"
    )


@pytest.mark.asyncio
async def test_journal_config_has_no_search_provider():
    """Agent config sanity — journal must not enable a search provider."""
    from local_agent_kit.agent import load_config

    template = Path(__file__).resolve().parents[1] / "templates" / "journal"
    cfg = load_config(template)
    assert cfg.search_provider == "none", (
        f"journal template enabled search.provider={cfg.search_provider!r} — "
        "this would make outbound requests"
    )
    assert cfg.web_search is False, "journal must have web_search disabled"


@pytest.mark.asyncio
async def test_journal_config_has_no_file_read_roots():
    """Journal templates should not auto-inject file contents — entries
    are user-typed, not file-read. file_read_roots must be empty."""
    from local_agent_kit.agent import load_config

    template = Path(__file__).resolve().parents[1] / "templates" / "journal"
    cfg = load_config(template)
    assert cfg.file_read_roots == [], (
        f"journal template enabled file_read with roots={cfg.file_read_roots} — "
        "remove from agent.yaml or document the privacy implication"
    )
