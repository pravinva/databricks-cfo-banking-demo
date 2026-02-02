#!/usr/bin/env python3
"""
Grant SELECT and MODIFY permissions to all account users for cfo_banking_demo catalog
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import time

# Initialize workspace client
w = WorkspaceClient()

# Warehouse ID
warehouse_id = "4b9b953939869799"

# SQL statements to grant permissions to all account users
grant_statements = [
    # Catalog-level
    "GRANT USE CATALOG ON CATALOG cfo_banking_demo TO `account users`",
    "GRANT SELECT ON CATALOG cfo_banking_demo TO `account users`",
    "GRANT MODIFY ON CATALOG cfo_banking_demo TO `account users`",

    # silver_finance
    "GRANT USE SCHEMA ON SCHEMA cfo_banking_demo.silver_finance TO `account users`",
    "GRANT SELECT ON SCHEMA cfo_banking_demo.silver_finance TO `account users`",
    "GRANT MODIFY ON SCHEMA cfo_banking_demo.silver_finance TO `account users`",

    # silver_treasury
    "GRANT USE SCHEMA ON SCHEMA cfo_banking_demo.silver_treasury TO `account users`",
    "GRANT SELECT ON SCHEMA cfo_banking_demo.silver_treasury TO `account users`",
    "GRANT MODIFY ON SCHEMA cfo_banking_demo.silver_treasury TO `account users`",

    # gold_regulatory
    "GRANT USE SCHEMA ON SCHEMA cfo_banking_demo.gold_regulatory TO `account users`",
    "GRANT SELECT ON SCHEMA cfo_banking_demo.gold_regulatory TO `account users`",
    "GRANT MODIFY ON SCHEMA cfo_banking_demo.gold_regulatory TO `account users`",

    # bronze_market_data
    "GRANT USE SCHEMA ON SCHEMA cfo_banking_demo.bronze_market_data TO `account users`",
    "GRANT SELECT ON SCHEMA cfo_banking_demo.bronze_market_data TO `account users`",
    "GRANT MODIFY ON SCHEMA cfo_banking_demo.bronze_market_data TO `account users`",

    # ml_models
    "GRANT USE SCHEMA ON SCHEMA cfo_banking_demo.ml_models TO `account users`",
    "GRANT SELECT ON SCHEMA cfo_banking_demo.ml_models TO `account users`",
    "GRANT MODIFY ON SCHEMA cfo_banking_demo.ml_models TO `account users`",

    # models
    "GRANT USE SCHEMA ON SCHEMA cfo_banking_demo.models TO `account users`",
    "GRANT SELECT ON SCHEMA cfo_banking_demo.models TO `account users`",
    "GRANT MODIFY ON SCHEMA cfo_banking_demo.models TO `account users`",
]

print("=" * 80)
print("GRANTING PERMISSIONS TO ALL ACCOUNT USERS")
print("=" * 80)
print(f"Warehouse ID: {warehouse_id}")
print()

success_count = 0
fail_count = 0

for i, sql in enumerate(grant_statements, 1):
    print(f"[{i}/{len(grant_statements)}] {sql[:70]}...")

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
            fail_count += 1
        else:
            print(f"  ✓ SUCCESS")
            success_count += 1

    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        fail_count += 1

print()
print("=" * 80)
print(f"SUMMARY: {success_count} succeeded, {fail_count} failed")
print("=" * 80)
print()

# Verify catalog permissions
verify_sql = "SHOW GRANTS ON CATALOG cfo_banking_demo"
print(f"Verifying: {verify_sql}")

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

except Exception as e:
    print(f"  ❌ ERROR: {e}")

print()
print("✓ Permission grant script completed!")
