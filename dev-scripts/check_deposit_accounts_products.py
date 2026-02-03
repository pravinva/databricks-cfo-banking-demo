#!/usr/bin/env python3
"""
Check what product types exist in deposit_accounts table
"""
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
WAREHOUSE_ID = "4b9b953939869799"

print("=" * 80)
print("CHECKING DEPOSIT ACCOUNTS PRODUCT TYPES")
print("=" * 80)

query = """
SELECT DISTINCT product_type
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
ORDER BY product_type
"""

print("\nQuerying distinct product types from deposit_accounts...")
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

# Summary
query2 = """
SELECT
    product_type,
    COUNT(*) as account_count,
    SUM(current_balance) / 1e9 as balance_billions
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
WHERE account_status = 'Active'
GROUP BY product_type
ORDER BY balance_billions DESC
"""

print("\nSummary by product type:")
print("-" * 60)
result2 = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=query2,
    wait_timeout="30s"
)

if result2.result and result2.result.data_array:
    print(f"{'Product Type':<20} {'Accounts':<15} {'Balance (B)':<15}")
    print("-" * 60)
    for row in result2.result.data_array:
        ptype = row[0] if row[0] else "NULL"
        count = int(row[1]) if row[1] else 0
        balance = float(row[2]) if row[2] else 0
        print(f"{ptype:<20} {count:<15,} ${balance:<14.2f}")

print("\n" + "=" * 80)
