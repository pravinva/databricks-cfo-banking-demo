"""
Diagnose why ABGR (g) is still NaN after historical data generation.
"""

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
WAREHOUSE_ID = "4b9b953939869799"

print("=" * 80)
print("DIAGNOSING ABGR (Average Balance Growth Rate) ISSUE")
print("=" * 80)

# Query 1: Check if LAG() is working
print("\n1. Testing LAG() function for balance history...")
query1 = """
SELECT
    COUNT(*) as total_rows,
    COUNT(CASE WHEN prior_balance IS NOT NULL THEN 1 END) as rows_with_prior,
    COUNT(CASE WHEN monthly_growth_rate IS NOT NULL THEN 1 END) as rows_with_growth,
    AVG(monthly_growth_rate) as avg_growth
FROM (
    SELECT
        account_id,
        effective_date,
        current_balance,
        LAG(current_balance, 1) OVER (PARTITION BY account_id ORDER BY effective_date) as prior_balance,
        (current_balance - LAG(current_balance, 1) OVER (PARTITION BY account_id ORDER BY effective_date)) /
        NULLIF(LAG(current_balance, 1) OVER (PARTITION BY account_id ORDER BY effective_date), 0) as monthly_growth_rate
    FROM cfo_banking_demo.bronze_core_banking.deposit_accounts_historical
    WHERE is_current = TRUE
    AND months_since_open >= 1
    LIMIT 10000
)
"""

result1 = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=query1,
    wait_timeout="50s"
)

if result1.result and result1.result.data_array:
    row = result1.result.data_array[0]
    print(f"  Total rows: {int(row[0]):,}")
    print(f"  Rows with prior_balance: {int(row[1]):,}")
    print(f"  Rows with growth_rate: {int(row[2]):,}")
    print(f"  Avg growth rate: {row[3]}")

    if int(row[1]) == 0:
        print("\n  ⚠️  PROBLEM: No prior_balance values (LAG returns NULL)")
        print("     This means each account only has ONE row where is_current=TRUE")

# Query 2: Check is_current distribution across time
print("\n2. Checking is_current flag distribution...")
query2 = """
SELECT
    effective_date,
    COUNT(*) as total_accounts,
    SUM(CASE WHEN is_current = TRUE THEN 1 ELSE 0 END) as current_count,
    SUM(CASE WHEN is_current = FALSE THEN 1 ELSE 0 END) as not_current_count
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts_historical
GROUP BY effective_date
ORDER BY effective_date DESC
LIMIT 5
"""

result2 = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=query2,
    wait_timeout="50s"
)

if result2.result and result2.result.data_array:
    print("  Recent months:")
    print("  Date       | Total  | Current | Not Current")
    print("  " + "-" * 50)
    for row in result2.result.data_array:
        print(f"  {row[0]} | {int(row[1]):>6,} | {int(row[2]):>7,} | {int(row[3]):>11,}")

# Query 3: Try without is_current filter
print("\n3. Testing ABGR calculation WITHOUT is_current filter...")
query3 = """
SELECT
    COUNT(*) as total_rows,
    COUNT(CASE WHEN prior_balance IS NOT NULL THEN 1 END) as rows_with_prior,
    COUNT(CASE WHEN monthly_growth_rate IS NOT NULL THEN 1 END) as rows_with_growth,
    AVG(monthly_growth_rate) as avg_growth
FROM (
    SELECT
        account_id,
        effective_date,
        current_balance,
        LAG(current_balance, 1) OVER (PARTITION BY account_id ORDER BY effective_date) as prior_balance,
        (current_balance - LAG(current_balance, 1) OVER (PARTITION BY account_id ORDER BY effective_date)) /
        NULLIF(LAG(current_balance, 1) OVER (PARTITION BY account_id ORDER BY effective_date), 0) as monthly_growth_rate
    FROM cfo_banking_demo.bronze_core_banking.deposit_accounts_historical
    WHERE months_since_open >= 1
    AND is_closed = FALSE
    LIMIT 100000
)
"""

result3 = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=query3,
    wait_timeout="50s"
)

if result3.result and result3.result.data_array:
    row = result3.result.data_array[0]
    print(f"  Total rows: {int(row[0]):,}")
    print(f"  Rows with prior_balance: {int(row[1]):,}")
    print(f"  Rows with growth_rate: {int(row[2]):,}")
    print(f"  Avg growth rate: {row[3]}")

# Query 4: Sample data from one account
print("\n4. Sample time-series for one account...")
query4 = """
SELECT
    account_id,
    effective_date,
    current_balance,
    is_current,
    is_closed,
    months_since_open
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts_historical
WHERE account_id = (
    SELECT account_id
    FROM cfo_banking_demo.bronze_core_banking.deposit_accounts_historical
    WHERE is_closed = FALSE
    LIMIT 1
)
ORDER BY effective_date
LIMIT 10
"""

result4 = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=query4,
    wait_timeout="50s"
)

if result4.result and result4.result.data_array:
    print(f"  Account: {result4.result.data_array[0][0]}")
    print("  Date       | Balance | Current | Closed | Months")
    print("  " + "-" * 55)
    for row in result4.result.data_array[:8]:
        print(f"  {row[1]} | ${float(row[2]):>8,.0f} | {row[3]:>7} | {row[4]:>6} | {float(row[5]):>6.1f}")

print("\n" + "=" * 80)
print("DIAGNOSIS COMPLETE")
print("=" * 80)
