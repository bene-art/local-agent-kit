"""Patterns — named architectural idioms shared across templates.

The kit's templates lean on a small set of recurring patterns. Each one is
codified here once so templates can reference a shared helper instead of
each reinventing it (and drifting from the model-as-narrator discipline).

Current patterns:
    narrate_only — Python computes the result, model narrates it. Used by
                   briefer and analyst.
"""
from local_agent_kit.patterns.narrate_only import (
    NarrationRubric,
    envelope,
)

__all__ = ["NarrationRubric", "envelope"]
