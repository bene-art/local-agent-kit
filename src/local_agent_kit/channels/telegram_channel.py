"""Telegram channel — Bot API polling interface.

Requires:
  - PAT_TG_BOT_TOKEN (Telegram bot token from @BotFather)
  - PAT_TG_CHAT_ID (your Telegram chat ID)

Usage:
    channel = TelegramChannel()
    async for msg in channel.listen():
        response = await agent.handle(msg.text)
        await channel.send(response)
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import AsyncIterator

import aiohttp

from .base import Channel, Message

logger = logging.getLogger(__name__)

TG_API_BASE = "https://api.telegram.org/bot"


class TelegramChannel(Channel):
    """Telegram Bot API channel with long polling."""

    def __init__(
        self,
        bot_token: str | None = None,
        chat_id: int | None = None,
        poll_timeout: int = 30,
    ):
        self.bot_token = bot_token or os.environ.get("PAT_TG_BOT_TOKEN", "")
        self.chat_id = chat_id or int(os.environ.get("PAT_TG_CHAT_ID", "0"))
        self.poll_timeout = poll_timeout
        self._session: aiohttp.ClientSession | None = None
        self._offset: int = 0

        if not self.bot_token:
            raise ValueError(
                "Telegram bot token required. Set PAT_TG_BOT_TOKEN or pass bot_token="
            )
        if not self.chat_id:
            raise ValueError(
                "Telegram chat ID required. Set PAT_TG_CHAT_ID or pass chat_id="
            )

    @property
    def _api(self) -> str:
        return f"{TG_API_BASE}{self.bot_token}"

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def start(self) -> None:
        await self.send("Agent online.")

    async def listen(self) -> AsyncIterator[Message]:
        """Long-poll Telegram for incoming messages."""
        session = await self._get_session()

        while True:
            try:
                async with session.get(
                    f"{self._api}/getUpdates",
                    params={
                        "offset": self._offset,
                        "timeout": self.poll_timeout,
                    },
                    timeout=aiohttp.ClientTimeout(total=self.poll_timeout + 10),
                ) as resp:
                    data = await resp.json()

                if not data.get("ok"):
                    logger.warning("Telegram API error: %s", data)
                    await asyncio.sleep(5)
                    continue

                for update in data.get("result", []):
                    self._offset = update["update_id"] + 1
                    msg = update.get("message", {})
                    text = msg.get("text", "")
                    chat_id = msg.get("chat", {}).get("id")
                    sender = msg.get("from", {}).get("first_name", "")

                    if not text or chat_id != self.chat_id:
                        continue

                    yield Message(
                        text=text,
                        sender=sender,
                        channel_id=str(chat_id),
                        thread_id=f"tg_{chat_id}",
                    )

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning("Telegram poll error: %s", exc)
                await asyncio.sleep(5)

    async def send(self, text: str, thread_id: str = "") -> bool:
        """Send a message via Telegram Bot API."""
        session = await self._get_session()
        # Telegram limit: 4096 chars
        text = text[:4096]
        try:
            async with session.post(
                f"{self._api}/sendMessage",
                json={"chat_id": self.chat_id, "text": text},
            ) as resp:
                data = await resp.json()
                return data.get("ok", False)
        except Exception as exc:
            logger.warning("Telegram send failed: %s", exc)
            return False

    async def stop(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
