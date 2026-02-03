#!/usr/bin/env python3
"""
Check what product types exist in deposit_runoff_predictions table
"""
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
WAREHOUSE_ID = "4b9b953939869799"

print("=" * 80)
print("CHECKING DEPOSIT RUNOFF PREDICTIONS TABLE")
print("=" * 80)

# Check what product types exist
query = """
SELECT DISTINCT product_type
FROM cfo_banking_demo.gold_analytics.deposit_runoff_predictions
ORDER BY product_type
"""

print("\n1. Querying distinct product types...")
result = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=query,
    wait_timeout="30s"
)

if result.result and result.result.data_array:
    print(f"\nFound {len(result.result.data_array)} product types:")
    for row in result.result.data_array:
        print(f"  - {row[0]}")
else:
    print("  ⚠️  No product types found!")

# Check all data
query2 = """
SELECT
    product_type,
    total_balance / 1e9 as balance_billions,
    avg_beta,
    runoff_25bps / 1e9 as runoff_25bps_billions,
    runoff_50bps / 1e9 as runoff_50bps_billions
FROM cfo_banking_demo.gold_analytics.deposit_runoff_predictions
ORDER BY total_balance DESC
"""

print("\n2. Full table data:")
print("-" * 80)
result2 = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=query2,
    wait_timeout="30s"
)

if result2.result and result2.result.data_array:
    print(f"{'Product Type':<25} {'Balance (B)':<15} {'Beta':<10} {'Runoff 25bps (B)':<20} {'Runoff 50bps (B)':<20}")
    print("-" * 100)
    for row in result2.result.data_array:
        ptype = row[0] if row[0] else "NULL"
        balance = float(row[1]) if row[1] else 0
        beta = float(row[2]) if row[2] else 0
        runoff25 = float(row[3]) if row[3] else 0
        runoff50 = float(row[4]) if row[4] else 0
        print(f"{ptype:<25} ${balance:<14.2f} {beta:<10.3f} ${runoff25:<19.2f} ${runoff50:<19.2f}")
else:
    print("  ⚠️  No data found in table!")

print("\n" + "=" * 80)
