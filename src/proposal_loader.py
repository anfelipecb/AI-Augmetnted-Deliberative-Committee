"""Load proposal text from .md or .pdf. Validates path and length."""

import re
from pathlib import Path

from pypdf import PdfReader

from src.config import MAX_PROPOSAL_CHARS

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if not (_PROJECT_ROOT / "pyproject.toml").exists():
    _PROJECT_ROOT = Path.cwd()


def clean_proposal_text(text: str) -> str:
    """
    Normalize and trim proposal text for reliable agent consumption.
    - Remove null bytes and other control characters
    - Normalize line endings to \\n
    - Collapse excessive blank lines (max 2 in a row)
    - Strip leading/trailing whitespace per line and overall
    """
    if not text:
        return ""
    # Drop null bytes and C0/C1 control chars except newline, tab, carriage return
    text = "".join(
        c for c in text
        if c in "\n\r\t" or (ord(c) >= 0x20 and ord(c) != 0x7F and ord(c) < 0x10000)
    )
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse 3+ newlines to at most 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip each line and then strip whole text
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(lines).strip()
    return text


class ProposalLoadError(Exception):
    """Raised when proposal cannot be loaded."""

    pass


def _check_path_safe(base: Path, path: Path) -> None:
    """Ensure path is under base (no path traversal)."""
    try:
        resolved = path.resolve()
        base_resolved = base.resolve()
        resolved.relative_to(base_resolved)
    except ValueError:
        raise ProposalLoadError(f"Path must be under {base}")


def load_proposal(path: str | Path, base_dir: Path | None = None) -> str:
    """
    Load proposal text from a .md or .pdf file.

    Args:
        path: File path (must be under base_dir or cwd).
        base_dir: Allowed base directory for path; default proposals/ under project root.

    Returns:
        Proposal text. Truncated to MAX_PROPOSAL_CHARS if longer.

    Raises:
        ProposalLoadError: If file missing, wrong type, or path not allowed.
    """
    p = Path(path)
    if not p.is_absolute():
        p = (base_dir or (_PROJECT_ROOT / "proposals")).resolve() / p
    if not p.exists():
        raise ProposalLoadError(f"File not found: {p}")
    if p.suffix.lower() not in (".md", ".pdf"):
        raise ProposalLoadError("Only .md and .pdf are supported")
    base = base_dir or _PROJECT_ROOT
    _check_path_safe(base, p)

    if p.suffix.lower() == ".md":
        text = p.read_text(encoding="utf-8", errors="replace")
    else:
        reader = PdfReader(p)
        parts = []
        for page in reader.pages:
            parts.append(page.extract_text() or "")
        text = "\n".join(parts)

    text = clean_proposal_text(text)
    if len(text) > MAX_PROPOSAL_CHARS:
        text = text[:MAX_PROPOSAL_CHARS] + "\n\n[Truncated for length.]"
    return text


def load_proposal_from_bytes(content: bytes, filename: str) -> str:
    """
    Load proposal text from in-memory bytes (e.g. web upload).

    Args:
        content: Raw file bytes.
        filename: Original filename (must end in .md or .pdf).

    Returns:
        Proposal text.

    Raises:
        ProposalLoadError: If type not allowed or PDF parse fails.
    """
    suffix = Path(filename).suffix.lower()
    if suffix not in (".md", ".pdf"):
        raise ProposalLoadError("Only .md and .pdf are allowed")
    if suffix == ".md":
        text = content.decode("utf-8", errors="replace")
    else:
        import io

        reader = PdfReader(io.BytesIO(content))
        parts = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(parts)
    text = clean_proposal_text(text)
    if len(text) > MAX_PROPOSAL_CHARS:
        text = text[:MAX_PROPOSAL_CHARS] + "\n\n[Truncated for length.]"
    return text
