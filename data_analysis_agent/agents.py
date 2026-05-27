"""
Agent definitions for the Data Analysis pipeline.

Four agents collaborate in a GroupChat:

  Planner   → reads dataset structure, writes step-by-step analysis plan
  Coder     → turns the plan into executable pandas / matplotlib code
  Executor  → runs the code, captures output and saves charts
  Insights  → reads all outputs and writes a plain-English report
"""
import os
import autogen
from config import get_llm_config

# Where generated charts will be saved
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ── Planner ────────────────────────────────────────────────────────────────────

PLANNER_SYSTEM = """You are a senior Data Analyst.
Your job is to look at a dataset description and the user's question, then produce
a clear, numbered analysis plan that another agent will turn into code.

Rules:
- Always start by listing the dataset columns and their types (inferred from the message).
- Break the analysis into 3–6 concrete numbered steps.
- Each step must name the exact chart type OR statistic to compute.
- Do NOT write any Python code yourself — only the plan.
- End your message with: PLAN COMPLETE
"""


def make_planner(llm_config: dict) -> autogen.AssistantAgent:
    return autogen.AssistantAgent(
        name="Planner",
        system_message=PLANNER_SYSTEM,
        llm_config=llm_config,
    )


# ── Coder ──────────────────────────────────────────────────────────────────────

CODER_SYSTEM = f"""You are an expert Python data scientist.
You receive an analysis plan and write clean, runnable Python code using
pandas, matplotlib, and seaborn.

Rules:
- Always start with the necessary imports.
- Read the CSV with: df = pd.read_csv(csv_path)  # csv_path is provided as a variable
- Save every chart to the output directory: OUTPUT_DIR = "{OUTPUT_DIR}"
  Use: plt.savefig(os.path.join(OUTPUT_DIR, "filename.png"), bbox_inches="tight")
- After each chart, call plt.close() to free memory.
- Print a summary statistic table for every analysis step.
- At the very end print: "=== ANALYSIS COMPLETE ==="
- Wrap the entire script in a single python code block.
- Do NOT use plt.show() — always save to file instead.
"""


def make_coder(llm_config: dict) -> autogen.AssistantAgent:
    return autogen.AssistantAgent(
        name="Coder",
        system_message=CODER_SYSTEM,
        llm_config=llm_config,
    )


# ── Executor ───────────────────────────────────────────────────────────────────

def make_executor() -> autogen.UserProxyAgent:
    """
    UserProxyAgent that auto-executes code blocks.
    human_input_mode=NEVER means it never pauses for keyboard input.
    """
    return autogen.UserProxyAgent(
        name="Executor",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=10,
        is_termination_msg=lambda msg: "TERMINATE" in msg.get("content", ""),
        code_execution_config={
            "work_dir": os.path.dirname(__file__),
            "use_docker": False,        # runs locally in the venv
        },
        default_auto_reply="Code executed. Waiting for Insights agent.",
    )


# ── Insights ───────────────────────────────────────────────────────────────────

INSIGHTS_SYSTEM = """You are a Business Intelligence Analyst.
You receive the printed output of a data analysis script and turn it into
a structured, easy-to-read executive report.

Your report must contain:
1. **Key Findings** — 3–5 bullet points of the most important discoveries.
2. **Trends** — any time-based or regional patterns observed.
3. **Top Performers** — best products, regions, sales reps.
4. **Recommendations** — 2–3 actionable business recommendations.
5. **Charts Generated** — list the file names of charts that were saved.

After the report, end your message with exactly: TERMINATE
"""


def make_insights(llm_config: dict) -> autogen.AssistantAgent:
    return autogen.AssistantAgent(
        name="Insights",
        system_message=INSIGHTS_SYSTEM,
        llm_config=llm_config,
    )


# ── GroupChat factory ──────────────────────────────────────────────────────────

def build_group_chat(
    planner: autogen.AssistantAgent,
    coder: autogen.AssistantAgent,
    executor: autogen.UserProxyAgent,
    insights: autogen.AssistantAgent,
    llm_config: dict,
) -> tuple[autogen.GroupChat, autogen.GroupChatManager]:
    """
    Wire the four agents into a GroupChat and return
    both the GroupChat and its Manager.

    Speaker order is enforced with a custom selection function so the
    conversation follows the intended pipeline:
        Planner → Coder → Executor → Insights → TERMINATE
    """

    def custom_speaker_selection(last_speaker, groupchat):
        messages = groupchat.messages
        if not messages:
            return planner

        last_content = messages[-1].get("content", "") or ""
        last_name    = last_speaker.name if last_speaker else ""

        # Seed message (first message is always from Executor) → Planner goes first
        if len(messages) == 1:
            return planner

        # After Planner finishes → Coder writes the code
        if last_name == "Planner":
            return coder

        # After Coder writes code → Executor runs it
        if last_name == "Coder":
            return executor

        # After Executor runs code → check if code actually ran (exitcode present)
        # or if Insights hasn't spoken yet — either way move to Insights
        if last_name == "Executor":
            # If code was executed (exitcode line present) → Insights
            if "exitcode:" in last_content:
                return insights
            # If this is the default auto-reply (no code to run) → Insights
            if "Waiting for Insights" in last_content:
                return insights
            # Otherwise Coder needs to fix/retry
            return coder

        # After Insights writes report → done
        if last_name == "Insights":
            return None  # triggers termination

        return planner  # fallback

    groupchat = autogen.GroupChat(
        agents=[executor, planner, coder, insights],
        messages=[],
        max_round=25,
        speaker_selection_method=custom_speaker_selection,
    )

    manager = autogen.GroupChatManager(
        groupchat=groupchat,
        llm_config=llm_config,
    )

    return groupchat, manager
