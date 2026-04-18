"""Channel base — abstract interface for communication channels."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator


@dataclass
class Message:
    """A message from a user."""
    text: str
    sender: str = ""
    channel_id: str = ""
    thread_id: str = ""


class Channel(ABC):
    """Abstract communication channel.

    Implement listen() and send() to create a new channel.
    Examples: Telegram, Discord, Slack, CLI, iMessage.
    """

    @abstractmethod
    async def listen(self) -> AsyncIterator[Message]:
        """Yield incoming messages. Runs forever."""
        ...

    @abstractmethod
    async def send(self, text: str, thread_id: str = "") -> bool:
        """Send a message back to the user. Returns True on success."""
        ...

    async def start(self) -> None:
        """Optional startup hook (e.g., send 'bot online' message)."""
        pass

    async def stop(self) -> None:
        """Optional shutdown hook."""
        pass
