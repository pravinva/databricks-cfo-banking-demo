#!/usr/bin/env python3
"""
Grant permissions to Databricks App service principal for data access
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import time

# Initialize workspace client
w = WorkspaceClient()

# Warehouse ID
warehouse_id = "4b9b953939869799"

# Service principal name from app
service_principal = "`app-40zbx9 cfo-banking-demo`"

# SQL statements to grant permissions
grant_statements = [
    f"GRANT USE CATALOG ON CATALOG cfo_banking_demo TO {service_principal}",
    f"GRANT USE SCHEMA ON SCHEMA cfo_banking_demo.silver_finance TO {service_principal}",
    f"GRANT USE SCHEMA ON SCHEMA cfo_banking_demo.silver_treasury TO {service_principal}",
    f"GRANT USE SCHEMA ON SCHEMA cfo_banking_demo.gold_regulatory TO {service_principal}",
    f"GRANT USE SCHEMA ON SCHEMA cfo_banking_demo.bronze_market_data TO {service_principal}",
    f"GRANT SELECT ON SCHEMA cfo_banking_demo.silver_finance TO {service_principal}",
    f"GRANT SELECT ON SCHEMA cfo_banking_demo.silver_treasury TO {service_principal}",
    f"GRANT SELECT ON SCHEMA cfo_banking_demo.gold_regulatory TO {service_principal}",
    f"GRANT SELECT ON SCHEMA cfo_banking_demo.bronze_market_data TO {service_principal}",
]

print("=" * 80)
print("GRANTING PERMISSIONS TO APP SERVICE PRINCIPAL")
print("=" * 80)
print(f"Service Principal: {service_principal}")
print(f"Warehouse ID: {warehouse_id}")
print()

for i, sql in enumerate(grant_statements, 1):
    print(f"[{i}/{len(grant_statements)}] Executing: {sql[:80]}...")

    try:
        statement = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=sql,
            wait_timeout="50s"
        )

        # Wait for completion
        max_wait_time = 60
        elapsed = 0
        while statement.status.state in [StatementState.PENDING, StatementState.RUNNING] and elapsed < max_wait_time:
            time.sleep(2)
            elapsed += 2
            statement = w.statement_execution.get_statement(statement.statement_id)

        if statement.status.state == StatementState.FAILED:
            error_msg = statement.status.error.message if statement.status.error else "Unknown error"
            print(f"  ❌ FAILED: {error_msg}")
        else:
            print(f"  ✓ SUCCESS")

    except Exception as e:
        print(f"  ❌ ERROR: {e}")

print()
print("=" * 80)
print("VERIFYING PERMISSIONS")
print("=" * 80)

# Verify catalog permissions
verify_sql = "SHOW GRANTS ON CATALOG cfo_banking_demo"
print(f"Executing: {verify_sql}")

try:
    statement = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=verify_sql,
        wait_timeout="50s"
    )

    # Wait for completion
    while statement.status.state in [StatementState.PENDING, StatementState.RUNNING]:
        time.sleep(2)
        statement = w.statement_execution.get_statement(statement.statement_id)

    if statement.status.state == StatementState.SUCCEEDED and statement.result:
        print("\nCatalog Grants:")
        if statement.result.data_array:
            for row in statement.result.data_array:
                print(f"  {row}")
    else:
        print("  No results or failed")

except Exception as e:
    print(f"  ❌ ERROR: {e}")

print()
print("✓ Permission grant script completed!")
print()
print("IMPORTANT: You also need to grant warehouse access via UI:")
print("  1. Go to: Compute > SQL Warehouses > 4b9b953939869799")
print("  2. Click 'Permissions' tab")
print("  3. Add service principal: app-40zbx9 cfo-banking-demo")
print("  4. Grant 'Can Use' permission")
