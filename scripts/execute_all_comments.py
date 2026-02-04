#!/usr/bin/env python3
"""
Execute all SQL COMMENT statements using Databricks CLI.
"""

import subprocess
import re
import sys
import time

def read_sql_statements(filepath):
    """Read and parse SQL COMMENT statements."""
    with open(filepath, 'r') as f:
        content = f.read()

    statements = []
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('COMMENT ON'):
            statements.append(line)

    return statements

def execute_statement(statement):
    """Execute a single COMMENT statement."""
    try:
        result = subprocess.run(
            [
                'databricks', 'experimental', 'apps-mcp', 'tools', 'query',
                statement
            ],
            capture_output=True,
            text=True,
            timeout=30,
            cwd='/Users/pravin.varma/Documents/Demo/databricks-cfo-banking-demo'
        )

        if result.returncode == 0:
            return True, None
        else:
            return False, result.stderr

    except Exception as e:
        return False, str(e)

def main():
    sql_file = 'scripts/genie_table_comments.sql'

    print("Reading SQL statements...")
    statements = read_sql_statements(sql_file)
    print(f"Found {len(statements)} COMMENT statements\n")

    success_count = 0
    failure_count = 0

    print("Executing statements...")
    print("=" * 80)

    for i, statement in enumerate(statements, 1):
        # Extract object name for display
        match = re.search(r'COMMENT ON (TABLE|COLUMN) ([\w.]+)', statement)
        if match:
            obj_type = match.group(1)
            obj_name = match.group(2)
            display_name = obj_name.replace('cfo_banking_demo.', '')
        else:
            display_name = "unknown"

        print(f"[{i}/{len(statements)}] {display_name}...", end=" ", flush=True)

        success, error = execute_statement(statement)

        if success:
            print("✓")
            success_count += 1
        else:
            print(f"✗")
            if error:
                print(f"    Error: {error[:100]}")
            failure_count += 1

        # Small delay to avoid rate limiting
        if i % 10 == 0:
            time.sleep(0.5)

    print("\n" + "=" * 80)
    print(f"Execution Complete")
    print(f"  Success: {success_count}/{len(statements)}")
    print(f"  Failed:  {failure_count}/{len(statements)}")
    print("=" * 80)

    if failure_count == 0:
        print("\n✅ All table and column comments updated successfully!")
        print("\nVerify in Databricks:")
        print("  1. Open Unity Catalog Data Explorer")
        print("  2. Navigate to cfo_banking_demo catalog")
        print("  3. Check table and column descriptions")
        return 0
    else:
        print(f"\n⚠️  {failure_count} statements failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
