"""Tests for Agent.handle auto-injection of CSV/JSONL via data_peek."""
from __future__ import annotations

from pathlib import Path

import pytest

from local_agent_kit.agent import Agent, AgentConfig
from local_agent_kit.channels.cli_channel import CLIChannel


@pytest.mark.asyncio
async def test_csv_path_injects_tabular_head(tmp_path: Path):
    csv = tmp_path / "sales.csv"
    csv.write_text("region,revenue\nNorth,100\nSouth,80\n")
    cfg = AgentConfig(file_read_roots=[str(tmp_path)])
    agent = Agent(config=cfg, channel=CLIChannel(agent_name="T"))
    out = await agent._maybe_show_data(f"What's in {csv}?")
    assert "[SYSTEM DATA — head of" in out
    assert "region | revenue" in out
    assert "North | 100" in out


@pytest.mark.asyncio
async def test_jsonl_path_injects_tabular_head(tmp_path: Path):
    jl = tmp_path / "events.jsonl"
    jl.write_text('{"id": 1, "type": "click"}\n{"id": 2, "type": "view"}\n')
    cfg = AgentConfig(file_read_roots=[str(tmp_path)])
    agent = Agent(config=cfg, channel=CLIChannel(agent_name="T"))
    out = await agent._maybe_show_data(f"What's in {jl}?")
    assert "[SYSTEM DATA — head of" in out
    assert "id | type" in out


@pytest.mark.asyncio
async def test_no_data_peek_when_rows_zero(tmp_path: Path):
    csv = tmp_path / "x.csv"
    csv.write_text("a,b\n1,2\n")
    cfg = AgentConfig(file_read_roots=[str(tmp_path)], data_peek_rows=0)
    agent = Agent(config=cfg, channel=CLIChannel(agent_name="T"))
    out = await agent._maybe_show_data(f"check {csv}")
    assert out == ""


@pytest.mark.asyncio
async def test_text_path_does_not_trigger_data_peek(tmp_path: Path):
    md = tmp_path / "notes.md"
    md.write_text("# heading")
    cfg = AgentConfig(file_read_roots=[str(tmp_path)])
    agent = Agent(config=cfg, channel=CLIChannel(agent_name="T"))
    # _maybe_show_data should ignore .md
    assert await agent._maybe_show_data(f"read {md}") == ""


@pytest.mark.asyncio
async def test_csv_path_does_not_trigger_file_read(tmp_path: Path):
    """CSV/JSONL should NOT be raw-file-read — they go through data_peek."""
    csv = tmp_path / "rows.csv"
    csv.write_text("a,b\n1,2\n3,4\n")
    cfg = AgentConfig(file_read_roots=[str(tmp_path)])
    agent = Agent(config=cfg, channel=CLIChannel(agent_name="T"))
    # _maybe_read_file should NOT match .csv
    assert await agent._maybe_read_file(f"read {csv}") == ""


@pytest.mark.asyncio
async def test_data_peek_outside_allowlist_returns_empty(tmp_path: Path):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    csv = elsewhere / "leak.csv"
    csv.write_text("x,y\n1,2\n")
    inside = tmp_path / "ok"
    inside.mkdir()
    cfg = AgentConfig(file_read_roots=[str(inside)])
    agent = Agent(config=cfg, channel=CLIChannel(agent_name="T"))
    # data_peek returns a "[access denied: ...]" envelope, which the
    # injection wrapper drops.
    assert await agent._maybe_show_data(f"check {csv}") == ""


def test_load_config_parses_data_peek_rows(tmp_path: Path):
    from local_agent_kit.agent import load_config

    agent_dir = tmp_path / "agent"
    agent_dir.mkdir()
    (agent_dir / "agent.yaml").write_text(
        "name: T\n"
        "channel: cli\n"
        "tools:\n"
        "  file_read:\n"
        "    roots: ['.']\n"
        "    data_peek_rows: 5\n"
    )
    cfg = load_config(agent_dir)
    assert cfg.data_peek_rows == 5
