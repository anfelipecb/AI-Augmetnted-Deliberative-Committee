"""Tests for proposal_loader (doc read: .md and .pdf)."""

import io

import pytest
from pypdf import PdfWriter

from src.proposal_loader import ProposalLoadError, load_proposal, load_proposal_from_bytes


def test_load_proposal_md(sample_proposal_md, proposals_dir):
    base = proposals_dir
    text = load_proposal(sample_proposal_md, base_dir=base)
    assert "Sample Proposal" in text
    assert "Chicago stadium" in text


def test_load_proposal_relative_path(proposals_dir):
    text = load_proposal("draft.md", base_dir=proposals_dir)
    assert "Sample Proposal" in text


def test_load_proposal_file_not_found(proposals_dir):
    with pytest.raises(ProposalLoadError, match="not found"):
        load_proposal(proposals_dir / "nonexistent.md", base_dir=proposals_dir)


def test_load_proposal_unsupported_extension(proposals_dir):
    (proposals_dir / "foo.txt").write_text("hi")
    with pytest.raises(ProposalLoadError, match="Only .md and .pdf"):
        load_proposal(proposals_dir / "foo.txt", base_dir=proposals_dir)


def test_load_proposal_path_traversal_rejected(tmp_path):
    # Base dir and a file outside it (sibling directory)
    base = tmp_path / "base"
    base.mkdir()
    (base / "draft.md").write_text("in base", encoding="utf-8")
    outside = tmp_path / "other"
    outside.mkdir()
    (outside / "doc.md").write_text("# Outside", encoding="utf-8")
    with pytest.raises(ProposalLoadError, match="must be under"):
        load_proposal(outside / "doc.md", base_dir=base)


def test_load_proposal_from_bytes_md():
    content = b"# Test\n\nBody text."
    text = load_proposal_from_bytes(content, "test.md")
    assert "Test" in text
    assert "Body text" in text


def test_load_proposal_from_bytes_bad_extension():
    with pytest.raises(ProposalLoadError, match="Only .md and .pdf"):
        load_proposal_from_bytes(b"x", "file.txt")


def test_load_proposal_from_bytes_pdf():
    """Doc read: PDF bytes are extracted to text (minimal PDF may yield empty text)."""
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    buf = io.BytesIO()
    writer.write(buf)
    pdf_bytes = buf.getvalue()
    text = load_proposal_from_bytes(pdf_bytes, "proposal.pdf")
    assert isinstance(text, str)
