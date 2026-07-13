"""Smoke tests for AgentConfig + load_config."""
from __future__ import annotations

from pathlib import Path

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
