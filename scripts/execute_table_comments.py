#!/usr/bin/env python3
"""
Execute SQL COMMENT statements in Databricks to update Unity Catalog metadata.
"""

import subprocess
import sys
import re
from typing import List

def read_sql_file(filepath: str) -> List[str]:
    """Read SQL file and extract COMMENT statements."""
    with open(filepath, 'r') as f:
        content = f.read()

    # Split by semicolons but preserve them
    statements = []
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('COMMENT ON'):
            statements.append(line)

    return statements

def execute_sql_statement(statement: str) -> tuple:
    """Execute a single SQL statement via databricks sql-statements execute."""
    try:
        result = subprocess.run(
            [
                "databricks", "sql-statements", "execute",
                "--warehouse-id", "auto",
                "--statement", statement
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            return (True, None)
        else:
            return (False, result.stderr)

    except subprocess.TimeoutExpired:
        return (False, "Timeout after 30 seconds")
    except Exception as e:
        return (False, str(e))

def main():
    """Main execution function."""

    sql_file = "scripts/genie_table_comments.sql"

    print(f"Reading SQL statements from {sql_file}...")
    statements = read_sql_file(sql_file)
    print(f"Found {len(statements)} COMMENT statements to execute\n")

    success_count = 0
    failure_count = 0

    for i, statement in enumerate(statements, 1):
        # Extract table/column name for display
        match = re.search(r'COMMENT ON (TABLE|COLUMN) ([\w.]+)', statement)
        if match:
            obj_type = match.group(1)
            obj_name = match.group(2)
            print(f"[{i}/{len(statements)}] Updating {obj_type}: {obj_name}...", end=" ")
        else:
            print(f"[{i}/{len(statements)}] Executing statement...", end=" ")

        success, error = execute_sql_statement(statement)

        if success:
            print("✓")
            success_count += 1
        else:
            print(f"✗ Error: {error}")
            failure_count += 1

    print(f"\n" + "="*80)
    print(f"Execution Summary:")
    print(f"  Success: {success_count}")
    print(f"  Failed:  {failure_count}")
    print(f"  Total:   {len(statements)}")
    print("="*80)

    if failure_count > 0:
        print("\n⚠️  Some statements failed. Check errors above.")
        sys.exit(1)
    else:
        print("\n✅ All table and column comments updated successfully!")
        print("\nNext steps:")
        print("1. Verify comments in Unity Catalog Data Explorer")
        print("2. Test Genie Space with natural language queries")

if __name__ == "__main__":
    main()
