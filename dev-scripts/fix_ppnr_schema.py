#!/usr/bin/env python3
"""
Fix PPNR training data schema conflict by dropping and recreating tables.
"""
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
WAREHOUSE_ID = "4b9b953939869799"

print("=" * 80)
print("FIXING PPNR SCHEMA CONFLICTS")
print("=" * 80)

tables_to_drop = [
    "cfo_banking_demo.gold_finance.ppnr_training_data",
    "cfo_banking_demo.gold_finance.nii_training_data",
    "cfo_banking_demo.gold_finance.fee_income_training_data",
    "cfo_banking_demo.gold_finance.expense_training_data"
]

for table in tables_to_drop:
    print(f"\nDropping {table}...")
    drop_sql = f"DROP TABLE IF EXISTS {table}"

    try:
        result = w.statement_execution.execute_statement(
            warehouse_id=WAREHOUSE_ID,
            statement=drop_sql,
            wait_timeout="30s"
        )
        print(f"   ✓ Dropped {table}")
    except Exception as e:
        print(f"   ⚠ Could not drop {table}: {str(e)[:100]}")

print("\n" + "=" * 80)
print("SCHEMA CLEANUP COMPLETE")
print("=" * 80)
print("\nNext: Re-run Train_PPNR_Models.py notebook to recreate tables with clean schema")
