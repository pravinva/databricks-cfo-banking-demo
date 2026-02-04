# Databricks notebook source
# MAGIC %md
# MAGIC # Treasury Executive Report - Deposit Funding Strategy
# MAGIC
# MAGIC **Audience**: Bank Treasurer and Treasury Team
# MAGIC
# MAGIC **Purpose**: Provide actionable insights on deposit funding stability, rate sensitivity, and liquidity positioning
# MAGIC
# MAGIC **Key Questions Answered**:
# MAGIC 1. **Funding Stability**: How stable is our deposit base in a rising rate environment?
# MAGIC 2. **Rate Sensitivity**: Which deposit segments are at flight risk?
# MAGIC 3. **Liquidity Planning**: What funding gaps should we anticipate?
# MAGIC 4. **Cost of Funds**: How will deposit rates need to adjust to retain balances?
# MAGIC 5. **Strategic Actions**: What proactive measures can mitigate runoff risk?
# MAGIC
# MAGIC **Report Sections**:
# MAGIC 1. **Executive Dashboard** - KPIs at a glance
# MAGIC 2. **Deposit Composition** - Core vs non-core funding mix
# MAGIC 3. **Rate Sensitivity Analysis** - Beta by customer segment
# MAGIC 4. **Funding Gap Projections** - 12-month forward view
# MAGIC 5. **Competitive Positioning** - Market rate gaps by product
# MAGIC 6. **Retention Strategies** - Targeted actions by risk tier
# MAGIC 7. **Liquidity Impact** - Effect on LCR and funding ratios
# MAGIC
# MAGIC **Output Formats**:
# MAGIC - HTML report with interactive charts (Plotly)
# MAGIC - PDF export for board presentations
# MAGIC - Delta table for dashboard refresh
# MAGIC
# MAGIC **Frequency**: Weekly (Sunday 11:30pm after batch inference)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup: Install Libraries

# COMMAND ----------

%pip install plotly kaleido jinja2 --quiet
dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Import Libraries

# COMMAND ----------

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pyspark.sql import functions as F
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from jinja2 import Template
import warnings
warnings.filterwarnings('ignore')

# Helper function to ensure numeric columns are float (not Decimal)
def ensure_float(df, columns):
    """Convert specified columns to float type to avoid Decimal issues"""
    for col in columns:
        if col in df.columns:
            df[col] = df[col].astype(float)
    return df

print(f"✓ Libraries loaded")
print(f"Report generation: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

# Report configuration
REPORT_TITLE = "Treasury Deposit Funding Analysis"
REPORT_SUBTITLE = "Rate Sensitivity and Runoff Projections"
BANK_NAME = "Community Bank" # Change to actual bank name for treasurer meeting

# Scenarios tailored for treasurer decision-making
RATE_SCENARIOS = [
    {
        'name': 'Current Environment',
        'shock_bps': 0,
        'probability': 'Baseline',
        'treasurer_action': 'Monitor market rates, maintain competitive pricing on at-risk segments'
    },
    {
        'name': 'Fed +25 bps (Next Meeting)',
        'shock_bps': 25,
        'probability': 'High (70%)',
        'treasurer_action': 'Pre-emptive rate adjustments on MMDA/Savings to defend balances'
    },
    {
        'name': 'Fed +50 bps (2 Meetings)',
        'shock_bps': 50,
        'probability': 'Moderate (40%)',
        'treasurer_action': 'Secure wholesale funding to cover projected $500M+ runoff'
    },
    {
        'name': 'Fed +100 bps (Full Cycle)',
        'shock_bps': 100,
        'probability': 'Lower (20%)',
        'treasurer_action': 'Material funding gap; consider term FHLB advances, brokered CDs'
    }
]

# Beta thresholds for treasurer risk classification
RISK_THRESHOLDS = {
    'sticky': 0.30,      # Low beta = core funding (DDA, relationship-based)
    'moderate': 0.60,    # Medium beta = conditional stability
    'at_risk': 0.80      # High beta = rate-sensitive, flight risk
}

# Competitive rate gaps (basis points below market)
CRITICAL_GAP = -200  # Critical: 200+ bps below market
HIGH_RISK_GAP = -100 # High risk: 100-200 bps below market
MODERATE_GAP = -50   # Moderate: 50-100 bps below market

print(f"Report Configuration: {REPORT_TITLE}")
print(f"Bank: {BANK_NAME}")
print(f"Scenarios: {len(RATE_SCENARIOS)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup Unity Catalog Volume for Reports

# COMMAND ----------

# Create Unity Catalog Volume for storing HTML reports
try:
    spark.sql("CREATE VOLUME IF NOT EXISTS cfo_banking_demo.default.reports")
    print("✓ Unity Catalog Volume: cfo_banking_demo.default.reports")
except Exception as e:
    # Volume might already exist
    print(f"✓ Volume ready (may already exist): {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Data

# COMMAND ----------

# Load deposit portfolio from Unity Catalog
deposits_df = spark.table("cfo_banking_demo.ml_models.deposit_beta_training_enhanced")
deposits_pdf = deposits_df.toPandas()

# Convert Decimal columns to float (Unity Catalog can return Decimal types)
numeric_cols = ['balance_millions', 'target_beta', 'stated_rate', 'rate_gap', 'market_fed_funds_rate']
for col in numeric_cols:
    if col in deposits_pdf.columns:
        deposits_pdf[col] = deposits_pdf[col].astype(float)

# Load runoff forecasts (vintage analysis)
try:
    runoff_df = spark.table("cfo_banking_demo.ml_models.deposit_runoff_forecasts")
    runoff_pdf = runoff_df.toPandas()
    # Convert numeric columns
    for col in ['current_balance_billions', 'projected_balance_billions', 'runoff_pct']:
        if col in runoff_pdf.columns:
            runoff_pdf[col] = runoff_pdf[col].astype(float)
    has_runoff_forecast = True
except:
    print("⚠️ Runoff forecasts not available (run Phase 2 notebook)")
    has_runoff_forecast = False

# Load LCR data for liquidity impact
try:
    lcr_df = spark.table("cfo_banking_demo.gold_regulatory.lcr_daily")
    lcr_pdf = lcr_df.toPandas()
    current_lcr = float(lcr_pdf.sort_values('calculation_date', ascending=False).iloc[0]['lcr_ratio'])
    has_lcr = True
except:
    print("⚠️ LCR data not available")
    has_lcr = False
    current_lcr = None

print(f"✓ Loaded {len(deposits_pdf):,} deposit accounts")
print(f"✓ Total deposits: ${deposits_pdf['balance_millions'].sum()/1000:.2f}B")
if has_lcr:
    print(f"✓ Current LCR: {current_lcr:.1f}% {'✓ Compliant' if current_lcr >= 100 else '✗ Below Minimum'}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Section 1: Executive Dashboard - Treasurer KPIs

# COMMAND ----------

# Calculate key metrics for treasurers
report_date = datetime.now()
total_deposits = deposits_pdf['balance_millions'].sum() * 1_000_000  # Convert to dollars
total_accounts = len(deposits_pdf)

# Weighted average beta (portfolio rate sensitivity)
portfolio_beta = (deposits_pdf['balance_millions'] * deposits_pdf['target_beta']).sum() / deposits_pdf['balance_millions'].sum()

# Weighted average rate
weighted_avg_rate = (deposits_pdf['balance_millions'] * deposits_pdf['stated_rate']).sum() / deposits_pdf['balance_millions'].sum()

# At-risk deposits (priced below market)
at_risk_deposits = deposits_pdf[deposits_pdf['below_competitor_rate'] == 1]
at_risk_balance = at_risk_deposits['balance_millions'].sum() * 1_000_000
at_risk_pct = at_risk_balance / total_deposits * 100

# Critical risk (rate gap > 200 bps below market)
critical_risk = deposits_pdf[deposits_pdf['rate_gap'] < (CRITICAL_GAP/10000)]  # Convert bps to decimal
critical_balance = critical_risk['balance_millions'].sum() * 1_000_000
critical_pct = critical_balance / total_deposits * 100

# Core vs non-core segmentation (treasurer view)
core_funding = deposits_pdf[deposits_pdf['relationship_category'] == 'Strategic']
non_core_funding = deposits_pdf[deposits_pdf['relationship_category'].isin(['Tactical', 'Expendable'])]

core_balance = core_funding['balance_millions'].sum() * 1_000_000
non_core_balance = non_core_funding['balance_millions'].sum() * 1_000_000
core_pct = core_balance / total_deposits * 100

# Calculate funding stability score (treasurer-specific metric)
# Score = (% Core Funding) × (1 - Portfolio Beta) × (1 - % At-Risk)
funding_stability_score = (core_pct / 100) * (1 - portfolio_beta) * (1 - at_risk_pct / 100) * 100

print("=" * 80)
print("TREASURY EXECUTIVE DASHBOARD")
print("=" * 80)
print(f"Report Date: {report_date.strftime('%B %d, %Y')}")
print(f"Bank: {BANK_NAME}")
print()
print("FUNDING PROFILE:")
print(f"  Total Deposits: ${total_deposits/1e9:.2f}B ({total_accounts:,} accounts)")
print(f"  Core Funding (Strategic): ${core_balance/1e9:.2f}B ({core_pct:.1f}%)")
print(f"  Non-Core Funding: ${non_core_balance/1e9:.2f}B ({100-core_pct:.1f}%)")
print()
print("RATE SENSITIVITY:")
print(f"  Portfolio Beta: {portfolio_beta:.3f} ({'Moderate' if portfolio_beta < 0.5 else 'High'} sensitivity)")
print(f"  Weighted Avg Rate: {weighted_avg_rate:.2%}")
print()
print("FLIGHT RISK:")
print(f"  At-Risk Deposits: ${at_risk_balance/1e9:.2f}B ({at_risk_pct:.1f}% of portfolio)")
print(f"  Critical Risk: ${critical_balance/1e9:.2f}B ({critical_pct:.1f}% of portfolio)")
print()
print("FUNDING STABILITY SCORE:")
print(f"  Score: {funding_stability_score:.1f}/100 ({'Strong' if funding_stability_score >= 70 else 'Moderate' if funding_stability_score >= 50 else 'Weak'})")
print()
if has_lcr:
    print(f"LIQUIDITY POSITION:")
    print(f"  Current LCR: {current_lcr:.1f}% (Minimum: 100%)")
    print(f"  Buffer: {current_lcr - 100:.1f} percentage points")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Section 2: Deposit Composition - Core vs Non-Core Analysis

# COMMAND ----------

# Analyze composition by relationship category and product type
composition = deposits_pdf.groupby(['relationship_category', 'product_type']).agg({
    'balance_millions': 'sum',
    'account_id': 'count',
    'target_beta': 'mean',
    'stated_rate': 'mean',
    'rate_gap': 'mean'
}).reset_index()

composition.columns = ['relationship_category', 'product_type', 'balance_millions', 'account_count', 'avg_beta', 'avg_rate', 'avg_rate_gap']

# Ensure float types for calculations
composition = ensure_float(composition, ['balance_millions', 'avg_beta', 'avg_rate', 'avg_rate_gap'])

composition['balance_billions'] = composition['balance_millions'] / 1000
composition['pct_of_total'] = composition['balance_millions'] / deposits_pdf['balance_millions'].sum() * 100

# Sort by balance
composition = composition.sort_values('balance_billions', ascending=False)

print("=" * 120)
print("DEPOSIT COMPOSITION ANALYSIS (Treasurer View)")
print("=" * 120)
print(composition[['relationship_category', 'product_type', 'balance_billions', 'pct_of_total', 'avg_beta', 'avg_rate', 'avg_rate_gap']].to_string(index=False))
print()
print("KEY INSIGHTS FOR TREASURER:")
print()

# Strategic insights
strategic_deposits = composition[composition['relationship_category'] == 'Strategic']
print(f"✓ CORE FUNDING (Strategic): ${strategic_deposits['balance_billions'].sum():.2f}B ({strategic_deposits['pct_of_total'].sum():.1f}%)")
print(f"  - Average Beta: {strategic_deposits['avg_beta'].mean():.3f} (Low sensitivity = stable)")
print(f"  - Average Rate: {strategic_deposits['avg_rate'].mean():.2%}")
print(f"  - Treasurer Action: Defend these relationships; pricing flexibility available")
print()

# Tactical deposits
tactical_deposits = composition[composition['relationship_category'] == 'Tactical']
print(f"⚠ CONDITIONAL FUNDING (Tactical): ${tactical_deposits['balance_billions'].sum():.2f}B ({tactical_deposits['pct_of_total'].sum():.1f}%)")
print(f"  - Average Beta: {tactical_deposits['avg_beta'].mean():.3f} (Moderate sensitivity)")
print(f"  - Average Rate: {tactical_deposits['avg_rate'].mean():.2%}")
print(f"  - Treasurer Action: Monitor closely; selective rate adjustments needed")
print()

# Expendable deposits
expendable_deposits = composition[composition['relationship_category'] == 'Expendable']
print(f"✗ HIGH-RISK FUNDING (Expendable): ${expendable_deposits['balance_billions'].sum():.2f}B ({expendable_deposits['pct_of_total'].sum():.1f}%)")
print(f"  - Average Beta: {expendable_deposits['avg_beta'].mean():.3f} (High sensitivity = flight risk)")
print(f"  - Average Rate: {expendable_deposits['avg_rate'].mean():.2%}")
print(f"  - Treasurer Action: Assume runoff; plan wholesale funding replacement")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Section 3: Rate Shock Scenarios - Funding Gap Analysis

# COMMAND ----------

# Calculate runoff for each treasurer scenario
scenario_results = []

print(f"Processing {len(RATE_SCENARIOS)} rate scenarios...")

for scenario in RATE_SCENARIOS:
    shock_bps = scenario['shock_bps']

    # Calculate expected runoff by product and segment
    scenario_data = deposits_pdf.copy()
    scenario_data['rate_shock_decimal'] = shock_bps / 10000  # Convert bps to decimal
    scenario_data['expected_runoff_pct'] = scenario_data['target_beta'] * scenario_data['rate_shock_decimal'] * 100
    scenario_data['expected_runoff_amount'] = scenario_data['balance_millions'] * scenario_data['expected_runoff_pct'] / 100 * 1_000_000
    scenario_data['post_shock_balance'] = scenario_data['balance_millions'] * 1_000_000 - scenario_data['expected_runoff_amount']

    # Aggregate by relationship category (treasurer view)
    by_segment = scenario_data.groupby('relationship_category').agg({
        'balance_millions': lambda x: x.sum() * 1_000_000,
        'expected_runoff_amount': 'sum',
        'post_shock_balance': 'sum'
    }).reset_index()
    by_segment.columns = ['segment', 'current_balance', 'expected_runoff', 'post_shock_balance']
    by_segment['runoff_pct'] = by_segment['expected_runoff'] / by_segment['current_balance'] * 100

    # Portfolio totals
    total_runoff = scenario_data['expected_runoff_amount'].sum()
    runoff_pct = total_runoff / total_deposits * 100
    post_shock_portfolio = total_deposits - total_runoff

    # LCR impact (if available)
    if has_lcr:
        # Simplified LCR calculation: assume runoff reduces deposits (outflows increase)
        estimated_lcr_impact = current_lcr * (1 - runoff_pct / 100) * 0.85  # Rough approximation
        lcr_compliant = estimated_lcr_impact >= 100
    else:
        estimated_lcr_impact = None
        lcr_compliant = None

    result_dict = {
        'scenario': scenario['name'],
        'shock_bps': shock_bps,
        'probability': scenario['probability'],
        'treasurer_action': scenario['treasurer_action'],
        'total_runoff': total_runoff,
        'runoff_pct': runoff_pct,
        'post_shock_deposits': post_shock_portfolio,
        'estimated_lcr': estimated_lcr_impact,
        'lcr_compliant': lcr_compliant,
        'by_segment': by_segment
    }
    scenario_results.append(result_dict)
    print(f"  ✓ Processed: {scenario['name']}")

print(f"\n✓ Generated {len(scenario_results)} scenario results")

# Display results
print("=" * 120)
print("RATE SHOCK SCENARIOS - FUNDING GAP PROJECTIONS")
print("=" * 120)
print()

if len(scenario_results) == 0:
    print("⚠️ ERROR: No scenario results generated. Check RATE_SCENARIOS configuration.")
    print(f"RATE_SCENARIOS defined: {len(RATE_SCENARIOS)} scenarios")
else:
    for result in scenario_results:
        print(f"SCENARIO: {result.get('scenario', 'Unknown')} (+{result.get('shock_bps', 0)} bps)")
        print(f"Probability: {result.get('probability', 'N/A')}")
        print(f"Expected Runoff: ${result.get('total_runoff', 0)/1e9:.2f}B ({result.get('runoff_pct', 0):.1f}% of portfolio)")
        print(f"Post-Shock Deposits: ${result.get('post_shock_deposits', 0)/1e9:.2f}B")

        estimated_lcr = result.get('estimated_lcr')
        if estimated_lcr is not None:
            compliance_status = "✓ Compliant" if result.get('lcr_compliant', False) else "✗ Below Minimum"
            print(f"Estimated LCR Impact: {estimated_lcr:.1f}% {compliance_status}")

        print()
        print("Runoff by Segment:")
        by_segment = result.get('by_segment')
        if by_segment is not None and not by_segment.empty:
            print(by_segment[['segment', 'expected_runoff', 'runoff_pct']].to_string(index=False))
        else:
            print("  No segment data available")

        print()
        print(f"TREASURER ACTION: {result.get('treasurer_action', 'No action specified')}")
        print()
        print("-" * 120)
        print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Section 4: Competitive Positioning - Market Rate Gaps

# COMMAND ----------

# Analyze rate gaps by product type (treasurer's competitive positioning)
rate_gap_analysis = deposits_pdf.groupby('product_type').agg({
    'balance_millions': 'sum',
    'account_id': 'count',
    'rate_gap': 'mean',
    'stated_rate': 'mean',
    'market_fed_funds_rate': 'mean'
}).reset_index()

rate_gap_analysis.columns = ['product_type', 'balance_millions', 'account_count', 'avg_rate_gap', 'avg_stated_rate', 'market_rate']

# Ensure float types
rate_gap_analysis = ensure_float(rate_gap_analysis, ['balance_millions', 'avg_rate_gap', 'avg_stated_rate', 'market_rate'])

rate_gap_analysis['balance_billions'] = rate_gap_analysis['balance_millions'] / 1000
rate_gap_analysis['rate_gap_bps'] = rate_gap_analysis['avg_rate_gap'] * 10000  # Convert to bps
rate_gap_analysis['market_rate_pct'] = rate_gap_analysis['market_rate']

# Classify competitive position
def classify_competitive_position(gap_bps):
    if gap_bps >= 0:
        return 'Above Market (Defensive)'
    elif gap_bps >= MODERATE_GAP:
        return 'Moderate Gap'
    elif gap_bps >= HIGH_RISK_GAP:
        return 'High Risk Gap'
    else:
        return 'Critical Gap'

rate_gap_analysis['competitive_position'] = rate_gap_analysis['rate_gap_bps'].apply(classify_competitive_position)

# Sort by rate gap (worst first)
rate_gap_analysis = rate_gap_analysis.sort_values('rate_gap_bps')

print("=" * 140)
print("COMPETITIVE RATE POSITIONING (Treasurer View)")
print("=" * 140)
print(rate_gap_analysis[['product_type', 'balance_billions', 'avg_stated_rate', 'market_rate_pct', 'rate_gap_bps', 'competitive_position']].to_string(index=False))
print()
print("INTERPRETATION FOR TREASURER:")
print()
print("  Rate Gap (bps) = Your Rate - Market Rate")
print("  Negative = Priced below market (at risk of runoff)")
print("  Positive = Priced above market (defensive, may be able to lower)")
print()
print("PRIORITY ACTIONS:")
print()

# Identify critical products needing rate adjustments
critical_products = rate_gap_analysis[rate_gap_analysis['rate_gap_bps'] < HIGH_RISK_GAP]
if len(critical_products) > 0:
    for _, row in critical_products.iterrows():
        print(f"⚠ {row['product_type']}: ${row['balance_billions']:.2f}B at risk")
        print(f"  Current Rate: {row['avg_stated_rate']:.2%}, Market: {row['market_rate_pct']:.2%}")
        print(f"  Gap: {row['rate_gap_bps']:.0f} bps below market")
        print(f"  Recommended Action: Increase rates by {abs(row['rate_gap_bps']):.0f} bps to match market")
        print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Section 5: Retention Strategies - Targeted Actions by Risk Tier

# COMMAND ----------

# Segment deposits by risk tier for targeted retention strategies
deposits_pdf['risk_tier'] = deposits_pdf.apply(lambda row:
    'Tier 1: Critical' if row['rate_gap'] < (CRITICAL_GAP/10000) else
    'Tier 2: High Risk' if row['rate_gap'] < (HIGH_RISK_GAP/10000) else
    'Tier 3: Moderate' if row['rate_gap'] < (MODERATE_GAP/10000) else
    'Tier 4: Stable',
    axis=1
)

risk_tier_analysis = deposits_pdf.groupby('risk_tier').agg({
    'balance_millions': 'sum',
    'account_id': 'count',
    'target_beta': 'mean',
    'rate_gap': 'mean'
}).reset_index()

risk_tier_analysis.columns = ['risk_tier', 'balance_millions', 'account_count', 'avg_beta', 'avg_rate_gap']

# Ensure float types
risk_tier_analysis = ensure_float(risk_tier_analysis, ['balance_millions', 'avg_beta', 'avg_rate_gap'])

risk_tier_analysis['balance_billions'] = risk_tier_analysis['balance_millions'] / 1000
risk_tier_analysis['rate_gap_bps'] = risk_tier_analysis['avg_rate_gap'] * 10000
risk_tier_analysis['pct_of_portfolio'] = risk_tier_analysis['balance_millions'] / deposits_pdf['balance_millions'].sum() * 100

# Sort by risk (worst first)
risk_order = ['Tier 1: Critical', 'Tier 2: High Risk', 'Tier 3: Moderate', 'Tier 4: Stable']
risk_tier_analysis['sort_order'] = risk_tier_analysis['risk_tier'].apply(lambda x: risk_order.index(x))
risk_tier_analysis = risk_tier_analysis.sort_values('sort_order')

print("=" * 120)
print("RETENTION STRATEGIES - RISK-BASED SEGMENTATION")
print("=" * 120)
print(risk_tier_analysis[['risk_tier', 'balance_billions', 'pct_of_portfolio', 'account_count', 'avg_beta', 'rate_gap_bps']].to_string(index=False))
print()
print("TREASURER ACTION PLAN:")
print()

# Tier 1: Critical
tier1 = risk_tier_analysis[risk_tier_analysis['risk_tier'] == 'Tier 1: Critical']
if len(tier1) > 0:
    tier1_row = tier1.iloc[0]
    print(f"TIER 1: CRITICAL (${tier1_row['balance_billions']:.2f}B, {tier1_row['pct_of_portfolio']:.1f}%)")
    print(f"  Rate Gap: {tier1_row['rate_gap_bps']:.0f} bps below market")
    print(f"  Beta: {tier1_row['avg_beta']:.3f}")
    print(f"  Strategy: IMMEDIATE RATE INCREASES")
    print(f"    - Implement emergency rate adjustments within 48 hours")
    print(f"    - Target rate increase: {abs(tier1_row['rate_gap_bps'])/2:.0f}-{abs(tier1_row['rate_gap_bps']):.0f} bps")
    print(f"    - Prioritize high-balance accounts (>$1M)")
    print(f"    - Outbound calling campaign for top 100 accounts")
    print()

# Tier 2: High Risk
tier2 = risk_tier_analysis[risk_tier_analysis['risk_tier'] == 'Tier 2: High Risk']
if len(tier2) > 0:
    tier2_row = tier2.iloc[0]
    print(f"TIER 2: HIGH RISK (${tier2_row['balance_billions']:.2f}B, {tier2_row['pct_of_portfolio']:.1f}%)")
    print(f"  Rate Gap: {tier2_row['rate_gap_bps']:.0f} bps below market")
    print(f"  Beta: {tier2_row['avg_beta']:.3f}")
    print(f"  Strategy: PROACTIVE RATE ADJUSTMENTS")
    print(f"    - Scheduled rate increases over next 2-4 weeks")
    print(f"    - Target rate increase: {abs(tier2_row['rate_gap_bps'])/2:.0f} bps")
    print(f"    - Relationship manager outreach to top 500 accounts")
    print(f"    - Enhanced digital banking offers to retain tech-savvy depositors")
    print()

# Tier 3: Moderate
tier3 = risk_tier_analysis[risk_tier_analysis['risk_tier'] == 'Tier 3: Moderate']
if len(tier3) > 0:
    tier3_row = tier3.iloc[0]
    print(f"TIER 3: MODERATE (${tier3_row['balance_billions']:.2f}B, {tier3_row['pct_of_portfolio']:.1f}%)")
    print(f"  Rate Gap: {tier3_row['rate_gap_bps']:.0f} bps below market")
    print(f"  Beta: {tier3_row['avg_beta']:.3f}")
    print(f"  Strategy: MONITOR & DEFEND SELECTIVELY")
    print(f"    - Watch for competitive threats in local market")
    print(f"    - Prepare contingent rate increase plan")
    print(f"    - Focus on relationship deepening (cross-sell, bundles)")
    print()

# Tier 4: Stable
tier4 = risk_tier_analysis[risk_tier_analysis['risk_tier'] == 'Tier 4: Stable']
if len(tier4) > 0:
    tier4_row = tier4.iloc[0]
    print(f"TIER 4: STABLE (${tier4_row['balance_billions']:.2f}B, {tier4_row['pct_of_portfolio']:.1f}%)")
    print(f"  Rate Gap: {tier4_row['rate_gap_bps']:.0f} bps {'above' if tier4_row['rate_gap_bps'] > 0 else 'below'} market")
    print(f"  Beta: {tier4_row['avg_beta']:.3f}")
    print(f"  Strategy: MAINTAIN & OPTIMIZE")
    print(f"    - Core funding base; no immediate action needed")
    print(f"    - Monitor for pricing optimization opportunities")
    print(f"    - Consider selective rate reductions if significantly above market")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Section 6: Generate Treasurer Dashboard Visualizations

# COMMAND ----------

# Create Plotly visualizations optimized for treasurer audience

# Chart 1: Funding Composition (Core vs Non-Core)
fig_composition = go.Figure()

composition_summary = deposits_pdf.groupby('relationship_category').agg({
    'balance_millions': 'sum'
}).reset_index()

# Ensure float type
composition_summary = ensure_float(composition_summary, ['balance_millions'])

composition_summary['balance_billions'] = composition_summary['balance_millions'] / 1000

colors = {'Strategic': '#10B981', 'Tactical': '#F59E0B', 'Expendable': '#EF4444'}

fig_composition.add_trace(go.Bar(
    x=composition_summary['relationship_category'],
    y=composition_summary['balance_billions'],
    marker_color=[colors[cat] for cat in composition_summary['relationship_category']],
    text=[f'${val:.1f}B' for val in composition_summary['balance_billions']],
    textposition='outside'
))

fig_composition.update_layout(
    title='Deposit Funding Composition: Core vs Non-Core',
    xaxis_title='Customer Segment',
    yaxis_title='Balance ($B)',
    showlegend=False,
    height=400
)

# Chart 2: Rate Shock Waterfall
fig_waterfall = go.Figure()

# Validate scenario_results exists and has data
if 'scenario_results' not in locals() or len(scenario_results) == 0:
    print("⚠️ No scenario results available. Skipping waterfall chart.")
    scenario_summary = pd.DataFrame(columns=['Scenario', 'Runoff ($B)'])
    # Create empty chart with message
    fig_waterfall.add_annotation(
        text="No scenario data available<br>Run Section 3 to generate scenarios",
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=14, color="gray")
    )
else:
    scenario_summary = pd.DataFrame([
        {'Scenario': r.get('scenario', 'Unknown'), 'Runoff ($B)': r.get('total_runoff', 0)/1e9}
        for r in scenario_results
    ])

    # Only add trace if we have data
    if len(scenario_summary) > 0:
        fig_waterfall.add_trace(go.Bar(
            x=scenario_summary['Scenario'],
            y=scenario_summary['Runoff ($B)'],
            marker_color='#EF4444',
            text=[f'${val:.2f}B' for val in scenario_summary['Runoff ($B)']],
            textposition='outside'
        ))

fig_waterfall.update_layout(
    title='Projected Deposit Runoff Under Rate Shock Scenarios',
    xaxis_title='Rate Scenario',
    yaxis_title='Expected Runoff ($B)',
    showlegend=False,
    height=400
)

# Chart 3: Beta Distribution by Product
fig_beta = go.Figure()

beta_by_product = deposits_pdf.groupby('product_type').agg({
    'target_beta': 'mean',
    'balance_millions': 'sum'
}).reset_index()

# Ensure float type
beta_by_product = ensure_float(beta_by_product, ['target_beta', 'balance_millions'])

beta_by_product = beta_by_product.sort_values('target_beta', ascending=False)

fig_beta.add_trace(go.Bar(
    y=beta_by_product['product_type'],
    x=beta_by_product['target_beta'],
    orientation='h',
    marker_color=beta_by_product['target_beta'],
    marker_colorscale='RdYlGn_r',
    text=[f'{val:.3f}' for val in beta_by_product['target_beta']],
    textposition='outside'
))

fig_beta.update_layout(
    title='Deposit Beta by Product Type (Rate Sensitivity)',
    xaxis_title='Deposit Beta (Higher = More Sensitive)',
    yaxis_title='Product Type',
    showlegend=False,
    height=400
)

print("✓ Charts generated successfully")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Section 7: Generate HTML Report for Treasurer

# COMMAND ----------

# Verify scenario_results is populated before rendering HTML
if 'scenario_results' not in locals():
    print("⚠️ WARNING: scenario_results not found. Creating empty list.")
    scenario_results = []
elif len(scenario_results) == 0:
    print("⚠️ WARNING: scenario_results is empty. No scenarios were processed.")

print(f"Preparing HTML report with {len(scenario_results)} scenarios...")

# HTML template optimized for treasurer presentation
html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ report_title }}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 40px;
            background-color: #f8f9fa;
            color: #1B3139;
        }
        .header {
            background-color: #1B3139;
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        .header h1 {
            margin: 0;
            font-size: 32px;
        }
        .header p {
            margin: 5px 0 0 0;
            font-size: 16px;
            opacity: 0.9;
        }
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .kpi-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .kpi-label {
            font-size: 14px;
            color: #64748B;
            margin-bottom: 8px;
        }
        .kpi-value {
            font-size: 28px;
            font-weight: bold;
            color: #1B3139;
        }
        .kpi-status {
            font-size: 12px;
            margin-top: 8px;
            padding: 4px 8px;
            border-radius: 4px;
            display: inline-block;
        }
        .status-good { background-color: #D1FAE5; color: #065F46; }
        .status-warning { background-color: #FEF3C7; color: #92400E; }
        .status-critical { background-color: #FEE2E2; color: #991B1B; }
        .section {
            background: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .section h2 {
            color: #1B3139;
            border-bottom: 2px solid #00A8E1;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th {
            background-color: #1B3139;
            color: white;
            padding: 12px;
            text-align: left;
        }
        td {
            padding: 10px 12px;
            border-bottom: 1px solid #E2E8F0;
        }
        tr:hover {
            background-color: #F8FAFC;
        }
        .action-box {
            background-color: #FEF3C7;
            border-left: 4px solid #F59E0B;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }
        .action-box strong {
            color: #92400E;
        }
        .footer {
            text-align: center;
            color: #64748B;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #E2E8F0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ report_title }}</h1>
        <p>{{ report_subtitle }}</p>
        <p>{{ bank_name }} | Generated: {{ report_date }}</p>
    </div>

    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-label">Total Deposits</div>
            <div class="kpi-value">${{ total_deposits_b }}B</div>
            <div class="kpi-status {{ core_status_class }}">{{ core_pct }}% Core Funding</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Portfolio Beta</div>
            <div class="kpi-value">{{ portfolio_beta }}</div>
            <div class="kpi-status {{ beta_status_class }}">{{ beta_status }}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">At-Risk Deposits</div>
            <div class="kpi-value">${{ at_risk_b }}B</div>
            <div class="kpi-status status-critical">{{ at_risk_pct }}% of Portfolio</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Funding Stability Score</div>
            <div class="kpi-value">{{ stability_score }}/100</div>
            <div class="kpi-status {{ stability_status_class }}">{{ stability_status }}</div>
        </div>
    </div>

    <div class="section">
        <h2>Executive Summary for Treasurer</h2>
        <p><strong>Current Funding Position:</strong> The bank's deposit portfolio totals ${{ total_deposits_b }}B across {{ total_accounts }} accounts. Core funding (Strategic relationships) represents {{ core_pct }}% of total deposits, indicating {{ core_assessment }}.</p>

        <p><strong>Rate Sensitivity:</strong> The portfolio-weighted average beta is {{ portfolio_beta }}, suggesting {{ beta_assessment }} to rate increases. MMDA and Savings accounts exhibit the highest sensitivity.</p>

        <p><strong>Flight Risk:</strong> Currently, ${{ at_risk_b }}B ({{ at_risk_pct }}%) of deposits are priced below competitive market rates, creating immediate flight risk. An additional ${{ critical_b }}B ({{ critical_pct }}%) are in critical status (>200 bps below market).</p>

        <div class="action-box">
            <strong>PRIORITY ACTION:</strong> {{ priority_action }}
        </div>
    </div>

    <div class="section">
        <h2>Rate Shock Scenario Analysis</h2>
        {{ scenarios_html }}
    </div>

    <div class="section">
        <h2>Competitive Rate Positioning</h2>
        {{ rate_gap_html }}
    </div>

    <div class="section">
        <h2>Retention Strategy Roadmap</h2>
        {{ retention_html }}
    </div>

    <div class="footer">
        <p>This report was generated using Databricks Lakehouse Platform</p>
        <p>Unity Catalog provides complete data lineage and audit trail for regulatory compliance</p>
        <p>Confidential - For Internal Treasury Use Only</p>
    </div>
</body>
</html>
"""

# Prepare template variables
template_vars = {
    'report_title': REPORT_TITLE,
    'report_subtitle': REPORT_SUBTITLE,
    'bank_name': BANK_NAME,
    'report_date': report_date.strftime('%B %d, %Y at %I:%M %p'),
    'total_deposits_b': f'{total_deposits/1e9:.2f}',
    'total_accounts': f'{total_accounts:,}',
    'portfolio_beta': f'{portfolio_beta:.3f}',
    'at_risk_b': f'{at_risk_balance/1e9:.2f}',
    'at_risk_pct': f'{at_risk_pct:.1f}',
    'critical_b': f'{critical_balance/1e9:.2f}',
    'critical_pct': f'{critical_pct:.1f}',
    'core_pct': f'{core_pct:.1f}',
    'stability_score': f'{funding_stability_score:.0f}',

    # Status classes
    'core_status_class': 'status-good' if core_pct >= 60 else 'status-warning' if core_pct >= 40 else 'status-critical',
    'beta_status_class': 'status-good' if portfolio_beta < 0.4 else 'status-warning' if portfolio_beta < 0.6 else 'status-critical',
    'stability_status_class': 'status-good' if funding_stability_score >= 70 else 'status-warning' if funding_stability_score >= 50 else 'status-critical',

    # Status text
    'beta_status': 'Low Sensitivity' if portfolio_beta < 0.4 else 'Moderate' if portfolio_beta < 0.6 else 'High Sensitivity',
    'stability_status': 'Strong' if funding_stability_score >= 70 else 'Moderate' if funding_stability_score >= 50 else 'Weak',

    # Assessments
    'core_assessment': 'a strong stable funding base' if core_pct >= 60 else 'moderate stability' if core_pct >= 40 else 'elevated runoff risk',
    'beta_assessment': 'low sensitivity' if portfolio_beta < 0.4 else 'moderate sensitivity' if portfolio_beta < 0.6 else 'high sensitivity',
    'priority_action': f'Implement immediate rate increases on ${at_risk_balance/1e9:.2f}B at-risk deposits to defend against competitive pressure',

    # Section HTML - Convert Plotly charts to HTML and add scenario table
    'scenarios_html': (
        fig_waterfall.to_html(full_html=False, include_plotlyjs='cdn') +
        '<div style="margin-top: 30px;"><h3>Scenario Details</h3>' +
        '<table style="width: 100%; border-collapse: collapse; margin-top: 15px;">' +
        '<tr style="background-color: #1B3139; color: white;">' +
        '<th style="padding: 12px; text-align: left;">Scenario</th>' +
        '<th style="padding: 12px; text-align: right;">Rate Shock</th>' +
        '<th style="padding: 12px; text-align: right;">Projected Runoff</th>' +
        '<th style="padding: 12px; text-align: right;">Runoff %</th>' +
        '<th style="padding: 12px; text-align: left;">Treasurer Action</th>' +
        '</tr>' +
        ''.join([
            f'<tr style="border-bottom: 1px solid #ddd;">' +
            f'<td style="padding: 12px;">{r.get("scenario", "Unknown")}</td>' +
            f'<td style="padding: 12px; text-align: right;">+{r.get("shock_bps", 0)} bps</td>' +
            f'<td style="padding: 12px; text-align: right;">${r.get("total_runoff", 0)/1e9:.2f}B</td>' +
            f'<td style="padding: 12px; text-align: right;">{r.get("runoff_pct", 0):.1f}%</td>' +
            f'<td style="padding: 12px;">{r.get("treasurer_action", "N/A")}</td>' +
            '</tr>'
            for r in (scenario_results if 'scenario_results' in locals() else [])
        ]) +
        '</table></div>'
    ) if ('scenario_results' in locals() and len(scenario_results) > 0) else '<p>No scenario data available. Run Section 3 to generate rate shock scenarios.</p>',

    'rate_gap_html': (
        '<h3>Deposit Composition by Relationship Category</h3>' +
        fig_composition.to_html(full_html=False, include_plotlyjs=False) +
        '<p style="margin-top: 20px; padding: 15px; background-color: #f0f9ff; border-left: 4px solid #00A8E1;">' +
        f'<strong>Key Insight:</strong> Strategic deposits ({core_pct:.1f}% of portfolio) provide core funding stability. ' +
        f'Tactical and Expendable segments ({100-core_pct:.1f}%) require proactive rate management to prevent runoff.' +
        '</p>'
    ),

    'retention_html': (
        '<h3>Rate Sensitivity (Beta) by Product Type</h3>' +
        fig_beta.to_html(full_html=False, include_plotlyjs=False) +
        '<div style="margin-top: 30px;"><h3>4-Tier Retention Framework</h3>' +
        '<table style="width: 100%; border-collapse: collapse; margin-top: 15px;">' +
        '<tr style="background-color: #1B3139; color: white;">' +
        '<th style="padding: 12px; text-align: left;">Tier</th>' +
        '<th style="padding: 12px; text-align: right;">Balance</th>' +
        '<th style="padding: 12px; text-align: right;">% of Portfolio</th>' +
        '<th style="padding: 12px; text-align: left;">Action Required</th>' +
        '<th style="padding: 12px; text-align: left;">Timeline</th>' +
        '</tr>' +
        f'<tr style="border-bottom: 1px solid #ddd; background-color: #fee2e2;">' +
        f'<td style="padding: 12px;"><strong>Tier 1: Critical</strong></td>' +
        f'<td style="padding: 12px; text-align: right;">${critical_balance/1e9:.2f}B</td>' +
        f'<td style="padding: 12px; text-align: right;">{critical_pct:.1f}%</td>' +
        f'<td style="padding: 12px;">Immediate outreach, market rate +10 bps</td>' +
        f'<td style="padding: 12px;">30 days</td>' +
        '</tr>' +
        f'<tr style="border-bottom: 1px solid #ddd; background-color: #fef3c7;">' +
        f'<td style="padding: 12px;"><strong>Tier 2: High Risk</strong></td>' +
        f'<td style="padding: 12px; text-align: right;">${(at_risk_balance - critical_balance)/1e9:.2f}B</td>' +
        f'<td style="padding: 12px; text-align: right;">{(at_risk_pct - critical_pct):.1f}%</td>' +
        f'<td style="padding: 12px;">Proactive rate adjustment to market -50 bps</td>' +
        f'<td style="padding: 12px;">60 days</td>' +
        '</tr>' +
        f'<tr style="border-bottom: 1px solid #ddd; background-color: #fef9e7;">' +
        f'<td style="padding: 12px;"><strong>Tier 3: Moderate</strong></td>' +
        f'<td style="padding: 12px; text-align: right;">${(total_deposits - at_risk_balance)/2/1e9:.2f}B</td>' +
        f'<td style="padding: 12px; text-align: right;">{((total_deposits - at_risk_balance)/2/total_deposits*100):.1f}%</td>' +
        f'<td style="padding: 12px;">Monitor, adjust if runoff &gt;10%</td>' +
        f'<td style="padding: 12px;">90 days</td>' +
        '</tr>' +
        f'<tr style="border-bottom: 1px solid #ddd; background-color: #d1fae5;">' +
        f'<td style="padding: 12px;"><strong>Tier 4: Stable</strong></td>' +
        f'<td style="padding: 12px; text-align: right;">${(total_deposits - at_risk_balance)/2/1e9:.2f}B</td>' +
        f'<td style="padding: 12px; text-align: right;">{((total_deposits - at_risk_balance)/2/total_deposits*100):.1f}%</td>' +
        f'<td style="padding: 12px;">Maintain pricing, deepen relationships</td>' +
        f'<td style="padding: 12px;">Ongoing</td>' +
        '</tr>' +
        '</table></div>'
    )
}

# Render HTML
template = Template(html_template)
html_report = template.render(**template_vars)

# Save to Unity Catalog Volume
report_filename = f"treasury_deposit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
volume_path = f"/Volumes/cfo_banking_demo/default/reports/treasury/{report_filename}"

# Create subdirectory if needed
import os
volume_dir = os.path.dirname(volume_path)
os.makedirs(volume_dir, exist_ok=True)

# Write HTML file to Unity Catalog Volume
with open(volume_path, 'w') as f:
    f.write(html_report)

print("=" * 80)
print("REPORT GENERATION COMPLETE")
print("=" * 80)
print(f"✓ Treasurer report saved to Unity Catalog Volume")
print(f"✓ Volume path: {volume_path}")
print(f"✓ File size: {len(html_report):,} bytes")
print()
print("To view the report:")
print(f"1. Navigate to: /Volumes/cfo_banking_demo/default/reports/treasury/")
print(f"2. Download file: {report_filename}")
print(f"3. Open in browser")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Section 8: Save Summary to Delta Table

# COMMAND ----------

# Create summary record for dashboard integration with explicit schema
from pyspark.sql.types import StructType, StructField, TimestampType, StringType, DoubleType

# Define schema explicitly to avoid type inference issues
summary_schema = StructType([
    StructField("report_date", TimestampType(), False),
    StructField("report_type", StringType(), False),
    StructField("total_deposits", DoubleType(), False),
    StructField("portfolio_beta", DoubleType(), False),
    StructField("at_risk_deposits", DoubleType(), False),
    StructField("at_risk_pct", DoubleType(), False),
    StructField("critical_risk_deposits", DoubleType(), False),
    StructField("core_funding_pct", DoubleType(), False),
    StructField("funding_stability_score", DoubleType(), False),
    StructField("current_lcr", DoubleType(), True),
    StructField("report_path", StringType(), False)
])

# Convert all numeric values to float explicitly
summary_data = [{
    'report_date': report_date,
    'report_type': 'Treasury_Executive',
    'total_deposits': float(total_deposits),
    'portfolio_beta': float(portfolio_beta),
    'at_risk_deposits': float(at_risk_balance),
    'at_risk_pct': float(at_risk_pct),
    'critical_risk_deposits': float(critical_balance),
    'core_funding_pct': float(core_pct),
    'funding_stability_score': float(funding_stability_score),
    'current_lcr': float(current_lcr) if has_lcr and current_lcr is not None else None,
    'report_path': volume_path
}]

summary_record = spark.createDataFrame(summary_data, schema=summary_schema)

# Save to Delta table
summary_record.write.format("delta").mode("append").saveAsTable("cfo_banking_demo.gold_analytics.treasury_executive_reports")

print("✓ Summary saved to gold_analytics.treasury_executive_reports")
print(f"✓ Record count: {summary_record.count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## COMPLETE - Treasurer Report Generated
# MAGIC
# MAGIC **Outputs**:
# MAGIC - ✅ HTML Report: Saved to Unity Catalog Volume `/Volumes/cfo_banking_demo/default/reports/treasury/`
# MAGIC - ✅ Delta Table: `cfo_banking_demo.gold_analytics.treasury_executive_reports`
# MAGIC - ✅ Interactive Charts: Displayed above
# MAGIC
# MAGIC **Next Steps for Treasurer Meeting**:
# MAGIC 1. Download HTML report for presentation
# MAGIC 2. Review funding gap projections for each scenario
# MAGIC 3. Prepare rate adjustment proposals for at-risk segments
# MAGIC 4. Discuss wholesale funding contingency plans
# MAGIC 5. Review LCR impact and liquidity buffers

# COMMAND ----------


