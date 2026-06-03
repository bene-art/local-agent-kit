"""Smoke tests for channel implementations."""
from __future__ import annotations

import os

import pytest

from local_agent_kit.channels.cli_channel import CLIChannel


def test_cli_channel_constructs():
    ch = CLIChannel(agent_name="TestBot")
    assert ch.agent_name == "TestBot"


def test_telegram_channel_requires_credentials(monkeypatch):
    from local_agent_kit.channels.telegram_channel import TelegramChannel

    monkeypatch.delenv("TG_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TG_CHAT_ID", raising=False)

    with pytest.raises(ValueError, match="Telegram bot token required"):
        TelegramChannel()


def test_telegram_channel_accepts_args(monkeypatch):
    from local_agent_kit.channels.telegram_channel import TelegramChannel

    monkeypatch.delenv("TG_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TG_CHAT_ID", raising=False)

    ch = TelegramChannel(bot_token="fake", chat_id=12345)
    assert ch.bot_token == "fake"
    assert ch.chat_id == 12345
