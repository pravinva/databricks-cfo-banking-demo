# Databricks notebook source
# MAGIC %md
# MAGIC # Deposit Analytics Report Generator
# MAGIC
# MAGIC **Purpose**: Generate comprehensive report showing the impact of rate changes on deposit portfolio behavior
# MAGIC
# MAGIC **Report Sections**:
# MAGIC 1. Executive Summary - Key metrics and findings
# MAGIC 2. Portfolio Composition - Current deposit mix and characteristics
# MAGIC 3. Deposit Beta Analysis - Rate sensitivity by product type
# MAGIC 4. Rate Shock Scenarios - Impact of +100bps, +200bps, +300bps shocks
# MAGIC 5. Deposit Runoff Projections - Expected outflows under stress
# MAGIC 6. Vintage Analysis - Cohort retention and decay patterns
# MAGIC 7. Recommendations - Strategic insights and action items
# MAGIC
# MAGIC **Output Formats**:
# MAGIC - HTML report (saved to DBFS)
# MAGIC - Delta table (for dashboard integration)
# MAGIC - PDF export (optional, requires additional setup)
# MAGIC
# MAGIC **Use Cases**:
# MAGIC - ALCO presentations
# MAGIC - Regulatory reporting (CCAR/DFAST)
# MAGIC - Executive briefings
# MAGIC - Board presentations

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup: Install Required Libraries

# COMMAND ----------

# MAGIC %pip install plotly kaleido matplotlib seaborn jinja2 weasyprint

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Import Libraries

# COMMAND ----------

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pyspark.sql import functions as F
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# For HTML report generation
from jinja2 import Template

print("Libraries imported successfully")
print(f"Report generation date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Section 1: Load Data and Calculate Key Metrics

# COMMAND ----------

# Load deposit portfolio data
deposits_df = spark.table("cfo_banking_demo.silver_treasury.deposit_portfolio")
deposits_pdf = deposits_df.toPandas()

# Load deposit beta predictions (from batch inference)
try:
    beta_predictions_df = spark.table("cfo_banking_demo.ml_models.deposit_beta_predictions")
    beta_predictions_pdf = beta_predictions_df.toPandas()
    has_predictions = True
except:
    print("⚠️ Warning: No deposit beta predictions found. Run Batch_Inference_Deposit_Beta_Model.py first.")
    has_predictions = False
    # Use static betas from portfolio table
    beta_predictions_pdf = deposits_pdf[['account_id', 'product_type', 'current_balance', 'beta']].copy()
    beta_predictions_pdf.rename(columns={'beta': 'predicted_beta'}, inplace=True)

# Load vintage analysis data
try:
    vintage_df = spark.table("cfo_banking_demo.ml_models.cohort_survival_rates")
    vintage_pdf = vintage_df.toPandas()
    has_vintage = True
except:
    print("⚠️ Warning: No vintage analysis data found.")
    has_vintage = False

# Load stress test results (if available)
try:
    stress_df = spark.table("cfo_banking_demo.ml_models.stress_test_results")
    stress_pdf = stress_df.toPandas()
    has_stress = True
except:
    print("⚠️ Warning: No stress test results found.")
    has_stress = False

print(f"✓ Loaded {len(deposits_pdf):,} deposit accounts")
print(f"✓ Total deposits: ${deposits_pdf['current_balance'].sum()/1e9:.2f}B")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Section 2: Calculate Executive Summary Metrics

# COMMAND ----------

# Calculate key portfolio metrics
report_date = datetime.now()
total_deposits = deposits_pdf['current_balance'].sum()
weighted_avg_rate = (deposits_pdf['current_balance'] * deposits_pdf['stated_rate']).sum() / total_deposits

# Calculate portfolio-level beta (weighted average)
if has_predictions:
    portfolio_beta = (beta_predictions_pdf['current_balance'] * beta_predictions_pdf['predicted_beta']).sum() / total_deposits
else:
    portfolio_beta = (deposits_pdf['current_balance'] * deposits_pdf['beta']).sum() / total_deposits

# Product mix
product_mix = deposits_pdf.groupby('product_type').agg({
    'current_balance': 'sum',
    'account_id': 'count'
}).reset_index()
product_mix.columns = ['product_type', 'total_balance', 'account_count']
product_mix['pct_of_total'] = product_mix['total_balance'] / total_deposits * 100
product_mix = product_mix.sort_values('total_balance', ascending=False)

# Beta by product type
beta_by_product = beta_predictions_pdf.groupby('product_type').agg({
    'predicted_beta': 'mean',
    'current_balance': 'sum'
}).reset_index()
beta_by_product.columns = ['product_type', 'avg_beta', 'total_balance']
beta_by_product = beta_by_product.sort_values('avg_beta', ascending=False)

print("=" * 80)
print("EXECUTIVE SUMMARY METRICS")
print("=" * 80)
print(f"Report Date: {report_date.strftime('%B %d, %Y')}")
print(f"Total Deposits: ${total_deposits/1e9:.2f}B")
print(f"Weighted Average Rate: {weighted_avg_rate:.2%}")
print(f"Portfolio Beta: {portfolio_beta:.3f}")
print(f"Number of Accounts: {len(deposits_pdf):,}")
print()
print("Product Mix:")
print(product_mix.to_string(index=False))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Section 3: Rate Shock Scenario Analysis

# COMMAND ----------

# Define rate shock scenarios
rate_shocks = [
    {'name': 'Baseline', 'shock_bps': 0, 'description': 'Current rates'},
    {'name': 'Moderate (+100 bps)', 'shock_bps': 100, 'description': 'Gradual rate increase'},
    {'name': 'Severe (+200 bps)', 'shock_bps': 200, 'description': 'Rapid rate shock'},
    {'name': 'Extreme (+300 bps)', 'shock_bps': 300, 'description': 'Crisis scenario'}
]

# Calculate runoff for each scenario
scenario_results = []

for scenario in rate_shocks:
    shock_bps = scenario['shock_bps']

    # Calculate deposit runoff based on beta
    # Runoff % = Beta × (Rate Shock / 100)
    # Higher beta = more rate sensitive = more runoff risk

    scenario_data = beta_predictions_pdf.copy()
    scenario_data['rate_shock_pct'] = shock_bps / 100  # Convert bps to percentage
    scenario_data['expected_runoff_pct'] = scenario_data['predicted_beta'] * scenario_data['rate_shock_pct']
    scenario_data['expected_runoff_amount'] = scenario_data['current_balance'] * scenario_data['expected_runoff_pct'] / 100
    scenario_data['post_shock_balance'] = scenario_data['current_balance'] - scenario_data['expected_runoff_amount']

    # Aggregate by product type
    by_product = scenario_data.groupby('product_type').agg({
        'current_balance': 'sum',
        'expected_runoff_amount': 'sum',
        'post_shock_balance': 'sum'
    }).reset_index()
    by_product['runoff_pct'] = by_product['expected_runoff_amount'] / by_product['current_balance'] * 100

    # Portfolio totals
    total_runoff = scenario_data['expected_runoff_amount'].sum()
    runoff_pct = total_runoff / total_deposits * 100

    scenario_results.append({
        'scenario': scenario['name'],
        'shock_bps': shock_bps,
        'total_runoff': total_runoff,
        'runoff_pct': runoff_pct,
        'by_product': by_product
    })

    print(f"\n{scenario['name']} ({scenario['description']}):")
    print(f"  Expected Runoff: ${total_runoff/1e9:.2f}B ({runoff_pct:.2%})")
    print(f"  Remaining Deposits: ${(total_deposits - total_runoff)/1e9:.2f}B")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Section 4: Create Visualizations

# COMMAND ----------

# Visualization 1: Product Mix (Pie Chart)
fig_product_mix = go.Figure(data=[go.Pie(
    labels=product_mix['product_type'],
    values=product_mix['total_balance'],
    hole=0.4,
    marker=dict(colors=px.colors.qualitative.Set3)
)])
fig_product_mix.update_layout(
    title="Deposit Portfolio Composition",
    annotations=[dict(text=f"${total_deposits/1e9:.1f}B", x=0.5, y=0.5, font_size=20, showarrow=False)]
)

# Visualization 2: Beta by Product Type (Bar Chart)
fig_beta = go.Figure(data=[go.Bar(
    x=beta_by_product['product_type'],
    y=beta_by_product['avg_beta'],
    marker_color='rgb(55, 83, 109)',
    text=[f"{val:.3f}" for val in beta_by_product['avg_beta']],
    textposition='auto'
)])
fig_beta.update_layout(
    title="Average Deposit Beta by Product Type",
    xaxis_title="Product Type",
    yaxis_title="Beta Coefficient",
    yaxis=dict(range=[0, 1.0])
)

# Visualization 3: Rate Shock Scenarios (Waterfall Chart)
fig_scenarios = go.Figure()
scenarios_for_chart = [r for r in scenario_results if r['shock_bps'] > 0]

fig_scenarios.add_trace(go.Bar(
    name='Expected Runoff',
    x=[r['scenario'] for r in scenarios_for_chart],
    y=[r['runoff_pct'] for r in scenarios_for_chart],
    marker_color='rgb(219, 64, 82)',
    text=[f"${r['total_runoff']/1e9:.2f}B\n({r['runoff_pct']:.1%})" for r in scenarios_for_chart],
    textposition='auto'
))

fig_scenarios.update_layout(
    title="Deposit Runoff Under Rate Shock Scenarios",
    xaxis_title="Scenario",
    yaxis_title="Expected Runoff (%)",
    yaxis=dict(tickformat=".1%")
)

# Visualization 4: Runoff by Product Type (Grouped Bar Chart)
fig_by_product = go.Figure()
for scenario_result in scenarios_for_chart:
    by_prod = scenario_result['by_product']
    fig_by_product.add_trace(go.Bar(
        name=scenario_result['scenario'],
        x=by_prod['product_type'],
        y=by_prod['runoff_pct'],
        text=[f"{val:.1f}%" for val in by_prod['runoff_pct']],
        textposition='auto'
    ))

fig_by_product.update_layout(
    title="Expected Runoff by Product Type and Scenario",
    xaxis_title="Product Type",
    yaxis_title="Expected Runoff (%)",
    barmode='group',
    yaxis=dict(tickformat=".1%")
)

print("✓ Visualizations created successfully")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Section 5: Vintage Analysis (if available)

# COMMAND ----------

if has_vintage:
    # Visualization 5: Cohort Survival Curves
    fig_vintage = go.Figure()

    # Get unique cohorts (limit to recent ones for readability)
    cohorts = vintage_pdf['cohort'].unique()[:12]  # Last 12 cohorts

    for cohort in cohorts:
        cohort_data = vintage_pdf[vintage_pdf['cohort'] == cohort].sort_values('months_since_origination')
        fig_vintage.add_trace(go.Scatter(
            x=cohort_data['months_since_origination'],
            y=cohort_data['retention_rate'] * 100,
            mode='lines',
            name=cohort,
            line=dict(width=2)
        ))

    fig_vintage.update_layout(
        title="Deposit Cohort Survival Curves (24-Month Retention)",
        xaxis_title="Months Since Origination",
        yaxis_title="Retention Rate (%)",
        yaxis=dict(range=[0, 100], tickformat=".0f"),
        xaxis=dict(range=[0, 24])
    )

    # Calculate average retention rates
    avg_retention = vintage_pdf.groupby('months_since_origination')['retention_rate'].mean()
    print("\nAverage Deposit Retention Rates:")
    print(f"  6 months: {avg_retention.iloc[6]*100:.1f}%")
    print(f"  12 months: {avg_retention.iloc[12]*100:.1f}%")
    print(f"  24 months: {avg_retention.iloc[23]*100:.1f}%")
else:
    fig_vintage = None
    print("⚠️ Skipping vintage analysis (data not available)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Section 6: Generate HTML Report

# COMMAND ----------

# HTML Template
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Deposit Analytics Report - {{ report_date }}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 40px;
            background-color: #f5f5f5;
        }
        .header {
            background-color: #1B3139;
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .header h1 {
            margin: 0;
            font-size: 36px;
        }
        .header p {
            margin: 10px 0 0 0;
            font-size: 18px;
            opacity: 0.9;
        }
        .section {
            background-color: white;
            padding: 30px;
            margin-bottom: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .section h2 {
            color: #1B3139;
            border-bottom: 3px solid #00A8E1;
            padding-bottom: 10px;
            margin-top: 0;
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .metric-card {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #00A8E1;
        }
        .metric-card h3 {
            margin: 0 0 10px 0;
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .metric-card .value {
            font-size: 28px;
            font-weight: bold;
            color: #1B3139;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #1B3139;
            color: white;
            font-weight: 600;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .positive {
            color: #28a745;
        }
        .negative {
            color: #dc3545;
        }
        .warning {
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }
        .recommendation {
            background-color: #d1ecf1;
            border-left: 4px solid #00A8E1;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }
        .chart {
            margin: 30px 0;
            text-align: center;
        }
        .footer {
            text-align: center;
            color: #666;
            margin-top: 40px;
            padding: 20px;
            border-top: 1px solid #ddd;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Deposit Analytics Report</h1>
        <p>Impact of Rate Changes on Portfolio Behavior</p>
        <p>{{ report_date }}</p>
    </div>

    <!-- Executive Summary -->
    <div class="section">
        <h2>1. Executive Summary</h2>
        <div class="metric-grid">
            <div class="metric-card">
                <h3>Total Deposits</h3>
                <div class="value">${{ total_deposits_b }}B</div>
            </div>
            <div class="metric-card">
                <h3>Portfolio Beta</h3>
                <div class="value">{{ portfolio_beta }}</div>
            </div>
            <div class="metric-card">
                <h3>Weighted Avg Rate</h3>
                <div class="value">{{ weighted_avg_rate }}</div>
            </div>
            <div class="metric-card">
                <h3>Total Accounts</h3>
                <div class="value">{{ num_accounts }}</div>
            </div>
        </div>

        <div class="warning">
            <strong>Key Finding:</strong> Portfolio beta of {{ portfolio_beta }} indicates {{ beta_assessment }} rate sensitivity.
            Under a +200bps rate shock, expected deposit runoff is ${{ severe_runoff_b }}B ({{ severe_runoff_pct }}).
        </div>
    </div>

    <!-- Portfolio Composition -->
    <div class="section">
        <h2>2. Portfolio Composition</h2>
        <table>
            <thead>
                <tr>
                    <th>Product Type</th>
                    <th>Balance</th>
                    <th>% of Total</th>
                    <th>Accounts</th>
                    <th>Avg Beta</th>
                </tr>
            </thead>
            <tbody>
                {% for row in product_mix %}
                <tr>
                    <td>{{ row.product_type }}</td>
                    <td>${{ "%.2f"|format(row.total_balance/1e9) }}B</td>
                    <td>{{ "%.1f"|format(row.pct_of_total) }}%</td>
                    <td>{{ "{:,}".format(row.account_count) }}</td>
                    <td>{{ "%.3f"|format(row.avg_beta) }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <!-- Rate Shock Scenarios -->
    <div class="section">
        <h2>3. Rate Shock Scenario Analysis</h2>
        <p>Expected deposit runoff under various interest rate shock scenarios:</p>

        <table>
            <thead>
                <tr>
                    <th>Scenario</th>
                    <th>Rate Shock</th>
                    <th>Expected Runoff</th>
                    <th>Runoff %</th>
                    <th>Remaining Deposits</th>
                </tr>
            </thead>
            <tbody>
                {% for scenario in scenarios %}
                <tr>
                    <td>{{ scenario.name }}</td>
                    <td>+{{ scenario.shock_bps }} bps</td>
                    <td class="negative">${{ "%.2f"|format(scenario.total_runoff/1e9) }}B</td>
                    <td class="negative">{{ "%.2f"|format(scenario.runoff_pct) }}%</td>
                    <td>${{ "%.2f"|format(scenario.remaining_deposits/1e9) }}B</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <div class="recommendation">
            <strong>Recommendation:</strong> Under severe (+200bps) scenario, maintain ${{ "%.2f"|format(scenarios[2].total_runoff/1e9) }}B
            in contingent liquidity sources (FHLB advances, repo lines, Fed discount window) to cover potential runoff.
        </div>
    </div>

    <!-- Product-Level Analysis -->
    <div class="section">
        <h2>4. Product-Level Rate Sensitivity</h2>
        <p>Expected runoff by product type under +200bps severe scenario:</p>

        <table>
            <thead>
                <tr>
                    <th>Product Type</th>
                    <th>Current Balance</th>
                    <th>Average Beta</th>
                    <th>Expected Runoff</th>
                    <th>Runoff %</th>
                </tr>
            </thead>
            <tbody>
                {% for row in product_runoff %}
                <tr>
                    <td>{{ row.product_type }}</td>
                    <td>${{ "%.2f"|format(row.current_balance/1e9) }}B</td>
                    <td>{{ "%.3f"|format(row.avg_beta) }}</td>
                    <td class="negative">${{ "%.2f"|format(row.expected_runoff/1e9) }}B</td>
                    <td class="negative">{{ "%.1f"|format(row.runoff_pct) }}%</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <!-- Recommendations -->
    <div class="section">
        <h2>5. Strategic Recommendations</h2>
        <ol>
            <li><strong>Liquidity Contingency:</strong> Maintain ${{ "%.2f"|format(scenarios[2].total_runoff/1e9) }}B in contingent liquidity sources to cover severe scenario runoff.</li>
            <li><strong>Product Mix Optimization:</strong> {{ product_recommendation }}</li>
            <li><strong>Rate Strategy:</strong> {{ rate_recommendation }}</li>
            <li><strong>Monitoring:</strong> Implement weekly deposit beta tracking and monthly model retraining to capture changing customer behavior.</li>
            <li><strong>Stress Testing:</strong> Include deposit runoff scenarios in ALCO stress tests and capital planning exercises (CCAR/DFAST).</li>
        </ol>
    </div>

    <div class="footer">
        <p>Report generated by Databricks CFO Banking Demo</p>
        <p>{{ report_date }}</p>
        <p>For internal use only - Confidential</p>
    </div>
</body>
</html>
"""

# COMMAND ----------

# Prepare data for HTML template
severe_scenario = scenario_results[2]  # +200bps scenario

# Determine beta assessment
if portfolio_beta < 0.3:
    beta_assessment = "low"
elif portfolio_beta < 0.6:
    beta_assessment = "moderate"
else:
    beta_assessment = "high"

# Product recommendations
high_beta_products = beta_by_product[beta_by_product['avg_beta'] > 0.7]['product_type'].tolist()
if high_beta_products:
    product_recommendation = f"Consider reducing exposure to highly rate-sensitive products ({', '.join(high_beta_products)}) which have betas > 0.70."
else:
    product_recommendation = "Current product mix has balanced rate sensitivity. Maintain diversification."

# Rate recommendations
if weighted_avg_rate < 0.02:  # Below 2%
    rate_recommendation = "Current deposit rates are competitive. Monitor competitors to avoid offering unnecessary rate premiums."
else:
    rate_recommendation = "Deposit rates are above market. Consider selective rate reductions on less rate-sensitive products (low beta)."

# Prepare product mix with betas
product_mix_with_beta = product_mix.merge(
    beta_by_product[['product_type', 'avg_beta']],
    on='product_type',
    how='left'
)

# Prepare product runoff for severe scenario
product_runoff = severe_scenario['by_product'].merge(
    beta_by_product[['product_type', 'avg_beta']],
    on='product_type',
    how='left'
)
product_runoff['expected_runoff'] = product_runoff['expected_runoff_amount']
product_runoff = product_runoff.sort_values('runoff_pct', ascending=False)

# Render HTML
template = Template(html_template)
html_report = template.render(
    report_date=report_date.strftime('%B %d, %Y'),
    total_deposits_b=f"{total_deposits/1e9:.2f}",
    portfolio_beta=f"{portfolio_beta:.3f}",
    weighted_avg_rate=f"{weighted_avg_rate:.2%}",
    num_accounts=f"{len(deposits_pdf):,}",
    beta_assessment=beta_assessment,
    severe_runoff_b=f"{severe_scenario['total_runoff']/1e9:.2f}",
    severe_runoff_pct=f"{severe_scenario['runoff_pct']:.1%}",
    product_mix=product_mix_with_beta.to_dict('records'),
    scenarios=[
        {
            'name': r['scenario'],
            'shock_bps': r['shock_bps'],
            'total_runoff': r['total_runoff'],
            'runoff_pct': r['runoff_pct'],
            'remaining_deposits': total_deposits - r['total_runoff']
        }
        for r in scenario_results if r['shock_bps'] > 0
    ],
    product_runoff=product_runoff.to_dict('records'),
    product_recommendation=product_recommendation,
    rate_recommendation=rate_recommendation
)

print("✓ HTML report generated successfully")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Section 7: Save Report Outputs

# COMMAND ----------

# Save HTML report to Unity Catalog Volume
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
html_filename = f"deposit_analytics_report_{timestamp}.html"
html_volume_path = f"/Volumes/cfo_banking_demo/gold_finance/reports/{html_filename}"

# Write HTML file to UC Volume
with open(html_volume_path, 'w') as f:
    f.write(html_report)

# Get workspace URL dynamically
try:
    from databricks.sdk.runtime import spark
    workspace_url = spark.conf.get("spark.databricks.workspaceUrl")
    html_report_url = f"https://{workspace_url}/explore/data/volumes/cfo_banking_demo/gold_finance/reports/{html_filename}"
except:
    # Fallback if spark context not available
    workspace_url = "<your-workspace>.cloud.databricks.com"
    html_report_url = f"https://{workspace_url}/explore/data/volumes/cfo_banking_demo/gold_finance/reports/{html_filename}"

print(f"✓ HTML report saved to: {html_volume_path}")
print(f"  Access URL: {html_report_url}")

# Generate PDF version
try:
    from weasyprint import HTML

    pdf_filename = f"deposit_analytics_report_{timestamp}.pdf"
    pdf_volume_path = f"/Volumes/cfo_banking_demo/gold_finance/reports/{pdf_filename}"

    # Convert HTML to PDF
    HTML(string=html_report).write_pdf(pdf_volume_path)

    pdf_report_url = f"https://{workspace_url}/explore/data/volumes/cfo_banking_demo/gold_finance/reports/{pdf_filename}"

    print(f"✓ PDF report saved to: {pdf_volume_path}")
    print(f"  Access URL: {pdf_report_url}")

except Exception as e:
    print(f"⚠️ Warning: Could not generate PDF - {str(e)}")
    print("  HTML report is still available")
    pdf_volume_path = None

# COMMAND ----------

# Save report summary to Delta table for dashboard integration
report_summary_data = {
    'report_date': [report_date],
    'total_deposits': [total_deposits],
    'portfolio_beta': [portfolio_beta],
    'weighted_avg_rate': [weighted_avg_rate],
    'num_accounts': [len(deposits_pdf)],
    'moderate_runoff_100bps': [scenario_results[1]['total_runoff']],
    'moderate_runoff_pct': [scenario_results[1]['runoff_pct']],
    'severe_runoff_200bps': [scenario_results[2]['total_runoff']],
    'severe_runoff_pct': [scenario_results[2]['runoff_pct']],
    'extreme_runoff_300bps': [scenario_results[3]['total_runoff']],
    'extreme_runoff_pct': [scenario_results[3]['runoff_pct']],
    'html_report_path': [html_volume_path],
    'pdf_report_path': [pdf_volume_path]
}

report_summary_df = spark.createDataFrame(pd.DataFrame(report_summary_data))

# Save to Delta table
report_summary_df.write \
    .format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .saveAsTable("cfo_banking_demo.gold_analytics.deposit_analytics_reports")

print("✓ Report summary saved to: cfo_banking_demo.gold_analytics.deposit_analytics_reports")

# COMMAND ----------

# Save scenario details to Delta table
scenario_details = []
for scenario in scenario_results:
    if scenario['shock_bps'] > 0:  # Skip baseline
        for _, row in scenario['by_product'].iterrows():
            scenario_details.append({
                'report_date': report_date,
                'scenario_name': scenario['scenario'],
                'shock_bps': scenario['shock_bps'],
                'product_type': row['product_type'],
                'current_balance': row['current_balance'],
                'expected_runoff': row['expected_runoff_amount'],
                'runoff_pct': row['runoff_pct'],
                'post_shock_balance': row['post_shock_balance']
            })

scenario_df = spark.createDataFrame(pd.DataFrame(scenario_details))

scenario_df.write \
    .format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .saveAsTable("cfo_banking_demo.gold_analytics.rate_shock_scenarios")

print("✓ Scenario details saved to: cfo_banking_demo.gold_analytics.rate_shock_scenarios")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Section 8: Display Visualizations (for notebook view)

# COMMAND ----------

# Display charts in notebook
fig_product_mix.show()

# COMMAND ----------

fig_beta.show()

# COMMAND ----------

fig_scenarios.show()

# COMMAND ----------

fig_by_product.show()

# COMMAND ----------

if fig_vintage:
    fig_vintage.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Report Generation Complete
# MAGIC
# MAGIC **Outputs Created:**
# MAGIC 1. ✅ HTML Report: `/dbfs/FileStore/reports/deposit_analytics_report_[timestamp].html`
# MAGIC 2. ✅ Delta Tables:
# MAGIC    - `cfo_banking_demo.gold_analytics.deposit_analytics_reports` - Report summaries
# MAGIC    - `cfo_banking_demo.gold_analytics.rate_shock_scenarios` - Detailed scenario results
# MAGIC 3. ✅ Visualizations: Displayed inline in notebook
# MAGIC
# MAGIC **Next Steps:**
# MAGIC - Access HTML report via Databricks Files UI
# MAGIC - Query Delta tables for dashboard integration
# MAGIC - Schedule this notebook as a weekly/monthly job
# MAGIC - Export report to PDF (requires additional PDF library setup)
# MAGIC
# MAGIC **Scheduling Recommendation:**
# MAGIC - **Frequency**: Weekly (Sunday 11pm, after batch inference)
# MAGIC - **Dependencies**: Run after `Batch_Inference_Deposit_Beta_Model.py`
# MAGIC - **Alerting**: Send report link to ALCO members via email integration
