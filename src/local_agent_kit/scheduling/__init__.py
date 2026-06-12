"""Scheduling — declarative recurring tasks for the kit.

See `schedule.py` for the parser + types and `local_scheduler.py` for the
in-process asyncio scheduler.

The parser (ScheduledTask, load_schedules) has no third-party deps and is
imported eagerly. The runtime (LocalScheduler) requires croniter — lazily
imported via __getattr__ so the `[schedule]` extra is only required when
LocalScheduler is actually referenced.
"""
from local_agent_kit.scheduling.schedule import (
    ScheduledTask,
    Scheduler,
    load_schedules,
)

__all__ = ["ScheduledTask", "Scheduler", "load_schedules", "LocalScheduler"]


def __getattr__(name: str):
    if name == "LocalScheduler":
        from local_agent_kit.scheduling.local_scheduler import LocalScheduler
        return LocalScheduler
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
