"""Claude agent invocation: system prompt from persona + API call."""

import logging

from anthropic import Anthropic
from anthropic import AuthenticationError, NotFoundError

from src.config import (
    ANTHROPIC_API_KEY,
    DELIBERATION_MODEL,
    SUMMARIZER_MODEL,
)
from src.criteria import CRITERIA_6, CRITERIA_LABELS, CRITERIA_SUB

logger = logging.getLogger(__name__)

# JSON schema for jury scoring. Enforced via Anthropic structured outputs.
_CRITERIA_PROPERTIES = {
    k: {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]} for k in CRITERIA_6
}
_CRITERIA_SCHEMA = {
    "type": "object",
    "properties": _CRITERIA_PROPERTIES,
    "required": list(CRITERIA_6),
    "additionalProperties": False,
}

JURY_ROUND1_SCHEMA = {
    "type": "object",
    "properties": {
        "impact": {"type": "integer", "minimum": 1, "maximum": 10},
        "fiscal": {"type": "integer", "minimum": 1, "maximum": 10},
        "sustainability": {"type": "integer", "minimum": 1, "maximum": 10},
        "justification": {"type": "string"},
        "criteria": _CRITERIA_SCHEMA,
    },
    "required": ["impact", "fiscal", "sustainability", "justification", "criteria"],
    "additionalProperties": False,
}

JURY_ROUND3_SCHEMA = {
    "type": "object",
    "properties": {
        "impact": {"type": "integer", "minimum": 1, "maximum": 10},
        "fiscal": {"type": "integer", "minimum": 1, "maximum": 10},
        "sustainability": {"type": "integer", "minimum": 1, "maximum": 10},
        "verdict": {"type": "string"},
        "criteria": _CRITERIA_SCHEMA,
    },
    "required": ["impact", "fiscal", "sustainability", "verdict", "criteria"],
    "additionalProperties": False,
}

CRITERIA_TEXT = """
Evaluate the proposal on these three criteria (score each 1-10 with justification):

- **Impact**: Does it benefit a cross-section of Chicagoans? Is it accessible and affordable? Does it offer opportunities for local engagement, youth activities, or partnerships?
- **Fiscal Responsibility**: Does it generate new tax revenues and job creation? Are public subsidies and/or debt justified? Are there accountability measures and long-term fiscal sustainability?
- **Sustainability**: Is the design sustainable and adaptive? Does it support a mix of uses beyond sports? Does it integrate environmental best practices and evolve with trends?
"""

CRITERIA_6_TEXT = """
Additionally assess the proposal on these six criteria, each as LOW, MEDIUM, or HIGH:

- **Fiscal Impact** ({sub_fiscal_impact})
- **Equity & Access** ({sub_equity_access})
- **Political Feasibility** ({sub_political_feasibility})
- **Sustainability** ({sub_sustainability})
- **Team Retention** ({sub_team_retention})
- **Accountability** ({sub_accountability})

When asked for structured scores, respond with valid JSON including a "criteria" object with keys: fiscal_impact, equity_access, political_feasibility, sustainability, team_retention, accountability; values must be exactly one of LOW, MEDIUM, HIGH.
""".format(
    sub_fiscal_impact=CRITERIA_SUB["fiscal_impact"],
    sub_equity_access=CRITERIA_SUB["equity_access"],
    sub_political_feasibility=CRITERIA_SUB["political_feasibility"],
    sub_sustainability=CRITERIA_SUB["sustainability"],
    sub_team_retention=CRITERIA_SUB["team_retention"],
    sub_accountability=CRITERIA_SUB["accountability"],
)


SUMMARIZER_SYSTEM = """You are an expert analyst. Produce a highly detailed summary of the Chicago stadium/urban policy proposal you receive.

Capture: key content, narrative, data from tables, figures, projections, and any quantitative or qualitative claims. The summary will be used by an expert panel to evaluate the proposal on Impact, Fiscal Responsibility, and Sustainability. Be thorough and preserve important details."""


def summarize_proposal(proposal_text: str) -> str:
    """
    Use Opus to produce a highly detailed summary of the proposal.
    The summary is persisted and used by all deliberation agents (Haiku).
    """
    if not ANTHROPIC_API_KEY:
        raise RuntimeError(
            "API configuration is missing. Set ANTHROPIC_API_KEY in `.env`."
        )
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    text = proposal_text[:200_000]  # Stay within context
    try:
        response = client.messages.create(
            model=SUMMARIZER_MODEL,
            max_tokens=8192,
            system=SUMMARIZER_SYSTEM,
            messages=[{"role": "user", "content": f"Summarize this proposal in detail:\n\n{text}"}],
        )
        return response.content[0].text if response.content else ""
    except Exception as e:
        logger.exception("Summarizer failed: %s", type(e).__name__)
        raise RuntimeError("Could not summarize proposal. Try again.") from e


def build_jury_system_prompt(persona_content: str) -> str:
    return f"""You are an expert panelist evaluating a Chicago stadium/urban policy proposal. Stay in character.

{persona_content}

You are evaluating the proposal against Chicago's stated criteria. {CRITERIA_TEXT}
{CRITERIA_6_TEXT}

Respond in character with your expertise and key questions in mind. When asked for scores, you must respond with only a single valid JSON object—no other text, markdown, or commentary before or after. The JSON must include "impact", "fiscal", "sustainability" (1-10), "justification" or "verdict", and "criteria" (object with fiscal_impact, equity_access, political_feasibility, sustainability, team_retention, accountability — each exactly LOW, MEDIUM, or HIGH)."""


def build_community_system_prompt(persona_content: str) -> str:
    return f"""You are a community stakeholder reacting to a Chicago stadium/urban policy proposal. Stay in character.

{persona_content}
{CRITERIA_6_TEXT}

React from lived experience: What changes for you? What worries you? What excites you? Be concrete. When asked for structured output, respond with valid JSON only: "reactions" (string with your narrative) and "criteria" (object with fiscal_impact, equity_access, political_feasibility, sustainability, team_retention, accountability — each LOW, MEDIUM, or HIGH)."""


def invoke_agent(
    agent_id: str,
    system_prompt: str,
    user_message: str,
    conversation_history: list[dict[str, str]] | None = None,
    model: str | None = None,
    output_schema: dict | None = None,
    max_tokens: int | None = None,
) -> str:
    """
    Call Claude with the given system prompt and user message.

    Args:
        agent_id: For logging only (not sent to API).
        system_prompt: Full system prompt including persona.
        user_message: This turn's user message.
        conversation_history: Optional prior messages [{"role": "user"|"assistant", "content": "..."}].
        model: Override model (default: DELIBERATION_MODEL).
        output_schema: Optional JSON schema to enforce structured output (Anthropic structured outputs).

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
    model_to_use = model or DELIBERATION_MODEL
    kwargs: dict = {
        "model": model_to_use,
        "max_tokens": max_tokens or 4096,
        "system": system_prompt,
        "messages": messages,
    }
    if output_schema:
        kwargs["output_config"] = {
            "format": {
                "type": "json_schema",
                "schema": output_schema,
            }
        }
    try:
        response = client.messages.create(**kwargs)
        return response.content[0].text if response.content else ""
    except NotFoundError as e:
        logger.error(
            "API call failed: NotFoundError (404). agent_id=%s model=%s",
            agent_id,
            model_to_use,
        )
        raise RuntimeError(
            "API returned 404. Check DELIBERATION_MODEL is valid for your account."
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
            model_to_use,
        )
        raise RuntimeError(
            "Evaluation could not be completed. Try again or check your proposal."
        ) from e
