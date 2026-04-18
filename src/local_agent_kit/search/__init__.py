"""Web search providers — how the agent sees the outside world.

v1 ships with:
  - Gemini (Google Search grounding, free tier)
  - DuckDuckGo (no API key needed)

Interface: implement SearchProvider.search() to add Brave, SerpAPI, etc.
"""
from local_agent_kit.search.base import SearchProvider

__all__ = ["SearchProvider"]
