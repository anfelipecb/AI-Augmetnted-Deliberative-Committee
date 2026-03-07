"""Format scores, verdicts, and synthesis into report and JSON."""

from typing import Any

from src.criteria import CRITERIA_6, CRITERIA_LABELS, LEVEL_TO_NUM

ScoreRow = dict[str, Any]  # agent_id, name, impact, fiscal, sustainability, justification, verdict, criteria

# Badge colors: LOW=red/pink, MEDIUM=yellow/gold, HIGH=green
BADGE_CSS = {
    "LOW": ("#c53030", "#feb2b2"),
    "MEDIUM": ("#b7791f", "#fef3c7"),
    "HIGH": ("#276749", "#c6f6d5"),
}

# Table header color (Harris/page maroon) for criteria column titles
TABLE_HEADER_COLOR = "#800000"


def compute_criteria_average(scores: list[dict]) -> dict[str, str]:
    """Map LOW=1, MEDIUM=2, HIGH=3; average per criterion; convert back to label. Returns dict of criterion -> LOW|MEDIUM|HIGH."""
    if not scores:
        return {c: "" for c in CRITERIA_6}
    sums: dict[str, list[float]] = {c: [] for c in CRITERIA_6}
    for row in scores:
        criteria = row.get("criteria") or {}
        for key in CRITERIA_6:
            val = (criteria.get(key) or "").strip().upper()
            if val in LEVEL_TO_NUM:
                sums[key].append(LEVEL_TO_NUM[val])
    out: dict[str, str] = {}
    for key in CRITERIA_6:
        nums = sums[key]
        if not nums:
            out[key] = ""
            continue
        avg = sum(nums) / len(nums)
        if avg < 1.5:
            out[key] = "LOW"
        elif avg <= 2.5:
            out[key] = "MEDIUM"
        else:
            out[key] = "HIGH"
    return out


def format_criteria_table_html(
    scores: list[dict],
    show_average: bool = True,
    name_key: str = "name",
) -> str:
    """Produce an HTML table: rows = agents (+ Average), columns = 6 criteria, cells = colored badges."""
    rows: list[list[str]] = []
    for row in scores:
        name = row.get(name_key, row.get("agent_id", "?"))
        criteria = row.get("criteria") or {}
        cell_vals = []
        for c in CRITERIA_6:
            val = (criteria.get(c) or "").strip().upper()
            if val not in BADGE_CSS:
                val = ""
            cell_vals.append(val)
        rows.append([str(name)] + cell_vals)
    if show_average and scores:
        avg_row = compute_criteria_average(scores)
        cells = [avg_row.get(c, "") for c in CRITERIA_6]
        rows.append(["Average"] + cells)
    headers = [""] + [CRITERIA_LABELS[c] for c in CRITERIA_6]
    lines = [
        "<table style='border-collapse: collapse; width: 100%;'>",
        "<thead><tr>",
    ]
    header_style = f"border: 1px solid #ccc; padding: 8px; text-align: left; background-color: {TABLE_HEADER_COLOR}; color: white; font-weight: 600;"
    for i, h in enumerate(headers):
        lines.append(f"<th style='{header_style}'>{h}</th>")
    lines.append("</tr></thead><tbody>")
    for row in rows:
        lines.append("<tr>")
        lines.append(f"<td style='border: 1px solid #ccc; padding: 8px; font-weight: 500;'>{row[0]}</td>")
        for val in row[1:]:
            if val and val in BADGE_CSS:
                fg, bg = BADGE_CSS[val]
                lines.append(
                    f"<td style='border: 1px solid #ccc; padding: 8px;'>"
                    f"<span style='color: {fg}; background: {bg}; padding: 4px 10px; border-radius: 9999px; font-weight: 600;'>{val}</span></td>"
                )
            else:
                lines.append(f"<td style='border: 1px solid #ccc; padding: 8px;'>—</td>")
        lines.append("</tr>")
    lines.append("</tbody></table>")
    return "\n".join(lines)


def format_scores_json(
    round1_scores: list[ScoreRow],
    final_scores: list[ScoreRow],
    community_scores: list[dict] | None = None,
) -> dict[str, Any]:
    """Produce a JSON-serializable summary of scores."""
    out: dict[str, Any] = {
        "round1": round1_scores,
        "final": final_scores,
    }
    if community_scores is not None and community_scores:
        out["community_scores"] = community_scores
    return out


def format_report_md(
    round1_scores: list[ScoreRow],
    final_scores: list[ScoreRow],
    synthesis: str,
    deliberation_preview: str = "",
) -> str:
    """Produce the main report in Markdown. Deliberation excerpt is not included (use Full deliberation log for that)."""
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
