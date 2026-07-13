"""Patterns — named architectural idioms shared across templates.

The kit's templates lean on a small set of recurring patterns. Each one is
codified here once so templates can reference a shared helper instead of
each reinventing it (and drifting from the model-as-narrator discipline).

Current patterns:
    narrate_only — Python computes the result, model narrates it. Used by
                   scheduled tasks with fetchers and data_query flows.
    state_flow   — deterministic Python-driven multi-step interactions.
                   Used by study_buddy.
"""
from local_agent_kit.patterns.narrate_only import (
    NarrationRubric,
    envelope,
)
from local_agent_kit.patterns.state_flow import Step, StateFlow, StateFlowError

__all__ = [
    "NarrationRubric",
    "envelope",
    "Step",
    "StateFlow",
    "StateFlowError",
]
