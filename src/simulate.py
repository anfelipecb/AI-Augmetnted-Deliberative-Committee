"""
Orchestrate committee deliberation: load proposal, run rounds, write logs and report.

CLI: python -m src.simulate --proposal <path> [--mode jury|full] [--output-dir <dir>]
"""

import argparse
import json
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Delay between API calls to stay under Anthropic rate limits (seconds)
API_DELAY_SECONDS = 2.5


def _log_phase(msg: str) -> None:
    """Log and flush so terminal/Docker shows progress immediately."""
    logger.info("%s", msg)
    sys.stderr.flush()

from src.agents import (
    build_community_system_prompt,
    build_jury_system_prompt,
    invoke_agent,
)
from src.config import OUTPUTS_DIR
from src.output import (
    format_deliberation_log_md,
    format_report_md,
    format_scores_json,
)
from src.personas import load_community_personas, load_jury_personas
from src.proposal_loader import ProposalLoadError, load_proposal


def _parse_scores_from_text(text: str) -> dict[str, int | str]:
    """Extract Impact, Fiscal, Sustainability (1-10) and justification/verdict from agent text."""
    out: dict[str, int | str] = {}
    patterns = [
        (r"(?:impact|Impact)\s*[:\s]+\s*(\d+)", "impact"),
        (r"(?:fiscal\s*responsibility|Fiscal Responsibility)\s*[:\s]+\s*(\d+)", "fiscal"),
        (r"(?:sustainability|Sustainability)\s*[:\s]+\s*(\d+)", "sustainability"),
    ]
    for pattern, key in patterns:
        m = re.search(pattern, text, re.I)
        if m:
            try:
                out[key] = int(m.group(1))
            except ValueError:
                pass
    # Defaults if not found
    for k in ("impact", "fiscal", "sustainability"):
        if k not in out:
            out[k] = 0
    # Verdict: last 1-2 sentences or a line starting with Verdict
    verdict_m = re.search(r"(?:Verdict|verdict)\s*[:\s]+(.+?)(?=\n\n|\Z)", text, re.S | re.I)
    if verdict_m:
        out["verdict"] = verdict_m.group(1).strip()[:500]
    else:
        sentences = re.findall(r"[^.!?]+[.!?]", text)
        out["verdict"] = " ".join(sentences[-2:]).strip()[:500] if sentences else ""
    # Justification: block of text before verdict or first 400 chars
    out["justification"] = text[:400].strip() if text else ""
    return out


def _run_round1_jury(
    proposal_text: str, community_summary: str, jury_personas: list
) -> tuple[list, list]:
    """Round 1: each jury agent scores the proposal. Returns (score_rows, log_entries)."""
    logger.info("Starting phase: Round 1 — Individual scoring (%d jury agents)", len(jury_personas))
    intro = (
        "Also included is a summary of community stakeholder reactions."
        if community_summary
        else ""
    )
    community_block = ""
    if community_summary:
        community_block = f"Community reactions summary:\n---\n{community_summary[:8000]}\n\n"
    prompt = f"""Below is a Chicago stadium/urban policy proposal to evaluate. {intro}

Proposal:
---
{proposal_text[:120000]}
---

{community_block}
---

Score the proposal on each criterion (1-10) and give a short justification. Use this format so we can parse it:

Impact: [1-10]
Fiscal Responsibility: [1-10]
Sustainability: [1-10]
Justification: [2-4 sentences]
"""
    log_entries: list[dict] = []
    score_rows: list[dict] = []
    for persona in jury_personas:
        _log_phase(f"Invoking agent: {persona['id']}")
        sys_prompt = build_jury_system_prompt(persona["content"])
        try:
            response = invoke_agent(persona["id"], sys_prompt, prompt, None)
        except RuntimeError as e:
            response = f"Unable to complete scoring. ({e.args[0] if e.args else 'API error'})"
        _log_phase(f"Agent {persona['id']} done")
        time.sleep(API_DELAY_SECONDS)
        log_entries.append(
            {
                "agent_id": persona["id"],
                "round": "Round 1 — Individual scoring",
                "timestamp": datetime.now().isoformat(),
                "content": response,
            }
        )
        parsed = _parse_scores_from_text(response)
        score_rows.append(
            {
                "agent_id": persona["id"],
                "name": persona["name"],
                "impact": parsed.get("impact", 0),
                "fiscal": parsed.get("fiscal", 0),
                "sustainability": parsed.get("sustainability", 0),
                "justification": parsed.get("justification", response[:400]),
            }
        )
    return score_rows, log_entries


def _run_round2_deliberation(
    jury_personas: list,
    round1_scores: list[dict],
    log_entries_so_far: list[dict],
) -> list[dict]:
    """Round 2: each agent reacts to others' scores in sequence."""
    logger.info("Starting phase: Round 2 — Deliberation (%d jury agents)", len(jury_personas))
    # Cap transcript size so prompt stays within model limits (~8k chars for user message)
    transcript_parts = [f"**{e['agent_id']}**: {e['content'][:1500]}" for e in log_entries_so_far]
    transcript = "\n\n".join(transcript_parts)[:6000]
    deliberation_prompt = f"""Here are the Round 1 scores and justifications from the panel:

{transcript}

---

Respond in character: react to your colleagues' scores and reasoning. Do you agree or disagree with any? What would you push back on or emphasize? Keep your response to a short paragraph."""
    new_entries: list[dict] = []
    for persona in jury_personas:
        _log_phase(f"Invoking agent: {persona['id']} (Round 2)")
        sys_prompt = build_jury_system_prompt(persona["content"])
        history = [{"role": "user", "content": deliberation_prompt[:8000]}]
        # Add prior agents' deliberation responses
        for e in new_entries:
            history.append({"role": "assistant", "content": e["content"][:1500]})
        try:
            response = invoke_agent(persona["id"], sys_prompt, deliberation_prompt, history[:10])
        except RuntimeError:
            response = "No additional comment."
        _log_phase(f"Agent {persona['id']} done (Round 2)")
        time.sleep(API_DELAY_SECONDS)
        new_entries.append(
            {
                "agent_id": persona["id"],
                "round": "Round 2 — Deliberation",
                "timestamp": datetime.now().isoformat(),
                "content": response,
            }
        )
    return log_entries_so_far + new_entries


def _run_round3_final(
    jury_personas: list,
    deliberation_log_entries: list[dict],
) -> tuple[list[dict], str]:
    """Round 3: final scores and verdicts; then synthesize."""
    logger.info("Starting phase: Round 3 — Final vote (%d jury agents)", len(jury_personas))
    transcript = "\n\n".join(
        f"**{e['agent_id']}** ({e['round']}): {e['content'][:1200]}"
        for e in deliberation_log_entries[-14:]
    )
    prompt = f"""Here is the deliberation so far:

{transcript}

---

Give your **final** scores (you may revise from Round 1) and a 2-sentence verdict. Use this format:

Impact: [1-10]
Fiscal Responsibility: [1-10]
Sustainability: [1-10]
Verdict: [Exactly 2 sentences.]
"""
    final_rows: list[dict] = []
    log_entries = list(deliberation_log_entries)
    for persona in jury_personas:
        _log_phase(f"Invoking agent: {persona['id']} (Round 3)")
        sys_prompt = build_jury_system_prompt(persona["content"])
        try:
            response = invoke_agent(persona["id"], sys_prompt, prompt[:8000], None)
        except RuntimeError:
            response = "Unable to complete."
        _log_phase(f"Agent {persona['id']} done (Round 3)")
        time.sleep(API_DELAY_SECONDS)
        log_entries.append(
            {
                "agent_id": persona["id"],
                "round": "Round 3 — Final vote",
                "timestamp": datetime.now().isoformat(),
                "content": response,
            }
        )
        parsed = _parse_scores_from_text(response)
        final_rows.append(
            {
                "agent_id": persona["id"],
                "name": persona["name"],
                "impact": parsed.get("impact", 0),
                "fiscal": parsed.get("fiscal", 0),
                "sustainability": parsed.get("sustainability", 0),
                "verdict": parsed.get("verdict", response[:300]),
            }
        )
    # Synthesis: one more call to produce consensus report
    synthesis = _run_synthesis(log_entries, final_rows)
    return final_rows, synthesis, log_entries


def _run_synthesis(log_entries: list[dict], final_rows: list[dict]) -> str:
    """Single call to produce a short consensus report."""
    logger.info("Starting phase: Synthesis")
    summary = "\n".join(
        f"- {r['name']}: I={r.get('impact')} F={r.get('fiscal')} S={r.get('sustainability')} — {str(r.get('verdict', ''))[:200]}"
        for r in final_rows
    )
    prompt = f"""Based on the final scores and verdicts:

{summary}

Write a short consensus report (4-6 sentences): key strengths of the proposal, key weaknesses, and under what conditions the panel would recommend proceeding. Preserve dissenting views where relevant. Write in neutral, professional tone."""
    try:
        return invoke_agent(
            "synthesis",
            "You are summarizing the panel's deliberation. Be concise and fair. Do not add new opinions.",
            prompt,
            None,
        )
    except RuntimeError:
        return "Synthesis could not be generated."


def _run_community_phase(proposal_text: str, community_personas: list) -> str:
    """Run community agents and return a summary for the jury."""
    logger.info("Starting phase: Community (%d agents)", len(community_personas))
    prompt = f"""Below is a Chicago stadium/urban policy proposal. React from your perspective: What changes for you? What worries you? What excites you? Be concrete.

Proposal (excerpt):
---
{proposal_text[:60000]}
---
"""
    parts: list[str] = []
    for persona in community_personas:
        _log_phase(f"Invoking community agent: {persona['id']}")
        sys_prompt = build_community_system_prompt(persona["content"])
        try:
            response = invoke_agent(persona["id"], sys_prompt, prompt, None)
        except RuntimeError:
            response = "No response."
        _log_phase(f"Agent {persona['id']} done")
        time.sleep(API_DELAY_SECONDS)
        parts.append(f"**{persona['name']}** ({persona['id']}): {response[:800]}")
    return "\n\n".join(parts)


def get_community_summary(proposal_text: str) -> str:
    """Run community phase and return summary (for full mode). Use before run_round1."""
    community_personas = load_community_personas()
    if not community_personas:
        return ""
    return _run_community_phase(proposal_text, community_personas)


def run_round1(
    proposal_text: str,
    community_summary: str,
    jury_personas: list,
    output_dir: Path | None = None,
) -> tuple[list, list, Path]:
    """
    Run Round 1 only: individual scoring. Creates output_dir, writes round1 files.
    Returns (round1_scores, log_entries, out_dir).
    """
    out = output_dir or (OUTPUTS_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_run")
    out.mkdir(parents=True, exist_ok=True)
    _log_phase("Starting Round 1 — Individual scoring")
    file_handler = logging.FileHandler(out / "run.log", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    src_logger = logging.getLogger("src")
    src_logger.addHandler(file_handler)
    try:
        round1_scores, log_entries = _run_round1_jury(
            proposal_text, community_summary, jury_personas
        )
        (out / "round1_scores.json").write_text(
            json.dumps({"round1": round1_scores}, indent=2), encoding="utf-8"
        )
        round1_entries = [e for e in log_entries if e.get("round") == "Round 1 — Individual scoring"]
        (out / "round1_log.md").write_text(
            format_deliberation_log_md(round1_entries), encoding="utf-8"
        )
        (out / "deliberation_log.md").write_text(
            format_deliberation_log_md(log_entries), encoding="utf-8"
        )
        return round1_scores, log_entries, out
    finally:
        src_logger.removeHandler(file_handler)


def run_round2(
    jury_personas: list,
    log_entries: list[dict],
    out_dir: Path,
) -> list[dict]:
    """Run Round 2 only: deliberation. Appends to log_entries, writes updated deliberation_log. Returns log_entries."""
    _log_phase("Starting Round 2 — Deliberation")
    file_handler = logging.FileHandler(out_dir / "run.log", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    src_logger = logging.getLogger("src")
    src_logger.addHandler(file_handler)
    try:
        log_entries = _run_round2_deliberation(jury_personas, [], log_entries)
        (out_dir / "deliberation_log.md").write_text(
            format_deliberation_log_md(log_entries), encoding="utf-8"
        )
        round2_entries = [e for e in log_entries if e.get("round") == "Round 2 — Deliberation"]
        (out_dir / "round2_log.md").write_text(
            format_deliberation_log_md(round2_entries), encoding="utf-8"
        )
        return log_entries
    finally:
        src_logger.removeHandler(file_handler)


def run_round3(
    jury_personas: list,
    log_entries: list[dict],
    round1_scores: list[dict],
    out_dir: Path,
) -> tuple[list[dict], str]:
    """Run Round 3 + synthesis. Writes report, scores, full log. Returns (final_scores, synthesis)."""
    _log_phase("Starting Round 3 — Final vote")
    file_handler = logging.FileHandler(out_dir / "run.log", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    src_logger = logging.getLogger("src")
    src_logger.addHandler(file_handler)
    try:
        final_scores, synthesis, full_log_entries = _run_round3_final(jury_personas, log_entries)
        (out_dir / "deliberation_log.md").write_text(
            format_deliberation_log_md(full_log_entries), encoding="utf-8"
        )
        deliberation_preview = "\n\n".join(e["content"][:500] for e in full_log_entries)
        report_md = format_report_md(round1_scores, final_scores, synthesis, deliberation_preview)
        (out_dir / "report.md").write_text(report_md, encoding="utf-8")
        scores_data = format_scores_json(round1_scores, final_scores)
        (out_dir / "scores.json").write_text(json.dumps(scores_data, indent=2), encoding="utf-8")
        return final_scores, synthesis
    finally:
        src_logger.removeHandler(file_handler)


def run(
    proposal_text: str,
    mode: str = "jury",
    output_dir: Path | None = None,
) -> Path:
    """
    Run the full deliberation and write outputs.

    Args:
        proposal_text: Full proposal text.
        mode: "jury" (7 experts), "jury_quick" (4 experts), or "full" (community then jury).
        output_dir: Where to write; default outputs/<timestamp>_run.

    Returns:
        Path to the run directory.
    """
    out = output_dir or (OUTPUTS_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_run")
    out.mkdir(parents=True, exist_ok=True)
    logger.info("Starting deliberation (mode=%s, output=%s)", mode, out.name)
    # Write API/run errors to run.log so you can inspect (e.g. docker compose + volume)
    log_file = out / "run.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )
    src_logger = logging.getLogger("src")
    src_logger.addHandler(file_handler)
    try:
        jury_personas = load_jury_personas(quick=(mode == "jury_quick"))
        community_personas = load_community_personas() if mode == "full" else []
        community_summary = ""
        if mode == "full" and community_personas:
            community_summary = _run_community_phase(proposal_text, community_personas)
            (out / "community_summary.md").write_text(community_summary, encoding="utf-8")
        round1_scores, log_entries = _run_round1_jury(
            proposal_text, community_summary, jury_personas
        )
        (out / "round1_scores.json").write_text(
            json.dumps({"round1": round1_scores}, indent=2), encoding="utf-8"
        )
        (out / "round1_log.md").write_text(
            format_deliberation_log_md([e for e in log_entries if e.get("round") == "Round 1 — Individual scoring"]),
            encoding="utf-8",
        )
        log_entries = _run_round2_deliberation(jury_personas, round1_scores, log_entries)
        (out / "round2_log.md").write_text(
            format_deliberation_log_md([e for e in log_entries if e.get("round") == "Round 2 — Deliberation"]),
            encoding="utf-8",
        )
        final_scores, synthesis, log_entries = _run_round3_final(jury_personas, log_entries)
        deliberation_preview = "\n\n".join(e["content"][:500] for e in log_entries)
        report_md = format_report_md(
            round1_scores, final_scores, synthesis, deliberation_preview
        )
        (out / "report.md").write_text(report_md, encoding="utf-8")
        (out / "deliberation_log.md").write_text(
            format_deliberation_log_md(log_entries), encoding="utf-8"
        )
        scores_data = format_scores_json(round1_scores, final_scores)
        (out / "scores.json").write_text(
            json.dumps(scores_data, indent=2), encoding="utf-8"
        )
    finally:
        src_logger.removeHandler(file_handler)
    return out


def _cli_proposal_path(path_str: str) -> Path:
    root = Path(__file__).resolve().parent.parent
    if not (root / "pyproject.toml").exists():
        root = Path.cwd()
    base = root / "proposals"
    p = Path(path_str)
    if not p.is_absolute():
        p = base / p
    return p.resolve()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run HPIC committee deliberation")
    parser.add_argument("--proposal", required=True, help="Path to proposal .md or .pdf")
    parser.add_argument(
        "--mode",
        choices=["jury", "jury_quick", "full"],
        default="jury",
        help="jury (7), jury_quick (4), or full (community + jury)",
    )
    parser.add_argument("--output-dir", type=Path, default=None, help="Output directory")
    args = parser.parse_args()
    try:
        proposal_path = _cli_proposal_path(args.proposal)
        root = Path(__file__).resolve().parent.parent
        if not (root / "pyproject.toml").exists():
            root = Path.cwd()
        text = load_proposal(proposal_path, base_dir=root)
    except ProposalLoadError as e:
        print(f"Error: {e}")
        raise SystemExit(1)
    out = run(text, mode=args.mode, output_dir=args.output_dir)
    print(f"Done. Outputs in {out}")


if __name__ == "__main__":
    main()
