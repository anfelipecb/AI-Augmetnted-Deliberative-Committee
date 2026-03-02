"""Tests for output formatting."""

from src.output import (
    format_deliberation_log_md,
    format_report_md,
    format_scores_json,
)

ROUND1 = [
    {
        "agent_id": "a1",
        "name": "Agent One",
        "impact": 7,
        "fiscal": 6,
        "sustainability": 8,
        "justification": "Good mix.",
    },
]
FINAL = [
    {
        "agent_id": "a1",
        "name": "Agent One",
        "impact": 7,
        "fiscal": 6,
        "sustainability": 8,
        "verdict": "Approve with conditions.",
    },
]


def test_format_scores_json():
    out = format_scores_json(ROUND1, FINAL)
    assert out["round1"] == ROUND1
    assert out["final"] == FINAL


def test_format_report_md():
    md = format_report_md(ROUND1, FINAL, "Synthesis: proceed with caution.", "")
    assert "Deliberation Report" in md
    assert "Agent One" in md
    assert "7" in md and "6" in md and "8" in md
    assert "Synthesis: proceed" in md
    assert "Approve with conditions" in md


def test_format_deliberation_log_md():
    entries = [
        {
            "agent_id": "a1",
            "round": "R1",
            "timestamp": "2025-01-01T12:00:00",
            "content": "My score is 7.",
        },
    ]
    md = format_deliberation_log_md(entries)
    assert "Deliberation Log" in md
    assert "a1" in md
    assert "My score is 7" in md
