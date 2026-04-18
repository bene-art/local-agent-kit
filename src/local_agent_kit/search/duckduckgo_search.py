"""DuckDuckGo search — no API key required.

Uses DuckDuckGo's HTML search and parses results.
Zero configuration. Perfect for onboarding.
"""
from __future__ import annotations

import logging

import httpx

from .base import SearchProvider

logger = logging.getLogger(__name__)

DDG_URL = "https://html.duckduckgo.com/html/"


class DuckDuckGoSearch(SearchProvider):
    """Web search via DuckDuckGo HTML scraping. No API key needed."""

    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=15.0,
                headers={"User-Agent": "LocalAgentKit/0.1"},
            )
        return self._client

    async def search(self, query: str, max_results: int = 5) -> str:
        client = self._get_client()

        try:
            resp = await client.post(DDG_URL, data={"q": query, "b": ""})
            resp.raise_for_status()
            html = resp.text

            # Parse results from HTML (simple extraction)
            results = []
            for block in html.split('class="result__a"')[1:max_results + 1]:
                # Extract title
                title_end = block.find("</a>")
                title = block[:title_end] if title_end > 0 else ""
                # Clean HTML tags
                import re
                title = re.sub(r"<[^>]+>", "", title).strip()

                # Extract snippet
                snippet_start = block.find('class="result__snippet"')
                if snippet_start > 0:
                    snippet_block = block[snippet_start:]
                    snippet_end = snippet_block.find("</a>")
                    snippet = snippet_block[:snippet_end] if snippet_end > 0 else ""
                    snippet = re.sub(r"<[^>]+>", "", snippet).strip()
                    snippet = snippet.replace('class="result__snippet">', "").strip()
                else:
                    snippet = ""

                if title:
                    results.append(f"- {title}: {snippet}" if snippet else f"- {title}")

            if results:
                text = "\n".join(results)
                logger.info("ddg_search: query=%r, results=%d", query[:50], len(results))
                return text

            return "[no results found]"

        except Exception as exc:
            logger.warning("ddg_search failed: %s", exc)
            return f"[search error: {exc}]"
