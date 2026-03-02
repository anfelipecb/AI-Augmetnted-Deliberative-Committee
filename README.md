# HPIC AI-Augmented Deliberative Committee

Evaluate Chicago stadium and urban policy proposals using an AI panel of expert and community perspectives.

## Quick start (Docker)

```bash
cp .env.example .env   # Add your ANTHROPIC_API_KEY
docker compose up
```

Open http://localhost:8501. Upload a proposal or choose one from the `proposals/` folder, select mode, and run deliberation.

## Local development (UV)

```bash
uv sync
cp .env.example .env   # Add your ANTHROPIC_API_KEY
uv run streamlit run app.py
```

CLI:

```bash
uv run python -m src.simulate --proposal proposals/draft.md [--mode jury|jury_quick|full] [--output-dir dir]
```

## Committee architecture and deliberation process

**Modes**

- **Jury only (4 experts — quick):** Four curated panelists (fiscal, political, community/equity, urban economics). Fastest option.
- **Jury only (7 experts):** Full expert panel from `agents/jury/`.
- **Full (community + jury):** Community stakeholders react first; their summary is then given to the jury.

**Rounds**

1. **Round 1 — Individual scoring**  
   Each jury member scores the proposal on Impact, Fiscal Responsibility, and Sustainability (1–10) with a short justification. Optionally informed by a community reactions summary (full mode).

2. **Round 2 — Deliberation**  
   Each panelist sees Round 1 scores and justifications and responds in character: agreement, disagreement, pushback, or emphasis.

3. **Round 3 — Final vote**  
   Each panelist gives final scores and a two-sentence verdict. A final **synthesis** call produces a short consensus report (strengths, weaknesses, conditions for recommendation).

In the app you can run **one round at a time** (see results after each) or **Run all rounds** in one go. Outputs (scores, deliberation log, report) are written to `outputs/<run_id>/`.

**Proposal length**

The app loads the full proposal (PDF or .md) up to 500,000 characters. When calling the API, the **jury sees the first 120,000 characters** of the proposal in Round 1; the **community phase** uses the first 60,000 characters. Very long documents are therefore evaluated on a leading excerpt; the rest is not sent to the model.

## Environment

- `ANTHROPIC_API_KEY` — from [Anthropic Console](https://console.anthropic.com/). Required.
- `CLAUDE_MODEL` (optional) — default `claude-opus-4-6`.

Never commit `.env`. Secrets are never sent to the browser or shown in the UI.

**Checking errors when something fails**

- **Docker:** `docker compose logs app` (or `docker compose logs -f app` to follow). API errors are logged to stderr.
- **Per-run log file:** After each run, the app writes `outputs/<run_id>/run.log` with API and run errors (e.g. 404, 401). With Docker, `outputs/` is bind-mounted, so check `./outputs/` on your host and open the latest run folder's `run.log`.

## Security

- API key is loaded only server-side; not in logs or error messages.
- Proposal uploads: only `.md` and `.pdf`, max 20 MB; saved to temp paths.
- Outputs are written only to `outputs/<run_id>/`.

## Adding or editing personas

Edit or add `.md` files under `agents/jury/` and `agents/community/`. Use the existing files as templates (Role, Background, Evaluation lens, Personality, Key questions or Key concerns).

## Lint and test

Install dev dependencies first: `uv sync --extra dev`

```bash
uv run ruff check .
uv run ruff format .
uv run pytest tests/ -v
```

To verify the API key and a simple prompt work (optional integration test):

```bash
uv run pytest tests/test_agents.py -m integration -v
```

Skipped if `ANTHROPIC_API_KEY` is unset or invalid.
