"""
AutoGen Data Analysis Agent — Streamlit Web UI
================================================
Run with:
    streamlit run app.py
"""
import streamlit as st
import pandas as pd
import os
import sys
import io
import re
import shutil
import tempfile
import threading
from pathlib import Path
from datetime import datetime

# ── Page config (must be first Streamlit call) ─────────────────────────────────
st.set_page_config(
    page_title="Data Analysis Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Overall background */
[data-testid="stAppViewContainer"] { background: #0f1117; }
[data-testid="stSidebar"] { background: #1a1d26; }

/* Cards */
.agent-card {
    background: #1e2130;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
    border-left: 4px solid #4f8ef7;
}
.agent-card.planner  { border-left-color: #f7c948; }
.agent-card.coder    { border-left-color: #4fcb71; }
.agent-card.executor { border-left-color: #f77f4f; }
.agent-card.insights { border-left-color: #af4ff7; }

.agent-label {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.35rem;
}
.planner-label  { color: #f7c948; }
.coder-label    { color: #4fcb71; }
.executor-label { color: #f77f4f; }
.insights-label { color: #af4ff7; }

/* Insight report box */
.report-box {
    background: #1a1d26;
    border: 1px solid #2a2d3e;
    border-radius: 12px;
    padding: 1.5rem 2rem;
}

/* Status badge */
.status-badge {
    display: inline-block;
    padding: 0.2rem 0.75rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
}
.status-running { background: #1a3a5c; color: #4f8ef7; }
.status-done    { background: #1a3a26; color: #4fcb71; }
.status-error   { background: #3a1a1a; color: #f74f4f; }

/* Suggested buttons */
.stButton > button {
    border-radius: 8px;
    border: 1px solid #2a2d3e;
    background: #1e2130;
    color: #c9d1e0;
    font-size: 0.82rem;
    padding: 0.4rem 0.8rem;
    transition: all 0.2s;
}
.stButton > button:hover {
    border-color: #4f8ef7;
    color: #ffffff;
    background: #1e2a40;
}

/* Chart caption */
.chart-caption {
    text-align: center;
    font-size: 0.78rem;
    color: #7a8499;
    margin-top: 0.25rem;
}
</style>
""", unsafe_allow_html=True)


# ── Constants ──────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

AGENT_COLORS = {
    "Planner":  ("planner",  "📋 Planner"),
    "Coder":    ("coder",    "💻 Coder"),
    "Executor": ("executor", "⚙️  Executor"),
    "Insights": ("insights", "💡 Insights"),
}

SUGGESTED_QUESTIONS = [
    "Monthly revenue trend and growth rate",
    "Top 5 products by total revenue",
    "Revenue breakdown by region with comparison",
    "Best performing sales channel",
    "Impact of discounts on revenue",
    "Sales rep performance ranking",
    "Category-wise sales distribution",
    "Seasonal sales patterns across quarters",
]


# ── Session state init ─────────────────────────────────────────────────────────
DEFAULT_QUESTION = (
    "Analyse 2024 sales performance: monthly revenue trend, "
    "top 5 products by revenue, revenue by region, "
    "best sales channel, and effect of discounts."
)

for key, default in {
    "messages":        [],
    "charts":          [],
    "insights_text":   "",
    "analysis_done":   False,
    "analysis_error":  "",
    "question_input":  DEFAULT_QUESTION,
    "csv_path":        str(BASE_DIR / "sales_data.csv"),
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ── Helpers ────────────────────────────────────────────────────────────────────

def parse_agent_messages(raw_output: str) -> list[dict]:
    """
    Parse AutoGen's stdout into a list of {agent, content} dicts.

    AutoGen prints blocks separated by dashes. Each block may start with
    noise lines like "Next speaker: X" or "[autogen.oai...] WARNING" before
    the actual "AgentName (to chat_manager):\n<content>" header.
    We search for the header anywhere inside the block, not just at the start.
    """
    blocks = re.split(r"-{40,}", raw_output)
    messages = []
    agent_pattern = re.compile(
        r"(Planner|Coder|Executor|Insights|chat_manager)\s+\(to\s+\S+\):\s*\n",
        re.MULTILINE,
    )
    for block in blocks:
        if not block.strip():
            continue
        m = agent_pattern.search(block)
        if m:
            agent   = m.group(1)
            content = block[m.end():].strip()
            # Strip TERMINATE marker
            content = content.replace("TERMINATE", "").strip()
            if content and len(content) > 5:
                messages.append({"agent": agent, "content": content})
    return messages


def run_autogen_pipeline(csv_path: str, question: str) -> tuple[str, str]:
    """
    Run the AutoGen GroupChat pipeline.
    Returns (raw_stdout, error_string).
    """
    # Lazy imports so Streamlit doesn't fail on cold start
    try:
        from config import get_llm_config
        from agents import (
            make_planner, make_coder, make_executor,
            make_insights, build_group_chat,
        )
    except Exception as e:
        return "", f"Import error: {e}"

    # Capture all stdout
    buffer = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buffer

    try:
        llm_config = get_llm_config(temperature=0)
        planner    = make_planner(llm_config)
        coder      = make_coder(llm_config)
        executor   = make_executor()
        insights   = make_insights(llm_config)

        _, manager = build_group_chat(planner, coder, executor, insights, llm_config)

        # Build seed message
        df = pd.read_csv(csv_path)
        col_info = ", ".join(
            f"{c} ({t})" for c, t in zip(df.columns, df.dtypes)
        )
        sample = df.head(3).to_string(index=False)
        seed = (
            f"## Analysis Request\n\n"
            f"**Question:** {question}\n\n"
            f"**Dataset Overview:**\n"
            f"Rows: {len(df):,}  |  Columns: {len(df.columns)}\n"
            f"Columns: {col_info}\n\n"
            f"First 3 rows:\n{sample}\n\n"
            f"The variable `csv_path` in the code should be set to: '{csv_path}'\n\n"
            "Start with the analysis plan (Planner), write and execute the code "
            "(Coder + Executor), then summarise findings (Insights)."
        )

        executor.initiate_chat(manager, message=seed)
        raw = buffer.getvalue()
        return raw, ""

    except Exception as e:
        raw = buffer.getvalue()
        return raw, str(e)
    finally:
        sys.stdout = old_stdout


def collect_charts() -> list[Path]:
    """Return sorted list of PNG charts in output/."""
    return sorted(OUTPUT_DIR.glob("*.png"))


def extract_insights(messages: list[dict]) -> str:
    """Return the last Insights agent message."""
    for msg in reversed(messages):
        if msg["agent"] == "Insights":
            return msg["content"].replace("TERMINATE", "").strip()
    return ""


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 Data Analysis Agent")
    st.markdown("---")
    st.markdown("""
**How it works**

1. **Upload** your CSV file
2. **Ask** a question about your data
3. **Run** — four AI agents collaborate:

| Agent | Role |
|---|---|
| 📋 Planner | Analysis plan |
| 💻 Coder | Writes Python code |
| ⚙️ Executor | Runs the code |
| 💡 Insights | Final report |

Charts are saved to `output/`
""")
    st.markdown("---")
    st.markdown("**Model:** GPT-4o via OpenAI")
    st.markdown("**Framework:** Microsoft AutoGen")
    st.markdown("---")

    # Clear results button
    if st.button("🗑️ Clear Results", width="stretch"):
        for f in OUTPUT_DIR.glob("*.png"):
            f.unlink()
        st.session_state.messages      = []
        st.session_state.charts        = []
        st.session_state.insights_text = ""
        st.session_state.analysis_done = False
        st.session_state.analysis_error = ""
        st.rerun()


# ── Main layout ────────────────────────────────────────────────────────────────
st.title("📊 Data Analysis Agent")
st.markdown("Upload a CSV, ask a question, and let four AI agents plan, code, execute, and report.")
st.markdown("---")

# ── Step 1: CSV Upload ─────────────────────────────────────────────────────────
col_upload, col_preview = st.columns([1, 2], gap="large")

with col_upload:
    st.subheader("① Upload Dataset")

    use_sample = st.checkbox("Use sample sales dataset", value=True)

    if use_sample:
        csv_path = str(BASE_DIR / "sales_data.csv")
        st.info("Using: `sales_data.csv` (1,000 rows of 2024 sales data)")
    else:
        uploaded = st.file_uploader("Upload your CSV file", type=["csv"])
        if uploaded:
            # Save to a temp location
            tmp_path = BASE_DIR / f"uploaded_{uploaded.name}"
            with open(tmp_path, "wb") as f:
                f.write(uploaded.read())
            csv_path = str(tmp_path)
            st.success(f"Uploaded: `{uploaded.name}`")
        else:
            csv_path = str(BASE_DIR / "sales_data.csv")
            st.warning("No file uploaded — using sample data.")

    st.session_state.csv_path = csv_path

with col_preview:
    st.subheader("② Preview Data")
    try:
        df_preview = pd.read_csv(csv_path)
        st.markdown(f"**{len(df_preview):,} rows × {len(df_preview.columns)} columns**")
        st.dataframe(df_preview.head(8), width="stretch", height=240)

        with st.expander("📈 Quick stats"):
            st.dataframe(df_preview.describe(), width="stretch")
    except Exception as e:
        st.error(f"Could not read CSV: {e}")

st.markdown("---")

# ── Step 2: Question ───────────────────────────────────────────────────────────
st.subheader("③ Ask a Question")

st.markdown("**Suggested questions — click to use:**")
q_cols = st.columns(4)
for i, suggestion in enumerate(SUGGESTED_QUESTIONS):
    with q_cols[i % 4]:
        if st.button(suggestion, key=f"sug_{i}", width="stretch"):
            st.session_state["question_input"] = suggestion

question = st.text_area(
    "Your analysis question",
    height=90,
    key="question_input",
    placeholder="e.g. Which product had the highest growth? What regions underperform?",
)

st.markdown("---")

# ── Step 3: Run ────────────────────────────────────────────────────────────────
st.subheader("④ Run Analysis")

run_col, status_col = st.columns([1, 3])
with run_col:
    run_clicked = st.button("▶ Run Analysis", type="primary", width="stretch")

with status_col:
    if st.session_state.analysis_done:
        st.markdown('<span class="status-badge status-done">✔ Analysis complete</span>', unsafe_allow_html=True)
    elif st.session_state.analysis_error:
        st.markdown(f'<span class="status-badge status-error">✖ Error</span>', unsafe_allow_html=True)

# ── Run pipeline ───────────────────────────────────────────────────────────────
if run_clicked and question.strip():
    # Clear previous results
    for f in OUTPUT_DIR.glob("*.png"):
        f.unlink()
    st.session_state.messages      = []
    st.session_state.charts        = []
    st.session_state.insights_text = ""
    st.session_state.analysis_done = False
    st.session_state.analysis_error = ""

    with st.spinner("🤖 Agents are working... This may take 1–3 minutes."):
        raw_output, error = run_autogen_pipeline(csv_path, question)

    if error and not raw_output:
        st.session_state.analysis_error = error
        st.error(f"Pipeline error: {error}")
    else:
        st.session_state.messages      = parse_agent_messages(raw_output)
        st.session_state.charts        = collect_charts()
        st.session_state.insights_text = extract_insights(st.session_state.messages)
        st.session_state.analysis_done = True
        if error:
            st.warning(f"Completed with warning: {error}")
        st.rerun()

elif run_clicked:
    st.warning("Please enter a question before running the analysis.")

st.markdown("---")

# ── Results ────────────────────────────────────────────────────────────────────
if st.session_state.analysis_done:

    # ── Agent Conversation Log ─────────────────────────────────────────────────
    with st.expander("🗣️ Agent Conversation Log", expanded=False):
        if st.session_state.messages:
            for msg in st.session_state.messages:
                agent = msg["agent"]
                css_cls, label = AGENT_COLORS.get(agent, ("", agent))
                content = msg["content"]

                # Render code blocks separately
                st.markdown(
                    f'<div class="agent-card {css_cls}">'
                    f'<div class="agent-label {css_cls}-label">{label}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                # Show code in st.code if it looks like code
                if "```python" in content or content.strip().startswith("import "):
                    # Extract and display code block
                    code_match = re.search(r"```python\n(.*?)```", content, re.DOTALL)
                    if code_match:
                        pre  = content[: content.index("```python")].strip()
                        post = content[content.index("```python") + len(code_match.group(0)):].strip()
                        if pre:
                            st.markdown(pre)
                        st.code(code_match.group(1), language="python")
                        if post:
                            st.markdown(post)
                    else:
                        st.code(content, language="python")
                else:
                    st.markdown(content)
                st.markdown("")
        else:
            st.info("No messages captured.")

    # ── Charts Gallery ─────────────────────────────────────────────────────────
    st.subheader("📈 Generated Charts")
    charts = st.session_state.charts
    if charts:
        cols_per_row = 2
        for row_start in range(0, len(charts), cols_per_row):
            row_charts = charts[row_start : row_start + cols_per_row]
            cols = st.columns(cols_per_row, gap="medium")
            for col, chart_path in zip(cols, row_charts):
                with col:
                    st.image(str(chart_path), width="stretch")
                    st.markdown(
                        f'<p class="chart-caption">{chart_path.stem.replace("_", " ").title()}</p>',
                        unsafe_allow_html=True,
                    )
    else:
        st.info("No charts were generated. Check the conversation log for details.")

    # ── Insights Report ────────────────────────────────────────────────────────
    st.subheader("💡 Insights Report")
    if st.session_state.insights_text:
        st.markdown(
            f'<div class="report-box">{st.session_state.insights_text}</div>',
            unsafe_allow_html=True,
        )

        # Download button
        st.download_button(
            label="⬇️ Download Report (.md)",
            data=st.session_state.insights_text,
            file_name=f"insights_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            width="content",
        )
    else:
        st.info("No insights report generated yet. Run the analysis to generate one.")

elif st.session_state.analysis_error:
    st.error(f"Analysis failed: {st.session_state.analysis_error}")
else:
    # Placeholder before first run
    st.markdown("""
<div style="text-align:center; padding: 3rem 0; color: #5a6478;">
    <div style="font-size: 3rem;">📊</div>
    <div style="font-size: 1.1rem; margin-top: 0.5rem;">
        Upload a CSV, ask a question, and click <strong>▶ Run Analysis</strong>
    </div>
    <div style="font-size: 0.85rem; margin-top: 0.5rem;">
        Results — charts, conversation log, and insights report — will appear here.
    </div>
</div>
""", unsafe_allow_html=True)
