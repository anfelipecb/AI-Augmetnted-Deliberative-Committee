"""
Streamlit UI for the AI-Augmented Deliberative Committee.

Upload or select a proposal, choose mode (jury size, full), run rounds step-by-step
or all at once. View results per round and full report. API key is never exposed.
"""

import json
import logging
from pathlib import Path

import streamlit as st

# So API errors show up in docker compose logs (stderr)
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s [%(name)s] %(message)s",
    force=True,
)

from src.config import ANTHROPIC_API_KEY, MAX_UPLOAD_BYTES
from src.personas import load_jury_personas
from src.proposal_loader import ProposalLoadError, load_proposal, load_proposal_from_bytes
from src.simulate import (
    get_community_summary,
    run,
    run_round1,
    run_round2,
    run_round3,
)

# Allowed MIME / extensions for upload
ALLOWED_EXTENSIONS = {".md", ".pdf"}


def _project_root() -> Path:
    root = Path(__file__).resolve().parent
    if not (root / "pyproject.toml").exists():
        root = Path.cwd()
    return root


def _check_api_configured() -> bool:
    if not ANTHROPIC_API_KEY:
        st.error(
            "API not configured. Set ANTHROPIC_API_KEY in `.env`."
        )
        return False
    return True


def _validate_upload(file) -> None:
    if file.size > MAX_UPLOAD_BYTES:
        raise ProposalLoadError(f"File size must be under {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.")
    ext = Path(file.name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ProposalLoadError("Only .md and .pdf files are allowed.")


# Session state for step-through runs
if "run_in_progress" not in st.session_state:
    st.session_state.run_in_progress = False
if "run_dir" not in st.session_state:
    st.session_state.run_dir = None
if "round1_scores" not in st.session_state:
    st.session_state.round1_scores = None
if "log_entries" not in st.session_state:
    st.session_state.log_entries = None
if "jury_personas" not in st.session_state:
    st.session_state.jury_personas = None
if "community_summary" not in st.session_state:
    st.session_state.community_summary = ""
if "round1_done" not in st.session_state:
    st.session_state.round1_done = False
if "round2_done" not in st.session_state:
    st.session_state.round2_done = False
if "round3_done" not in st.session_state:
    st.session_state.round3_done = False

st.set_page_config(
    page_title="Proposal Evaluation",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Harris School of Public Policy / HPIC Challenge banner
st.markdown(
    """
    <div style="
        background: linear-gradient(90deg, #1a365d 0%, #2c5282 100%);
        color: white;
        padding: 0.85rem 1.25rem;
        margin-bottom: 1.25rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    ">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;">
            <span style="font-size: 1.15rem; font-weight: 700; letter-spacing: 0.02em;">
                Harris School of Public Policy
            </span>
            <span style="
                font-size: 0.9rem;
                font-weight: 600;
                background: rgba(255,255,255,0.2);
                padding: 0.3rem 0.8rem;
                border-radius: 9999px;
            ">
                HPIC Challenge
            </span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.title("AI-Augmented Deliberative Committee")
st.caption(
    "Evaluate Chicago stadium and urban policy proposals using expert and community perspectives."
)

root = _project_root()
proposals_dir = root / "proposals"
outputs_dir = root / "outputs"
outputs_dir.mkdir(parents=True, exist_ok=True)

# Sidebar: proposal source and mode
st.sidebar.header("Input")
proposal_source = st.sidebar.radio(
    "Proposal source",
    ["Upload a file", "Choose from proposals folder"],
    label_visibility="collapsed",
)
proposal_text: str | None = None
proposal_name = ""

if proposal_source == "Upload a file":
    uploaded = st.sidebar.file_uploader(
        "Upload proposal (.md or .pdf)",
        type=["md", "pdf"],
        label_visibility="collapsed",
    )
    if uploaded:
        try:
            _validate_upload(uploaded)
            proposal_text = load_proposal_from_bytes(uploaded.read(), uploaded.name)
            proposal_name = Path(uploaded.name).stem
        except ProposalLoadError as e:
            st.sidebar.error(str(e))
            proposal_text = None
elif proposal_source == "Choose from proposals folder":
    if proposals_dir.is_dir():
        files = sorted(p for p in proposals_dir.iterdir() if p.suffix.lower() in ALLOWED_EXTENSIONS)
        options = ["— Select a file —"] + [p.name for p in files]
        chosen = st.sidebar.selectbox("File", options, label_visibility="collapsed")
        if chosen and chosen != "— Select a file —":
            path = proposals_dir / chosen
            try:
                proposal_text = load_proposal(path, base_dir=root)
                proposal_name = path.stem
            except ProposalLoadError as e:
                st.sidebar.error(str(e))
                proposal_text = None
    else:
        st.sidebar.info("No proposals folder found. Upload a file instead.")

mode = st.sidebar.selectbox(
    "Mode",
    [
        "Jury only (4 experts — quick)",
        "Jury only (7 experts)",
        "Full (community + jury)",
    ],
    index=0,
)
if "4 experts" in mode:
    mode_key = "jury_quick"
elif "Full" in mode:
    mode_key = "full"
else:
    mode_key = "jury"

st.sidebar.markdown("---")
st.sidebar.caption(
    "Decision-support tool. Not a substitute for public process or elected governance."
)

# Main: require proposal and API
if not proposal_text:
    st.info("Upload a proposal or select one from the sidebar to get started.")
    st.stop()

if not _check_api_configured():
    st.stop()

st.subheader("Proposal")
st.caption(f"Using: {proposal_name} · Mode: {mode_key}")
with st.expander("View proposal text (excerpt)", expanded=False):
    st.text(proposal_text[:8000] + ("..." if len(proposal_text) > 8000 else ""))

# ---- Step-through: Round 1 / Round 2 / Round 3 ----
st.markdown("---")
st.subheader("Deliberation")

st.caption("Run one round at a time to see results quickly, or run all rounds at once. Watch the terminal for progress (each agent logs when it starts and finishes).")

col_r1, col_r2, col_r3, col_all = st.columns(4)

with col_r1:
    run_r1 = st.button("Run Round 1", type="primary", help="Individual scoring by each expert")
with col_r2:
    run_r2 = st.button("Run Round 2", disabled=not st.session_state.round1_done, help="Deliberation: react to each other's scores")
with col_r3:
    run_r3 = st.button("Run Round 3", disabled=not st.session_state.round2_done, help="Final scores, verdicts, and synthesis")
with col_all:
    run_all = st.button("Run all rounds", help="Run Round 1, 2, and 3 in one go (takes longer)")

if st.session_state.run_in_progress:
    st.warning("A run is already in progress. Please wait.")
    run_r1 = run_r2 = run_r3 = run_all = False

def _clear_rounds_after_r1():
    st.session_state.round2_done = False
    st.session_state.round3_done = False

if run_r1 and proposal_text:
    st.session_state.run_in_progress = True
    try:
        progress = st.progress(0, text="Round 1 — Loading jurors…")
        jury_personas = load_jury_personas(quick=(mode_key == "jury_quick"))
        community_summary = ""
        if mode_key == "full":
            progress.progress(20, text="Community phase…")
            community_summary = get_community_summary(proposal_text)
            st.session_state.community_summary = community_summary
        progress.progress(40, text="Round 1 — Individual scoring…")
        round1_scores, log_entries, out_dir = run_round1(
            proposal_text, community_summary, jury_personas
        )
        st.session_state.run_dir = out_dir
        st.session_state.round1_scores = round1_scores
        st.session_state.log_entries = log_entries
        st.session_state.jury_personas = jury_personas
        st.session_state.round1_done = True
        _clear_rounds_after_r1()
        progress.progress(100, text="Round 1 done.")
        st.success(f"Round 1 complete. Outputs in `{out_dir.name}`.")
    except Exception as e:
        st.error(f"Round 1 failed: {e}")
    finally:
        st.session_state.run_in_progress = False
        st.rerun()

if run_r2 and st.session_state.round1_done and st.session_state.log_entries is not None and st.session_state.jury_personas is not None:
    st.session_state.run_in_progress = True
    try:
        progress = st.progress(0, text="Round 2 — Deliberation…")
        log_entries = run_round2(
            st.session_state.jury_personas,
            st.session_state.log_entries,
            Path(st.session_state.run_dir),
        )
        st.session_state.log_entries = log_entries
        st.session_state.round2_done = True
        st.session_state.round3_done = False
        progress.progress(100, text="Round 2 done.")
        st.success("Round 2 complete.")
    except Exception as e:
        st.error(f"Round 2 failed: {e}")
    finally:
        st.session_state.run_in_progress = False
        st.rerun()

if run_r3 and st.session_state.round2_done and st.session_state.log_entries is not None and st.session_state.jury_personas is not None and st.session_state.round1_scores is not None:
    st.session_state.run_in_progress = True
    try:
        progress = st.progress(0, text="Round 3 — Final vote & synthesis…")
        run_round3(
            st.session_state.jury_personas,
            st.session_state.log_entries,
            st.session_state.round1_scores,
            Path(st.session_state.run_dir),
        )
        st.session_state.round3_done = True
        progress.progress(100, text="Done.")
        st.success("Round 3 and synthesis complete.")
    except Exception as e:
        st.error(f"Round 3 failed: {e}")
    finally:
        st.session_state.run_in_progress = False
        st.rerun()

if run_all and proposal_text:
    st.session_state.run_in_progress = True
    try:
        progress = st.progress(0, text="Running all rounds… (see terminal for progress)")
        out_dir = run(proposal_text, mode=mode_key, output_dir=None)
        st.session_state.run_dir = out_dir
        st.session_state.round1_done = True
        st.session_state.round2_done = True
        st.session_state.round3_done = True
        # Load written outputs into state for display (run() writes scores.json, not round1_scores.json)
        if (out_dir / "scores.json").exists():
            data = json.loads((out_dir / "scores.json").read_text())
            st.session_state.round1_scores = data.get("round1", [])
        st.session_state.log_entries = []
        progress.progress(100, text="Done.")
        st.success(f"All rounds complete. Outputs in `{out_dir.name}`.")
    except Exception as e:
        st.error(f"Run failed: {e}")
    finally:
        st.session_state.run_in_progress = False
        st.rerun()

# ---- Per-round summary (scrollable) ----
run_dir = st.session_state.run_dir
if run_dir is not None:
    run_dir = Path(run_dir)

if run_dir and run_dir.is_dir():
    st.markdown("---")
    st.subheader("Results (by round)")

    # Round 1
    if st.session_state.round1_done and st.session_state.round1_scores:
        with st.expander("Round 1 — Individual scoring", expanded=True):
            rows = st.session_state.round1_scores
            for r in rows:
                name = r.get("name", r.get("agent_id", "?"))
                st.markdown(f"**{name}** — Impact: {r.get('impact', '—')}/10 · Fiscal: {r.get('fiscal', '—')}/10 · Sustainability: {r.get('sustainability', '—')}/10")
                if r.get("justification"):
                    st.caption(r["justification"][:400] + ("…" if len(r.get("justification", "")) > 400 else ""))
                st.markdown("")
            if (run_dir / "round1_log.md").exists():
                with st.expander("Full Round 1 log", expanded=False):
                    st.markdown((run_dir / "round1_log.md").read_text(encoding="utf-8"))

    # Round 2
    if st.session_state.round2_done:
        with st.expander("Round 2 — Deliberation", expanded=True):
            if (run_dir / "round2_log.md").exists():
                st.markdown((run_dir / "round2_log.md").read_text(encoding="utf-8"))
            else:
                r2_entries = [e for e in (st.session_state.log_entries or []) if e.get("round") == "Round 2 — Deliberation"]
                for e in r2_entries:
                    st.markdown(f"**{e.get('agent_id', '?')}**")
                    st.markdown(e.get("content", "")[:800])
                    st.markdown("")

    # Round 3 + Synthesis + Full report
    if st.session_state.round3_done:
        with st.expander("Round 3 — Final vote & synthesis", expanded=True):
            report_path = run_dir / "report.md"
            if report_path.exists():
                st.markdown(report_path.read_text(encoding="utf-8"))
        with st.expander("Full deliberation log", expanded=False):
            log_path = run_dir / "deliberation_log.md"
            if log_path.exists():
                st.markdown(log_path.read_text(encoding="utf-8"))
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "Download report (Markdown)",
                data=(run_dir / "report.md").read_text(encoding="utf-8") if (run_dir / "report.md").exists() else "",
                file_name="report.md",
                mime="text/markdown",
                key="dl_report",
            )
        with col2:
            if (run_dir / "deliberation_log.md").exists():
                st.download_button(
                    "Download deliberation log (Markdown)",
                    data=(run_dir / "deliberation_log.md").read_text(encoding="utf-8"),
                    file_name="deliberation_log.md",
                    mime="text/markdown",
                    key="dl_log",
                )

# Backward compat: if they had last_run_dir from before, show it (legacy single run)
if not run_dir and st.session_state.get("last_run_dir") and Path(st.session_state.last_run_dir).is_dir():
    out_dir = Path(st.session_state.last_run_dir)
    st.subheader("Results")
    if (out_dir / "report.md").exists():
        st.markdown((out_dir / "report.md").read_text(encoding="utf-8"))
    with st.expander("Full deliberation log", expanded=False):
        if (out_dir / "deliberation_log.md").exists():
            st.markdown((out_dir / "deliberation_log.md").read_text(encoding="utf-8"))
