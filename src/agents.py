"""Claude agent invocation: system prompt from persona + API call."""

import logging

from anthropic import Anthropic
from anthropic import AuthenticationError, NotFoundError

from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL

logger = logging.getLogger(__name__)

CRITERIA_TEXT = """
Evaluate the proposal on these three criteria (score each 1-10 with justification):

- **Impact**: Does it benefit a cross-section of Chicagoans? Is it accessible and affordable? Does it offer opportunities for local engagement, youth activities, or partnerships?
- **Fiscal Responsibility**: Does it generate new tax revenues and job creation? Are public subsidies and/or debt justified? Are there accountability measures and long-term fiscal sustainability?
- **Sustainability**: Is the design sustainable and adaptive? Does it support a mix of uses beyond sports? Does it integrate environmental best practices and evolve with trends?
"""


def build_jury_system_prompt(persona_content: str) -> str:
    return f"""You are an expert panelist evaluating a Chicago stadium/urban policy proposal. Stay in character.

{persona_content}

You are evaluating the proposal against Chicago's stated criteria. {CRITERIA_TEXT}

Respond in character with your expertise and key questions in mind. Output structured responses when asked for scores (Impact, Fiscal Responsibility, Sustainability, each 1-10 plus short justification)."""


def build_community_system_prompt(persona_content: str) -> str:
    return f"""You are a community stakeholder reacting to a Chicago stadium/urban policy proposal. Stay in character.

{persona_content}

React from lived experience: What changes for you? What worries you? What excites you? Be concrete and specific to your perspective."""


def invoke_agent(
    agent_id: str,
    system_prompt: str,
    user_message: str,
    conversation_history: list[dict[str, str]] | None = None,
) -> str:
    """
    Call Claude with the given system prompt and user message.

    Args:
        agent_id: For logging only (not sent to API).
        system_prompt: Full system prompt including persona.
        user_message: This turn's user message.
        conversation_history: Optional prior messages [{"role": "user"|"assistant", "content": "..."}].

    Returns:
        Assistant message text.

    Raises:
        RuntimeError: If API key is missing or API call fails (message is safe for UI).
    """
    if not ANTHROPIC_API_KEY:
        raise RuntimeError(
            "API configuration is missing. Set ANTHROPIC_API_KEY in `.env`."
        )
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    messages: list[dict[str, str]] = []
    if conversation_history:
        for m in conversation_history:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_message})
    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            system=system_prompt,
            messages=messages,
        )
        return response.content[0].text if response.content else ""
    except NotFoundError as e:
        logger.error(
            "API call failed: NotFoundError (404). agent_id=%s model=%s",
            agent_id,
            CLAUDE_MODEL,
        )
        raise RuntimeError(
            "API returned 404. Check CLAUDE_MODEL is valid for your account."
        ) from e
    except AuthenticationError as e:
        logger.error("API call failed: AuthenticationError (401). agent_id=%s", agent_id)
        raise RuntimeError(
            "API returned 401. Check ANTHROPIC_API_KEY is valid."
        ) from e
    except Exception as e:
        logger.exception(
            "API call failed: %s. agent_id=%s model=%s",
            type(e).__name__,
            agent_id,
            CLAUDE_MODEL,
        )
        raise RuntimeError(
            "Evaluation could not be completed. Try again or check your proposal."
        ) from e
