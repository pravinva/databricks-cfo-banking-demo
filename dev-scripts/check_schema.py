#!/usr/bin/env python3
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import time

w = WorkspaceClient()
warehouse_id = "4b9b953939869799"

# Check deposit_portfolio schema
sql = "DESCRIBE TABLE cfo_banking_demo.silver_treasury.deposit_portfolio"

statement = w.statement_execution.execute_statement(
    warehouse_id=warehouse_id,
    statement=sql,
    wait_timeout="50s"
)

while statement.status.state in [StatementState.PENDING, StatementState.RUNNING]:
    time.sleep(2)
    statement = w.statement_execution.get_statement(statement.statement_id)

if statement.result and statement.result.data_array:
    print("deposit_portfolio columns:")
    for row in statement.result.data_array:
        print(f"  - {row[0]}: {row[1]}")
