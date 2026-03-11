---
title: "Advanced Machine Learning - Final Project"
author: "Andres F. Camacho"
date: "March 10, 2026"
output: pdf_document
geometry: margin=1in
fontsize: 11pt
colorlinks: true
linkcolor: blue
urlcolor: blue
citecolor: blue
hyperrefoptions:
  - colorlinks
  - linkcolor=blue
  - urlcolor=blue
  - citecolor=blue
header-includes:
  - \usepackage{float}
  - \floatplacement{figure}{H}
---


## Introduction

Last Saturday, March 7th, I participated with my team in the Harris Public Policy Challenge (HPIC) on Chicago stadium and urban policy. The question I faced was simple but daunting: how do you evaluate a policy proposal when it’s impossible to get everyone in Chicago in the same room? The city has 2.7 million residents, each with their own perspective on stadiums, subsidies, displacement, and civic identity. Ignoring those voices isn’t an option, but convening them all isn’t realistic either.

That’s where the idea came from. After taking the course *AI Agents for Social Science* and *Advanced Machine Learning for Public Policy*, I proposed using AI agents to simulate a deliberative committee: expert panelists and community stakeholders who could evaluate proposals together, push back on each other, and produce a structured assessment. The goal wasn’t to replace human judgment but to *inform* it by surfacing tensions and tradeoffs that a single analyst might miss, and to give voice to perspectives that are often absent from policy debates. I ran my team's proposal through the system; it didn't score high on all components, but the deliberation surfaced gaps and tensions that helped us improve it before submission.

This report describes what I built, why, and how it works. Here’s the project in practice: you can explore the **live app** and the **code** yourself.

**Try it:** [Streamlit Dashboard](https://ai-augmetnted-deliberative-committee-hpic.streamlit.app) · [GitHub Repository](https://github.com/anfelipecb/AI-Augmetnted-Deliberative-Committee)

## The Problem

The Harris challenge asks: *What should be the City of Chicago’s policy toward supporting professional sports teams and facilities?* Stadium deals are messy. They involve fiscal trade-offs (who pays, who benefits?), equity concerns (who gets displaced, who gets jobs?), and political feasibility (will City Council pass it?). Evaluating proposals well means hearing from fiscal experts, community organizers, urban economists, and residents who actually live near these projects. But convening that panel is costly and slow. In practice, a lot of voices never get heard.

I wanted to see if AI agents could help. Not to make the decision, but to *inform* it by simulating a diverse panel that deliberates, disagrees, and produces a structured evaluation. The idea: rather than ignoring 2.7 million Chicagoans, I'd build agents that represent different perspectives and let them debate.

## Literature Motivation and Recent Developments

This project is grounded in recent advancements in multi-agent LLM systems, synthetic sampling, and AI ethics. The design of the deliberative committee draws heavily from the following literature:

**Societies of Thought and Deliberation.** The core mechanism of the committee is motivated by Kim, Evans, et al. (2026), who demonstrate that reasoning models generate "societies of thought," simulating multi-agent-like dialogue to diversify perspectives, debate among cognitive personas, and reconcile conflicting views. By structuring the jury to deliberate across three rounds, this project harnesses these emergent dynamics to surface tradeoffs that a single evaluator might miss. Furthermore, Lai et al. (2025) find that "biased" or opinionated AI agents improve human decision-making by acting as strong heuristics; similarly, assigning jury members explicit expert lenses (e.g., fiscal constraint, urban economics) sharpens the debate and provides clear, adversarial evaluation.

**Digital Doubles and Synthetic Subjects.** To capture community impact, the pipeline simulates stakeholders using real demographic data. This approach is motivated by Broska et al. (2025), who propose the "Mixed Subjects Design," treating LLMs as "Silicon Subjects." This framework validates using digital doubles to model population responses when recruiting specific demographics is too costly. I sampled from ACS 2022 5-year estimates (income, housing, commute, occupation tables) to ground each community profile in real demographic data for their neighborhood and sector. The eight community stakeholders (a Pilsen renter, an Austin business owner, a Bronzeville homeowner, and others) are digital doubles across four geographic zones (South Side, West Side, North Side, Loop-adjacent). Same proposal, same personas yields reproducible evaluations; different proposals or modes let me explore how perspectives shift.

**Persona Control and Ethics.** The distinct personalities and evaluation criteria of the committee members are theoretically supported by Chen et al. (2025), who show that "persona vectors" can reliably control character traits and analytical focuses in LLMs. Finally, deploying such a system for urban policy requires careful consideration of AI agency. Consistent with Gabriel et al. (2025), who call for a new ethics for a world of AI agents, this project emphasizes transparency: deliberation logs are fully traceable, and the final synthesis preserves both consensus and dissenting views, ensuring human oversight over the policy evaluation process.

## How It Works

I use a two-tier setup: Opus for document understanding (summarizes the proposal), Haiku for deliberation (cheaper, faster). Three modes: *jury only (quick)* with four experts, *jury only (full)* with seven, or *full* with community stakeholders first, then the jury.

Three rounds. Round 1: each jury member scores Impact, Fiscal Responsibility, Sustainability (1–10) plus six criteria (LOW/MEDIUM/HIGH). Round 2: they see each other’s scores and respond in character: agreement, pushback, emphasis. Round 3: final scores, two-sentence verdicts, and a synthesis report.

**Evaluation criteria.** The three main scores (Impact, Fiscal Responsibility, Sustainability) and the six sub-criteria come from the HPIC challenge's stated evaluation framework. The challenge asks whether proposals benefit a cross-section of Chicagoans (Impact), generate tax revenues and justify subsidies (Fiscal Responsibility), and support sustainable, adaptive design (Sustainability). I operationalized these into six criteria that jurors rate as LOW, MEDIUM, or HIGH: **Fiscal Impact** (revenue, debt, public cost), **Equity & Access** (community benefit, affordability), **Political Feasibility** (legal, legislative, stakeholder support), **Sustainability** (long-term adaptability, risk), **Team Retention** (likelihood of keeping major league franchises), and **Accountability** (oversight, enforceability). These reflect the policy considerations the challenge highlighted (public funding, displacement, community engagement, and long-term fiscal responsibility), so the deliberation aligns with what the City of Chicago would evaluate.

## What I Built

Full pipeline (summarizer, jury rounds, community phase, synthesis), seven jury personas and eight community personas, a Streamlit app, CLI, and Docker. I also added an evaluation suite that validates outputs (score ranges, criteria, verdict consistency) and a demo notebook with alignment tests. Unit tests, integration test, and evaluation tests round it out.

## Code Repository and Key Components

The project is organized as follows. Personas live in `agents/jury/` and `agents/community/` (markdown files). The orchestration logic is in `src/simulate.py`; agent invocation and prompt building in `src/agents.py`; persona loading in `src/personas.py`; criteria definitions in `src/criteria.py`; and output formatting in `src/output.py`. The evaluation suite is in `src/evaluation.py`. The Streamlit app is `app.py`.

**Main simulation flow.** The `run()` function in `src/simulate.py` orchestrates the full pipeline: summarizer (Opus), optional community phase, then jury rounds 1–3 and synthesis. Each round writes outputs to the run directory.

```python
# src/simulate.py: main run() flow (simplified)
def run(proposal_text: str, mode: str = "jury", output_dir: Path | None = None) -> Path:
    proposal_summary = _run_summarizer(proposal_text, out)
    jury_personas = load_jury_personas(quick=(mode == "jury_quick"))
    community_summary = ""
    if mode == "full":
        community_personas = load_community_personas()
        community_summary, _ = _run_community_phase(proposal_summary, community_personas)
    round1_scores, log_entries = _run_round1_jury(
        proposal_summary, community_summary, jury_personas
    )
    log_entries = _run_round2_deliberation(jury_personas, round1_scores, log_entries)
    final_scores, synthesis, log_entries = _run_round3_final(jury_personas, log_entries, round1_scores)
    # ... write report.md, scores.json, deliberation_log.md
```

**How prompts and context get passed.** Each agent receives a *system prompt* (persona + fixed criteria) and a *user message* (the proposal + context for that round). The system prompt is built by concatenating the persona markdown with the evaluation criteria:

```python
# src/agents.py: system prompt from persona + criteria
def build_jury_system_prompt(persona_content: str) -> str:
    return f"""You are an expert panelist evaluating a Chicago stadium/urban policy proposal. Stay in character.

{persona_content}

You are evaluating the proposal against Chicago's stated criteria. {CRITERIA_TEXT}
{CRITERIA_6_TEXT}

Respond in character... When asked for scores, you must respond with only a single valid JSON object..."""
```

`CRITERIA_TEXT` injects the three main scores (Impact, Fiscal Responsibility, Sustainability) with 1–10 scale and guidance; `CRITERIA_6_TEXT` injects the six sub-criteria (LOW/MEDIUM/HIGH) with sub-definitions from `src/criteria.py`.

**Round 1 user prompt.** The user message includes the proposal summary (or community summary in full mode) and instructions for JSON output. Each jury persona gets the same user message but a different system prompt (their persona):

```python
# src/simulate.py: Round 1 prompt construction
prompt = f"""Below is a detailed summary of a Chicago stadium/urban policy proposal to evaluate. {intro}

Proposal summary:
---
{proposal_text[:120000]}
---

{community_block}
---

Score the proposal. You must respond with only a single JSON object...
"""
# For each persona:
sys_prompt = build_jury_system_prompt(persona["content"])
response = invoke_agent(persona["id"], sys_prompt, prompt, None)
```

**Agent invocation.** The `invoke_agent` function sends the system prompt and messages to the Anthropic API. For Round 2 and 3, `conversation_history` can include prior rounds so the agent sees the deliberation so far. For Round 1 (scoring), the API uses Anthropic structured outputs: a JSON schema is passed via `output_config.format`, and the model is constrained to return valid JSON. Round 3 uses prompt-only JSON; when the model returns prose (e.g. after seeing the long deliberation transcript), scores fall back to Round 1.

```python
# src/agents.py: API call (with optional output_schema for scoring rounds)
def invoke_agent(agent_id, system_prompt, user_message, conversation_history=None, model=None, output_schema=None):
    kwargs = {"model": model or DELIBERATION_MODEL, "max_tokens": 4096, "system": system_prompt, "messages": messages}
    if output_schema:
        kwargs["output_config"] = {"format": {"type": "json_schema", "schema": output_schema}}
    response = client.messages.create(**kwargs)
    return response.content[0].text
```

So the flow is: persona content becomes the system prompt; the proposal summary plus round-specific context becomes the user message; prior rounds (when applicable) are passed as conversation_history. For scoring rounds, the schema guarantees valid JSON; the API returns the agent's text, which is parsed for scores and criteria.

## Verification

The evaluation suite (`uv run python -m src.evaluation --run-dir outputs/<run_id>`) checks that scores are valid, criteria are LOW/MEDIUM/HIGH, and verdicts align with scores. Similar in spirit to the portfolio homework's backtesting, I validate that the pipeline produces sensible, consistent outputs.

**HPIC Demo Notebook.** I included `docs/notebooks/hpic_demo.ipynb` to showcase the concept, allowing readers and the professor to explore the project without running the full app. The notebook walks through: (1) introduction and main components (summarization, deliberation, personas, outputs); (2) simulation flow and the four quick jury profiles; (3) a sample run on `docs/notebooks/sample_proposal.md` (runs the full pipeline; requires `ANTHROPIC_API_KEY` in `.env`; falls back to embedded data if the API fails); (4) visualizations (bar chart of scores by agent, criteria heatmap); (5) alignment tests (persona differentiation, lens alignment; e.g., does Sarah Chen weight fiscal highly? does Marcus Thompson weight impact and equity_access highly?); and (6) integration with the evaluation suite. The sample proposal is committed to the repo, so the notebook is reproducible without prior runs in `outputs/`.

## Effort

I have been working on this project for the last couple of months, investigating the literature on AI agents and digital doubles, reading papers from the AI Agents for Social Science course, and trying different combinations of models, prompts, and persona designs. The work spans the full pipeline (summarization with Opus, deliberation with Haiku), seven jury personas and eight community stakeholders grounded in ACS 2022 data, the Streamlit app and CLI, Docker deployment, the evaluation suite, and the demo notebook. I estimate roughly 50–70 hours total: research and design (~15 h), persona development and ACS data integration (~12 h), pipeline implementation and debugging (~15 h), UI and deployment (~8 h), evaluation suite and documentation (~10 h). The HPIC challenge on March 7th was a milestone; the Advanced ML final project additions (evaluation suite, demo notebook, report) came afterward.

## Limitations

No formal hallucination detection yet. Persona differentiation is heuristic. The verdict consistency check uses a fixed set of phrases. Future work: claim extraction and grounding against the proposal, better metrics for persona differentiation.

## Conclusion

The HPIC AI-Augmented Deliberative Committee is an application of multi-agent systems to policy deliberation. Digital doubles + societies of thought = a way to surface diverse perspectives when you can’t get 2.7 million people in a room. The project is on GitHub with full docs, a demo notebook, and an evaluation suite. Feel free to run it, fork it, or just explore the live app.

**Links:** [Streamlit Dashboard](https://ai-augmetnted-deliberative-committee-hpic.streamlit.app) · [GitHub](https://github.com/anfelipecb/AI-Augmetnted-Deliberative-Committee)

## Annex: Example Community Stakeholder Profile

Below is one of the eight community stakeholder profiles (digital doubles) used in full mode. Each profile is sampled from ACS 2022 tables (e.g., B19013 income, B25064 rent, B25077 home values, B08303 commute) and stored as a markdown file; the system prompt is built from this content plus fixed criteria. This example (Rosa Delgado, a Pilsen renter) illustrates the structure: personal profile, location and housing, economic profile, community context, and stakeholder perspective, with methodology notes citing the source tables.

```markdown
# Rosa Delgado

## Personal Profile
- Age: 34
- Household composition: Married, 3 children (ages 12, 9, 6)
- Years in Chicago/neighborhood: 16 years (grew up in Little Village, moved to Pilsen at 18)
- Primary language: Spanish (limited English proficiency)

## Location & Housing
- Neighborhood: East Pilsen, near 18th & Morgan
- Housing tenure: Renter
- Monthly rent: $1,350 (up from $950 three years ago)

## Economic Profile
- Occupation: Restaurant server at downtown hotel
- Annual household income: $47,800 (combined with husband's construction work)
- Education: High school diploma
- Commute: 35-40 minutes via Pink Line to Loop

## Community Context
- Neighborhood ties: Shops at Supermercado Monterrey on 18th St, children attend Benito Juárez Community Academy
- Community involvement: Attends community meetings through church (St. Adalbert)

## Stakeholder Perspective
- Primary concerns: Rent increases and displacement; transit reliability; affordable family activities; access to information in Spanish
- Priorities: Affordable housing protections; living-wage jobs accessible by transit; family-friendly public spaces
- Perspective on development: Skeptical of development without renter protections; worries about gentrification; needs concrete affordability guarantees

*Methodology: Income and rent from ACS 2022 Tables B19013, B25064 (Community Area 31 - Lower West Side/Pilsen)*
```

## References


- Kim, J., Lai, S., Scherrer, N., Agüera y Arcas, B., & Evans, J. (2026). Reasoning Models Generate Societies of Thought. arXiv:2601.10825. https://arxiv.org/html/2601.10825v1
- Broska et al. (2025). The Mixed Subjects Design: Treating Large Language Models as Potentially Informative Observations.
- Chen et al. (2025). Persona Vectors: Monitoring and Controlling Character Traits in Language Models.
- Lai et al. (2025). Biased AI improves human decision-making but reduces trust.
- Gabriel et al. (2025). We need a new ethics for a world of AI agents.
- U.S. Census Bureau. American Community Survey 2022 5-year estimates. https://data.census.gov
- City of Chicago Data Portal. https://data.cityofchicago.org
- Anthropic API. https://docs.anthropic.com
