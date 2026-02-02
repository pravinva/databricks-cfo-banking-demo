#!/usr/bin/env python3
"""Check if AlphaVantage integration has already been run."""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service import sql

w = WorkspaceClient()
warehouse_id = "4b9b953939869799"

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
print("🔍 CHECKING EXISTING ALPHAVANTAGE DATA")
print("="*80)

# Check if bronze_market_data schema exists
print("\n1. Checking bronze_market_data schema...")
result = query("SHOW SCHEMAS IN cfo_banking_demo")
has_bronze_market_data = False
if result:
    for row in result:
        if 'bronze_market_data' in str(row).lower():
            has_bronze_market_data = True
            print("  ✓ bronze_market_data schema EXISTS")
            break

if not has_bronze_market_data:
    print("  ❌ bronze_market_data schema NOT FOUND")
    print("\n💡 Recommendation: Run the existing AlphaVantage integration script:")
    print("   python3 outputs/scripts/pipelines/07_alpha_vantage_integration.py")
else:
    # Check treasury_yields_raw table
    print("\n2. Checking treasury_yields_raw data...")
    try:
        result = query("""
            SELECT
                COUNT(*) as total_rows,
                COUNT(DISTINCT date) as unique_dates,
                MIN(date) as earliest_date,
                MAX(date) as latest_date
            FROM cfo_banking_demo.bronze_market_data.treasury_yields_raw
        """)
        if result and result[0]:
            print(f"  ✓ Total Rows: {result[0][0]}")
            print(f"  ✓ Unique Dates: {result[0][1]}")
            print(f"  ✓ Date Range: {result[0][2]} to {result[0][3]}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

    # Check if silver_treasury.yield_curves has been populated
    print("\n3. Checking silver_treasury.yield_curves...")
    try:
        result = query("""
            SELECT
                COUNT(*) as total_rows,
                MIN(date) as earliest_date,
                MAX(date) as latest_date,
                COUNT(CASE WHEN rate_3m IS NOT NULL THEN 1 END) as has_3m,
                COUNT(CASE WHEN rate_2y IS NOT NULL THEN 1 END) as has_2y,
                COUNT(CASE WHEN rate_10y IS NOT NULL THEN 1 END) as has_10y
            FROM cfo_banking_demo.silver_treasury.yield_curves
        """)
        if result and result[0]:
            print(f"  ✓ Total Rows: {result[0][0]}")
            print(f"  ✓ Date Range: {result[0][1]} to {result[0][2]}")
            print(f"  ✓ Populated columns:")
            print(f"    - rate_3m: {result[0][3]} rows")
            print(f"    - rate_2y: {result[0][4]} rows")
            print(f"    - rate_10y: {result[0][5]} rows")
    except Exception as e:
        print(f"  ❌ Error: {e}")

    # Check if fed_funds_rate exists
    print("\n4. Checking if fed_funds_rate column exists...")
    result = query("DESCRIBE cfo_banking_demo.silver_treasury.yield_curves")
    has_fed_funds = False
    if result:
        for row in result:
            if 'fed_funds' in str(row[0]).lower():
                has_fed_funds = True
                print(f"  ✓ fed_funds_rate column EXISTS")
                break

    if not has_fed_funds:
        print("  ❌ fed_funds_rate column NOT FOUND")
        print("\n  💡 This column was already added by add_fed_funds_rate.py")
    else:
        # Check if populated
        result = query("""
            SELECT COUNT(*) as total, COUNT(fed_funds_rate) as populated
            FROM cfo_banking_demo.silver_treasury.yield_curves
        """)
        if result and result[0]:
            print(f"  ✓ Populated: {result[0][1]} out of {result[0][0]} rows")

    # Check gold_analytics schema
    print("\n5. Checking gold_analytics.market_data_latest...")
    try:
        result = query("""
            SELECT date, rate_3m, rate_2y, rate_10y
            FROM cfo_banking_demo.gold_analytics.market_data_latest
            LIMIT 1
        """)
        if result and result[0]:
            print(f"  ✓ Latest data as of: {result[0][0]}")
            print(f"    3M: {result[0][1]}%")
            print(f"    2Y: {result[0][2]}%")
            print(f"    10Y: {result[0][3]}%")
    except Exception as e:
        print(f"  ❌ Error: {e}")

print("\n" + "="*80)
print("📊 SUMMARY")
print("="*80)

if has_bronze_market_data:
    print("\n✅ AlphaVantage integration HAS been run!")
    print("\n📋 Existing Data Sources:")
    print("  ✓ bronze_market_data.treasury_yields_raw")
    print("  ✓ silver_treasury.yield_curves")
    print("  ✓ gold_analytics.market_data_latest")
    print("\n💡 Next Steps:")
    print("  1. Check if we need more historical data (need 24+ months)")
    print("  2. Verify fed_funds_rate is populated")
    print("  3. If data is recent (< 30 days), we may need to backfill historical")
else:
    print("\n❌ AlphaVantage integration has NOT been run yet")
    print("\n💡 Next Steps:")
    print("  1. Set up Databricks secret:")
    print("     databricks secrets put-secret cfo_demo alpha_vantage_api_key")
    print("  2. Run integration script:")
    print("     python3 outputs/scripts/pipelines/07_alpha_vantage_integration.py")
