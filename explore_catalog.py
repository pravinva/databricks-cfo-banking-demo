#!/usr/bin/env python3
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import time
import json

w = WorkspaceClient()
warehouse_id = "4b9b953939869799"

def execute_sql(sql_query):
    """Execute SQL and return results"""
    statement = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql_query,
        wait_timeout="50s"
    )

    while statement.status.state in [StatementState.PENDING, StatementState.RUNNING]:
        time.sleep(2)
        statement = w.statement_execution.get_statement(statement.statement_id)

    if statement.result and statement.result.data_array:
        return statement.result.data_array
    return []

# Get all schemas in catalog
print("Exploring cfo_banking_demo catalog...")
print("=" * 100)

schemas = execute_sql("SHOW SCHEMAS IN cfo_banking_demo")
print(f"\nFound {len(schemas)} schemas:")
for schema in schemas:
    print(f"  - {schema[0]}")

catalog_info = {}

# For each schema, get tables
for schema_row in schemas:
    schema_name = schema_row[0]
    if schema_name == "information_schema":
        continue

    print(f"\n{'=' * 100}")
    print(f"SCHEMA: {schema_name}")
    print(f"{'=' * 100}")

    catalog_info[schema_name] = {}

    # Get tables in schema
    tables = execute_sql(f"SHOW TABLES IN cfo_banking_demo.{schema_name}")
    print(f"\nTables in {schema_name}: {len(tables)}")

    for table_row in tables:
        table_name = table_row[1]  # Table name is in second column
        full_table_name = f"cfo_banking_demo.{schema_name}.{table_name}"

        print(f"\n  Table: {table_name}")
        print(f"  {'-' * 80}")

        # Get table schema
        schema_info = execute_sql(f"DESCRIBE TABLE {full_table_name}")
        columns = []
        for col in schema_info:
            col_name = col[0]
            col_type = col[1]
            if col_name and not col_name.startswith('#'):  # Skip partition info
                columns.append({"name": col_name, "type": col_type})
                print(f"    {col_name:40s} {col_type}")

        # Get row count
        try:
            count_result = execute_sql(f"SELECT COUNT(*) FROM {full_table_name}")
            row_count = count_result[0][0] if count_result else 0
            print(f"\n    Row count: {row_count:,}")
        except:
            row_count = "N/A"
            print(f"\n    Row count: Unable to determine")

        # Get sample data
        try:
            sample = execute_sql(f"SELECT * FROM {full_table_name} LIMIT 3")
            if sample:
                print(f"\n    Sample data (first 3 rows):")
                for i, row in enumerate(sample, 1):
                    print(f"      Row {i}: {row[:5]}...")  # Show first 5 columns
        except:
            print(f"\n    Sample data: Unable to retrieve")

        # Store in catalog info
        catalog_info[schema_name][table_name] = {
            "full_name": full_table_name,
            "columns": columns,
            "row_count": row_count
        }

# Save to JSON
with open('catalog_info.json', 'w') as f:
    json.dump(catalog_info, f, indent=2)

print("\n" + "=" * 100)
print(f"✓ Catalog exploration complete!")
print(f"  Details saved to: catalog_info.json")
print("=" * 100)
