"""
Check what columns are available in the Phase 1 training table.
"""

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
WAREHOUSE_ID = "4b9b953939869799"

print("=" * 80)
print("CHECKING PHASE 1 TRAINING TABLE COLUMNS")
print("=" * 80)

query = """
DESCRIBE TABLE cfo_banking_demo.ml_models.deposit_beta_training_enhanced
"""

result = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=query,
    wait_timeout="50s"
)

if result.result and result.result.data_array:
    print("\nAvailable columns:")
    print("  " + "-" * 60)
    for row in result.result.data_array[:50]:  # First 50 columns
        print(f"  {row[0]:<40} {row[1]}")
