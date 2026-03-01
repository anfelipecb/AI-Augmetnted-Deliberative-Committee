# AI-Augmented Deliberative Committee for Chicago Stadium Policy

## The Problem

Chicago's decisions about professional sports facilities — public subsidies, stadium locations, community impact agreements — are made through processes that structurally underrepresent the populations most affected. Public comment periods are limited, dominated by organized interests, and occur late in the decision cycle. The people who live near proposed stadiums, who ride the CTA, who rent in gentrifying corridors, rarely have proportional voice.

Meanwhile, the evaluation criteria that matter — fiscal responsibility, community impact, sustainability — require expertise that no single stakeholder group holds entirely.

## The Proposal

We propose an **AI-Augmented Deliberative Committee**: a system of LLM-based agents, each grounded in a specific stakeholder perspective or domain expertise, that can evaluate any stadium policy option against Chicago's stated criteria. The system operates in two layers:

### Layer 1: Expert Jury Panel

Seven domain-expert agents that evaluate proposals against the HPIC criteria (Impact, Fiscal Responsibility, Sustainability):

| Agent | Role | Evaluation Focus |
|-------|------|-----------------|
| **Dr. Elena Vasquez** | Urban Economist | Economic impact analysis, displacement effects, cost-benefit rigor |
| **Marcus Thompson** | Community Organizer & Equity Advocate | Neighborhood impact, accessibility, anti-displacement, community benefits |
| **Dr. Sarah Chen** | Public Finance Expert (Mansueto affiliate) | Municipal debt, deal structure, accountability mechanisms, taxpayer risk |
| **James Okafor, AIA** | Sustainable Urban Designer | Climate resilience, mixed-use potential, transit integration, adaptive design |
| **Ald. Patricia Reilly (ret.)** | Former Alderperson & Governance Expert | Political feasibility, City Council dynamics, implementation realism |
| **Dr. Kevin Whitfield** | Sports Industry Analyst | Team leverage, comparable deals, league economics, relocation dynamics |
| **Dr. Amara Osei** | Data Scientist (Mansueto Institute) | Empirical rigor, causal inference, spatial analysis, evidence quality |

### Layer 2: Community Stakeholder Voices

Agents representing populations directly affected by stadium decisions, calibrated from census data, community surveys, and neighborhood profiles:

| Agent | Represents | Key Concerns |
|-------|-----------|-------------|
| **Rosa Delgado** | Pilsen renter, service worker | Rent increases, displacement, transit access to jobs, affordable tickets |
| **David Washington** | Bronzeville homeowner, retired CPS teacher | Property values, neighborhood character, youth programming, legacy |
| **Mei-Lin Park** | Chinatown small business owner | Foot traffic, parking, construction disruption, local hiring |
| **James Kowalski** | Bridgeport tradesman, Bears season ticket holder | Construction jobs, game-day experience, parking, neighborhood pride |
| **Aisha Johnson** | South Shore single mother, CTA commuter | Transit reliability, public safety, childcare access, public spending priorities |
| **Tom Brennan** | South Loop condo owner, remote tech worker | Noise, property values, neighborhood density, event-day disruption |

### How It Works

**Phase 1 — Stakeholder Reaction**
Each community agent reads a proposed policy option and responds from lived experience: What changes for them? What worries them? What excites them? This surfaces ground-level concerns that policy briefs miss.

**Phase 2 — Expert Evaluation**
Each jury agent scores the proposal on three dimensions (1-10):
- **Impact**: Does it benefit a cross-section of Chicagoans? Is it accessible and affordable?
- **Fiscal Responsibility**: Does it generate net revenue? Are subsidies justified? Are there accountability mechanisms?
- **Sustainability**: Is the design adaptive? Environmentally sound? Useful beyond game days?

Each score includes written justification citing specific proposal elements.

**Phase 3 — Deliberation**
Agents engage in structured discussion. Expert agents respond to community concerns. Community agents react to expert assessments. Key dynamics:
- The economist and community organizer may agree stadiums are bad investments but for different reasons (efficiency vs. equity)
- The designer will push for 365-day-use thinking
- The politician will reality-check what City Council will actually pass
- The data scientist will probe whether claims are backed by evidence

**Phase 4 — Synthesis**
Final scores, a consensus report identifying strengths, weaknesses, and conditions under which the proposal should proceed. Dissenting opinions are preserved, not averaged away.

## Why This Approach

1. **Scalable representation**: You can't put 2.7 million Chicagoans in a room. You can model their heterogeneous concerns and ensure no perspective is structurally excluded from evaluation.

2. **Repeatable and comparable**: Run the same panel against multiple policy options (full public subsidy, no subsidy, hybrid models, different locations) and compare results systematically.

3. **Transparent reasoning**: Every score comes with written justification. Unlike a closed-door negotiation, the reasoning is auditable.

4. **Addresses the core critique**: The general consensus in stadium economics is that public subsidies are questionable investments. But cities keep making them. The problem isn't information — it's process. This tool ensures the process structurally includes the voices that usually get excluded.

5. **Adaptable**: The same framework can evaluate other major urban infrastructure decisions beyond stadiums — transit expansions, housing developments, school closings.

## Limitations & Honest Caveats

- **Agents are not people.** They are models calibrated on demographic and attitudinal data. They approximate, not replace, genuine community input.
- **Garbage in, garbage out.** If the underlying persona calibration is biased or shallow, the outputs will be too.
- **Not a substitute for democracy.** This is a decision-support tool, not a decision-making tool. It complements, not replaces, public hearings and elected governance.
- **Model dependency.** Outputs may vary across LLM providers and versions. Results should be interpreted as structured deliberation, not ground truth.

## Implementation Status

### Current Progress
- [x] Agent persona definitions (7 jury + 6 community stakeholders)
- [x] Evaluation criteria mapped to HPIC rubric
- [x] Deliberation protocol designed (4 phases)
- [ ] Python simulation runner (`src/simulate.py`)
- [ ] Agent system prompts (`src/agents.py`)
- [ ] Output formatting and scoring aggregation
- [ ] Testing against sample policy options

### Technical Stack
- Python 3.11 + Anthropic Claude API
- Structured agent prompts with persona grounding
- Multi-round conversation orchestration
- Markdown output reports

### To Run (once implemented)
```bash
pip install -r requirements.txt
cp .env.example .env  # add your ANTHROPIC_API_KEY
# Place your proposal in proposals/draft.md
python src/simulate.py --mode jury proposals/draft.md
python src/simulate.py --mode stakeholders proposals/draft.md
python src/simulate.py --mode full proposals/draft.md  # both layers
```

## Policy Considerations This Framework Addresses

From the HPIC case brief:
- **Public funding & subsidies** → Evaluated by Chen (finance) and Vasquez (economics)
- **Economic impact uncertainty** → Stress-tested by Osei (data) and Vasquez (economics)
- **Impact and accessibility** → Centered by Thompson (equity) and all community agents
- **Stadium location & urban planning** → Evaluated by Okafor (design) and Reilly (politics)
- **Long-term fiscal responsibility** → Core focus of Chen (finance)
- **Community engagement** → The entire Layer 2 exists for this
- **Environmental sustainability** → Okafor (design) primary, Osei (data) secondary
