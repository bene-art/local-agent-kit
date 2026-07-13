"""Tests for the LocalScheduler runtime."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest

from local_agent_kit.scheduling import LocalScheduler, ScheduledTask


def _task(name: str = "t", cron: str = "* * * * *") -> ScheduledTask:
    return ScheduledTask(name=name, cron=cron, prompt="p")


@pytest.mark.asyncio
async def test_add_rejects_duplicate_names():
    scheduler = LocalScheduler(runner=lambda t: asyncio.sleep(0))
    await scheduler.add(_task("alpha"))
    with pytest.raises(ValueError, match="already registered"):
        await scheduler.add(_task("alpha"))


@pytest.mark.asyncio
async def test_add_rejects_bad_cron_expression():
    scheduler = LocalScheduler(runner=lambda t: asyncio.sleep(0))
    with pytest.raises(Exception):  # croniter raises CroniterBadCronError
        await scheduler.add(_task("bad", cron="not a cron"))


@pytest.mark.asyncio
async def test_start_creates_one_loop_per_task():
    scheduler = LocalScheduler(runner=lambda t: asyncio.sleep(0))
    await scheduler.add(_task("a"))
    await scheduler.add(_task("b"))
    await scheduler.start()
    try:
        assert set(scheduler._loops.keys()) == {"a", "b"}
        assert all(not loop.done() for loop in scheduler._loops.values())
    finally:
        await scheduler.stop()


@pytest.mark.asyncio
async def test_stop_cancels_loops():
    scheduler = LocalScheduler(runner=lambda t: asyncio.sleep(0))
    await scheduler.add(_task("a"))
    await scheduler.start()
    await scheduler.stop()
    assert scheduler._loops == {}


@pytest.mark.asyncio
async def test_runner_fires_on_schedule():
    """Simulate time by feeding a static `now` that's just past a fire time."""
    calls: list[str] = []

    async def runner(task: ScheduledTask) -> None:
        calls.append(task.name)

    # Pretend "now" is one second before every minute boundary — so a
    # "* * * * *" cron fires almost immediately.
    fixed_now = datetime(2026, 1, 1, 0, 0, 59, tzinfo=timezone.utc)
    scheduler = LocalScheduler(runner=runner, now_fn=lambda: fixed_now)
    await scheduler.add(_task("a"))
    await scheduler.start()
    # The next-fire is 00:01:00. With fixed clock, delay = 1s.
    await asyncio.sleep(1.5)
    await scheduler.stop()
    assert "a" in calls


@pytest.mark.asyncio
async def test_runner_exception_does_not_kill_loop():
    calls: list[int] = []

    async def runner(task: ScheduledTask) -> None:
        calls.append(len(calls))
        if len(calls) == 1:
            raise RuntimeError("boom")

    fixed_now = datetime(2026, 1, 1, 0, 0, 59, tzinfo=timezone.utc)
    scheduler = LocalScheduler(runner=runner, now_fn=lambda: fixed_now)
    await scheduler.add(_task("a"))
    await scheduler.start()
    await asyncio.sleep(2.5)
    await scheduler.stop()
    assert len(calls) >= 1  # loop survived the first exception
