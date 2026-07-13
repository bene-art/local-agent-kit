"""Smoke tests for channel implementations."""
from __future__ import annotations

from local_agent_kit.channels.cli_channel import CLIChannel


def test_cli_channel_constructs():
    ch = CLIChannel(agent_name="TestBot")
    assert ch.agent_name == "TestBot"
