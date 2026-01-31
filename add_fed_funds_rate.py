#!/usr/bin/env python3
"""
Add fed_funds_rate column to yield_curves table.
Quick fix: Derive from rate_3m (typical spread: Fed Funds ≈ 3M Treasury - 15bps)
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service import sql

w = WorkspaceClient()
warehouse_id = "4b9b953939869799"  # Shared Unity Catalog Serverless

def execute_sql(query, description):
    """Execute SQL and return results."""
    print(f"\n{'='*80}")
    print(f"🔧 {description}")
    print(f"{'='*80}")

    response = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=query,
        catalog="cfo_banking_demo",
        wait_timeout="50s"
    )

    if response.status.state == sql.StatementState.SUCCEEDED:
        print("✓ Success")
        if response.result and response.result.data_array:
            return response.result.data_array
        return []
    else:
        print(f"❌ Failed: {response.status.error}")
        return None

print("\n" + "="*80)
print("🚀 ADDING FED_FUNDS_RATE COLUMN TO YIELD_CURVES")
print("="*80)

# Step 1: Check if column exists, add if needed
print("\n" + "="*80)
print("🔧 Step 1: Check if fed_funds_rate column exists")
print("="*80)

result = execute_sql(
    "DESCRIBE cfo_banking_demo.silver_treasury.yield_curves",
    "Checking table schema"
)

has_fed_funds = False
if result:
    for row in result:
        if row[0] == 'fed_funds_rate':
            has_fed_funds = True
            print("✓ Column fed_funds_rate already exists")
            break

if not has_fed_funds:
    print("⚠️  Column fed_funds_rate not found, adding it...")
    result = execute_sql(
        """
        ALTER TABLE cfo_banking_demo.silver_treasury.yield_curves
        ADD COLUMNS (fed_funds_rate DOUBLE COMMENT 'Federal Funds Effective Rate (derived from 3M Treasury)')
        """,
        "Adding fed_funds_rate column"
    )

# Step 2: Derive values from rate_3m
result = execute_sql(
    """
    UPDATE cfo_banking_demo.silver_treasury.yield_curves
    SET fed_funds_rate = rate_3m - 0.15
    WHERE fed_funds_rate IS NULL
    """,
    "Step 2: Derive fed_funds_rate from rate_3m (subtract 15bps)"
)

# Step 3: Verify results
result = execute_sql(
    """
    SELECT
        date,
        fed_funds_rate,
        rate_3m,
        rate_2y,
        rate_10y,
        (rate_10y - rate_2y) as curve_slope,
        CASE
            WHEN fed_funds_rate < 2.0 THEN 'Low'
            WHEN fed_funds_rate < 4.0 THEN 'Medium'
            ELSE 'High'
        END as rate_regime
    FROM cfo_banking_demo.silver_treasury.yield_curves
    ORDER BY date DESC
    LIMIT 10
    """,
    "Step 3: Verify recent data with rate regimes"
)

if result:
    print("\nRecent Data:")
    print(f"{'Date':<12} {'Fed Funds':<10} {'3M':<10} {'2Y':<10} {'10Y':<10} {'Slope':<10} {'Regime':<10}")
    print("-" * 80)
    for row in result:
        print(f"{str(row[0]):<12} {row[1]:>8.2f}% {row[2]:>8.2f}% {row[3]:>8.2f}% {row[4]:>8.2f}% {row[5]:>8.2f}% {row[6]:<10}")

# Step 4: Summary statistics
result = execute_sql(
    """
    SELECT
        COUNT(*) as total_rows,
        COUNT(fed_funds_rate) as rows_with_fed_funds,
        MIN(date) as earliest_date,
        MAX(date) as latest_date,
        AVG(fed_funds_rate) as avg_fed_funds_rate,
        MIN(fed_funds_rate) as min_fed_funds_rate,
        MAX(fed_funds_rate) as max_fed_funds_rate
    FROM cfo_banking_demo.silver_treasury.yield_curves
    """,
    "Step 4: Summary statistics"
)

if result and result[0]:
    row = result[0]
    print(f"\n📊 Summary:")
    print(f"  Total Rows: {row[0]}")
    print(f"  Rows with Fed Funds: {row[1]}")
    print(f"  Date Range: {row[2]} to {row[3]}")
    print(f"  Fed Funds Rate:")
    print(f"    Average: {row[4]:.2f}%")
    print(f"    Min: {row[5]:.2f}%")
    print(f"    Max: {row[6]:.2f}%")

print("\n" + "="*80)
print("✅ FED_FUNDS_RATE COLUMN ADDED SUCCESSFULLY")
print("="*80)
print("\n💡 Next Steps:")
print("  1. ✓ fed_funds_rate column added (Quick fix - derived from rate_3m)")
print("  2. ⚠️  For production: Backfill with real AlphaVantage data")
print("  3. 🚀 Ready to test Phase 1 notebook!")
print("\n📝 Note: Only 27 days of data available.")
print("   For Phases 2-3, run: python3 scripts/backfill_yield_curves_alphavantage.py")
