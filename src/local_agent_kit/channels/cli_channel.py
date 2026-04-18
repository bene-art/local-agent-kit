"""CLI channel — zero-setup terminal interface.

No API keys, no bot tokens, no external services.
Great for testing and first-time onboarding.

Usage:
    channel = CLIChannel(agent_name="Patrick")
    async for msg in channel.listen():
        response = await agent.handle(msg.text)
        await channel.send(response)
"""
from __future__ import annotations

import asyncio
import sys

from .base import Channel, Message


class CLIChannel(Channel):
    """Terminal-based channel. stdin → agent → stdout."""

    def __init__(self, agent_name: str = "Agent"):
        self.agent_name = agent_name

    async def start(self) -> None:
        print(f"\n{self.agent_name} is online. Type a message (Ctrl+C to quit).\n")

    async def listen(self):
        """Read from stdin, yield Messages."""
        while True:
            try:
                line = await asyncio.to_thread(
                    input, "You: "
                )
                line = line.strip()
                if not line:
                    continue
                if line.lower() in ("quit", "exit", "q"):
                    break
                yield Message(text=line, sender="user", channel_id="cli")
            except (EOFError, KeyboardInterrupt):
                break

    async def send(self, text: str, thread_id: str = "") -> bool:
        print(f"\n{self.agent_name}: {text}\n")
        return True

    async def stop(self) -> None:
        print(f"\n{self.agent_name} offline.")
