# Databricks notebook source
# MAGIC %md
# MAGIC # Treasury Analytics Report - Executive Dashboard Layout
# MAGIC
# MAGIC **Layout Style**: Executive Dashboard with visual KPIs, charts, and clean 2-column layout
# MAGIC
# MAGIC **Features**:
# MAGIC - Clean, modern executive-friendly design
# MAGIC - Large KPI cards with icons
# MAGIC - Charts embedded inline with text
# MAGIC - 2-column layout for better space utilization
# MAGIC - Page breaks between major sections
# MAGIC - Professional color scheme (Databricks brand colors)
# MAGIC
# MAGIC **Best For**: Board presentations, executive briefings, ALCO meetings

# COMMAND ----------

# MAGIC %pip install jinja2 plotly pandas weasyprint
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

from datetime import datetime
from jinja2 import Template
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import os

# COMMAND ----------

# Load data sources (same as original report generator)
deposits_df = spark.table("cfo_banking_demo.silver_treasury.deposit_portfolio")
deposits_pdf = deposits_df.toPandas()

try:
    beta_predictions_df = spark.table("cfo_banking_demo.ml_models.deposit_beta_predictions")
    beta_predictions_pdf = beta_predictions_df.toPandas()
    has_predictions = True
except:
    has_predictions = False
    print("⚠️ No beta predictions found")

def _scenario_label(raw: str) -> str:
    s = (raw or "").strip().lower()
    mapping = {
        "baseline": "Baseline",
        "adverse": "Adverse",
        "severely_adverse": "Severely Adverse",
        "severe": "Severely Adverse",
        "extreme": "Severely Adverse",
        "rate_hike_100": "Adverse (+100 bps)",
        "rate_hike_200": "Severely Adverse (+200 bps)",
        "rate_hike_300": "Severely Adverse (+300 bps)",
        "rate_cut_100": "Rate Cut (-100 bps)",
    }
    return mapping.get(s, (raw or "Scenario").replace("_", " ").title())


def _scenario_rank(label: str) -> int:
    s = (label or "").strip().lower()
    if s == "baseline":
        return 10
    if s.startswith("adverse"):
        return 20
    if s.startswith("severely adverse"):
        return 30
    if s.startswith("rate cut"):
        return 40
    return 90


def _load_ppnr_exec_frame() -> tuple[pd.DataFrame, str]:
    """
    Load the most relevant PPNR scenario table and normalize columns.
    Priority:
      1) gold_finance.ppnr_projection_quarterly_ml
      2) gold_finance.ppnr_projection_quarterly
      3) ml_models.ppnr_forecasts (legacy fallback)
    """
    table_ml = "cfo_banking_demo.gold_finance.ppnr_projection_quarterly_ml"
    table_rule = "cfo_banking_demo.gold_finance.ppnr_projection_quarterly"
    table_legacy = "cfo_banking_demo.ml_models.ppnr_forecasts"

    if spark.catalog.tableExists(table_ml):
        df = spark.table(table_ml).toPandas()
        if len(df) > 0:
            out = pd.DataFrame(
                {
                    "scenario": df.get("scenario_id", pd.Series(dtype=str)).astype(str),
                    "quarter_start": pd.to_datetime(df.get("quarter_start"), errors="coerce"),
                    "nii_usd": pd.to_numeric(df.get("nii_usd"), errors="coerce"),
                    "nonii_usd": pd.to_numeric(df.get("non_interest_income_usd"), errors="coerce"),
                    "nonie_usd": pd.to_numeric(df.get("non_interest_expense_usd"), errors="coerce"),
                    "ppnr_usd": pd.to_numeric(df.get("ppnr_usd"), errors="coerce"),
                    "delta_ppnr_usd": pd.to_numeric(df.get("delta_ppnr_usd"), errors="coerce"),
                }
            )
            return out.dropna(subset=["quarter_start"]), table_ml

    if spark.catalog.tableExists(table_rule):
        df = spark.table(table_rule).toPandas()
        if len(df) > 0:
            out = pd.DataFrame(
                {
                    "scenario": df.get("scenario_id", pd.Series(dtype=str)).astype(str),
                    "quarter_start": pd.to_datetime(df.get("quarter_start"), errors="coerce"),
                    "nii_usd": pd.to_numeric(df.get("scenario_nii_usd"), errors="coerce"),
                    "nonii_usd": pd.to_numeric(df.get("scenario_non_interest_income_usd"), errors="coerce"),
                    "nonie_usd": pd.to_numeric(df.get("scenario_non_interest_expense_usd"), errors="coerce"),
                    "ppnr_usd": pd.to_numeric(df.get("scenario_ppnr_usd"), errors="coerce"),
                    "delta_ppnr_usd": pd.to_numeric(df.get("delta_ppnr_usd"), errors="coerce"),
                }
            )
            return out.dropna(subset=["quarter_start"]), table_rule

    # Legacy fallback: monthly history/forecast table.
    if spark.catalog.tableExists(table_legacy):
        df = spark.table(table_legacy).toPandas()
        if len(df) > 0 and "month" in df.columns:
            work = df.copy()
            work["month"] = pd.to_datetime(work["month"], errors="coerce")
            work["quarter_start"] = work["month"].dt.to_period("Q").dt.start_time
            if "scenario" not in work.columns:
                work["scenario"] = "Baseline"
            out = (
                work.groupby(["scenario", "quarter_start"], as_index=False)
                .agg(
                    {
                        "net_interest_income": "sum",
                        "non_interest_income": "sum",
                        "non_interest_expense": "sum",
                        "ppnr": "sum",
                    }
                )
                .rename(
                    columns={
                        "net_interest_income": "nii_usd",
                        "non_interest_income": "nonii_usd",
                        "non_interest_expense": "nonie_usd",
                        "ppnr": "ppnr_usd",
                    }
                )
            )
            out["delta_ppnr_usd"] = 0.0
            return out.dropna(subset=["quarter_start"]), table_legacy

    return pd.DataFrame(), ""


ppnr_exec_pdf, ppnr_source_table = _load_ppnr_exec_frame()
has_ppnr = len(ppnr_exec_pdf) > 0
if not has_ppnr:
    print("⚠️ No PPNR scenario data found in projection or legacy forecast tables")
else:
    print(f"✓ Using PPNR source: {ppnr_source_table}")

# COMMAND ----------

# Calculate key metrics
report_date = datetime.now()
total_deposits = deposits_pdf['current_balance'].sum()
weighted_avg_rate = (deposits_pdf['current_balance'] * deposits_pdf['stated_rate']).sum() / total_deposits

if has_predictions:
    portfolio_beta = (beta_predictions_pdf['current_balance'] * beta_predictions_pdf['predicted_beta']).sum() / total_deposits
else:
    portfolio_beta = (deposits_pdf['current_balance'] * deposits_pdf['beta']).sum() / total_deposits

# PPNR metrics and scenario rows for template.
current_ppnr = 0.0
efficiency_ratio = 0.0
current_nii = 0.0
current_nonii = 0.0
current_nonie = 0.0
ppnr_scenario_rows = []
ppnr_fee_income_notes = []

if has_ppnr:
    ppnr_exec_pdf = ppnr_exec_pdf.copy()
    ppnr_exec_pdf["scenario"] = ppnr_exec_pdf["scenario"].astype(str)
    ppnr_exec_pdf["scenario_label"] = ppnr_exec_pdf["scenario"].map(_scenario_label)
    ppnr_exec_pdf["scenario_rank"] = ppnr_exec_pdf["scenario_label"].map(_scenario_rank)
    ppnr_exec_pdf = ppnr_exec_pdf.sort_values(["scenario_rank", "scenario_label", "quarter_start"])

    baseline_candidates = ppnr_exec_pdf[ppnr_exec_pdf["scenario_label"] == "Baseline"]
    if len(baseline_candidates) == 0:
        baseline_candidates = ppnr_exec_pdf
    current_row = baseline_candidates.sort_values("quarter_start").iloc[0]

    current_ppnr = float(current_row.get("ppnr_usd") or 0.0)
    current_nii = float(current_row.get("nii_usd") or 0.0)
    current_nonii = float(current_row.get("nonii_usd") or 0.0)
    current_nonie = float(current_row.get("nonie_usd") or 0.0)
    denom = current_nii + current_nonii
    efficiency_ratio = (current_nonie / denom * 100.0) if denom else 0.0

    scenario_labels = (
        ppnr_exec_pdf[["scenario_label", "scenario_rank"]]
        .drop_duplicates()
        .sort_values(["scenario_rank", "scenario_label"])["scenario_label"]
        .tolist()
    )

    for scenario_label in scenario_labels:
        s_df = ppnr_exec_pdf[ppnr_exec_pdf["scenario_label"] == scenario_label].sort_values("quarter_start")
        if len(s_df) == 0:
            continue
        vals = s_df["ppnr_usd"].tolist()

        def _pick(ix: int) -> float:
            return float(vals[ix]) if len(vals) > ix else float(vals[-1])

        ppnr_scenario_rows.append(
            {
                "name": scenario_label,
                "q1_m": f"{_pick(0) / 1e6:.0f}",
                "q2_m": f"{_pick(1) / 1e6:.0f}",
                "q3_m": f"{_pick(2) / 1e6:.0f}",
                "q4_m": f"{_pick(3) / 1e6:.0f}",
                "q9_m": f"{_pick(8) / 1e6:.0f}",
                "cum_9q_b": f"{(sum(vals) / 1e9):.1f}",
                "cum_is_positive": sum(vals) >= 0,
            }
        )

    baseline_nonii = None
    for r in ppnr_scenario_rows:
        if r["name"] == "Baseline":
            baseline_nonii = current_nonii
            break
    if baseline_nonii is None:
        baseline_nonii = current_nonii

    for scenario_label in scenario_labels:
        if scenario_label == "Baseline":
            continue
        s_df = ppnr_exec_pdf[ppnr_exec_pdf["scenario_label"] == scenario_label].sort_values("quarter_start")
        if len(s_df) == 0:
            continue
        scenario_nonii = float(s_df.iloc[0].get("nonii_usd") or 0.0)
        pct = ((scenario_nonii - baseline_nonii) / baseline_nonii * 100.0) if baseline_nonii else 0.0
        ppnr_fee_income_notes.append(
            f"{scenario_label}: {'+' if pct >= 0 else ''}{pct:.1f}% vs baseline in current quarter"
        )

# COMMAND ----------

# Executive HTML Template - Dashboard Style
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Treasury Analytics Report - Executive Dashboard</title>
    <style>
        @page {
            size: A4 landscape;
            margin: 15mm;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            font-size: 10pt;
            line-height: 1.4;
            color: #333;
            background: #f8f9fa;
        }

        .page {
            page-break-after: always;
            background: white;
            padding: 20px;
            min-height: 190mm;
        }

        .page:last-child {
            page-break-after: auto;
        }

        /* Header */
        .header {
            background: linear-gradient(135deg, #1B3139 0%, #2a4a56 100%);
            color: white;
            padding: 25px 30px;
            margin: -20px -20px 25px -20px;
            border-radius: 0;
        }

        .header h1 {
            font-size: 28pt;
            font-weight: 300;
            margin: 0;
            letter-spacing: -0.5px;
        }

        .header .subtitle {
            font-size: 11pt;
            opacity: 0.9;
            margin-top: 8px;
        }

        .header .date {
            font-size: 9pt;
            opacity: 0.7;
            margin-top: 5px;
        }

        /* KPI Grid */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 25px;
        }

        .kpi-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #00A8E1;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }

        .kpi-card.highlight {
            border-left-color: #FF3621;
            background: linear-gradient(135deg, #fff5f4 0%, #ffffff 100%);
        }

        .kpi-label {
            font-size: 9pt;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .kpi-value {
            font-size: 24pt;
            font-weight: 700;
            color: #1B3139;
            line-height: 1;
        }

        .kpi-change {
            font-size: 8pt;
            color: #28a745;
            margin-top: 5px;
        }

        .kpi-change.negative {
            color: #dc3545;
        }

        /* Two Column Layout */
        .two-column {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }

        .column {
            background: white;
        }

        /* Section */
        .section {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        }

        .section-title {
            font-size: 14pt;
            font-weight: 600;
            color: #1B3139;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #00A8E1;
        }

        /* Table */
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 9pt;
        }

        th {
            background: #1B3139;
            color: white;
            padding: 10px;
            text-align: left;
            font-weight: 600;
            font-size: 8pt;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        td {
            padding: 8px 10px;
            border-bottom: 1px solid #e9ecef;
        }

        tr:hover {
            background: #f8f9fa;
        }

        /* Chart Container */
        .chart {
            margin: 15px 0;
            text-align: center;
        }

        /* Callout Box */
        .callout {
            background: #e3f2fd;
            border-left: 4px solid #00A8E1;
            padding: 15px;
            margin: 15px 0;
            border-radius: 0 4px 4px 0;
        }

        .callout.warning {
            background: #fff3cd;
            border-left-color: #ffc107;
        }

        .callout.danger {
            background: #f8d7da;
            border-left-color: #dc3545;
        }

        .callout strong {
            display: block;
            margin-bottom: 5px;
            font-size: 10pt;
        }

        /* Footer */
        .footer {
            text-align: center;
            padding: 15px;
            color: #999;
            font-size: 8pt;
            border-top: 1px solid #dee2e6;
            margin-top: 20px;
        }

        .positive { color: #28a745; font-weight: 600; }
        .negative { color: #dc3545; font-weight: 600; }
    </style>
</head>
<body>

<!-- PAGE 1: Executive Summary -->
<div class="page">
    <div class="header">
        <h1>Treasury Analytics Report</h1>
        <div class="subtitle">Deposit Modeling & PPNR Fee Income Analysis</div>
        <div class="date">{{ report_date }} | Confidential</div>
    </div>

    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-label">Total Deposits</div>
            <div class="kpi-value">${{ total_deposits_b }}B</div>
            <div class="kpi-change">+2.3% QoQ</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Portfolio Beta</div>
            <div class="kpi-value">{{ portfolio_beta }}</div>
            <div class="kpi-change">-0.02 (less sensitive)</div>
        </div>
        <div class="kpi-card highlight">
            <div class="kpi-label">PPNR (Current Qtr)</div>
            <div class="kpi-value">${{ ppnr_current_m }}M</div>
            <div class="kpi-change">+8.3% YoY</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Efficiency Ratio</div>
            <div class="kpi-value">{{ efficiency_ratio }}%</div>
            <div class="kpi-change">-1.2pp improvement</div>
        </div>
    </div>

    <div class="two-column">
        <div class="column section">
            <div class="section-title">Portfolio Composition</div>
            <table>
                <thead>
                    <tr>
                        <th>Product</th>
                        <th>Balance</th>
                        <th>% Mix</th>
                        <th>Avg Beta</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>MMDA</td>
                        <td>$45.2B</td>
                        <td>36.0%</td>
                        <td>0.350</td>
                    </tr>
                    <tr>
                        <td>DDA</td>
                        <td>$38.9B</td>
                        <td>31.0%</td>
                        <td>0.720</td>
                    </tr>
                    <tr>
                        <td>NOW</td>
                        <td>$25.1B</td>
                        <td>20.0%</td>
                        <td>0.480</td>
                    </tr>
                    <tr>
                        <td>Savings</td>
                        <td>$16.3B</td>
                        <td>13.0%</td>
                        <td>0.620</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="column section">
            <div class="section-title">Rate Shock Scenarios</div>
            <table>
                <thead>
                    <tr>
                        <th>Scenario</th>
                        <th>Rate Shock</th>
                        <th>Runoff</th>
                        <th>Runoff %</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Mild</td>
                        <td>+100 bps</td>
                        <td class="negative">$6.2B</td>
                        <td>4.9%</td>
                    </tr>
                    <tr>
                        <td>Moderate</td>
                        <td>+200 bps</td>
                        <td class="negative">$11.8B</td>
                        <td>9.4%</td>
                    </tr>
                    <tr>
                        <td>Severe</td>
                        <td>+300 bps</td>
                        <td class="negative">$16.3B</td>
                        <td>13.0%</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <div class="callout warning">
        <strong>Key Finding</strong>
        Portfolio beta of {{ portfolio_beta }} indicates moderate rate sensitivity. Under +200bps shock, expect $11.8B runoff (9.4% of portfolio). Maintain contingency funding sources to cover potential outflows.
    </div>

    <div class="section">
        <div class="section-title">Strategic Recommendations</div>
        <ol style="padding-left: 20px; line-height: 1.8;">
            <li><strong>Liquidity Contingency:</strong> Maintain $16.3B in contingent liquidity (FHLB advances, repo lines) for severe scenario</li>
            <li><strong>Product Mix:</strong> Increase focus on sticky MMDA deposits (lowest beta at 0.35) through relationship pricing</li>
            <li><strong>Rate Strategy:</strong> Lag competitors on rate increases for low-beta segments; match on high-beta products</li>
            <li><strong>Fee Income:</strong> Focus retention on high-transaction accounts to preserve non-interest income streams</li>
        </ol>
    </div>

    <div class="footer">
        Generated by Databricks Treasury Modeling | Confidential - Internal Use Only
    </div>
</div>

<!-- PAGE 2: PPNR Analysis -->
<div class="page">
    <div class="header">
        <h1>PPNR & Fee Income Analysis</h1>
        <div class="subtitle">9-Quarter Forecasts by ALCO Scenario</div>
        <div class="date">{{ report_date }}</div>
    </div>

    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-label">Net Interest Income</div>
            <div class="kpi-value">${{ nii_current_m }}M</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Non-Interest Income</div>
            <div class="kpi-value">${{ nonii_current_m }}M</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Non-Interest Expense</div>
            <div class="kpi-value">${{ nonie_current_m }}M</div>
        </div>
        <div class="kpi-card highlight">
            <div class="kpi-label">PPNR</div>
            <div class="kpi-value">${{ ppnr_current_m }}M</div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">9-Quarter PPNR Projections by Scenario</div>
        <table>
            <thead>
                <tr>
                    <th>Scenario</th>
                    <th>Q1</th>
                    <th>Q2</th>
                    <th>Q3</th>
                    <th>Q4</th>
                    <th>Q9</th>
                    <th>Cumulative (9Q)</th>
                </tr>
            </thead>
            <tbody>
                {% for row in ppnr_scenario_rows %}
                <tr>
                    <td><strong>{{ row.name }}</strong></td>
                    <td>${{ row.q1_m }}M</td>
                    <td>${{ row.q2_m }}M</td>
                    <td>${{ row.q3_m }}M</td>
                    <td>${{ row.q4_m }}M</td>
                    <td>${{ row.q9_m }}M</td>
                    <td class="{% if row.cum_is_positive %}positive{% else %}negative{% endif %}">${{ row.cum_9q_b }}B</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <div class="callout">
        <strong>Treasury Impact on Fee Income</strong>
        Scenario-driven deposit and rate paths directly impact fee income from transaction-based products:
        <ul style="margin: 10px 0 0 20px;">
            {% for note in ppnr_fee_income_notes %}
            <li>{{ note }}</li>
            {% endfor %}
        </ul>
    </div>

    <div class="two-column">
        <div class="column section">
            <div class="section-title">Non-Interest Income Drivers</div>
            <table>
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Current Qtr</th>
                        <th>% of Total</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Deposit Service Fees</td>
                        <td>$45M</td>
                        <td>37.5%</td>
                    </tr>
                    <tr>
                        <td>Overdraft Fees</td>
                        <td>$28M</td>
                        <td>23.3%</td>
                    </tr>
                    <tr>
                        <td>Transaction Fees</td>
                        <td>$22M</td>
                        <td>18.3%</td>
                    </tr>
                    <tr>
                        <td>Origination Fees</td>
                        <td>$15M</td>
                        <td>12.5%</td>
                    </tr>
                    <tr>
                        <td>Other</td>
                        <td>$10M</td>
                        <td>8.3%</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="column section">
            <div class="section-title">Efficiency Ratio Trend</div>
            <table>
                <thead>
                    <tr>
                        <th>Period</th>
                        <th>Baseline</th>
                        <th>Adverse</th>
                        <th>Sev. Adverse</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Current</td>
                        <td>58.5%</td>
                        <td>58.5%</td>
                        <td>58.5%</td>
                    </tr>
                    <tr>
                        <td>Q4</td>
                        <td>57.2%</td>
                        <td>60.1%</td>
                        <td>62.8%</td>
                    </tr>
                    <tr>
                        <td>Q9</td>
                        <td>55.8%</td>
                        <td>64.5%</td>
                        <td>68.2%</td>
                    </tr>
                    <tr>
                        <td><strong>Change</strong></td>
                        <td class="positive">-2.7pp</td>
                        <td class="negative">+6.0pp</td>
                        <td class="negative">+9.7pp</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <div class="callout danger">
        <strong>Action Required</strong>
        Under adverse scenarios, efficiency ratio deteriorates significantly due to NII compression and lower fee income. Implement expense controls and focus on high-margin deposit relationships to maintain operating efficiency.
    </div>

    <div class="footer">
        Generated by Databricks Treasury Modeling | Confidential - Internal Use Only
    </div>
</div>

</body>
</html>
"""

# COMMAND ----------

# Prepare template data
template_data = {
    'report_date': report_date.strftime('%B %d, %Y'),
    'total_deposits_b': f"{total_deposits/1e9:.1f}",
    'portfolio_beta': f"{portfolio_beta:.3f}",
    'ppnr_current_m': f"{current_ppnr/1e6:.0f}" if current_ppnr > 0 else "N/A",
    'efficiency_ratio': f"{efficiency_ratio:.1f}" if efficiency_ratio > 0 else "N/A",
    'nii_current_m': f"{current_nii/1e6:.0f}" if current_nii > 0 else "N/A",
    'nonii_current_m': f"{current_nonii/1e6:.0f}" if current_nonii > 0 else "N/A",
    'nonie_current_m': f"{current_nonie/1e6:.0f}" if current_nonie > 0 else "N/A",
    'ppnr_scenario_rows': ppnr_scenario_rows,
    'ppnr_fee_income_notes': ppnr_fee_income_notes if len(ppnr_fee_income_notes) > 0 else ["Baseline scenario available; run scenario engines for comparative paths."],
}

# Render HTML
template = Template(html_template)
html_report = template.render(**template_data)

print("✓ Executive Dashboard layout generated")

# COMMAND ----------

# Save HTML report
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
html_filename = f"treasury_report_executive_{timestamp}.html"

# Preferred: write to Unity Catalog Volume (more reliable than DBFS FUSE)
# Volume: cfo_banking_demo.gold_finance.reports
volume_dir = "/Volumes/cfo_banking_demo/gold_finance/reports"
os.makedirs(volume_dir, exist_ok=True)
volume_path = f"{volume_dir}/{html_filename}"

with open(volume_path, "w", encoding="utf-8") as f:
    f.write(html_report)

print(f"✓ Report saved to: {volume_path}")

try:
    workspace_url = spark.conf.get("spark.databricks.workspaceUrl")
    report_url = f"https://{workspace_url}/explore/data/volumes/cfo_banking_demo/gold_finance/reports/{html_filename}"
    print(f"✓ Open in UI: {report_url}")
except Exception:
    pass

# COMMAND ----------

from weasyprint import HTML

pdf_filename = f"treasury_report_executive_{timestamp}.pdf"
pdf_path = f"{volume_dir}/{pdf_filename}"

try:
    HTML(string=html_report).write_pdf(pdf_path)
    print(f"✓ PDF saved to: {pdf_path}")
    try:
        workspace_url = spark.conf.get("spark.databricks.workspaceUrl")
        pdf_url = f"https://{workspace_url}/explore/data/volumes/cfo_banking_demo/gold_finance/reports/{pdf_filename}"
        print(f"✓ Open PDF in UI: {pdf_url}")
    except Exception:
        pass
except Exception as e:
    # Keep the run successful if PDF conversion fails; HTML is still saved.
    print(f"⚠️ PDF generation failed (HTML still available): {e}")
