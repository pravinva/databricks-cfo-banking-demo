#!/usr/bin/env python3
"""
Analyze schema gaps for deposit beta modeling.
Determine what columns exist vs what notebooks expect.
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service import sql

w = WorkspaceClient()
warehouse_id = "8baced1ff014912d"

def query(sql_text):
    response = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql_text,
        catalog="cfo_banking_demo",
        wait_timeout="50s"
    )
    if response.status.state == sql.StatementState.SUCCEEDED:
        return response.result.data_array if response.result else []
    return None

print("\n" + "="*80)
print("📊 DEPOSIT ACCOUNTS SCHEMA")
print("="*80)

result = query("DESCRIBE cfo_banking_demo.bronze_core_banking.deposit_accounts")
if result:
    print("\nActual columns in deposit_accounts:")
    for row in result:
        print(f"  - {row[0]}: {row[1]}")

print("\n" + "="*80)
print("📈 YIELD CURVES SCHEMA")
print("="*80)

result = query("DESCRIBE cfo_banking_demo.silver_treasury.yield_curves")
if result:
    print("\nActual columns in yield_curves:")
    for row in result:
        print(f"  - {row[0]}: {row[1]}")

print("\n" + "="*80)
print("💰 GENERAL LEDGER SCHEMA")
print("="*80)

result = query("DESCRIBE cfo_banking_demo.silver_finance.general_ledger")
if result:
    print("\nActual columns in general_ledger:")
    for row in result:
        print(f"  - {row[0]}: {row[1]}")

print("\n" + "="*80)
print("🔍 SAMPLE DATA ANALYSIS")
print("="*80)

# Get sample deposit account
result = query("""
    SELECT *
    FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
    WHERE is_current = true
    LIMIT 1
""")
if result:
    print("\nSample deposit account row:")
    print(result[0])

# Get yield curve sample
result = query("""
    SELECT *
    FROM cfo_banking_demo.silver_treasury.yield_curves
    ORDER BY date DESC
    LIMIT 3
""")
if result:
    print("\nRecent yield curves (last 3 days):")
    for row in result:
        print(f"  {row}")

print("\n" + "="*80)
print("📋 DATA REQUIREMENTS SUMMARY")
print("="*80)

print("""
CRITICAL FINDINGS:

1. YIELD CURVES TABLE
   ✓ EXISTS: rate_3m, rate_2y, rate_5y, rate_10y, rate_30y
   ❌ MISSING: fed_funds_rate, treasury_3m, treasury_2y, treasury_10y
   📅 DATE RANGE: 2025-12-12 to 2026-01-22 (only 27 days!)

   ISSUE: Notebooks expect fed_funds_rate for rate regime classification
   ISSUE: Only 27 days of data - need 24+ months for model training

2. DEPOSIT ACCOUNTS TABLE
   ❌ MISSING RELATIONSHIP FEATURES:
     - product_count (how many products customer has)
     - relationship_length_years
     - relationship_score
     - relationship_category (Strategic/Tactical/Expendable)
     - primary_bank_flag
     - direct_deposit_flag
     - cross_sell_online, cross_sell_mobile, cross_sell_autopay

   ❌ MISSING COMPETITIVE FEATURES:
     - competitor_avg_rate
     - online_bank_avg_rate
     - market_rate_spread
     - competitor_rate_spread

   ❌ MISSING MARKET REGIME FEATURES:
     - rate_regime (low/medium/high)
     - rate_change_velocity_3m
     - yield_curve_slope
     - yield_curve_inverted

3. GENERAL LEDGER TABLE
   ❌ Schema mismatch: column 'account_number' vs 'account_num'

RECOMMENDATIONS:

A. IMMEDIATE FIXES (Schema Changes):
   1. Add alias columns to deposit_accounts or compute them in notebooks
   2. Rename general_ledger.account_num -> account_number OR update notebooks

B. DATA ENRICHMENT NEEDED:
   1. Yield Curves:
      - Add fed_funds_rate column (can derive from rate_3m or fetch from AlphaVantage)
      - Backfill 24+ months of historical data

   2. Competitive Rates:
      - Add competitor_avg_rate (hardcode or fetch from RateWatch API)
      - Add online_bank_avg_rate (hardcode or fetch from DepositAccounts.com)

   3. Customer Relationships:
      - Compute product_count from existing data
      - Compute relationship_length_years from first_account_date
      - Derive other relationship features

C. ALPHAVANTAGE API REQUIREMENTS:
   YES - Use AlphaVantage for:
   - Fed Funds Rate (FRED API: DFF)
   - Treasury yields backfill (TREASURY_YIELD endpoint)
   - Real-time updates for stress testing

   AlphaVantage URLs:
   - Fed Funds: https://www.alphavantage.co/query?function=FEDERAL_FUNDS_RATE&apikey=YOUR_KEY
   - 3M Treasury: https://www.alphavantage.co/query?function=TREASURY_YIELD&interval=daily&maturity=3month&apikey=YOUR_KEY

D. TABLE CREATION:
   NO - Don't need to create new tables beyond what notebooks already create
   YES - Need to populate/enrich existing tables with missing columns
""")
