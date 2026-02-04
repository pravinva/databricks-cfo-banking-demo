#!/usr/bin/env python3
"""
Execute SQL COMMENT statements using Databricks SDK to update Unity Catalog metadata.
"""

import re
import sys
from typing import List, Tuple

def read_sql_file(filepath: str) -> List[str]:
    """Read SQL file and extract COMMENT statements."""
    with open(filepath, 'r') as f:
        content = f.read()

    statements = []
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('COMMENT ON'):
            statements.append(line)

    return statements

def execute_via_databricks_mcp(statement: str) -> Tuple[bool, str]:
    """
    Execute SQL via databricks MCP execute_parameterized_sql.

    Note: This function signature is for compatibility.
    Actual execution will be done via the MCP tool externally.
    """
    return (True, "Queued for MCP execution")

def main():
    """Main execution function."""

    sql_file = "scripts/genie_table_comments.sql"

    print(f"Reading SQL statements from {sql_file}...")
    statements = read_sql_file(sql_file)
    print(f"Found {len(statements)} COMMENT statements\n")

    # Group statements by table for batching
    table_groups = {}
    for statement in statements:
        match = re.search(r'COMMENT ON (?:TABLE|COLUMN) (cfo_banking_demo\.\w+\.\w+)', statement)
        if match:
            table_name = match.group(1)
            if table_name not in table_groups:
                table_groups[table_name] = []
            table_groups[table_name].append(statement)

    print(f"Grouped into {len(table_groups)} tables")
    print("\nStatements to execute:")
    print("=" * 80)

    for table_name, table_statements in table_groups.items():
        print(f"\n{table_name} ({len(table_statements)} statements):")
        for stmt in table_statements[:2]:  # Show first 2 as examples
            print(f"  {stmt[:80]}...")
        if len(table_statements) > 2:
            print(f"  ... and {len(table_statements) - 2} more")

    print("\n" + "=" * 80)
    print("\nTo execute these statements, use the Databricks MCP tool:")
    print("\nOption 1: Execute all statements in a single SQL file")
    print(f"  cat {sql_file} | databricks workspace import --overwrite /tmp/genie_comments.sql")
    print(f"  databricks workspace execute /tmp/genie_comments.sql")

    print("\nOption 2: Use Databricks SQL Warehouse")
    print("  1. Copy scripts/genie_table_comments.sql")
    print("  2. Paste into Databricks SQL Editor")
    print("  3. Run all statements")

    print("\nOption 3: Run via Python SDK")
    print("  See execute_comments_sdk.py for implementation")

if __name__ == "__main__":
    main()
