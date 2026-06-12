"""Tests for QuizProgress."""
from __future__ import annotations

from pathlib import Path

from local_agent_kit.memory import QuizProgress


def test_record_increments_counts(tmp_path: Path):
    qp = QuizProgress(tmp_path / "q.db")
    qp.record("photosynthesis", "reactants", correct=True)
    qp.record("photosynthesis", "reactants", correct=False)
    qp.record("photosynthesis", "reactants", correct=False)
    stats = qp.stats("photosynthesis")
    assert stats["reactants"]["correct_count"] == 1
    assert stats["reactants"]["wrong_count"] == 2
    assert stats["reactants"]["last_grade"] == "wrong"


def test_stats_per_quiz(tmp_path: Path):
    qp = QuizProgress(tmp_path / "q.db")
    qp.record("q1", "a", correct=True)
    qp.record("q2", "a", correct=False)
    assert qp.stats("q1")["a"]["correct_count"] == 1
    assert qp.stats("q2")["a"]["wrong_count"] == 1
    assert "a" in qp.stats("q1") and "a" in qp.stats("q2")


def test_order_steps_never_seen_first(tmp_path: Path):
    qp = QuizProgress(tmp_path / "q.db")
    qp.record("q1", "b", correct=True)
    # `c` is never seen → tier 0; `a` never seen → tier 0; `b` is correct → tier 2
    order = qp.order_steps("q1", ["a", "b", "c"])
    assert order == ["a", "c", "b"]


def test_order_steps_wrong_before_correct(tmp_path: Path):
    qp = QuizProgress(tmp_path / "q.db")
    qp.record("q1", "a", correct=True)
    qp.record("q1", "b", correct=False)
    qp.record("q1", "c", correct=True)
    order = qp.order_steps("q1", ["a", "b", "c"])
    # b (wrong) before a, c (correct)
    assert order.index("b") < order.index("a")
    assert order.index("b") < order.index("c")


def test_order_steps_stable_within_tier(tmp_path: Path):
    qp = QuizProgress(tmp_path / "q.db")
    # All never-seen — should preserve input order
    assert qp.order_steps("q1", ["x", "y", "z"]) == ["x", "y", "z"]
    qp.record("q1", "x", correct=True)
    qp.record("q1", "y", correct=True)
    # x and y both correct (tier 2), z never seen (tier 0)
    assert qp.order_steps("q1", ["x", "y", "z"]) == ["z", "x", "y"]


def test_last_grade_updates_on_re_record(tmp_path: Path):
    qp = QuizProgress(tmp_path / "q.db")
    qp.record("q1", "a", correct=False)
    assert qp.stats("q1")["a"]["last_grade"] == "wrong"
    qp.record("q1", "a", correct=True)
    assert qp.stats("q1")["a"]["last_grade"] == "correct"
    # Counts accumulate
    assert qp.stats("q1")["a"]["correct_count"] == 1
    assert qp.stats("q1")["a"]["wrong_count"] == 1


def test_persists_across_instances(tmp_path: Path):
    path = tmp_path / "q.db"
    qp1 = QuizProgress(path)
    qp1.record("q1", "a", correct=True)
    qp2 = QuizProgress(path)
    assert qp2.stats("q1")["a"]["correct_count"] == 1
