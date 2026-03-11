"""Tests for the HPIC evaluation suite."""

import json
from pathlib import Path

import pytest

from src.criteria import CRITERIA_6
from src.evaluation import (
    evaluate_run,
    load_run_outputs,
    validate_scores,
)


def test_validate_scores_valid():
    """Valid scores (1-10, valid criteria) pass all tests."""
    scores = [
        {
            "agent_id": "a1",
            "name": "Agent One",
            "impact": 7,
            "fiscal": 6,
            "sustainability": 8,
            "verdict": "The proposal shows promise with some concerns.",
            "criteria": {c: "MEDIUM" for c in CRITERIA_6},
        },
    ]
    result = validate_scores(scores, synthesis="Short consensus report.")
    assert result["passed"] is True
    assert all(t["passed"] for t in result["tests"])
    assert any("All validation tests passed" in a for a in result["advice"])


def test_validate_scores_invalid_range():
    """Score 11 or 0 fails."""
    scores = [
        {
            "agent_id": "a1",
            "name": "Agent One",
            "impact": 11,
            "fiscal": 6,
            "sustainability": 8,
            "verdict": "Good.",
            "criteria": {c: "MEDIUM" for c in CRITERIA_6},
        },
    ]
    result = validate_scores(scores)
    assert result["passed"] is False
    assert any("Score validity" in t["test"] and not t["passed"] for t in result["tests"])

    scores[0]["impact"] = 0
    scores[0]["fiscal"] = 0
    result2 = validate_scores(scores)
    assert result2["passed"] is False


def test_validate_scores_invalid_criteria():
    """Invalid criterion value (e.g. 'MED') fails."""
    scores = [
        {
            "agent_id": "a1",
            "name": "Agent One",
            "impact": 7,
            "fiscal": 6,
            "sustainability": 8,
            "verdict": "Good.",
            "criteria": {c: "MED" if c == "fiscal_impact" else "MEDIUM" for c in CRITERIA_6},
        },
    ]
    # fiscal_impact is "MED" which is invalid
    result = validate_scores(scores)
    assert result["passed"] is False
    assert any("Criteria validity" in t["test"] and not t["passed"] for t in result["tests"])


def test_validate_scores_verdict_consistency():
    """Low scores + 'strongly approve' fails consistency check."""
    scores = [
        {
            "agent_id": "a1",
            "name": "Agent One",
            "impact": 2,
            "fiscal": 2,
            "sustainability": 3,
            "verdict": "I strongly approve of this excellent proposal.",
            "criteria": {c: "LOW" for c in CRITERIA_6},
        },
    ]
    result = validate_scores(scores)
    assert result["passed"] is False
    assert any("Verdict" in t["test"] and not t["passed"] for t in result["tests"])


def test_validate_scores_empty_fails():
    """Empty scores list fails."""
    result = validate_scores([])
    assert result["passed"] is False
    assert "No score rows found" in result["advice"][0]


def test_validate_scores_synthesis_required():
    """When synthesis is provided as empty, fails."""
    scores = [
        {
            "agent_id": "a1",
            "name": "Agent One",
            "impact": 7,
            "fiscal": 6,
            "sustainability": 8,
            "verdict": "Good.",
            "criteria": {c: "MEDIUM" for c in CRITERIA_6},
        },
    ]
    result = validate_scores(scores, synthesis="")
    assert result["passed"] is False
    assert any("Synthesis" in t["test"] and not t["passed"] for t in result["tests"])


def test_evaluate_run_with_fixture(tmp_path):
    """Use tmp_path fixture with minimal valid scores.json and report.md; evaluate_run returns all_passed True."""
    scores_data = {
        "round1": [
            {
                "agent_id": "sarah_chen",
                "name": "Dr. Sarah Chen",
                "impact": 6,
                "fiscal": 7,
                "sustainability": 6,
                "justification": "Reasonable fiscal structure.",
                "criteria": {c: "MEDIUM" for c in CRITERIA_6},
            },
        ],
        "final": [
            {
                "agent_id": "sarah_chen",
                "name": "Dr. Sarah Chen",
                "impact": 6,
                "fiscal": 7,
                "sustainability": 6,
                "verdict": "Proceed with conditions. Ensure accountability.",
                "criteria": {c: "MEDIUM" for c in CRITERIA_6},
            },
        ],
    }
    (tmp_path / "scores.json").write_text(
        json.dumps(scores_data, indent=2),
        encoding="utf-8",
    )
    report = """# Deliberation Report

## Round 1 — Individual Scores

### Dr. Sarah Chen
- **Impact**: 6/10
- **Fiscal Responsibility**: 7/10
- **Sustainability**: 6/10

## Final Scores & Verdicts

### Dr. Sarah Chen
- **Impact**: 6/10
- **Fiscal Responsibility**: 7/10
- **Sustainability**: 6/10
**Verdict**: Proceed with conditions.

## Synthesis

The panel finds the proposal has merit with some fiscal safeguards needed.
"""
    (tmp_path / "report.md").write_text(report, encoding="utf-8")

    result = evaluate_run(tmp_path)
    assert result["all_passed"] is True
    assert result["error"] is None
    assert result["round1_result"]["passed"] is True
    assert result["final_result"]["passed"] is True


def test_evaluate_run_missing_files(tmp_path):
    """Missing scores.json raises or returns error."""
    result = evaluate_run(tmp_path)
    assert result["all_passed"] is False
    assert result["error"] is not None
    assert "scores.json" in result["error"] or "not found" in result["error"].lower()


def test_load_run_outputs(tmp_path):
    """load_run_outputs loads scores and extracts synthesis from report."""
    scores_data = {"round1": [], "final": []}
    (tmp_path / "scores.json").write_text(
        json.dumps(scores_data, indent=2),
        encoding="utf-8",
    )
    (tmp_path / "report.md").write_text(
        "# Report\n\n## Synthesis\n\nThis is the synthesis text.",
        encoding="utf-8",
    )
    out = load_run_outputs(tmp_path)
    assert out["round1"] == []
    assert out["final"] == []
    assert out["synthesis"] == "This is the synthesis text."


def test_load_run_outputs_missing_raises(tmp_path):
    """load_run_outputs raises FileNotFoundError when scores.json missing."""
    with pytest.raises(FileNotFoundError, match="scores.json"):
        load_run_outputs(tmp_path)
