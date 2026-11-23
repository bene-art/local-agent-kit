"""LocalScheduler — in-process asyncio runner for ScheduledTask.

Sleeps until each task's next fire time, then invokes a caller-supplied
runner function (typically `Agent.handle()`). Designed to live next to the
agent's main loop, not replace it.

This is the simplest correct implementation:
  - One asyncio task per ScheduledTask, looping (sleep → fire → repeat).
  - Each task computes its own next-fire from `croniter` against now.
  - `stop()` cancels all tasks and awaits cleanup.

For headless/cron-emitting variants (LaunchdAgent, SystemdTimer), see
the Scheduler protocol in `schedule.py`.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Awaitable, Callable

from croniter import croniter

from local_agent_kit.scheduling.schedule import ScheduledTask

logger = logging.getLogger(__name__)

TaskRunner = Callable[[ScheduledTask], Awaitable[None]]


class LocalScheduler:
    """Asyncio scheduler that fires ScheduledTasks on cron cadence.

    Usage:
        async def runner(task: ScheduledTask) -> None:
            response = await agent.handle(task.prompt)
            await channel_registry[task.channel].send(response)

        scheduler = LocalScheduler(runner)
        for task in load_schedules(agent_yaml):
            await scheduler.add(task)
        await scheduler.start()
        ...
        await scheduler.stop()
    """

    def __init__(self, runner: TaskRunner, *, now_fn: Callable[[], datetime] | None = None):
        self._runner = runner
        self._now_fn = now_fn or (lambda: datetime.now(timezone.utc))
        self._tasks: dict[str, ScheduledTask] = {}
        self._loops: dict[str, asyncio.Task] = {}
        self._stopped = asyncio.Event()

    async def add(self, task: ScheduledTask) -> None:
        if task.name in self._tasks:
            raise ValueError(f"scheduled task already registered: {task.name}")
        croniter(task.cron, self._now_fn())  # validates cron expression
        self._tasks[task.name] = task

    async def start(self) -> None:
        self._stopped.clear()
        for task in self._tasks.values():
            if task.name not in self._loops:
                self._loops[task.name] = asyncio.create_task(
                    self._run_loop(task), name=f"schedule:{task.name}"
                )

    async def stop(self) -> None:
        self._stopped.set()
        for loop in self._loops.values():
            loop.cancel()
        if self._loops:
            await asyncio.gather(*self._loops.values(), return_exceptions=True)
        self._loops.clear()

    async def _run_loop(self, task: ScheduledTask) -> None:
        cron = croniter(task.cron, self._now_fn())
        while not self._stopped.is_set():
            next_fire = cron.get_next(datetime)
            delay = (next_fire - self._now_fn()).total_seconds()
            if delay > 0:
                try:
                    await asyncio.wait_for(self._stopped.wait(), timeout=delay)
                    return
                except asyncio.TimeoutError:
                    pass
            try:
                await self._runner(task)
            except Exception:
                logger.exception("scheduled task %s failed", task.name)
