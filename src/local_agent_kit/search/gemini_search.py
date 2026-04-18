"""Gemini search — Google Search grounding via Gemini Flash API.

Requires: GEMINI_API_KEY environment variable.
Free tier: 15 RPM, 1M TPM.
"""
from __future__ import annotations

import logging
import os

import httpx

from .base import SearchProvider

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiSearch(SearchProvider):
    """Web search via Gemini Flash + Google Search grounding."""

    def __init__(self, model: str = "gemini-2.5-flash"):
        self.model = model
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def search(self, query: str, max_results: int = 5) -> str:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return "[GEMINI_API_KEY not set — web search unavailable]"

        client = self._get_client()
        url = f"{GEMINI_API_URL}/{self.model}:generateContent?key={api_key}"

        body = {
            "contents": [{"role": "user", "parts": [{"text": query}]}],
            "tools": [{"google_search": {}}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 400,
            },
        }

        try:
            resp = await client.post(url, json=body)
            resp.raise_for_status()
            data = resp.json()

            parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts)

            if text:
                logger.info("gemini_search: query=%r, len=%d", query[:50], len(text))
                return text

            return "[search returned empty]"

        except Exception as exc:
            logger.warning("gemini_search failed: %s", exc)
            return f"[search error: {exc}]"
