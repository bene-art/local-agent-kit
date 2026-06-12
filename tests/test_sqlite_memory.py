"""Tests for SQLiteMemory."""
from __future__ import annotations

from pathlib import Path

import pytest

from local_agent_kit.memory import Memory, SQLiteMemory


def test_implements_memory_protocol(tmp_path: Path):
    mem: Memory = SQLiteMemory(tmp_path / "m.db")
    assert hasattr(mem, "append")
    assert hasattr(mem, "history")
    assert hasattr(mem, "count")


def test_append_then_history(tmp_path: Path):
    mem = SQLiteMemory(tmp_path / "m.db")
    mem.append("t1", "user", "hello")
    mem.append("t1", "assistant", "hi there")
    assert mem.history("t1") == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi there"},
    ]


def test_history_is_per_thread(tmp_path: Path):
    mem = SQLiteMemory(tmp_path / "m.db")
    mem.append("t1", "user", "one")
    mem.append("t2", "user", "two")
    assert mem.history("t1") == [{"role": "user", "content": "one"}]
    assert mem.history("t2") == [{"role": "user", "content": "two"}]


def test_count(tmp_path: Path):
    mem = SQLiteMemory(tmp_path / "m.db")
    assert mem.count("t1") == 0
    mem.append("t1", "user", "hi")
    mem.append("t1", "assistant", "back")
    assert mem.count("t1") == 2


def test_max_history_prunes_oldest(tmp_path: Path):
    mem = SQLiteMemory(tmp_path / "m.db", max_history=3)
    for i in range(5):
        mem.append("t", "user", f"msg{i}")
    rows = mem.history("t", limit=10)
    assert len(rows) == 3
    assert [r["content"] for r in rows] == ["msg2", "msg3", "msg4"]


def test_add_exchange_sugar(tmp_path: Path):
    mem = SQLiteMemory(tmp_path / "m.db")
    mem.add_exchange("t1", "Q?", "A.")
    history = mem.history("t1")
    assert [(r["role"], r["content"]) for r in history] == [
        ("user", "Q?"),
        ("assistant", "A."),
    ]


def test_clear_removes_thread(tmp_path: Path):
    mem = SQLiteMemory(tmp_path / "m.db")
    mem.append("t1", "user", "x")
    mem.append("t1", "user", "y")
    mem.append("t2", "user", "z")
    removed = mem.clear("t1")
    assert removed == 2
    assert mem.count("t1") == 0
    assert mem.count("t2") == 1


def test_long_content_truncated(tmp_path: Path):
    mem = SQLiteMemory(tmp_path / "m.db")
    huge = "x" * 5000
    mem.append("t", "user", huge)
    [row] = mem.history("t")
    assert row["content"].endswith("...[truncated]")
    assert len(row["content"]) < len(huge)


def test_persists_across_instances(tmp_path: Path):
    path = tmp_path / "m.db"
    mem1 = SQLiteMemory(path)
    mem1.append("t1", "user", "remembered")
    mem2 = SQLiteMemory(path)
    assert mem2.history("t1") == [{"role": "user", "content": "remembered"}]
