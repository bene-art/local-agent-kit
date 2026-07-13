"""Smoke tests for AgentConfig + load_config + from_directory wiring."""
from __future__ import annotations

from pathlib import Path

import pytest

from local_agent_kit.agent import AgentConfig, load_config


def test_agent_config_defaults():
    cfg = AgentConfig()
    assert cfg.name == "Agent"
    assert cfg.model == "gemma3:12b"
    assert cfg.search_provider == "none"
    assert cfg.memory_enabled is True


def test_load_config_reads_agent_yaml(tmp_path: Path):
    agent_dir = tmp_path / "my-agent"
    agent_dir.mkdir()
    (agent_dir / "agent.yaml").write_text(
        "name: Test\n"
        "model: gemma3:4b\n"
        "search:\n"
        "  provider: duckduckgo\n"
    )
    cfg = load_config(agent_dir)
    assert cfg.name == "Test"
    assert cfg.model == "gemma3:4b"
    assert cfg.search_provider == "duckduckgo"


def test_load_config_reads_identity_md(tmp_path: Path):
    agent_dir = tmp_path / "my-agent"
    identity_dir = agent_dir / "identity"
    identity_dir.mkdir(parents=True)
    (identity_dir / "IDENTITY.md").write_text("# IDENTITY\n\nTest agent.\n")
    cfg = load_config(agent_dir)
    assert "Test agent" in cfg.system_prompt


def test_load_config_missing_dir_returns_defaults(tmp_path: Path):
    # Non-existent directory: load_config should still return defaults, not crash.
    cfg = load_config(tmp_path / "does-not-exist")
    assert cfg.name == "Agent"
    assert cfg.system_prompt == ""


def _write_agent_yaml(tmp_path: Path, body: str) -> Path:
    agent_dir = tmp_path / "agent"
    agent_dir.mkdir()
    (agent_dir / "agent.yaml").write_text(body)
    return agent_dir


def test_from_directory_provider_none_disables_search(tmp_path: Path):
    # 'none' must mean none, even with web_search left on — the agent
    # makes no outbound search requests unless explicitly configured to.
    from local_agent_kit.agent import Agent
    from local_agent_kit.channels.cli_channel import CLIChannel

    agent_dir = _write_agent_yaml(
        tmp_path, "search:\n  provider: none\ntools:\n  web_search: true\n"
    )
    agent = Agent.from_directory(agent_dir, channel=CLIChannel(agent_name="t"))
    assert agent.search is None


def test_from_directory_provider_duckduckgo_selects_ddg(tmp_path: Path, monkeypatch):
    # The config decides the provider — the environment must not. A stray
    # cloud API key in the env used to silently hijack search selection.
    from local_agent_kit.agent import Agent
    from local_agent_kit.channels.cli_channel import CLIChannel
    from local_agent_kit.search.duckduckgo_search import DuckDuckGoSearch

    monkeypatch.setenv("GEMINI_API_KEY", "should-be-ignored")
    agent_dir = _write_agent_yaml(
        tmp_path, "search:\n  provider: duckduckgo\ntools:\n  web_search: true\n"
    )
    agent = Agent.from_directory(agent_dir, channel=CLIChannel(agent_name="t"))
    assert isinstance(agent.search, DuckDuckGoSearch)


def test_from_directory_unknown_provider_raises(tmp_path: Path):
    from local_agent_kit.agent import Agent
    from local_agent_kit.channels.cli_channel import CLIChannel

    agent_dir = _write_agent_yaml(
        tmp_path, "search:\n  provider: gemini\ntools:\n  web_search: true\n"
    )
    with pytest.raises(ValueError, match="unknown search.provider"):
        Agent.from_directory(agent_dir, channel=CLIChannel(agent_name="t"))


def test_from_directory_web_search_false_disables_search(tmp_path: Path):
    from local_agent_kit.agent import Agent
    from local_agent_kit.channels.cli_channel import CLIChannel

    agent_dir = _write_agent_yaml(
        tmp_path, "search:\n  provider: duckduckgo\ntools:\n  web_search: false\n"
    )
    agent = Agent.from_directory(agent_dir, channel=CLIChannel(agent_name="t"))
    assert agent.search is None
