#!/usr/bin/env python3
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import time

w = WorkspaceClient()
warehouse_id = "4b9b953939869799"

# Check yield_curves schema
sql = "DESCRIBE TABLE cfo_banking_demo.silver_treasury.yield_curves"

statement = w.statement_execution.execute_statement(
    warehouse_id=warehouse_id,
    statement=sql,
    wait_timeout="50s"
)

while statement.status.state in [StatementState.PENDING, StatementState.RUNNING]:
    time.sleep(2)
    statement = w.statement_execution.get_statement(statement.statement_id)

if statement.result and statement.result.data_array:
    print("yield_curves columns:")
    for row in statement.result.data_array:
        print(f"  - {row[0]}: {row[1]}")

print("\n" + "="*80)

# Check sample data
sql2 = "SELECT * FROM cfo_banking_demo.silver_treasury.yield_curves LIMIT 5"

statement2 = w.statement_execution.execute_statement(
    warehouse_id=warehouse_id,
    statement=sql2,
    wait_timeout="50s"
)

while statement2.status.state in [StatementState.PENDING, StatementState.RUNNING]:
    time.sleep(2)
    statement2 = w.statement_execution.get_statement(statement2.statement_id)

if statement2.result and statement2.result.data_array:
    print("\nSample data:")
    for row in statement2.result.data_array[:3]:
        print(f"  {row}")
