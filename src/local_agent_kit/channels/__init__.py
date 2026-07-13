"""Communication channels — how the agent talks to users.

The kit ships with the CLI channel (zero setup, fully local).

Interface: implement Channel.listen() and Channel.send() to add
Telegram, Discord, Slack, iMessage, etc., and pass the instance to
Agent.from_directory(channel=...).
"""
from local_agent_kit.channels.base import Channel, Message

__all__ = ["Channel", "Message"]
