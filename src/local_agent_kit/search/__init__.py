"""Web search providers — how the agent sees the outside world.

The kit ships with DuckDuckGo (no API key, no account). Search is
opt-in via `search.provider` in agent.yaml and off by default.

Interface: implement SearchProvider.search() to add Brave, SerpAPI,
etc., and pass the instance to Agent.from_directory(search=...).
"""
from local_agent_kit.search.base import SearchProvider

__all__ = ["SearchProvider"]
