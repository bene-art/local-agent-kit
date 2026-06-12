"""Schedule — declarative recurring task definition.

A `Schedule` is a config-level construct: declared in agent.yaml under a
`schedules:` block, parsed into one or more `ScheduledTask` instances at
agent boot, and run by a `Scheduler` that lives alongside the agent's
main loop.

The model is NOT invoked to decide WHEN to run — that's deterministic
(cron-like). The model is invoked only inside the task's prompt body,
following the inline-injection pattern: any fetched data is rendered
into the prompt as `[SYSTEM DATA]` before the model sees it.

Example agent.yaml block:

    schedules:
      - name: morning_brief
        cron: "0 7 * * *"             # 7am daily
        prompt: "Summarize the news for today."
        channel: telegram             # send result here

This module implements the parser (`load_schedules`). The `Scheduler`
runtime that actually fires tasks needs a cron-expression library and
lands once that dependency is approved.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


_REQUIRED_FIELDS = ("name", "cron", "prompt", "channel")


@dataclass(frozen=True)
class ScheduledTask:
    """One declared schedule entry, parsed from agent.yaml."""

    name: str
    cron: str          # five-field cron: "minute hour day month weekday"
    prompt: str        # the message handed to Agent.handle() at fire time
    channel: str       # name of a configured channel for sending the result
    fetcher: str | None = None
    # Optional dotted Python path to a callable that returns a string.
    # If set, the runner calls it at fire time, wraps the result with
    # `narrate_only.envelope()`, and appends to `prompt` before calling
    # Agent.handle(). Enables the "Python computes, model narrates" pattern
    # used by the briefer template.


class Scheduler(Protocol):
    """Drives ScheduledTask execution on a cron-like cadence.

    Planned implementations:
        LocalScheduler  — in-process, asyncio-based. Default for `lak bot`.
        LaunchdAgent    — emits a launchd plist (macOS, headless).
        SystemdTimer    — emits a systemd unit (Linux, headless).
    """

    async def add(self, task: ScheduledTask) -> None: ...
    async def start(self) -> None: ...
    async def stop(self) -> None: ...


def _validate_cron(expr: str) -> None:
    """Lightweight check: 5 whitespace-separated fields, non-empty.

    Full cron-expression validation is deferred to the Scheduler runtime,
    which will use a proper cron library. This catches obvious typos at
    boot time so users learn about the error before the schedule should
    have fired.
    """
    if not isinstance(expr, str) or not expr.strip():
        raise ValueError(f"cron must be a non-empty string, got {expr!r}")
    fields = expr.split()
    if len(fields) != 5:
        raise ValueError(
            f"cron must have 5 fields (minute hour day month weekday), got {len(fields)}: {expr!r}"
        )


def load_schedules(agent_yaml: dict[str, Any]) -> list[ScheduledTask]:
    """Parse the `schedules:` block of agent.yaml into ScheduledTask objects.

    Empty or missing block returns []. Validation is strict — bad cron
    strings or missing required fields raise at boot rather than failing
    silently at fire time.
    """
    raw = agent_yaml.get("schedules")
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError(f"agent.yaml 'schedules' must be a list, got {type(raw).__name__}")

    tasks: list[ScheduledTask] = []
    for i, entry in enumerate(raw):
        if not isinstance(entry, dict):
            raise ValueError(f"schedules[{i}] must be a mapping, got {type(entry).__name__}")
        missing = [f for f in _REQUIRED_FIELDS if f not in entry]
        if missing:
            raise ValueError(f"schedules[{i}] missing required fields: {missing}")
        _validate_cron(entry["cron"])
        fetcher = entry.get("fetcher")
        if fetcher is not None and not isinstance(fetcher, str):
            raise ValueError(
                f"schedules[{i}].fetcher must be a string (dotted import path), got {type(fetcher).__name__}"
            )
        tasks.append(
            ScheduledTask(
                name=str(entry["name"]),
                cron=str(entry["cron"]),
                prompt=str(entry["prompt"]),
                channel=str(entry["channel"]),
                fetcher=fetcher,
            )
        )

    names = [t.name for t in tasks]
    duplicates = {n for n in names if names.count(n) > 1}
    if duplicates:
        raise ValueError(f"schedules contain duplicate names: {sorted(duplicates)}")

    return tasks
