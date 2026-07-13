"""Local Agent Kit — build local-first AI agents on consumer hardware."""
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("local-agent-kit")
except PackageNotFoundError:  # uninstalled checkout (e.g. vendored copy)
    __version__ = "0.0.0+unknown"
