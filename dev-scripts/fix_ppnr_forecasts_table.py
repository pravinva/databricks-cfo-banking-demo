#!/usr/bin/env python3
"""
Fix PPNR forecasts table schema conflict.
"""
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
WAREHOUSE_ID = "4b9b953939869799"

print("=" * 80)
print("FIXING PPNR FORECASTS TABLE")
print("=" * 80)

table = "cfo_banking_demo.ml_models.ppnr_forecasts"

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
print("TABLE DROPPED - Re-run PPNR notebook to recreate with clean schema")
print("=" * 80)
