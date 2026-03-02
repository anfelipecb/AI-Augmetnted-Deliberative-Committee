"""Tests for Claude agent invocation: mocked unit tests and optional API integration."""

import os

import pytest

from src.agents import (
    build_community_system_prompt,
    build_jury_system_prompt,
    invoke_agent,
)


def test_build_jury_system_prompt():
    persona = "# Dr. Test\n\n## Role\nEconomist."
    out = build_jury_system_prompt(persona)
    assert "Dr. Test" in out
    assert "Economist" in out
    assert "Impact" in out
    assert "Fiscal Responsibility" in out
    assert "Sustainability" in out


def test_build_community_system_prompt():
    persona = "# Jane\n\n## Key concerns\nHousing."
    out = build_community_system_prompt(persona)
    assert "Jane" in out
    assert "Housing" in out
    assert "lived experience" in out.lower()


def test_invoke_agent_raises_when_no_api_key(monkeypatch):
    monkeypatch.setattr("src.agents.ANTHROPIC_API_KEY", None)
    with pytest.raises(RuntimeError, match="API configuration is missing"):
        invoke_agent("test", "You are a test.", "Hello", None)


def test_invoke_agent_returns_mocked_response(monkeypatch):
    """Unit test: mock Anthropic so we verify the call path without a real API key."""
    fake_response = type("R", (), {"content": [type("C", (), {"text": "Mocked reply"})()]})()

    def mock_create(*args, **kwargs):
        return fake_response

    mock_client = type("Client", (), {"messages": type("M", (), {"create": mock_create})()})()

    def fake_anthropic(*, api_key):
        return mock_client

    monkeypatch.setattr("src.agents.Anthropic", fake_anthropic)
    monkeypatch.setattr("src.agents.ANTHROPIC_API_KEY", "fake-key-for-test")
    result = invoke_agent("test_id", "System", "User message", None)
    assert result == "Mocked reply"


def test_invoke_agent_with_history_returns_mocked_response(monkeypatch):
    """Unit test: with conversation_history, mock returns the reply."""
    fake_response = type("R", (), {"content": [type("C", (), {"text": "Follow-up"})()]})()

    def mock_create(*args, **kwargs):
        return fake_response

    mock_client = type("Client", (), {"messages": type("M", (), {"create": mock_create})()})()

    def fake_anthropic(*, api_key):
        return mock_client

    monkeypatch.setattr("src.agents.Anthropic", fake_anthropic)
    monkeypatch.setattr("src.agents.ANTHROPIC_API_KEY", "fake-key")
    history = [{"role": "user", "content": "First"}, {"role": "assistant", "content": "Ok"}]
    result = invoke_agent("id", "Sys", "Second", history)
    assert result == "Follow-up"


@pytest.mark.integration
def test_invoke_agent_real_simple_prompt():
    """
    Integration test: one real API call with a simple prompt.
    Run with: uv run pytest tests/test_agents.py -m integration -v
    Skipped if ANTHROPIC_API_KEY is not set or invalid (401).
    """
    from dotenv import load_dotenv

    load_dotenv()
    from src.config import ANTHROPIC_API_KEY

    if not (ANTHROPIC_API_KEY or "").strip():
        pytest.skip(
            "No API configured (set ANTHROPIC_API_KEY); skip integration test"
        )
    try:
        result = invoke_agent(
            "integration_test",
            "You are a helpful assistant. Reply with exactly one word: OK",
            "Reply with only the single word OK.",
            None,
        )
        assert isinstance(result, str)
        assert len(result.strip()) > 0
    except RuntimeError as e:
        cause = getattr(e, "__cause__", None)
        if cause and ("401" in str(cause) or "authentication" in str(cause).lower()):
            pytest.skip("ANTHROPIC_API_KEY invalid or expired; skip API integration test")
        raise
