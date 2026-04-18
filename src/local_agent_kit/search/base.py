"""Search provider base — abstract interface for web search."""
from __future__ import annotations

from abc import ABC, abstractmethod


class SearchProvider(ABC):
    """Abstract web search provider.

    Implement search() to create a new provider.
    Examples: Gemini grounding, Brave Search, DuckDuckGo, SerpAPI.
    """

    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> str:
        """Search the web and return results as text.

        Args:
            query: The search query.
            max_results: Maximum number of results.

        Returns:
            Search results as formatted text, or error message.
        """
        ...
