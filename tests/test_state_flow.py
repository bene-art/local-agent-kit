"""Tests for the StateFlow pattern."""
from __future__ import annotations

import pytest

from local_agent_kit.patterns import StateFlow, StateFlowError, Step


def _steps(*items: tuple[str, str]) -> list[Step]:
    return [Step(id=i, prompt=p) for i, p in items]


def test_empty_step_list_raises():
    with pytest.raises(StateFlowError, match="at least one"):
        StateFlow([])


def test_duplicate_step_ids_rejected():
    with pytest.raises(StateFlowError, match="duplicate"):
        StateFlow(_steps(("a", "x"), ("a", "y")))


def test_unknown_next_target_rejected():
    with pytest.raises(StateFlowError, match="not a known"):
        StateFlow([Step(id="a", prompt="x", next="nowhere")])


def test_linear_progression():
    flow = StateFlow(_steps(("a", "Q1?"), ("b", "Q2?")))
    assert flow.render() == "Q1?"
    flow.submit("answer1")
    assert flow.render() == "Q2?"
    flow.submit("answer2")
    assert flow.is_complete()
    assert flow.answers == {"a": "answer1", "b": "answer2"}


def test_capture_false_skips_storage():
    flow = StateFlow([
        Step(id="intro", prompt="Hi", capture=False),
        Step(id="name", prompt="What's your name?"),
    ])
    flow.submit("ignored")
    flow.submit("Alice")
    assert flow.answers == {"name": "Alice"}


def test_explicit_next_jumps():
    flow = StateFlow([
        Step(id="a", prompt="Q1", next="c"),
        Step(id="b", prompt="Q2 (skipped)"),
        Step(id="c", prompt="Q3"),
    ])
    flow.submit("hello")
    assert flow.render() == "Q3"
    flow.submit("world")
    assert flow.is_complete()
    assert flow.answers == {"a": "hello", "c": "world"}


def test_follow_up_shown_once_then_advances():
    flow = StateFlow([
        Step(id="q", prompt="Main", follow_up="Say more"),
        Step(id="r", prompt="Next"),
    ])
    flow.submit("short", follow_up=True)
    assert flow.render() == "Say more"           # follow-up rendered
    flow.submit("longer", follow_up=True)         # ignored second time
    assert flow.render() == "Next"


def test_submit_after_complete_raises():
    flow = StateFlow(_steps(("a", "Q")))
    flow.submit("done")
    with pytest.raises(StateFlowError, match="complete"):
        flow.submit("extra")


def test_render_after_complete_raises():
    flow = StateFlow(_steps(("a", "Q")))
    flow.submit("done")
    with pytest.raises(StateFlowError, match="complete"):
        flow.render()


def test_answers_returns_a_copy():
    flow = StateFlow(_steps(("a", "Q")))
    flow.submit("hi")
    snapshot = flow.answers
    snapshot["a"] = "tampered"
    assert flow.answers == {"a": "hi"}


def test_from_yaml_minimal():
    data = {"steps": [
        {"id": "q1", "prompt": "What?"},
        {"id": "q2", "prompt": "Why?", "capture": False},
    ]}
    flow = StateFlow.from_yaml(data)
    assert flow.render() == "What?"
    flow.submit("because")
    flow.submit("reasons")
    assert flow.answers == {"q1": "because"}


def test_from_yaml_rejects_missing_keys():
    with pytest.raises(StateFlowError, match="requires"):
        StateFlow.from_yaml({"steps": [{"id": "q1"}]})
