"""Load agent persona .md files into structured data for system prompts."""

from pathlib import Path

from src.config import AGENTS_COMMUNITY_DIR, AGENTS_JURY_DIR

PersonaDict = dict[str, str]


def _persona_id_from_path(p: Path) -> str:
    return p.stem.lower().replace(" ", "_")


def _name_from_content(content: str) -> str:
    """First # heading is the display name."""
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("# ") and len(line) > 2:
            return line[2:].strip()
    return "Unknown"


# Four "quick" jury IDs: fiscal, political, community/equity, urban economics
QUICK_JURY_IDS = ("sarah_chen", "patricia_reilly", "marcus_thompson", "elena_vasquez")


def load_jury_personas(quick: bool = False) -> list[PersonaDict]:
    """Load jury agent .md files from agents/jury/. If quick=True, only the 4 curated experts."""
    all_personas = _load_personas_from_dir(AGENTS_JURY_DIR)
    if not quick:
        return all_personas
    ids_set = set(QUICK_JURY_IDS)
    return [p for p in all_personas if p["id"] in ids_set]


def load_community_personas() -> list[PersonaDict]:
    """Load all community agent .md files from agents/community/."""
    return _load_personas_from_dir(AGENTS_COMMUNITY_DIR)


def _load_personas_from_dir(dir_path: Path) -> list[PersonaDict]:
    if not dir_path.is_dir():
        return []
    out: list[PersonaDict] = []
    for p in sorted(dir_path.iterdir()):
        if p.suffix.lower() != ".md":
            continue
        content = p.read_text(encoding="utf-8", errors="replace")
        out.append(
            {
                "id": _persona_id_from_path(p),
                "name": _name_from_content(content),
                "content": content,
            }
        )
    return out
