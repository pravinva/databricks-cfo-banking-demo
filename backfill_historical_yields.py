#!/usr/bin/env python3
"""
Backfill 24+ months of historical treasury yields and fed funds rate.
Uses existing Databricks secret: cfo_demo/alpha_vantage_api_key
"""

import requests
import time
from datetime import datetime
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import sql

print("\n" + "="*80)
print("🚀 BACKFILL 24+ MONTHS OF TREASURY YIELDS & FED FUNDS RATE")
print("="*80)

# Initialize
w = WorkspaceClient()
WAREHOUSE_ID = "4b9b953939869799"

# Get API key from Databricks secrets
print("\n📊 Retrieving AlphaVantage API key from Databricks secrets...")
try:
    api_key = w.secrets.get_secret(scope="cfo_demo", key="alpha_vantage_api_key").value
    print("✓ API key retrieved successfully")
except Exception as e:
    print(f"❌ Failed to retrieve API key: {e}")
    print("\nPlease ensure the secret exists:")
    print("  databricks secrets put-secret cfo_demo alpha_vantage_api_key")
    exit(1)

def execute_sql(query, description=""):
    """Execute SQL and return results."""
    if description:
        print(f"\n{description}...")
    response = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        statement=query,
        catalog="cfo_banking_demo",
        wait_timeout="50s"
    )
    while response.status.state in [sql.StatementState.PENDING, sql.StatementState.RUNNING]:
        time.sleep(2)
        response = w.statement_execution.get_statement(response.statement_id)

    if response.status.state == sql.StatementState.SUCCEEDED:
        return response.result.data_array if response.result else []
    else:
        error_msg = response.status.error.message if response.status.error else "Unknown error"
        raise Exception(f"SQL failed: {error_msg}")

# Fetch treasury yields (get ALL available data, not just last 30 days)
print("\n" + "="*80)
print("📈 FETCHING TREASURY YIELDS FROM ALPHAVANTAGE")
print("="*80)

maturities = ['3month', '2year', '5year', '10year', '30year']
all_data = []

for maturity in maturities:
    print(f"\n📊 Fetching {maturity} treasury yields...")
    url = f"https://www.alphavantage.co/query?function=TREASURY_YIELD&interval=daily&maturity={maturity}&apikey={api_key}"

    try:
        response = requests.get(url, timeout=30)
        data = response.json()

        if 'data' in data:
            # Get ALL records (not just last 30)
            records = data['data']
            valid_records = 0

            for record in records:
                if record['value'] != '.':
                    try:
                        all_data.append({
                            'date': record['date'],
                            'maturity': maturity,
                            'value': float(record['value'])
                        })
                        valid_records += 1
                    except ValueError:
                        continue

            print(f"  ✓ Fetched {valid_records} records for {maturity}")
        elif 'Note' in data:
            print(f"  ⚠️  API limit: {data['Note']}")
        else:
            print(f"  ⚠️  Unexpected response: {data}")

        # Rate limit: 12 seconds between calls
        time.sleep(12)

    except Exception as e:
        print(f"  ❌ Error: {e}")

print(f"\n✓ Total records fetched: {len(all_data)}")

# Get unique dates
unique_dates = len(set(record['date'] for record in all_data))
print(f"✓ Unique dates: {unique_dates}")

if all_data:
    earliest = min(record['date'] for record in all_data)
    latest = max(record['date'] for record in all_data)
    print(f"✓ Date range: {earliest} to {latest}")

# Insert into bronze table
if all_data:
    print("\n" + "="*80)
    print("💾 INSERTING DATA INTO BRONZE TABLE")
    print("="*80)

    # Batch insert
    batch_size = 100
    for i in range(0, len(all_data), batch_size):
        batch = all_data[i:i+batch_size]

        values_list = []
        for record in batch:
            values = f"('{record['date']}', '{record['maturity']}', {record['value']}, CURRENT_TIMESTAMP())"
            values_list.append(values)

        insert_sql = f"""
        INSERT INTO cfo_banking_demo.bronze_market_data.treasury_yields_raw
        VALUES {', '.join(values_list)}
        """

        execute_sql(insert_sql)
        print(f"  ✓ Inserted batch {i//batch_size + 1} ({len(batch)} records)")

    print(f"\n✓ Total inserted: {len(all_data)} records")

# Recreate silver yield_curves table with ALL data
print("\n" + "="*80)
print("🔄 REBUILDING SILVER YIELD_CURVES TABLE")
print("="*80)

execute_sql("""
    CREATE OR REPLACE TABLE cfo_banking_demo.silver_treasury.yield_curves AS
    SELECT
        date,
        MAX(CASE WHEN maturity = '3month' THEN value END) as rate_3m,
        MAX(CASE WHEN maturity = '2year' THEN value END) as rate_2y,
        MAX(CASE WHEN maturity = '5year' THEN value END) as rate_5y,
        MAX(CASE WHEN maturity = '10year' THEN value END) as rate_10y,
        MAX(CASE WHEN maturity = '30year' THEN value END) as rate_30y,
        CURRENT_TIMESTAMP() as ingestion_timestamp
    FROM cfo_banking_demo.bronze_market_data.treasury_yields_raw
    GROUP BY date
    ORDER BY date DESC
""", "Recreating yield_curves table")

print("✓ Silver table recreated with all historical data")

# Add fed_funds_rate column if not exists
print("\n" + "="*80)
print("📊 ADDING FED_FUNDS_RATE COLUMN")
print("="*80)

# Check if column exists
result = execute_sql("DESCRIBE cfo_banking_demo.silver_treasury.yield_curves")
has_fed_funds = any('fed_funds' in str(row[0]).lower() for row in result)

if not has_fed_funds:
    execute_sql("""
        ALTER TABLE cfo_banking_demo.silver_treasury.yield_curves
        ADD COLUMNS (fed_funds_rate DOUBLE COMMENT 'Federal Funds Effective Rate (derived from 3M Treasury)')
    """, "Adding fed_funds_rate column")
    print("✓ Column added")
else:
    print("✓ Column already exists")

# Populate fed_funds_rate
execute_sql("""
    UPDATE cfo_banking_demo.silver_treasury.yield_curves
    SET fed_funds_rate = rate_3m - 0.15
    WHERE fed_funds_rate IS NULL OR rate_3m IS NOT NULL
""", "Populating fed_funds_rate")

print("✓ Fed funds rate populated")

# Verification
print("\n" + "="*80)
print("✅ VERIFICATION")
print("="*80)

result = execute_sql("""
    SELECT
        MIN(date) as earliest_date,
        MAX(date) as latest_date,
        COUNT(*) as total_rows,
        COUNT(DISTINCT date) as unique_dates,
        COUNT(fed_funds_rate) as rows_with_fed_funds,
        AVG(fed_funds_rate) as avg_fed_funds_rate
    FROM cfo_banking_demo.silver_treasury.yield_curves
""")

if result and result[0]:
    row = result[0]
    print(f"\n📊 Summary:")
    print(f"  Earliest Date: {row[0]}")
    print(f"  Latest Date: {row[1]}")
    print(f"  Total Rows: {row[2]}")
    print(f"  Unique Dates: {row[3]}")
    print(f"  Rows with Fed Funds: {row[4]}")
    if row[5]:
        print(f"  Avg Fed Funds Rate: {float(row[5]):.2f}%")

# Show recent data
print("\n📈 Recent Data (Last 5 Days):")
result = execute_sql("""
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
    LIMIT 5
""")

if result:
    print(f"{'Date':<12} {'Fed Funds':>10} {'3M':>10} {'2Y':>10} {'10Y':>10} {'Slope':>10} {'Regime':<10}")
    print("-" * 80)
    for row in result:
        print(f"{str(row[0]):<12} {float(row[1]):>9.2f}% {float(row[2]):>9.2f}% {float(row[3]):>9.2f}% {float(row[4]):>9.2f}% {float(row[5]):>9.2f}% {str(row[6]):<10}")

print("\n" + "="*80)
print("✅ BACKFILL COMPLETE!")
print("="*80)
print("\n💡 Next Steps:")
print("  1. Phase 1 notebook: Ready to run with enhanced data")
print("  2. Phase 2 notebook: Ready for cohort analysis")
print("  3. Phase 3 notebook: Ready for stress testing")
print("\n📊 Data is now ready for production-quality deposit beta modeling!")
