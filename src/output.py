"""Format scores, verdicts, and synthesis into report and JSON."""

from typing import Any

ScoreRow = dict[str, Any]  # agent_id, name, impact, fiscal, sustainability, justification, verdict


def format_scores_json(
    round1_scores: list[ScoreRow], final_scores: list[ScoreRow]
) -> dict[str, Any]:
    """Produce a JSON-serializable summary of scores."""
    return {
        "round1": round1_scores,
        "final": final_scores,
    }


def format_report_md(
    round1_scores: list[ScoreRow],
    final_scores: list[ScoreRow],
    synthesis: str,
    deliberation_preview: str = "",
) -> str:
    """Produce the main report in Markdown."""
    lines = [
        "# Deliberation Report",
        "",
        "## Round 1 — Individual Scores",
        "",
    ]
    for row in round1_scores:
        name = row.get("name", row.get("agent_id", "Unknown"))
        lines.append(f"### {name}")
        lines.append("")
        lines.append(f"- **Impact**: {row.get('impact', '—')}/10")
        lines.append(f"- **Fiscal Responsibility**: {row.get('fiscal', '—')}/10")
        lines.append(f"- **Sustainability**: {row.get('sustainability', '—')}/10")
        if row.get("justification"):
            lines.append("")
            lines.append(row["justification"])
        lines.append("")

    lines.extend(
        [
            "## Final Scores & Verdicts",
            "",
        ]
    )
    for row in final_scores:
        name = row.get("name", row.get("agent_id", "Unknown"))
        lines.append(f"### {name}")
        lines.append("")
        lines.append(f"- **Impact**: {row.get('impact', '—')}/10")
        lines.append(f"- **Fiscal Responsibility**: {row.get('fiscal', '—')}/10")
        lines.append(f"- **Sustainability**: {row.get('sustainability', '—')}/10")
        if row.get("verdict"):
            lines.append("")
            lines.append("**Verdict**: " + row["verdict"])
        lines.append("")

    lines.extend(
        [
            "## Synthesis",
            "",
            synthesis or "_No synthesis generated._",
            "",
        ]
    )
    if deliberation_preview:
        lines.extend(
            [
                "---",
                "",
                "## Deliberation (excerpt)",
                "",
                deliberation_preview[:3000] + ("..." if len(deliberation_preview) > 3000 else ""),
                "",
            ]
        )
    return "\n".join(lines)


def format_deliberation_log_md(entries: list[dict[str, Any]]) -> str:
    """Format deliberation log entries into a single Markdown document."""
    lines = ["# Deliberation Log", ""]
    for e in entries:
        agent_id = e.get("agent_id", "?")
        round_name = e.get("round", "?")
        ts = e.get("timestamp", "")
        lines.append(f"## [{ts}] {round_name} — {agent_id}")
        lines.append("")
        lines.append(e.get("content", ""))
        lines.append("")
    return "\n".join(lines)
