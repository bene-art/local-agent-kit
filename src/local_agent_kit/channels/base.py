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
    def listen(self) -> AsyncIterator[Message]:
        """Yield incoming messages. Runs forever.

        Implement as an async generator (`async def` with `yield`) — which
        is why this is declared `def`: an async generator function returns
        its iterator synchronously.
        """
        ...

    @abstractmethod
    async def send(self, text: str, thread_id: str | None = None) -> bool:
        """Send a message back to the user. Returns True on success.

        thread_id is None for messages with no originating thread
        (e.g. scheduled task results).
        """
        ...

    async def start(self) -> None:
        """Optional startup hook (e.g., send 'bot online' message)."""
        pass

    async def stop(self) -> None:
        """Optional shutdown hook."""
        pass
