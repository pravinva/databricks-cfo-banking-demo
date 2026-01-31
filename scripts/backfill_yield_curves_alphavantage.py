#!/usr/bin/env python3
"""
Backfill 24 months of treasury yields and fed funds rate from AlphaVantage.

Usage:
    export ALPHAVANTAGE_API_KEY="your_key_here"
    python3 scripts/backfill_yield_curves_alphavantage.py

Requirements:
    - AlphaVantage API key (free tier: 25 calls/day)
    - Databricks workspace configured
"""

import os
import requests
import pandas as pd
from datetime import datetime
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import sql

# Configuration
ALPHAVANTAGE_KEY = os.getenv("ALPHAVANTAGE_API_KEY", "YOUR_KEY_HERE")
WAREHOUSE_ID = "4b9b953939869799"  # Shared Unity Catalog Serverless
CATALOG = "cfo_banking_demo"
SCHEMA = "silver_treasury"
TABLE = "yield_curves"

w = WorkspaceClient()

def execute_sql(query):
    """Execute SQL statement and return results."""
    response = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        statement=query,
        catalog=CATALOG,
        wait_timeout="50s"
    )
    if response.status.state == sql.StatementState.SUCCEEDED:
        return response.result.data_array if response.result else []
    else:
        raise Exception(f"Query failed: {response.status.error}")

def fetch_federal_funds_rate():
    """Fetch Federal Funds Rate from AlphaVantage FRED API."""
    print("📊 Fetching Federal Funds Rate...")
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "FEDERAL_FUNDS_RATE",
        "apikey": ALPHAVANTAGE_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "data" not in data:
        print(f"❌ API Error: {data}")
        raise ValueError(f"API Error: {data}")

    df = pd.DataFrame(data["data"])
    df["date"] = pd.to_datetime(df["date"])
    df["fed_funds_rate"] = df["value"].astype(float)
    df = df[["date", "fed_funds_rate"]]

    print(f"✓ Fetched {len(df)} days of Fed Funds data")
    print(f"  Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"  Latest rate: {df['fed_funds_rate'].iloc[0]:.2f}%")
    return df

def fetch_treasury_yield(maturity):
    """
    Fetch Treasury Yield from AlphaVantage.

    Args:
        maturity: 3month, 2year, 5year, 10year, 30year
    """
    print(f"📊 Fetching Treasury Yield: {maturity}...")
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TREASURY_YIELD",
        "interval": "daily",
        "maturity": maturity,
        "apikey": ALPHAVANTAGE_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "data" not in data:
        print(f"❌ API Error: {data}")
        raise ValueError(f"API Error: {data}")

    df = pd.DataFrame(data["data"])
    df["date"] = pd.to_datetime(df["date"])

    # Map maturity to column name
    maturity_map = {
        "3month": "rate_3m",
        "2year": "rate_2y",
        "5year": "rate_5y",
        "10year": "rate_10y",
        "30year": "rate_30y"
    }
    column_name = maturity_map[maturity]

    df[column_name] = df["value"].astype(float)
    df = df[["date", column_name]]

    print(f"✓ Fetched {len(df)} days of {maturity} Treasury data")
    print(f"  Latest rate: {df[column_name].iloc[0]:.2f}%")
    return df

def backfill_yield_curves(start_date="2024-01-01"):
    """
    Backfill yield curves from start_date to today.

    Args:
        start_date: Start date in YYYY-MM-DD format
    """
    print("\n" + "="*80)
    print("🚀 STARTING YIELD CURVE BACKFILL")
    print("="*80)
    print(f"Start Date: {start_date}")
    print(f"API Key: {ALPHAVANTAGE_KEY[:10]}..." if len(ALPHAVANTAGE_KEY) > 10 else "API Key: [NOT SET]")
    print(f"Warehouse: {WAREHOUSE_ID}")

    if ALPHAVANTAGE_KEY == "YOUR_KEY_HERE":
        print("\n❌ ERROR: AlphaVantage API key not set!")
        print("Please set environment variable:")
        print("  export ALPHAVANTAGE_API_KEY='your_key_here'")
        print("\nGet a free key at: https://www.alphavantage.co/support/#api-key")
        return

    # Fetch all data (6 API calls total)
    try:
        fed_funds = fetch_federal_funds_rate()
        yield_3m = fetch_treasury_yield("3month")
        yield_2y = fetch_treasury_yield("2year")
        yield_5y = fetch_treasury_yield("5year")
        yield_10y = fetch_treasury_yield("10year")
        yield_30y = fetch_treasury_yield("30year")
    except Exception as e:
        print(f"\n❌ Error fetching data: {str(e)}")
        return

    # Merge all data on date
    print("\n📊 Merging all yield curve data...")
    merged = fed_funds
    merged = merged.merge(yield_3m, on="date", how="outer")
    merged = merged.merge(yield_2y, on="date", how="outer")
    merged = merged.merge(yield_5y, on="date", how="outer")
    merged = merged.merge(yield_10y, on="date", how="outer")
    merged = merged.merge(yield_30y, on="date", how="outer")

    # Filter to start_date
    merged = merged[merged["date"] >= start_date]
    merged = merged.sort_values("date")

    # Add ingestion timestamp
    merged["ingestion_timestamp"] = datetime.now()

    print(f"✓ Merged {len(merged)} days of data")
    print(f"\nDate Range: {merged['date'].min().date()} to {merged['date'].max().date()}")
    print(f"\nSample data (first 3 rows):")
    print(merged.head(3).to_string())

    # Insert into Databricks using SQL
    print("\n📊 Inserting into Databricks...")

    # Prepare INSERT statements (batch insert)
    insert_values = []
    for _, row in merged.iterrows():
        values = (
            f"('{row['date'].date()}', "
            f"{row['fed_funds_rate'] if pd.notna(row['fed_funds_rate']) else 'NULL'}, "
            f"{row['rate_3m'] if pd.notna(row['rate_3m']) else 'NULL'}, "
            f"{row['rate_2y'] if pd.notna(row['rate_2y']) else 'NULL'}, "
            f"{row['rate_5y'] if pd.notna(row['rate_5y']) else 'NULL'}, "
            f"{row['rate_10y'] if pd.notna(row['rate_10y']) else 'NULL'}, "
            f"{row['rate_30y'] if pd.notna(row['rate_30y']) else 'NULL'}, "
            f"CURRENT_TIMESTAMP())"
        )
        insert_values.append(values)

    # Use MERGE to upsert (avoid duplicates)
    merge_query = f"""
    MERGE INTO {CATALOG}.{SCHEMA}.{TABLE} as target
    USING (
        SELECT * FROM VALUES
        {', '.join(insert_values)}
        AS tmp(date, fed_funds_rate, rate_3m, rate_2y, rate_5y, rate_10y, rate_30y, ingestion_timestamp)
    ) as source
    ON target.date = source.date
    WHEN MATCHED THEN
        UPDATE SET
            target.fed_funds_rate = source.fed_funds_rate,
            target.rate_3m = COALESCE(source.rate_3m, target.rate_3m),
            target.rate_2y = COALESCE(source.rate_2y, target.rate_2y),
            target.rate_5y = COALESCE(source.rate_5y, target.rate_5y),
            target.rate_10y = COALESCE(source.rate_10y, target.rate_10y),
            target.rate_30y = COALESCE(source.rate_30y, target.rate_30y),
            target.ingestion_timestamp = source.ingestion_timestamp
    WHEN NOT MATCHED THEN
        INSERT (date, fed_funds_rate, rate_3m, rate_2y, rate_5y, rate_10y, rate_30y, ingestion_timestamp)
        VALUES (source.date, source.fed_funds_rate, source.rate_3m, source.rate_2y, source.rate_5y, source.rate_10y, source.rate_30y, source.ingestion_timestamp)
    """

    try:
        execute_sql(merge_query)
        print("✓ Data inserted successfully")
    except Exception as e:
        print(f"❌ Error inserting data: {str(e)}")
        # Fallback: try adding fed_funds_rate column first
        print("\n⚠️  Trying to add fed_funds_rate column...")
        try:
            execute_sql(f"""
                ALTER TABLE {CATALOG}.{SCHEMA}.{TABLE}
                ADD COLUMN IF NOT EXISTS fed_funds_rate DOUBLE
                COMMENT 'Federal Funds Effective Rate'
            """)
            print("✓ Column added, retrying insert...")
            execute_sql(merge_query)
            print("✓ Data inserted successfully")
        except Exception as e2:
            print(f"❌ Still failed: {str(e2)}")
            return

    # Verify results
    print("\n📊 Verification:")
    result = execute_sql(f"""
        SELECT
            MIN(date) as earliest_date,
            MAX(date) as latest_date,
            COUNT(*) as total_rows,
            COUNT(DISTINCT date) as unique_dates,
            COUNT(fed_funds_rate) as rows_with_fed_funds,
            AVG(fed_funds_rate) as avg_fed_funds_rate
        FROM {CATALOG}.{SCHEMA}.{TABLE}
    """)

    if result:
        print(f"\n  Earliest Date: {result[0][0]}")
        print(f"  Latest Date: {result[0][1]}")
        print(f"  Total Rows: {result[0][2]}")
        print(f"  Unique Dates: {result[0][3]}")
        print(f"  Rows with Fed Funds: {result[0][4]}")
        print(f"  Avg Fed Funds Rate: {result[0][5]:.2f}%" if result[0][5] else "N/A")

    # Show recent data
    print("\n📊 Recent Yield Curve Data:")
    result = execute_sql(f"""
        SELECT
            date,
            fed_funds_rate,
            rate_3m,
            rate_2y,
            rate_10y,
            (rate_10y - rate_2y) as curve_slope
        FROM {CATALOG}.{SCHEMA}.{TABLE}
        ORDER BY date DESC
        LIMIT 5
    """)

    if result:
        print("\n  Date        | Fed Funds | 3M    | 2Y    | 10Y   | Slope")
        print("  " + "-"*70)
        for row in result:
            print(f"  {row[0]} | {row[1]:8.2f}% | {row[2]:5.2f}% | {row[3]:5.2f}% | {row[4]:5.2f}% | {row[5]:5.2f}%")

    print("\n" + "="*80)
    print("✅ BACKFILL COMPLETE")
    print("="*80)
    print(f"\n💡 Next Steps:")
    print(f"  1. Run Phase 1 notebook: notebooks/Phase1_Enhanced_Deposit_Beta_Model.py")
    print(f"  2. Verify rate_regime classification is working")
    print(f"  3. Schedule weekly updates: scripts/weekly_yield_curve_update.py")

if __name__ == "__main__":
    import sys

    # Parse command line args
    start_date = sys.argv[1] if len(sys.argv) > 1 else "2024-01-01"

    print(f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                    YIELD CURVE BACKFILL - ALPHAVANTAGE                     ║
╚════════════════════════════════════════════════════════════════════════════╝

This script will:
  1. Fetch Federal Funds Rate from AlphaVantage FRED API
  2. Fetch Treasury Yields (3M, 2Y, 5Y, 10Y, 30Y)
  3. Merge and backfill {CATALOG}.{SCHEMA}.{TABLE}
  4. Add missing fed_funds_rate column if needed

API Usage: 6 calls total (well within free tier limit of 25/day)

""")

    backfill_yield_curves(start_date=start_date)
