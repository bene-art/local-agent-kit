"""Narrate-only — Python computes, model narrates.

The pattern for templates where small local models would unreliably perform
the computation themselves (arithmetic, aggregation, structured-data
summarization).

Used by:
    briefer    — fetches data, formats it deterministically, model adds
                 one sentence of framing.
    analyst    — Python computes group-by/sum/mean from a CSV/JSONL, model
                 describes the result in plain language.

The contract:
    1. Caller computes the result in Python and produces a formatted string.
    2. Caller wraps the string with `envelope()` to create a [SYSTEM DATA]
       block that the agent's existing handling recognizes.
    3. Agent.handle() is called with a prompt that *references* the
       envelope but does NOT ask the model to re-derive the computation.
    4. The model's job is narration only — describe, frame, summarize.
       Never re-compute.

`NarrationRubric` is the eval-time check: a response that mentions a number
absent from the envelope body fails. Used to gate any template built on
this pattern.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


# Match the envelope format Agent._maybe_search emits, so injected
# narrate-only data is indistinguishable from injected search data at the
# model's input layer.
_ENVELOPE_TEMPLATE = "\n\n[SYSTEM DATA — {label}]\n{body}"

# Numbers: integers, decimals, percentages, with optional thousands
# separators. The separator alternative requires at least one `,NNN` group
# so plain "1200" doesn't get sliced into "120" + "0" by the greedy match.
_NUMBER_RE = re.compile(r"-?\d{1,3}(?:[,_]\d{3})+(?:\.\d+)?%?|-?\d+(?:\.\d+)?%?")


def envelope(label: str, body: str) -> str:
    """Wrap a deterministically-computed string for inline injection.

    Args:
        label: short tag identifying the data source —
               e.g. "portfolio summary", "csv aggregation".
        body:  the pre-computed text. Never call this with model output;
               this is the seam that enforces "Python computes."

    Returns:
        A string formatted to match the agent's [SYSTEM DATA] convention,
        appendable directly to a user prompt before calling Agent.handle().
    """
    if not isinstance(label, str) or not label.strip():
        raise ValueError("envelope() requires a non-empty label")
    if not isinstance(body, str):
        raise TypeError(f"envelope() body must be a string, got {type(body).__name__}")
    return _ENVELOPE_TEMPLATE.format(label=label, body=body)


def _extract_numbers(text: str) -> set[str]:
    """Return the set of number tokens appearing in `text`, normalized."""
    raw = _NUMBER_RE.findall(text)
    return {n.replace(",", "").replace("_", "") for n in raw}


@dataclass(frozen=True)
class NarrationRubric:
    """Eval-time rubric — flags responses that fabricate numbers not in
    the envelope.

    A response that mentions a number absent from `envelope_body` fails
    the rubric. Used by templates' promptfoo suites to gate the
    narrate-only contract.

    The rubric is intentionally simple:
      - Extract every number-shaped token from the response.
      - Pass if every one of those tokens also appears in envelope_body.
      - A response with no numbers passes trivially (pure framing is fine).

    Verbatim copy-paste of envelope numbers is NOT a fabrication — small
    local models will lift visible numbers, and that's the desired
    behavior here.
    """

    envelope_body: str

    def evaluate(self, response: str) -> bool:
        """True if response only narrates numbers/facts present in envelope_body."""
        envelope_numbers = _extract_numbers(self.envelope_body)
        response_numbers = _extract_numbers(response)
        return response_numbers.issubset(envelope_numbers)

    def fabricated(self, response: str) -> set[str]:
        """Return the set of number tokens in the response that are NOT in
        the envelope. Empty set means the response is grounded."""
        envelope_numbers = _extract_numbers(self.envelope_body)
        response_numbers = _extract_numbers(response)
        return response_numbers - envelope_numbers
