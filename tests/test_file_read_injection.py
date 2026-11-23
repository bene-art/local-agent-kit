"""Tests for Agent.handle auto-injection via file_read."""
from __future__ import annotations

from pathlib import Path

import pytest

from local_agent_kit.agent import AgentConfig, load_config


def test_load_config_parses_file_read_roots(tmp_path: Path):
    agent_dir = tmp_path / "agent"
    agent_dir.mkdir()
    (agent_dir / "agent.yaml").write_text(
        "name: T\n"
        "channel: cli\n"
        "tools:\n"
        "  file_read:\n"
        "    roots: [~/notes, ./docs]\n"
        "    max_chars: 1500\n"
    )
    cfg = load_config(agent_dir)
    assert cfg.file_read_roots == ["~/notes", "./docs"]
    assert cfg.file_read_max_chars == 1500


def test_load_config_default_file_read_roots_empty():
    cfg = AgentConfig()
    assert cfg.file_read_roots == []


@pytest.mark.asyncio
async def test_maybe_read_file_returns_empty_without_roots(tmp_path: Path):
    from local_agent_kit.agent import Agent, AgentConfig
    from local_agent_kit.channels.cli_channel import CLIChannel
    agent = Agent(config=AgentConfig(), channel=CLIChannel(agent_name="T"))
    out = await agent._maybe_read_file("Explain ./script.py")
    assert out == ""


@pytest.mark.asyncio
async def test_maybe_read_file_injects_when_path_inside_allowlist(tmp_path: Path):
    from local_agent_kit.agent import Agent, AgentConfig
    from local_agent_kit.channels.cli_channel import CLIChannel

    target = tmp_path / "script.py"
    target.write_text("def hello(): return 1")
    config = AgentConfig(file_read_roots=[str(tmp_path)])
    agent = Agent(config=config, channel=CLIChannel(agent_name="T"))
    msg = f"Explain {target}"
    out = await agent._maybe_read_file(msg)
    assert "[SYSTEM DATA — file_read" in out
    assert "def hello()" in out


@pytest.mark.asyncio
async def test_maybe_read_file_skips_denial_envelopes(tmp_path: Path):
    """Denials shouldn't be injected as 'data'."""
    from local_agent_kit.agent import Agent, AgentConfig
    from local_agent_kit.channels.cli_channel import CLIChannel

    config = AgentConfig(file_read_roots=[str(tmp_path)])
    agent = Agent(config=config, channel=CLIChannel(agent_name="T"))
    # Path that matches the regex but points nowhere → file_read returns "[file not found: ...]"
    out = await agent._maybe_read_file("Explain ./nonexistent.py")
    assert out == ""


@pytest.mark.asyncio
async def test_maybe_read_file_ignores_messages_without_paths(tmp_path: Path):
    from local_agent_kit.agent import Agent, AgentConfig
    from local_agent_kit.channels.cli_channel import CLIChannel
    config = AgentConfig(file_read_roots=[str(tmp_path)])
    agent = Agent(config=config, channel=CLIChannel(agent_name="T"))
    out = await agent._maybe_read_file("Tell me a story")
    assert out == ""
