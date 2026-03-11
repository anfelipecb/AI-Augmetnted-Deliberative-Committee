"""
Evaluation suite for HPIC deliberation pipeline outputs.

Validates score ranges, criteria validity, verdict-score consistency,
and synthesis presence. Run via: uv run python -m src.evaluation --run-dir outputs/<run_id>
"""

import argparse
import json
import re
from pathlib import Path

from src.criteria import CRITERIA_6, VALID_LEVELS

# Phrases that indicate strong positive verdict (inconsistent with low scores)
STRONG_POSITIVE_PHRASES = [
    r"strongly\s+approve",
    r"highly\s+recommend",
    r"excellent\s+proposal",
    r"fully\s+support",
    r"wholeheartedly\s+endorse",
]

# Phrases that indicate strong negative verdict (inconsistent with high scores)
STRONG_NEGATIVE_PHRASES = [
    r"strongly\s+oppose",
    r"cannot\s+support",
    r"reject\s+this",
    r"fundamentally\s+flawed",
    r"do\s+not\s+recommend",
]


def validate_scores(
    scores: list[dict],
    synthesis: str | None = None,
) -> dict:
    """
    Validate a list of score rows (round1 or final format).

    Args:
        scores: List of dicts with impact, fiscal, sustainability, verdict, criteria.
        synthesis: Optional synthesis text to validate.

    Returns:
        Dict with passed, tests, advice.
    """
    tests: list[dict] = []
    advice: list[str] = []
    all_passed = True

    # Test 1: All agents responded
    n_agents = len(scores)
    agents_ok = n_agents >= 1
    tests.append({
        "test": "All agents responded",
        "expected": ">= 1 agent",
        "actual": f"{n_agents} agents",
        "passed": agents_ok,
    })
    if not agents_ok:
        all_passed = False
        advice.append("No score rows found. Pipeline may have failed.")
        return {"passed": False, "tests": tests, "advice": advice}

    # Test 2: Score validity (1-10) for all rows
    score_failures: list[str] = []
    for row in scores:
        name = row.get("name", row.get("agent_id", "?"))
        for key in ("impact", "fiscal", "sustainability"):
            val = row.get(key)
            if val is None:
                val = 0
            try:
                num = int(val) if not isinstance(val, int) else val
            except (ValueError, TypeError):
                num = -1
            if not (1 <= num <= 10):
                score_failures.append(f"{name} {key}={val}")
    scores_ok = len(score_failures) == 0
    tests.append({
        "test": "Score validity (1-10)",
        "expected": "All impact, fiscal, sustainability in 1-10",
        "actual": "OK" if scores_ok else "; ".join(score_failures[:5]),
        "passed": scores_ok,
    })
    if not scores_ok:
        all_passed = False
        advice.extend(f"Invalid score: {f}" for f in score_failures[:5])

    # Test 3: Criteria validity (LOW, MEDIUM, HIGH when present)
    crit_failures: list[str] = []
    for row in scores:
        name = row.get("name", row.get("agent_id", "?"))
        criteria = row.get("criteria") or {}
        for ckey in CRITERIA_6:
            val = (criteria.get(ckey) or "").strip().upper()
            if val and val not in VALID_LEVELS:
                crit_failures.append(f"{name} {ckey}={val}")
    crit_ok = len(crit_failures) == 0
    tests.append({
        "test": "Criteria validity",
        "expected": "LOW, MEDIUM, or HIGH",
        "actual": "OK" if crit_ok else "; ".join(crit_failures[:5]),
        "passed": crit_ok,
    })
    if not crit_ok:
        all_passed = False
        advice.extend(f"Invalid criterion: {f}" for f in crit_failures[:5])

    # Test 4: Verdict-score consistency
    verdict_failures: list[str] = []
    for row in scores:
        name = row.get("name", row.get("agent_id", "?"))
        verdict = (row.get("verdict") or row.get("justification") or "").lower()
        imp = int(row.get("impact", 0) or 0)
        fis = int(row.get("fiscal", 0) or 0)
        sus = int(row.get("sustainability", 0) or 0)
        avg = (imp + fis + sus) / 3 if (imp or fis or sus) else 5

        if avg < 4 and verdict:
            for pat in STRONG_POSITIVE_PHRASES:
                if re.search(pat, verdict, re.I):
                    verdict_failures.append(f"{name}: low scores, positive verdict")
                    break
        elif avg > 7 and verdict:
            for pat in STRONG_NEGATIVE_PHRASES:
                if re.search(pat, verdict, re.I):
                    verdict_failures.append(f"{name}: high scores, negative verdict")
                    break
    verdict_ok = len(verdict_failures) == 0
    tests.append({
        "test": "Verdict-score consistency",
        "expected": "Verdict aligns with scores",
        "actual": "OK" if verdict_ok else "; ".join(verdict_failures),
        "passed": verdict_ok,
    })
    if not verdict_ok:
        all_passed = False
        advice.extend(verdict_failures)

    # Test 5: Synthesis presence (when provided)
    if synthesis is not None:
        syn_ok = isinstance(synthesis, str) and len(synthesis.strip()) > 0
        tests.append({
            "test": "Synthesis present",
            "expected": "Non-empty synthesis",
            "actual": f"{len((synthesis or '').strip())} chars",
            "passed": syn_ok,
        })
        if not syn_ok:
            all_passed = False
            advice.append("Synthesis is missing or empty.")

    if all_passed:
        advice.insert(0, "All validation tests passed.")

    return {
        "passed": all_passed,
        "tests": tests,
        "advice": advice,
    }


def load_run_outputs(run_dir: Path) -> dict:
    """
    Load outputs from a run directory.

    Args:
        run_dir: Path to outputs/<run_id>_run.

    Returns:
        Dict with round1, final, synthesis, report_text, proposal_summary.
        round1 and final are lists of score rows.

    Raises:
        FileNotFoundError: If scores.json is missing.
    """
    run_dir = Path(run_dir)
    scores_path = run_dir / "scores.json"
    if not scores_path.exists():
        raise FileNotFoundError(f"scores.json not found in {run_dir}")

    data = json.loads(scores_path.read_text(encoding="utf-8"))
    round1 = data.get("round1") or []
    final = data.get("final") or []

    report_path = run_dir / "report.md"
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""

    # Extract synthesis from report (section after "## Synthesis")
    synthesis = ""
    if "## Synthesis" in report_text:
        parts = report_text.split("## Synthesis", 1)
        if len(parts) > 1:
            synthesis = parts[1].strip().split("\n## ")[0].strip()

    proposal_path = run_dir / "proposal_summary.md"
    proposal_summary = (
        proposal_path.read_text(encoding="utf-8") if proposal_path.exists() else ""
    )

    return {
        "round1": round1,
        "final": final,
        "synthesis": synthesis,
        "report_text": report_text,
        "proposal_summary": proposal_summary,
    }


def evaluate_run(run_dir: Path) -> dict:
    """
    Evaluate a run directory: load outputs and validate.

    Args:
        run_dir: Path to outputs/<run_id>_run.

    Returns:
        Dict with all_passed, round1_result, final_result, advice, error.
        If load fails, error is set and all_passed is False.
    """
    try:
        outputs = load_run_outputs(run_dir)
    except FileNotFoundError as e:
        return {
            "all_passed": False,
            "round1_result": None,
            "final_result": None,
            "advice": [str(e)],
            "error": str(e),
        }

    round1_result = validate_scores(
        outputs["round1"],
        synthesis=None,
    )
    final_result = validate_scores(
        outputs["final"],
        synthesis=outputs["synthesis"],
    )

    all_passed = round1_result["passed"] and final_result["passed"]
    advice = []
    if not round1_result["passed"]:
        advice.extend(round1_result["advice"])
    if not final_result["passed"]:
        advice.extend(final_result["advice"])

    return {
        "all_passed": all_passed,
        "round1_result": round1_result,
        "final_result": final_result,
        "advice": advice,
        "error": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate HPIC deliberation run outputs"
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        required=True,
        help="Path to run directory (e.g. outputs/20260307_181216_run)",
    )
    args = parser.parse_args()

    result = evaluate_run(args.run_dir)
    status = "PASS" if result["all_passed"] else "FAIL"
    print(f"\nEvaluation: {status}\n")
    if result["error"]:
        print(f"Error: {result['error']}")
        return
    for a in result["advice"]:
        print(f"  {a}")
    if result["round1_result"]:
        failed = [t for t in result["round1_result"]["tests"] if not t["passed"]]
        if failed:
            print("\nRound 1 failed tests:")
            for t in failed:
                print(f"  - {t['test']}: expected {t['expected']}, got {t['actual']}")
    if result["final_result"]:
        failed = [t for t in result["final_result"]["tests"] if not t["passed"]]
        if failed:
            print("\nFinal failed tests:")
            for t in failed:
                print(f"  - {t['test']}: expected {t['expected']}, got {t['actual']}")


if __name__ == "__main__":
    main()
