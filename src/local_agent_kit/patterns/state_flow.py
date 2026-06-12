"""StateFlow — deterministic Python-driven multi-step interactions.

The pattern for templates where the model would lose track of a sequence
across turns (quiz loops, structured interviews, intake forms). Python
owns the state machine: current step, captured answers, transitions.
The model is called only at bounded points to render or grade.

Used by:
    interviewer  — declares a list of questions; one per turn; writes
                   captured answers to a structured output file.
    study_buddy  — declares a quiz; one question per turn; tracks score.

Contract:
    Step          — one node in the flow (id, prompt, optional follow-up,
                    optional explicit `next` step id).
    StateFlow     — holds the step list, current index, captured answers.
                    Caller-driven: render current() to the user, submit()
                    the user's response, repeat until is_complete().

Templates wire this OUTSIDE Agent.run — pass each rendered step through
Agent.handle() if you want model framing, or skip the model and surface
the step prompt directly. The state machine itself never calls the model.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Step:
    """One node in a StateFlow."""

    id: str
    prompt: str
    capture: bool = True             # store the user's response under this id
    follow_up: str | None = None     # one optional clarifying prompt
    next: str | None = None          # explicit jump; default = linear


class StateFlowError(ValueError):
    """Raised on malformed StateFlow construction or runtime misuse."""


class StateFlow:
    """Deterministic, single-active-step interaction state machine."""

    def __init__(self, steps: list[Step]):
        if not steps:
            raise StateFlowError("StateFlow requires at least one step")
        seen: set[str] = set()
        for s in steps:
            if s.id in seen:
                raise StateFlowError(f"duplicate step id: {s.id!r}")
            seen.add(s.id)

        self._steps: dict[str, Step] = {s.id: s for s in steps}
        self._order: list[str] = [s.id for s in steps]
        self._cursor: int = 0
        self._answers: dict[str, str] = {}
        self._follow_up_pending: bool = False

        # Validate explicit `next` references resolve to known steps.
        for s in steps:
            if s.next is not None and s.next not in self._steps:
                raise StateFlowError(
                    f"step {s.id!r} declares next={s.next!r} which is not a known step id"
                )

    @property
    def current(self) -> Step | None:
        """The active Step, or None if the flow has completed."""
        if self._cursor >= len(self._order):
            return None
        return self._steps[self._order[self._cursor]]

    def is_complete(self) -> bool:
        return self.current is None

    @property
    def answers(self) -> dict[str, str]:
        """Captured answers keyed by Step.id. Returns a copy."""
        return dict(self._answers)

    def render(self) -> str:
        """The prompt text the user should see for the active step.

        If a follow-up is pending (the previous submit() flagged the answer
        as too short), return the follow-up prompt instead of the main one.
        """
        step = self.current
        if step is None:
            raise StateFlowError("flow is complete; nothing to render")
        if self._follow_up_pending and step.follow_up:
            return step.follow_up
        return step.prompt

    def submit(self, response: str, *, follow_up: bool = False) -> None:
        """Record the user's response and advance.

        Args:
            response: the user's raw input.
            follow_up: if True, the caller (or a classifier) judged the
                response insufficient; render the step's follow_up next
                turn. Only honored once per step — the second pass always
                advances regardless.
        """
        step = self.current
        if step is None:
            raise StateFlowError("flow is complete; cannot submit")

        # Single follow-up only — if we've already shown it, advance no
        # matter what the caller passed in.
        if follow_up and step.follow_up and not self._follow_up_pending:
            self._follow_up_pending = True
            if step.capture:
                self._answers[step.id] = response
            return

        if step.capture:
            self._answers[step.id] = response

        self._follow_up_pending = False
        if step.next is not None:
            self._cursor = self._order.index(step.next)
        else:
            self._cursor += 1

    @classmethod
    def from_yaml(cls, data: dict[str, Any]) -> "StateFlow":
        """Construct from a parsed YAML dict.

        Expected shape:
            steps:
              - id: q1
                prompt: "What is the goal?"
                follow_up: "Be more specific."
              - id: q2
                prompt: "Who is the owner?"
        """
        raw = data.get("steps")
        if not isinstance(raw, list):
            raise StateFlowError("StateFlow YAML must have a top-level `steps` list")

        steps: list[Step] = []
        for i, entry in enumerate(raw):
            if not isinstance(entry, dict):
                raise StateFlowError(f"steps[{i}] must be a mapping")
            if "id" not in entry or "prompt" not in entry:
                raise StateFlowError(f"steps[{i}] requires `id` and `prompt`")
            steps.append(
                Step(
                    id=str(entry["id"]),
                    prompt=str(entry["prompt"]),
                    capture=bool(entry.get("capture", True)),
                    follow_up=entry.get("follow_up"),
                    next=entry.get("next"),
                )
            )
        return cls(steps)
