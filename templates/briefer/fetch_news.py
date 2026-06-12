"""Example data fetcher for the briefer template.

Pulls the latest headlines from an RSS feed and formats them as plain
text suitable for inline injection. The agent's model then narrates the
headlines — Python computes, model narrates.

Reads the feed URL from BRIEFER_RSS_URL (default: Hacker News front page).
No external dependencies — uses httpx (already in the kit) and stdlib XML.

Wire it into a schedule:

    schedules:
      - name: morning_brief
        cron: "0 7 * * *"
        prompt: "Frame today's headlines in one sentence."
        channel: cli
        fetcher: templates.briefer.fetch_news:get_headlines
"""
from __future__ import annotations

import asyncio
import os
import xml.etree.ElementTree as ET

import httpx

DEFAULT_FEED = "https://news.ycombinator.com/rss"
MAX_HEADLINES = 8
TIMEOUT_S = 10.0


async def get_headlines() -> str:
    """Fetch the configured RSS feed and return a formatted headline list."""
    url = os.environ.get("BRIEFER_RSS_URL", DEFAULT_FEED)

    async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
        resp = await client.get(url, headers={"User-Agent": "local-agent-kit/briefer"})
        resp.raise_for_status()
        body = resp.text

    root = ET.fromstring(body)
    # RSS 2.0: channel/item/title — find regardless of namespace nesting
    items = root.findall(".//item")
    if not items:
        return "No headlines available."

    lines: list[str] = []
    for item in items[:MAX_HEADLINES]:
        title_el = item.find("title")
        if title_el is None or not (title_el.text or "").strip():
            continue
        lines.append(f"- {title_el.text.strip()}")

    if not lines:
        return "No headlines available."

    header = f"Top {len(lines)} headlines from {url}:"
    return header + "\n" + "\n".join(lines)


if __name__ == "__main__":
    print(asyncio.run(get_headlines()))
