#!/usr/bin/env python3
"""
Check what product types exist in deposit_beta_training_enhanced table
"""
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
WAREHOUSE_ID = "4b9b953939869799"

print("=" * 80)
print("CHECKING DEPOSIT BETA TRAINING ENHANCED TABLE")
print("=" * 80)

# Check if table exists
query_check = """
SHOW TABLES IN cfo_banking_demo.ml_models LIKE 'deposit_beta_training_enhanced'
"""

print("\n1. Checking if table exists...")
try:
    result = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        statement=query_check,
        wait_timeout="30s"
    )

    if result.result and result.result.data_array and len(result.result.data_array) > 0:
        print("   ✓ Table exists")
    else:
        print("   ⚠️  Table does NOT exist!")
        print("\n" + "=" * 80)
        print("SOLUTION: Run the deposit beta training notebook to create this table")
        print("=" * 80)
        exit(0)
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# Check what product types exist
query = """
SELECT DISTINCT product_type
FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
ORDER BY product_type
"""

print("\n2. Querying distinct product types...")
try:
    result = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        statement=query,
        wait_timeout="30s"
    )

    if result.result and result.result.data_array:
        print(f"\nFound {len(result.result.data_array)} product types:")
        for row in result.result.data_array:
            print(f"  - {row[0]}")
    else:
        print("  ⚠️  No product types found in table!")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Check summary
query2 = """
SELECT
    product_type,
    COUNT(*) as account_count,
    SUM(balance_millions) as balance_millions,
    AVG(target_beta) as avg_beta,
    relationship_category
FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
WHERE effective_date = (SELECT MAX(effective_date) FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced)
GROUP BY product_type, relationship_category
ORDER BY balance_millions DESC
"""

print("\n3. Summary by product type and relationship:")
print("-" * 80)
try:
    result2 = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        statement=query2,
        wait_timeout="30s"
    )

    if result2.result and result2.result.data_array:
        print(f"{'Product Type':<20} {'Accounts':<12} {'Balance (M)':<15} {'Avg Beta':<12} {'Relationship':<15}")
        print("-" * 90)
        for row in result2.result.data_array:
            ptype = row[0] if row[0] else "NULL"
            count = int(row[1]) if row[1] else 0
            balance = float(row[2]) if row[2] else 0
            beta = float(row[3]) if row[3] else 0
            rel = row[4] if row[4] else "NULL"
            print(f"{ptype:<20} {count:<12,} ${balance:<14.1f} {beta:<12.3f} {rel:<15}")
    else:
        print("  ⚠️  No data found in table!")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 80)
