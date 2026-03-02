"""Load configuration from environment. Never log or re-export secrets."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Project root: directory containing pyproject.toml or, if not found, cwd
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if not (_PROJECT_ROOT / "pyproject.toml").exists():
    _PROJECT_ROOT = Path.cwd()

# Anthropic API (direct)
ANTHROPIC_API_KEY: str | None = (os.environ.get("ANTHROPIC_API_KEY") or "").strip() or None
CLAUDE_MODEL: str = (os.environ.get("CLAUDE_MODEL") or "").strip() or "claude-opus-4-6"

AGENTS_JURY_DIR: Path = _PROJECT_ROOT / "agents" / "jury"
AGENTS_COMMUNITY_DIR: Path = _PROJECT_ROOT / "agents" / "community"
OUTPUTS_DIR: Path = _PROJECT_ROOT / "outputs"

# Proposal text cap (chars) to avoid token abuse
MAX_PROPOSAL_CHARS: int = 500_000

# Allowed proposal extensions
ALLOWED_PROPOSAL_EXTENSIONS: set[str] = {".md", ".pdf"}

# Max upload size (bytes) for web UI
MAX_UPLOAD_BYTES: int = 20 * 1024 * 1024  # 20 MB
