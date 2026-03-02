"""Pytest fixtures for HPIC committee tests."""

import pytest

SAMPLE_PROPOSAL_MD = """# Sample Proposal

This is a test proposal for Chicago stadium policy.

## Summary

We propose a mixed-use development with community benefits.
"""


@pytest.fixture
def sample_proposal_md(tmp_path):
    """A temporary .md proposal file."""
    p = tmp_path / "draft.md"
    p.write_text(SAMPLE_PROPOSAL_MD, encoding="utf-8")
    return p


@pytest.fixture
def proposals_dir(tmp_path):
    """A temporary proposals directory containing a sample .md."""
    (tmp_path / "draft.md").write_text(SAMPLE_PROPOSAL_MD, encoding="utf-8")
    return tmp_path
