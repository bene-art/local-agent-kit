"""Tests for the schedule parser."""
from __future__ import annotations

import pytest

from local_agent_kit.scheduling import ScheduledTask, load_schedules


def test_missing_schedules_block_returns_empty_list():
    assert load_schedules({}) == []


def test_explicit_null_schedules_returns_empty_list():
    assert load_schedules({"schedules": None}) == []


def test_parses_well_formed_entry():
    tasks = load_schedules({
        "schedules": [
            {"name": "morning", "cron": "0 7 * * *", "prompt": "Brief me."}
        ]
    })
    assert tasks == [ScheduledTask(name="morning", cron="0 7 * * *", prompt="Brief me.")]


def test_rejects_non_list_schedules():
    with pytest.raises(ValueError, match="must be a list"):
        load_schedules({"schedules": "not a list"})


def test_rejects_entry_missing_required_field():
    with pytest.raises(ValueError, match="missing required fields"):
        load_schedules({"schedules": [{"name": "x", "cron": "0 7 * * *"}]})  # no prompt


def test_rejects_bad_cron_field_count():
    with pytest.raises(ValueError, match="5 fields"):
        load_schedules({"schedules": [{"name": "x", "cron": "0 7", "prompt": "p"}]})


def test_rejects_duplicate_names():
    with pytest.raises(ValueError, match="duplicate names"):
        load_schedules({
            "schedules": [
                {"name": "morning", "cron": "0 7 * * *", "prompt": "p"},
                {"name": "morning", "cron": "0 8 * * *", "prompt": "q"},
            ]
        })
