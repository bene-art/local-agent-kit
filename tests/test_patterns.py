"""Tests for the narrate-only pattern."""
from __future__ import annotations

import pytest

from local_agent_kit.patterns.narrate_only import NarrationRubric, envelope


def test_envelope_format_matches_system_data_convention():
    result = envelope("portfolio summary", "Total: 42")
    assert result.startswith("\n\n[SYSTEM DATA — portfolio summary]\n")
    assert "Total: 42" in result


def test_envelope_rejects_empty_label():
    with pytest.raises(ValueError):
        envelope("", "body")


def test_rubric_passes_when_response_uses_only_envelope_numbers():
    rubric = NarrationRubric(envelope_body="Revenue: 1,200. Growth: 8.5%.")
    assert rubric.evaluate("Revenue hit 1200 with 8.5% growth.") is True


def test_rubric_fails_when_response_fabricates_a_number():
    rubric = NarrationRubric(envelope_body="Total: 42.")
    assert rubric.evaluate("The total was 99.") is False


def test_rubric_passes_when_response_has_no_numbers():
    rubric = NarrationRubric(envelope_body="Total: 42.")
    assert rubric.evaluate("Things look stable overall.") is True


def test_rubric_reports_fabricated_set():
    rubric = NarrationRubric(envelope_body="Total: 42.")
    assert rubric.fabricated("Total 42 and also 7 and 99.") == {"7", "99"}
