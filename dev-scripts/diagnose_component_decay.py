"""
Diagnostic script to investigate why component decay metrics show 0s and NaNs.
"""

from databricks.sdk import WorkspaceClient
import os

# Initialize Databricks client
w = WorkspaceClient()

# Warehouse ID from notebooks
WAREHOUSE_ID = "4b9b953939869799"

print("=" * 80)
print("DIAGNOSING COMPONENT DECAY METRICS ISSUE")
print("=" * 80)

# Query 1: Check account_status_transitions CTE
print("\n1. Checking account_status_transitions CTE...")
query1 = """
SELECT
    COUNT(*) as total_accounts,
    SUM(is_closed) as closed_accounts,
    AVG(account_lifetime_years) as avg_lifetime,
    MIN(account_lifetime_years) as min_lifetime,
    MAX(account_lifetime_years) as max_lifetime
FROM (
    SELECT
        account_id,
        MAX(CASE WHEN is_current = FALSE THEN 1 ELSE 0 END) as is_closed,
        DATEDIFF(MAX(effective_date), account_open_date) / 365.25 as account_lifetime_years
    FROM cfo_banking_demo.ml_models.deposit_cohort_analysis
    GROUP BY account_id, account_open_date
)
"""
result1 = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=query1,
    wait_timeout="50s"
)
if result1.result and result1.result.data_array:
    row = result1.result.data_array[0]
    print(f"  Total accounts: {row[0]}")
    print(f"  Closed accounts: {row[1]}")
    print(f"  Avg lifetime: {row[2]:.2f} years" if row[2] else "  Avg lifetime: None")
    print(f"  Min lifetime: {row[3]:.2f} years" if row[3] else "  Min lifetime: None")
    print(f"  Max lifetime: {row[4]:.2f} years" if row[4] else "  Max lifetime: None")

    if int(row[1]) == 0:
        print("\n  ⚠️  PROBLEM: No closed accounts (all is_current = TRUE)")
        print("     This is why closure rate λ = 0!")

# Query 2: Check is_current distribution in cohort_analysis
print("\n2. Checking is_current distribution...")
query2 = """
SELECT
    is_current,
    COUNT(*) as row_count,
    COUNT(DISTINCT account_id) as unique_accounts
FROM cfo_banking_demo.ml_models.deposit_cohort_analysis
GROUP BY is_current
"""
result2 = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=query2,
    wait_timeout="50s"
)
if result2.result and result2.result.data_array:
    print("  is_current distribution:")
    for row in result2.result.data_array:
        print(f"    is_current={row[0]}: {row[1]} rows, {row[2]} unique accounts")

# Query 3: Check balance_growth_among_survivors
print("\n3. Checking balance growth calculations...")
query3 = """
SELECT
    COUNT(*) as total_rows,
    COUNT(CASE WHEN prior_balance IS NOT NULL THEN 1 END) as rows_with_prior,
    COUNT(CASE WHEN monthly_growth_rate IS NOT NULL THEN 1 END) as rows_with_growth_rate,
    AVG(monthly_growth_rate) as avg_growth_rate
FROM (
    SELECT
        account_id,
        months_since_open,
        current_balance,
        LAG(current_balance, 1) OVER (PARTITION BY account_id ORDER BY months_since_open) as prior_balance,
        (current_balance - LAG(current_balance, 1) OVER (PARTITION BY account_id ORDER BY months_since_open)) /
        NULLIF(LAG(current_balance, 1) OVER (PARTITION BY account_id ORDER BY months_since_open), 0) as monthly_growth_rate
    FROM cfo_banking_demo.ml_models.deposit_cohort_analysis
    WHERE is_current = TRUE
    AND months_since_open >= 1
)
"""
result3 = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=query3,
    wait_timeout="50s"
)
if result3.result and result3.result.data_array:
    row = result3.result.data_array[0]
    print(f"  Total rows: {row[0]}")
    print(f"  Rows with prior_balance: {row[1]}")
    print(f"  Rows with growth_rate: {row[2]}")
    print(f"  Avg growth rate: {row[3]}" if row[3] else "  Avg growth rate: NULL")

    if int(row[1]) == 0:
        print("\n  ⚠️  PROBLEM: No prior balance data (only 1 snapshot per account)")
        print("     LAG() returns NULL when there's only 1 row per account")
        print("     This is why ABGR (g) = NaN!")

# Query 4: Check how many months of data each account has
print("\n4. Checking time-series depth per account...")
query4 = """
SELECT
    COUNT(DISTINCT months_since_open) as snapshots_per_account,
    COUNT(DISTINCT account_id) as account_count
FROM cfo_banking_demo.ml_models.deposit_cohort_analysis
GROUP BY account_id
ORDER BY snapshots_per_account DESC
LIMIT 10
"""
result4 = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=query4,
    wait_timeout="50s"
)
if result4.result and result4.result.data_array:
    print("  Snapshots per account distribution:")
    for row in result4.result.data_array[:5]:
        print(f"    {row[0]} snapshot(s): {row[1]} accounts")

# Query 5: Check raw deposit_accounts table structure
print("\n5. Checking source deposit_accounts table...")
query5 = """
SELECT
    COUNT(*) as total_rows,
    COUNT(DISTINCT account_id) as unique_accounts,
    COUNT(DISTINCT effective_date) as unique_dates,
    COUNT(DISTINCT account_id) / COUNT(*) as accounts_to_rows_ratio
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
"""
result5 = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=query5,
    wait_timeout="50s"
)
if result5.result and result5.result.data_array:
    row = result5.result.data_array[0]
    print(f"  Total rows: {row[0]}")
    print(f"  Unique accounts: {row[1]}")
    print(f"  Unique dates: {row[2]}")
    print(f"  Accounts/Rows ratio: {float(row[3]):.4f}")

    if float(row[3]) > 0.99:
        print("\n  ⚠️  CRITICAL: Each account has only ~1 row")
        print("     This means deposit_accounts is a SNAPSHOT table, not historical!")
        print("     No time-series data → Cannot calculate λ or g")

print("\n" + "=" * 80)
print("DIAGNOSIS COMPLETE")
print("=" * 80)
print("\nRECOMMENDATION:")
print("If deposit_accounts is snapshot-only, we need to either:")
print("  1. Use proxy metrics (balance changes, cohort comparisons)")
print("  2. Create synthetic historical data based on cohort behavior")
print("  3. Wait for actual historical data accumulation")
