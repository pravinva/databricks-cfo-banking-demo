"""
Verify that deposit_accounts_historical table exists and has data.
"""

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
WAREHOUSE_ID = "4b9b953939869799"

print("=" * 80)
print("VERIFYING HISTORICAL DATA TABLE")
print("=" * 80)

# Check if table exists and has data
query = """
SELECT
    COUNT(*) as total_rows,
    COUNT(DISTINCT account_id) as unique_accounts,
    COUNT(DISTINCT effective_date) as unique_months,
    SUM(CASE WHEN is_closed = TRUE THEN 1 ELSE 0 END) as closed_snapshots,
    COUNT(DISTINCT CASE WHEN is_closed = TRUE THEN account_id END) as unique_closed_accounts,
    MIN(effective_date) as earliest_date,
    MAX(effective_date) as latest_date
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts_historical
"""

try:
    result = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        statement=query,
        wait_timeout="50s"
    )

    if result.result and result.result.data_array:
        row = result.result.data_array[0]
        print("\n✓ Table exists and has data:\n")
        print(f"  Total rows: {int(row[0]):,}")
        print(f"  Unique accounts: {int(row[1]):,}")
        print(f"  Unique months: {row[2]}")
        print(f"  Closed account snapshots: {int(row[3]):,}")
        print(f"  Unique closed accounts: {int(row[4]):,}")
        print(f"  Date range: {row[5]} to {row[6]}")

        print("\n" + "=" * 80)
        print("STATUS: Historical data is READY for Phase 2/3 notebooks")
        print("=" * 80)
    else:
        print("\n✗ Table exists but has NO DATA")
        print("\nNeed to run: python3 generate_deposit_history.py")

except Exception as e:
    if "TABLE_OR_VIEW_NOT_FOUND" in str(e):
        print("\n✗ Table does NOT exist")
        print("\nNeed to run: python3 generate_deposit_history.py")
    else:
        print(f"\n✗ Error: {e}")
