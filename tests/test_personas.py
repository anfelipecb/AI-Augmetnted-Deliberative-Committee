"""Tests for persona loading."""

import pytest

from src.personas import QUICK_JURY_IDS, load_community_personas, load_jury_personas


@pytest.fixture
def agents_dir(tmp_path):
    """Create minimal agents/jury and agents/community with one .md each."""
    jury_dir = tmp_path / "agents" / "jury"
    community_dir = tmp_path / "agents" / "community"
    jury_dir.mkdir(parents=True)
    community_dir.mkdir(parents=True)
    (jury_dir / "test_agent.md").write_text(
        "# Dr. Test Agent\n\n## Role\nEconomist.",
        encoding="utf-8",
    )
    (community_dir / "test_community.md").write_text(
        "# Test Community\n\n## Role\nResident.\n\n## Key concerns\nHousing.",
        encoding="utf-8",
    )
    return tmp_path


def test_load_jury_personas(monkeypatch, agents_dir):
    from src import personas

    monkeypatch.setattr(personas, "AGENTS_JURY_DIR", agents_dir / "agents" / "jury")
    out = load_jury_personas()
    assert len(out) == 1
    assert out[0]["id"] == "test_agent"
    assert "Test Agent" in out[0]["name"]
    assert "Economist" in out[0]["content"]


def test_load_community_personas(monkeypatch, agents_dir):
    from src import personas

    monkeypatch.setattr(personas, "AGENTS_COMMUNITY_DIR", agents_dir / "agents" / "community")
    out = load_community_personas()
    assert len(out) == 1
    assert out[0]["id"] == "test_community"
    assert "Key concerns" in out[0]["content"]


def test_load_jury_personas_real_structure():
    """If agents/jury exists in project, we get at least 1 persona."""
    from src.config import AGENTS_JURY_DIR

    if not AGENTS_JURY_DIR.is_dir():
        pytest.skip("agents/jury not found")
    out = load_jury_personas()
    assert len(out) >= 1
    for p in out:
        assert "id" in p and "name" in p and "content" in p
        assert p["content"].strip().startswith("# ")


def test_load_jury_personas_quick():
    """With quick=True we get only the 4 curated jury IDs (if present)."""
    from src.config import AGENTS_JURY_DIR

    if not AGENTS_JURY_DIR.is_dir():
        pytest.skip("agents/jury not found")
    out = load_jury_personas(quick=True)
    assert len(out) <= 4
    for p in out:
        assert p["id"] in QUICK_JURY_IDS
        assert "id" in p and "name" in p and "content" in p
