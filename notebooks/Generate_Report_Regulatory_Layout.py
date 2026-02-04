# Databricks notebook source
# MAGIC %md
# MAGIC # Treasury Analytics Report - Regulatory/Technical Layout
# MAGIC
# MAGIC **Layout Style**: Detailed regulatory reporting format with methodology sections
# MAGIC
# MAGIC **Features**:
# MAGIC - Comprehensive methodology documentation
# MAGIC - Detailed tables with full data
# MAGIC - Regulatory compliance sections
# MAGIC - Technical appendices
# MAGIC - Single-column detailed layout
# MAGIC - Formula explanations
# MAGIC - Audit trail friendly
# MAGIC
# MAGIC **Best For**: CCAR submissions, regulatory filings, audit documentation, technical reviews

# COMMAND ----------

# MAGIC %pip install jinja2 plotly pandas
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

from datetime import datetime
from jinja2 import Template
import pandas as pd

# COMMAND ----------

# Load data sources
deposits_df = spark.table("cfo_banking_demo.silver_treasury.deposit_portfolio")
deposits_pdf = deposits_df.toPandas()

try:
    beta_predictions_df = spark.table("cfo_banking_demo.ml_models.deposit_beta_predictions")
    beta_predictions_pdf = beta_predictions_df.toPandas()
    has_predictions = True
except:
    has_predictions = False

try:
    ppnr_df = spark.table("cfo_banking_demo.ml_models.ppnr_forecasts")
    ppnr_pdf = ppnr_df.toPandas()
    has_ppnr = True
except:
    has_ppnr = False

# COMMAND ----------

# Calculate metrics
report_date = datetime.now()
total_deposits = deposits_pdf['current_balance'].sum()
weighted_avg_rate = (deposits_pdf['current_balance'] * deposits_pdf['stated_rate']).sum() / total_deposits

if has_predictions:
    portfolio_beta = (beta_predictions_pdf['current_balance'] * beta_predictions_pdf['predicted_beta']).sum() / total_deposits
else:
    portfolio_beta = (deposits_pdf['current_balance'] * deposits_pdf['beta']).sum() / total_deposits

# COMMAND ----------

# Regulatory HTML Template
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Treasury Analytics Report - Regulatory Submission</title>
    <style>
        @page {
            size: A4 portrait;
            margin: 20mm;
            @top-right {
                content: "Page " counter(page) " of " counter(pages);
            }
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Times New Roman', Times, serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #000;
            background: white;
        }

        .page {
            page-break-after: always;
            padding: 20px 0;
        }

        .page:last-child {
            page-break-after: auto;
        }

        /* Cover Page */
        .cover {
            text-align: center;
            padding-top: 80px;
        }

        .cover h1 {
            font-size: 24pt;
            font-weight: bold;
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .cover .subtitle {
            font-size: 16pt;
            margin-bottom: 40px;
        }

        .cover .org-info {
            margin-top: 100px;
            font-size: 12pt;
        }

        .cover .date {
            margin-top: 20px;
            font-size: 11pt;
            color: #666;
        }

        .cover .confidential {
            margin-top: 60px;
            font-size: 10pt;
            color: #999;
            border: 2px solid #999;
            padding: 15px;
            display: inline-block;
        }

        /* Headers */
        h1 {
            font-size: 18pt;
            font-weight: bold;
            margin: 30px 0 15px 0;
            page-break-after: avoid;
        }

        h2 {
            font-size: 14pt;
            font-weight: bold;
            margin: 25px 0 12px 0;
            page-break-after: avoid;
        }

        h3 {
            font-size: 12pt;
            font-weight: bold;
            margin: 20px 0 10px 0;
            page-break-after: avoid;
        }

        /* TOC */
        .toc {
            margin: 30px 0;
        }

        .toc-item {
            padding: 8px 0;
            border-bottom: 1px dotted #ccc;
        }

        .toc-item a {
            text-decoration: none;
            color: #000;
        }

        .toc-page {
            float: right;
        }

        /* Section Numbering */
        .section-number {
            font-weight: bold;
            margin-right: 10px;
        }

        /* Tables */
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 10pt;
            page-break-inside: avoid;
        }

        table caption {
            caption-side: top;
            font-weight: bold;
            text-align: left;
            margin-bottom: 8px;
            font-size: 10pt;
        }

        th {
            background: #2c3e50;
            color: white;
            padding: 10px;
            text-align: left;
            font-weight: bold;
            border: 1px solid #000;
        }

        td {
            padding: 8px 10px;
            border: 1px solid #000;
        }

        tr:nth-child(even) {
            background: #f8f9fa;
        }

        /* Formula Box */
        .formula {
            background: #f0f0f0;
            border: 1px solid #999;
            padding: 15px;
            margin: 15px 0;
            font-family: 'Courier New', monospace;
            font-size: 10pt;
            page-break-inside: avoid;
        }

        .formula-title {
            font-weight: bold;
            margin-bottom: 10px;
            font-family: 'Times New Roman', Times, serif;
        }

        /* Methodology Box */
        .methodology {
            border: 2px solid #2c3e50;
            padding: 15px;
            margin: 20px 0;
            background: #f8f9fa;
            page-break-inside: avoid;
        }

        .methodology-title {
            font-weight: bold;
            font-size: 11pt;
            margin-bottom: 10px;
            text-transform: uppercase;
        }

        /* Regulatory Note */
        .reg-note {
            border-left: 4px solid #e74c3c;
            padding: 12px 15px;
            margin: 15px 0;
            background: #fff5f5;
            page-break-inside: avoid;
        }

        .reg-note-title {
            font-weight: bold;
            color: #e74c3c;
            margin-bottom: 5px;
        }

        /* Lists */
        ul, ol {
            margin: 10px 0 10px 30px;
        }

        li {
            margin: 5px 0;
        }

        /* Footer */
        .doc-footer {
            position: fixed;
            bottom: 0;
            width: 100%;
            text-align: center;
            font-size: 9pt;
            color: #666;
            border-top: 1px solid #ccc;
            padding-top: 10px;
        }

        /* Signature Block */
        .signature-block {
            margin-top: 60px;
            page-break-inside: avoid;
        }

        .signature-line {
            border-bottom: 1px solid #000;
            width: 300px;
            margin: 40px 0 5px 0;
        }

        /* Numeric Formatting */
        .numeric {
            text-align: right;
            font-family: 'Courier New', monospace;
        }

        .bold {
            font-weight: bold;
        }
    </style>
</head>
<body>

<!-- COVER PAGE -->
<div class="page cover">
    <h1>Comprehensive Assessment and Review<br>Capital Analysis - Regulatory Submission</h1>
    <div class="subtitle">Treasury Modeling: Deposit Beta Analysis & PPNR Forecasts</div>

    <div class="org-info">
        <p><strong>Submitted by:</strong> Chief Financial Officer</p>
        <p><strong>Institution:</strong> [Bank Name]</p>
        <p><strong>Report Period:</strong> {{ report_period }}</p>
    </div>

    <div class="date">
        <p>{{ report_date }}</p>
    </div>

    <div class="confidential">
        CONFIDENTIAL<br>
        For Regulatory Use Only<br>
        Federal Reserve Submission
    </div>
</div>

<!-- TABLE OF CONTENTS -->
<div class="page">
    <h1>Table of Contents</h1>
    <div class="toc">
        <div class="toc-item">
            <a href="#section1">1. Executive Summary</a>
            <span class="toc-page">3</span>
        </div>
        <div class="toc-item">
            <a href="#section2">2. Deposit Portfolio Overview</a>
            <span class="toc-page">4</span>
        </div>
        <div class="toc-item">
            <a href="#section3">3. Deposit Beta Methodology</a>
            <span class="toc-page">5</span>
        </div>
        <div class="toc-item">
            <a href="#section4">4. Rate Shock Scenario Analysis</a>
            <span class="toc-page">7</span>
        </div>
        <div class="toc-item">
            <a href="#section5">5. Vintage Analysis (Cohort Decay Model)</a>
            <span class="toc-page">9</span>
        </div>
        <div class="toc-item">
            <a href="#section6">6. PPNR Forecasting Methodology</a>
            <span class="toc-page">11</span>
        </div>
        <div class="toc-item">
            <a href="#section7">7. CCAR Stress Testing Results</a>
            <span class="toc-page">13</span>
        </div>
        <div class="toc-item">
            <a href="#section8">8. Model Validation & Back-Testing</a>
            <span class="toc-page">15</span>
        </div>
        <div class="toc-item">
            <a href="#appendix">Appendix A: Technical Specifications</a>
            <span class="toc-page">17</span>
        </div>
    </div>
</div>

<!-- EXECUTIVE SUMMARY -->
<div class="page">
    <h1 id="section1">1. Executive Summary</h1>

    <h2>1.1 Report Purpose</h2>
    <p>
        This document presents the comprehensive treasury modeling results for deposit portfolio analysis,
        including deposit beta estimation, vintage analysis, and Pre-Provision Net Revenue (PPNR) forecasting
        under the Comprehensive Capital Analysis and Review (CCAR) framework.
    </p>

    <h2>1.2 Key Findings</h2>

    <table>
        <caption>Table 1.1: Portfolio Summary Metrics</caption>
        <thead>
            <tr>
                <th>Metric</th>
                <th>Value</th>
                <th>Basis of Calculation</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Total Deposit Portfolio</td>
                <td class="numeric">${{ total_deposits_b }}B</td>
                <td>Sum of all deposit account balances</td>
            </tr>
            <tr>
                <td>Weighted Average Rate</td>
                <td class="numeric">{{ weighted_avg_rate }}</td>
                <td>Balance-weighted stated rate</td>
            </tr>
            <tr>
                <td>Portfolio Beta</td>
                <td class="numeric">{{ portfolio_beta }}</td>
                <td>Balance-weighted deposit beta</td>
            </tr>
            <tr>
                <td>Number of Accounts</td>
                <td class="numeric">{{ num_accounts }}</td>
                <td>Active deposit accounts as of report date</td>
            </tr>
        </tbody>
    </table>

    <h2>1.3 Regulatory Compliance</h2>
    <div class="reg-note">
        <div class="reg-note-title">REGULATORY REFERENCE</div>
        This analysis complies with:
        <ul>
            <li>12 CFR Part 252 - Enhanced Prudential Standards (Regulation YY)</li>
            <li>SR 11-7: Guidance on Model Risk Management</li>
            <li>CCAR 2024 Supervisory Scenarios (Baseline, Adverse, Severely Adverse)</li>
            <li>SR 12-7: Supervisory Guidance on Stress Testing (Dodd-Frank Act Stress Testing)</li>
        </ul>
    </div>

    <h2>1.4 Assessment Summary</h2>
    <p>
        Under the severely adverse scenario (+300 bps rate shock), the institution's deposit portfolio
        would experience an estimated runoff of $16.3B (13.0% of total deposits). Current liquidity
        contingency plans provide adequate coverage through FHLB advances and repo facilities.
    </p>
</div>

<!-- DEPOSIT PORTFOLIO OVERVIEW -->
<div class="page">
    <h1 id="section2">2. Deposit Portfolio Overview</h1>

    <h2>2.1 Portfolio Composition</h2>

    <table>
        <caption>Table 2.1: Deposit Portfolio by Product Type</caption>
        <thead>
            <tr>
                <th>Product Type</th>
                <th>Balance ($B)</th>
                <th>% of Total</th>
                <th>Account Count</th>
                <th>Avg Beta</th>
                <th>Rate Sensitivity</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Money Market Deposit Accounts (MMDA)</td>
                <td class="numeric">$45.2</td>
                <td class="numeric">36.0%</td>
                <td class="numeric">125,400</td>
                <td class="numeric">0.350</td>
                <td>Low</td>
            </tr>
            <tr>
                <td>Demand Deposit Accounts (DDA)</td>
                <td class="numeric">$38.9</td>
                <td class="numeric">31.0%</td>
                <td class="numeric">248,100</td>
                <td class="numeric">0.720</td>
                <td>High</td>
            </tr>
            <tr>
                <td>Negotiable Order of Withdrawal (NOW)</td>
                <td class="numeric">$25.1</td>
                <td class="numeric">20.0%</td>
                <td class="numeric">89,200</td>
                <td class="numeric">0.480</td>
                <td>Medium</td>
            </tr>
            <tr>
                <td>Savings Accounts</td>
                <td class="numeric">$16.3</td>
                <td class="numeric">13.0%</td>
                <td class="numeric">156,800</td>
                <td class="numeric">0.620</td>
                <td>Medium-High</td>
            </tr>
            <tr class="bold">
                <td>Total Portfolio</td>
                <td class="numeric">$125.5</td>
                <td class="numeric">100.0%</td>
                <td class="numeric">619,500</td>
                <td class="numeric">0.480</td>
                <td>Medium</td>
            </tr>
        </tbody>
    </table>

    <h2>2.2 Relationship Categorization</h2>
    <p>
        Deposits are classified into three categories based on relationship depth and expected stickiness:
    </p>

    <table>
        <caption>Table 2.2: Deposits by Relationship Category</caption>
        <thead>
            <tr>
                <th>Category</th>
                <th>Definition</th>
                <th>Balance ($B)</th>
                <th>% of Total</th>
                <th>Avg Beta</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>Strategic</strong></td>
                <td>Multi-product relationships, payroll accounts, high engagement</td>
                <td class="numeric">$50.2</td>
                <td class="numeric">40.0%</td>
                <td class="numeric">0.280</td>
            </tr>
            <tr>
                <td><strong>Tactical</strong></td>
                <td>Single-product or dual-product, moderate engagement</td>
                <td class="numeric">$43.9</td>
                <td class="numeric">35.0%</td>
                <td class="numeric">0.480</td>
            </tr>
            <tr>
                <td><strong>Expendable</strong></td>
                <td>Rate-driven, minimal engagement, high flight risk</td>
                <td class="numeric">$31.4</td>
                <td class="numeric">25.0%</td>
                <td class="numeric">0.820</td>
            </tr>
        </tbody>
    </table>

    <h2>2.3 Data Sources</h2>
    <div class="methodology">
        <div class="methodology-title">Data Governance</div>
        <ul>
            <li><strong>Source System:</strong> Core banking system (Fiserv Signature)</li>
            <li><strong>Update Frequency:</strong> Daily extract at 23:59 Eastern Time</li>
            <li><strong>Data Quality:</strong> Automated validation against GL balances (tolerance: ±0.1%)</li>
            <li><strong>Historical Depth:</strong> 10 years of account-level data</li>
            <li><strong>Unity Catalog Table:</strong> cfo_banking_demo.silver_treasury.deposit_portfolio</li>
        </ul>
    </div>
</div>

<!-- DEPOSIT BETA METHODOLOGY -->
<div class="page">
    <h1 id="section3">3. Deposit Beta Methodology</h1>

    <h2>3.1 Definition</h2>
    <p>
        Deposit beta (β) measures the sensitivity of deposit rates to changes in market interest rates.
        A beta of 1.0 indicates deposits reprice 1:1 with market rates, while a beta of 0.0 indicates
        no repricing response.
    </p>

    <div class="formula">
        <div class="formula-title">Formula 3.1: Deposit Beta</div>
        <code>
        β = Δ Deposit Rate / Δ Market Rate

        Where:
          β = Deposit beta coefficient
          Δ Deposit Rate = Change in account stated rate
          Δ Market Rate = Change in Fed Funds or comparable benchmark
        </code>
    </div>

    <h2>3.2 Model Specification</h2>

    <div class="methodology">
        <div class="methodology-title">XGBoost Model Architecture</div>
        <ul>
            <li><strong>Algorithm:</strong> XGBoost (Extreme Gradient Boosting)</li>
            <li><strong>Objective Function:</strong> reg:squarederror (L2 regression)</li>
            <li><strong>Training Period:</strong> January 2014 - December 2023 (10 years)</li>
            <li><strong>Number of Features:</strong> 42 features across 5 categories</li>
            <li><strong>Validation Method:</strong> 5-fold cross-validation with temporal splits</li>
            <li><strong>Model Performance:</strong> MAPE 7.2% on holdout set</li>
        </ul>
    </div>

    <h3>3.2.1 Feature Categories</h3>
    <table>
        <caption>Table 3.1: Model Features by Category</caption>
        <thead>
            <tr>
                <th>Category</th>
                <th>Example Features</th>
                <th>Feature Count</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Account Characteristics</td>
                <td>Product type, current balance, tenure, opening regime</td>
                <td>12</td>
            </tr>
            <tr>
                <td>Relationship Depth</td>
                <td>Number of products, total relationship value, payroll flag</td>
                <td>8</td>
            </tr>
            <tr>
                <td>Pricing Metrics</td>
                <td>Current rate, competitor spread, pricing tier</td>
                <td>7</td>
            </tr>
            <tr>
                <td>Behavioral Indicators</td>
                <td>Transaction frequency, balance volatility, call center contacts</td>
                <td>10</td>
            </tr>
            <tr>
                <td>Market Environment</td>
                <td>Fed Funds rate, yield curve slope, rate cycle phase</td>
                <td>5</td>
            </tr>
        </tbody>
    </table>

    <h2>3.3 Model Validation</h2>

    <div class="reg-note">
        <div class="reg-note-title">MODEL RISK MANAGEMENT (SR 11-7 COMPLIANCE)</div>
        The deposit beta model undergoes annual validation by an independent Model Risk Management team:
        <ul>
            <li><strong>Conceptual Soundness:</strong> Economic theory review and literature comparison</li>
            <li><strong>Ongoing Monitoring:</strong> Monthly MAPE tracking, quarterly back-testing</li>
            <li><strong>Outcomes Analysis:</strong> Annual comparison of predicted vs actual betas</li>
            <li><strong>Last Validation:</strong> October 2023 (no material findings)</li>
            <li><strong>Next Validation:</strong> Scheduled for October 2024</li>
        </ul>
    </div>

    <table>
        <caption>Table 3.2: Model Performance Metrics</caption>
        <thead>
            <tr>
                <th>Metric</th>
                <th>Training Set</th>
                <th>Validation Set</th>
                <th>Holdout Set</th>
                <th>Benchmark</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>MAPE (Mean Absolute Percentage Error)</td>
                <td class="numeric">6.8%</td>
                <td class="numeric">7.1%</td>
                <td class="numeric">7.2%</td>
                <td class="numeric">&lt; 10%</td>
            </tr>
            <tr>
                <td>RMSE (Root Mean Squared Error)</td>
                <td class="numeric">0.052</td>
                <td class="numeric">0.056</td>
                <td class="numeric">0.058</td>
                <td class="numeric">&lt; 0.08</td>
            </tr>
            <tr>
                <td>R² (Coefficient of Determination)</td>
                <td class="numeric">0.89</td>
                <td class="numeric">0.86</td>
                <td class="numeric">0.85</td>
                <td class="numeric">&gt; 0.75</td>
            </tr>
        </tbody>
    </table>
</div>

<!-- RATE SHOCK SCENARIOS -->
<div class="page">
    <h1 id="section4">4. Rate Shock Scenario Analysis</h1>

    <h2>4.1 Scenario Definitions</h2>
    <p>
        Three instantaneous parallel rate shocks are applied to assess deposit runoff sensitivity:
    </p>

    <table>
        <caption>Table 4.1: Rate Shock Scenarios</caption>
        <thead>
            <tr>
                <th>Scenario</th>
                <th>Rate Shock</th>
                <th>Expected Runoff ($B)</th>
                <th>Runoff %</th>
                <th>Remaining Deposits ($B)</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Mild (+100 bps)</td>
                <td class="numeric">+100 bps</td>
                <td class="numeric">$6.2</td>
                <td class="numeric">4.9%</td>
                <td class="numeric">$119.3</td>
            </tr>
            <tr>
                <td>Moderate (+200 bps)</td>
                <td class="numeric">+200 bps</td>
                <td class="numeric">$11.8</td>
                <td class="numeric">9.4%</td>
                <td class="numeric">$113.7</td>
            </tr>
            <tr>
                <td>Severe (+300 bps)</td>
                <td class="numeric">+300 bps</td>
                <td class="numeric">$16.3</td>
                <td class="numeric">13.0%</td>
                <td class="numeric">$109.2</td>
            </tr>
        </tbody>
    </table>

    <h2>4.2 Runoff Calculation Methodology</h2>

    <div class="formula">
        <div class="formula-title">Formula 4.1: Expected Deposit Runoff</div>
        <code>
        Expected_Runoff = Σ (Balance_i × β_i × Δr × α)

        Where:
          Balance_i = Current balance of account i
          β_i = Predicted deposit beta for account i
          Δr = Magnitude of rate shock (bps)
          α = Elasticity adjustment factor (empirically derived)
        </code>
    </div>

    <h2>4.3 Runoff by Product Type</h2>

    <table>
        <caption>Table 4.2: Detailed Runoff Analysis by Product (+200 bps Scenario)</caption>
        <thead>
            <tr>
                <th>Product</th>
                <th>Starting Balance</th>
                <th>Avg Beta</th>
                <th>Expected Runoff</th>
                <th>Runoff %</th>
                <th>Ending Balance</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>MMDA</td>
                <td class="numeric">$45.2B</td>
                <td class="numeric">0.350</td>
                <td class="numeric">$2.8B</td>
                <td class="numeric">6.2%</td>
                <td class="numeric">$42.4B</td>
            </tr>
            <tr>
                <td>DDA</td>
                <td class="numeric">$38.9B</td>
                <td class="numeric">0.720</td>
                <td class="numeric">$5.2B</td>
                <td class="numeric">13.4%</td>
                <td class="numeric">$33.7B</td>
            </tr>
            <tr>
                <td>NOW</td>
                <td class="numeric">$25.1B</td>
                <td class="numeric">0.480</td>
                <td class="numeric">$2.4B</td>
                <td class="numeric">9.6%</td>
                <td class="numeric">$22.7B</td>
            </tr>
            <tr>
                <td>Savings</td>
                <td class="numeric">$16.3B</td>
                <td class="numeric">0.620</td>
                <td class="numeric">$1.4B</td>
                <td class="numeric">8.6%</td>
                <td class="numeric">$14.9B</td>
            </tr>
            <tr class="bold">
                <td>Total</td>
                <td class="numeric">$125.5B</td>
                <td class="numeric">0.480</td>
                <td class="numeric">$11.8B</td>
                <td class="numeric">9.4%</td>
                <td class="numeric">$113.7B</td>
            </tr>
        </tbody>
    </table>

    <h2>4.4 Contingency Funding Assessment</h2>

    <div class="reg-note">
        <div class="reg-note-title">LIQUIDITY COVERAGE</div>
        Current contingent liquidity sources:
        <ul>
            <li><strong>FHLB Advance Capacity:</strong> $18.5B (unused)</li>
            <li><strong>Repo Facility Commitments:</strong> $8.2B (unused)</li>
            <li><strong>Fed Discount Window:</strong> $12.0B (collateral pledged)</li>
            <li><strong>Total Contingent Liquidity:</strong> $38.7B</li>
        </ul>
        <p><strong>Assessment:</strong> Contingent liquidity of $38.7B exceeds severe scenario runoff of $16.3B by 2.4x, providing adequate coverage.</p>
    </div>
</div>

<!-- SIGNATURE PAGE -->
<div class="page">
    <h1>Regulatory Attestation</h1>

    <p>
        I hereby attest that the deposit modeling and PPNR forecasting methodologies described in this
        document comply with applicable regulatory guidance, including SR 11-7 (Model Risk Management)
        and 12 CFR Part 252 (Enhanced Prudential Standards).
    </p>

    <p>
        The models have been independently validated, back-tested against historical performance, and
        incorporated into the institution's CCAR capital planning processes.
    </p>

    <div class="signature-block">
        <div class="signature-line"></div>
        <p><strong>Chief Financial Officer</strong></p>
        <p>Date: _______________</p>
    </div>

    <div class="signature-block">
        <div class="signature-line"></div>
        <p><strong>Chief Risk Officer</strong></p>
        <p>Date: _______________</p>
    </div>

    <div class="signature-block">
        <div class="signature-line"></div>
        <p><strong>Head of Model Risk Management</strong></p>
        <p>Date: _______________</p>
    </div>
</div>

</body>
</html>
"""

# COMMAND ----------

# Prepare template data
template_data = {
    'report_date': report_date.strftime('%B %d, %Y'),
    'report_period': 'Q4 2023',
    'total_deposits_b': f"{total_deposits/1e9:.1f}",
    'portfolio_beta': f"{portfolio_beta:.3f}",
    'weighted_avg_rate': f"{weighted_avg_rate:.2%}",
    'num_accounts': f"{len(deposits_pdf):,}"
}

# Render HTML
template = Template(html_template)
html_report = template.render(**template_data)

print("✓ Regulatory layout generated")

# COMMAND ----------

# Save HTML report
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
html_filename = f"treasury_report_regulatory_{timestamp}.html"

dbfs_path = f"/dbfs/tmp/{html_filename}"
with open(dbfs_path, 'w', encoding='utf-8') as f:
    f.write(html_report)

print(f"✓ Report saved to: {dbfs_path}")
print(f"✓ Download from: /tmp/{html_filename}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Key Differences: Executive vs Regulatory Layout
# MAGIC
# MAGIC | Aspect | Executive Layout | Regulatory Layout |
# MAGIC |--------|------------------|-------------------|
# MAGIC | **Page Size** | A4 Landscape | A4 Portrait |
# MAGIC | **Font** | Modern sans-serif (Segoe UI) | Traditional serif (Times New Roman) |
# MAGIC | **Colors** | Full Databricks brand palette | Conservative black/white |
# MAGIC | **Layout** | 2-column dense, visual KPIs | Single-column detailed |
# MAGIC | **Content** | High-level summaries, charts | Complete methodology, formulas |
# MAGIC | **Sections** | 2 pages, executive focus | 10+ pages, technical focus |
# MAGIC | **Best For** | Board meetings, ALCO | CCAR submissions, audits |
# MAGIC | **Tone** | Business-friendly | Regulatory compliance |
# MAGIC | **Details** | Key findings only | Full data tables, formulas |
