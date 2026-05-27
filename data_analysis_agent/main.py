"""
Data Analysis Agent — Entry Point
==================================
Usage:
    python main.py                            # uses default CSV + question
    python main.py --csv my_data.csv          # custom CSV file
    python main.py --question "Your question" # custom analysis question

The four-agent pipeline runs automatically:
  Planner → Coder → Executor → Insights
"""
import argparse
import os
import sys
import pandas as pd

from config import get_llm_config
from agents import make_planner, make_coder, make_executor, make_insights, build_group_chat

# ── Default values ─────────────────────────────────────────────────────────────

DEFAULT_CSV = os.path.join(os.path.dirname(__file__), "sales_data.csv")

DEFAULT_QUESTION = (
    "Analyse our 2024 sales performance. "
    "I want to know: (1) monthly revenue trend, "
    "(2) top 5 products by total revenue, "
    "(3) revenue breakdown by region, "
    "(4) which sales channel performs best, "
    "(5) the effect of discounts on revenue."
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def describe_dataset(csv_path: str) -> str:
    """Return a compact dataset description to seed the agents."""
    df = pd.read_csv(csv_path)
    col_info = ", ".join(
        f"{col} ({dtype})" for col, dtype in zip(df.columns, df.dtypes)
    )
    sample = df.head(3).to_string(index=False)
    return (
        f"Dataset path: {csv_path}\n"
        f"Rows: {len(df):,}  |  Columns: {len(df.columns)}\n"
        f"Columns: {col_info}\n\n"
        f"First 3 rows:\n{sample}"
    )


def build_seed_message(csv_path: str, question: str) -> str:
    """Construct the opening message that kicks off the GroupChat."""
    dataset_info = describe_dataset(csv_path)
    return (
        f"## Analysis Request\n\n"
        f"**Question:** {question}\n\n"
        f"**Dataset Overview:**\n{dataset_info}\n\n"
        f"The variable `csv_path` in the generated code should be set to: '{csv_path}'\n\n"
        "Please start by creating a detailed analysis plan (Planner), "
        "then write and execute the code (Coder + Executor), "
        "and finally summarise the findings (Insights)."
    )


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AutoGen Data Analysis Agent")
    parser.add_argument("--csv",      default=DEFAULT_CSV,      help="Path to the CSV file")
    parser.add_argument("--question", default=DEFAULT_QUESTION, help="Analysis question")
    args = parser.parse_args()

    # Validate CSV
    if not os.path.exists(args.csv):
        print(f"ERROR: CSV file not found: {args.csv}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  AutoGen Data Analysis Agent")
    print("=" * 60)
    print(f"  CSV      : {args.csv}")
    print(f"  Question : {args.question[:80]}...")
    print("=" * 60 + "\n")

    # Build LLM config and agents
    llm_config = get_llm_config(temperature=0)

    planner  = make_planner(llm_config)
    coder    = make_coder(llm_config)
    executor = make_executor()
    insights = make_insights(llm_config)

    groupchat, manager = build_group_chat(
        planner, coder, executor, insights, llm_config
    )

    # Kick off the conversation — Executor initiates, agents take over
    seed_message = build_seed_message(args.csv, args.question)

    print("Starting multi-agent conversation...\n")
    executor.initiate_chat(
        manager,
        message=seed_message,
    )

    # ── Done ────────────────────────────────────────────────────────────────
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    charts = [f for f in os.listdir(output_dir) if f.endswith(".png")]

    print("\n" + "=" * 60)
    print("  Analysis Complete!")
    print("=" * 60)
    if charts:
        print(f"  Charts saved to: {output_dir}/")
        for chart in sorted(charts):
            print(f"    - {chart}")
    else:
        print("  No charts were generated.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
