"""
Diagnostic script to investigate why cohort survival rates query returns zero rows.
"""

from databricks.sdk import WorkspaceClient
import os

# Initialize Databricks client
w = WorkspaceClient()

# Warehouse ID from notebooks
WAREHOUSE_ID = "4b9b953939869799"

print("=" * 80)
print("DIAGNOSING COHORT SURVIVAL RATES ISSUE")
print("=" * 80)

# Query 1: Check if cohort_analysis table has data
print("\n1. Checking deposit_cohort_analysis table...")
query1 = """
SELECT
    COUNT(*) as total_rows,
    COUNT(DISTINCT cohort_quarter) as unique_cohorts,
    MIN(months_since_open) as min_months,
    MAX(months_since_open) as max_months,
    COUNT(CASE WHEN months_since_open = 0 THEN 1 END) as rows_with_month_0
FROM cfo_banking_demo.ml_models.deposit_cohort_analysis
"""
result1 = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=query1,
    wait_timeout="50s"
)
if result1.result and result1.result.data_array:
    row = result1.result.data_array[0]
    print(f"  Total rows: {row[0]}")
    print(f"  Unique cohorts: {row[1]}")
    print(f"  Min months_since_open: {row[2]}")
    print(f"  Max months_since_open: {row[3]}")
    print(f"  Rows with months_since_open = 0: {row[4]}")

    if int(row[4]) == 0:
        print("\n  ⚠️  PROBLEM FOUND: No rows with months_since_open = 0")
        print("     This is why cohort_initial_balances CTE returns zero rows!")

# Query 2: Sample data from cohort_analysis
print("\n2. Sample data from cohort_analysis table...")
query2 = """
SELECT
    account_id,
    cohort_quarter,
    relationship_category,
    product_type,
    is_surge_balance,
    opening_regime,
    months_since_open,
    current_balance
FROM cfo_banking_demo.ml_models.deposit_cohort_analysis
ORDER BY cohort_quarter, months_since_open
LIMIT 10
"""
result2 = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=query2,
    wait_timeout="50s"
)
if result2.result and result2.result.data_array:
    print("  Sample rows:")
    for row in result2.result.data_array[:5]:
        print(f"    Account: {row[0]}, Cohort: {row[1]}, Months: {row[6]}, Balance: {row[7]}")

# Query 3: Check min months_since_open per cohort
print("\n3. Checking minimum months_since_open per cohort...")
query3 = """
SELECT
    cohort_quarter,
    relationship_category,
    product_type,
    MIN(months_since_open) as min_month,
    COUNT(*) as row_count
FROM cfo_banking_demo.ml_models.deposit_cohort_analysis
GROUP BY cohort_quarter, relationship_category, product_type
ORDER BY cohort_quarter
LIMIT 10
"""
result3 = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=query3,
    wait_timeout="50s"
)
if result3.result and result3.result.data_array:
    print("  Per-cohort minimums:")
    for row in result3.result.data_array[:5]:
        print(f"    Cohort: {row[0]}, Category: {row[1]}, Product: {row[2]}, Min months: {row[3]}, Rows: {row[4]}")

# Query 4: Test the cohort_initial_balances CTE with original WHERE clause
print("\n4. Testing cohort_initial_balances CTE (WHERE months_since_open = 0)...")
query4 = """
SELECT COUNT(*) as result_rows
FROM (
    SELECT
        cohort_quarter,
        cohort_year,
        cohort_q,
        relationship_category,
        product_type,
        is_surge_balance,
        opening_regime,
        COUNT(DISTINCT account_id) as initial_account_count
    FROM cfo_banking_demo.ml_models.deposit_cohort_analysis
    WHERE months_since_open = 0
    GROUP BY cohort_quarter, cohort_year, cohort_q, relationship_category,
             product_type, is_surge_balance, opening_regime
)
"""
result4 = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=query4,
    wait_timeout="50s"
)
if result4.result and result4.result.data_array:
    print(f"  Rows returned by cohort_initial_balances: {result4.result.data_array[0][0]}")

# Query 5: Test cohort_balances_over_time CTE
print("\n5. Testing cohort_balances_over_time CTE...")
query5 = """
SELECT COUNT(*) as result_rows
FROM (
    SELECT
        cohort_quarter,
        cohort_year,
        cohort_q,
        relationship_category,
        product_type,
        is_surge_balance,
        opening_regime,
        months_since_open,
        COUNT(DISTINCT account_id) as account_count
    FROM cfo_banking_demo.ml_models.deposit_cohort_analysis
    WHERE months_since_open <= 36 AND months_since_open > 0
    GROUP BY cohort_quarter, cohort_year, cohort_q, relationship_category,
             product_type, is_surge_balance, opening_regime, months_since_open
)
"""
result5 = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=query5,
    wait_timeout="50s"
)
if result5.result and result5.result.data_array:
    print(f"  Rows returned by cohort_balances_over_time: {result5.result.data_array[0][0]}")

print("\n" + "=" * 80)
print("DIAGNOSIS COMPLETE")
print("=" * 80)
