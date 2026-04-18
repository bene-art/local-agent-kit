"""Communication channels — how the agent talks to users.

v1 ships with:
  - CLI (zero setup, great for testing)
  - Telegram (production, requires bot token)

Interface: implement Channel.listen() and Channel.send()
to add Discord, Slack, iMessage, etc.
"""
from local_agent_kit.channels.base import Channel, Message

__all__ = ["Channel", "Message"]
