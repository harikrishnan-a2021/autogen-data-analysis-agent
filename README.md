# AutoGen Data Analysis Agent

An intelligent AI-powered data analysis system that uses a multi-agent architecture to automatically analyze CSV datasets and generate business insights.

## Features

- **4-Agent Pipeline**: Planner → Coder → Executor → Insights
- **Automatic Analysis**: Reads your question, creates a plan, writes code, executes it, and generates a report
- **Multiple LLM Support**: Works with Ollama (local), OpenAI, or Anthropic
- **Dual Interface**: CLI for scripting + Streamlit web UI for interactive analysis
- **Chart Generation**: Automatically saves charts and visualizations
- **Executive Reports**: Generates structured business intelligence summaries

## How It Works

```
Your CSV + Question
        ↓
    Planner Agent       → Reads dataset structure, creates analysis plan
        ↓
    Coder Agent         → Converts plan to executable pandas/matplotlib code
        ↓
    Executor Agent      → Runs code, saves charts, captures output
        ↓
    Insights Agent      → Transforms output into business report
        ↓
    Final Report
```

## Installation

1. **Clone the repository**
```bash
git clone https://github.com/harikrishnan-a2021/autogen-data-analysis-agent.git
cd autogen-data-analysis-agent
```

2. **Create a virtual environment** (optional but recommended)
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r data_analysis_agent/requirements.txt
```

4. **Configure LLM** (see Configuration section below)

## Configuration

The project supports three LLM providers. Set up via `.env` file in the `data_analysis_agent/` directory:

### Option 1: Ollama (Local, Free - Default)
```bash
cp data_analysis_agent/.env.example data_analysis_agent/.env
# Edit .env with:
USE_OLLAMA=true
OLLAMA_MODEL=llama3.1:8b  # or another model
OLLAMA_BASE_URL=http://localhost:11434/v1
```

Then run Ollama locally:
```bash
ollama pull llama3.1:8b
ollama serve
```

### Option 2: OpenAI
```env
USE_OLLAMA=false
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4o
```

### Option 3: Anthropic
```env
USE_OLLAMA=false
ANTHROPIC_API_KEY=your-api-key-here
```

## Usage

### CLI (Command Line)

**Basic usage** with default data:
```bash
python data_analysis_agent/main.py
```

**Custom CSV file:**
```bash
python data_analysis_agent/main.py --csv my_data.csv
```

**Custom analysis question:**
```bash
python data_analysis_agent/main.py --question "What are my top selling products?"
```

**Combined:**
```bash
python data_analysis_agent/main.py --csv sales.csv --question "Analyze Q1 performance"
```

### Streamlit Web UI

```bash
cd data_analysis_agent
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

## Project Structure

```
data_analysis_agent/
├── main.py                  # CLI entry point
├── app.py                   # Streamlit web UI
├── agents.py                # Agent definitions (Planner, Coder, Executor, Insights)
├── config.py                # LLM configuration
├── generate_sample_data.py  # Script to generate sample sales data
├── requirements.txt         # Python dependencies
├── .env.example             # Example environment variables
├── sales_data.csv           # Sample dataset
└── output/                  # Generated charts and outputs
```
## Sample Output

The system automatically generates charts and analysis reports. Here's a real example from running the analysis:

### Real Generated Charts

**1. Monthly Revenue Trend**

Shows revenue fluctuations across the year with peak months reaching $50K+.

![Monthly Revenue Trend](data_analysis_agent/output/monthly_revenue_trend.png)

**2. Regional Performance Analysis**

The East region leads with $568K in revenue, followed by North at $491K.

![Regional Performance Analysis](data_analysis_agent/output/top_regions_by_revenue.png)

**3. Price-Volume Correlation**

Lower price points ($0-$200) drive high volume; premium items ($1000+) show steady but lower volume.

![Price-Volume Correlation](data_analysis_agent/output/units_sold_vs_unit_price.png)

### Executive Report Example

The Insights Agent automatically generates a structured business report:

```
═══════════════════════════════════════════════════════════
           SALES PERFORMANCE ANALYSIS REPORT
═══════════════════════════════════════════════════════════

EXECUTIVE SUMMARY
─────────────────
Total Revenue:              $2,347,156
Number of Transactions:     10,000
Average Transaction Value:  $234.72

KEY FINDINGS
────────────
✓ East region dominates with 24.2% of total revenue ($568K)
✓ Monthly volatility ranges from $5K to $50K (no clear seasonality)
✓ Price sensitivity observed: high volume at budget price points
✓ Regional disparity suggests different market maturity levels

RECOMMENDATIONS
───────────────
1. Scale East region operations; proven high revenue generation
2. Investigate North region decline (20.9% → trending lower)
3. Optimize inventory for $0-$200 price segment (highest volume)
4. Test premium positioning at $1000+ price points
5. Implement region-specific pricing strategies

═══════════════════════════════════════════════════════════
```

### Full Sample Report

A complete analysis report with detailed findings is available in [`data_analysis_agent/output/SAMPLE_REPORT.md`](data_analysis_agent/output/SAMPLE_REPORT.md).
## Example

Given a sales CSV with columns: `date`, `product`, `revenue`, `region`, `discount`, `channel`

**Question:**
```
Analyse our 2024 sales performance. I want to know:
(1) monthly revenue trend
(2) top 5 products by total revenue
(3) revenue breakdown by region
(4) which sales channel performs best
(5) the effect of discounts on revenue
```

**Output:**
- Step-by-step analysis plan (text)
- Executable Python code (auto-generated)
- 5+ visualizations (saved to `output/`)
- Executive business report with:
  - Key findings
  - Trends
  - Top performers
  - Recommendations

## Sample Data Generation

To generate sample sales data:
```bash
python data_analysis_agent/generate_sample_data.py
```

This creates a CSV with realistic sales data for testing.

## Requirements

- Python 3.8+
- AutoGen 0.2.0b2
- pandas, matplotlib, seaborn
- Streamlit (for web UI)
- OpenAI/Anthropic API key (optional, if not using Ollama)

See `data_analysis_agent/requirements.txt` for all dependencies.

## Troubleshooting

**"Module not found" errors:**
```bash
pip install -r data_analysis_agent/requirements.txt
```

**Ollama connection refused:**
- Make sure Ollama is running: `ollama serve`
- Check `OLLAMA_BASE_URL` in `.env`

**Empty analysis output:**
- Ensure your CSV has proper headers
- Try a simpler question first
- Check LLM is responding (test with a shorter question)

## License

MIT License - feel free to modify and distribute.

## Contributing

Contributions welcome! Feel free to submit issues and pull requests.

---

**Built with:**
- [AutoGen](https://github.com/microsoft/autogen) - Multi-agent framework
- [Streamlit](https://streamlit.io) - Web UI
- [pandas](https://pandas.pydata.org) - Data analysis
- [matplotlib](https://matplotlib.org) & [seaborn](https://seaborn.pydata.org) - Visualization
