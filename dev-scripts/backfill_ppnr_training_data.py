"""
Backfill loan_portfolio_historical table for PPNR model training.

Creates a historical table with 24 months of snapshots by:
1. Taking current loan_portfolio snapshots
2. Generating monthly snapshots going back 24 months with realistic changes
3. Creating loan_portfolio_historical table (separate from main table)

Note: deposit_accounts_historical already exists from previous script.
"""

from databricks.sdk import WorkspaceClient
from datetime import datetime, timedelta

w = WorkspaceClient()
WAREHOUSE_ID = "4b9b953939869799"

print("=" * 80)
print("BACKFILLING LOAN PORTFOLIO HISTORICAL - 24 MONTHS")
print("=" * 80)

# Step 1: Create loan_portfolio_historical table
print("\n1. Creating loan_portfolio_historical table structure...")

create_table_sql = """
CREATE TABLE IF NOT EXISTS cfo_banking_demo.bronze_core_banking.loan_portfolio_historical (
    loan_id STRING,
    customer_id STRING,
    product_type STRING,
    borrower_name STRING,
    borrower_segment STRING,
    branch_id STRING,
    effective_date DATE,
    origination_date DATE,
    maturity_date DATE,
    original_amount DECIMAL(18,2),
    current_balance DECIMAL(18,2),
    interest_rate DECIMAL(8,4),
    loan_term_months INT,
    payment_frequency STRING,
    collateral_type STRING,
    collateral_value DECIMAL(18,2),
    loan_to_value_ratio DECIMAL(8,4),
    credit_score INT,
    debt_service_coverage_ratio DECIMAL(8,4),
    risk_rating STRING,
    is_performing BOOLEAN,
    days_past_due INT,
    last_payment_date DATE,
    is_current BOOLEAN,
    last_updated TIMESTAMP
) USING DELTA
PARTITIONED BY (effective_date)
"""

result = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=create_table_sql,
    wait_timeout="50s"
)
print("   ✓ Table created")

# Step 2: Backfill loan_portfolio_historical with monthly snapshots
print("\n2. Backfilling loan_portfolio_historical with 24 months of snapshots...")

backfill_loans_sql = """
INSERT OVERWRITE cfo_banking_demo.bronze_core_banking.loan_portfolio_historical
WITH current_snapshot AS (
    -- Get current month's data
    SELECT *
    FROM cfo_banking_demo.bronze_core_banking.loan_portfolio
    WHERE DATE_TRUNC('month', effective_date) = DATE_TRUNC('month', CURRENT_DATE())
),
month_sequence AS (
    -- Generate monthly dates for past 24 months (excluding current month)
    SELECT explode(sequence(
        add_months(DATE_TRUNC('month', CURRENT_DATE()), -24),
        add_months(DATE_TRUNC('month', CURRENT_DATE()), -1),
        interval 1 month
    )) as month_date
),
historical_snapshots AS (
    SELECT
        c.loan_id,
        c.customer_id,
        c.product_type,
        c.borrower_name,
        c.borrower_segment,
        c.branch_id,

        -- Set effective_date to historical month
        m.month_date as effective_date,

        c.origination_date,
        c.maturity_date,
        c.original_amount,

        -- Current balance decreases going back in time (amortization in reverse)
        c.current_balance * (
            1.0 + (months_between(CURRENT_DATE(), m.month_date) * 0.015)  -- Balance was higher 1.5% per month
        ) as current_balance,

        -- Interest rate was higher in the past due to Fed rate environment
        c.interest_rate * (
            1.0 + (months_between(CURRENT_DATE(), m.month_date) * 0.015)
        ) as interest_rate,

        c.loan_term_months,
        c.payment_frequency,
        c.collateral_type,
        c.collateral_value,
        c.loan_to_value_ratio,
        c.credit_score,
        c.debt_service_coverage_ratio,
        c.risk_rating,
        c.is_performing,
        c.days_past_due,
        c.last_payment_date,

        FALSE as is_current,  -- Historical snapshots are not current
        c.last_updated

    FROM current_snapshot c
    CROSS JOIN month_sequence m
)
SELECT * FROM historical_snapshots
"""

print("   Executing SQL (generating 24 months of loan snapshots)...")
result = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=backfill_loans_sql,
    wait_timeout="50s"
)
print("   ✓ Loan portfolio backfilled")

# Step 3: Verify the backfilled data
print("\n3. Verifying backfilled data...")

verify_deposits_sql = """
SELECT
    'deposit_accounts' as table_name,
    COUNT(*) as total_rows,
    COUNT(DISTINCT DATE_TRUNC('month', effective_date)) as unique_months,
    MIN(effective_date) as earliest_date,
    MAX(effective_date) as latest_date,
    SUM(current_balance) / 1e9 as total_balance_billions
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
"""

result = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=verify_deposits_sql,
    wait_timeout="50s"
)

if result.result and result.result.data_array:
    row = result.result.data_array[0]
    print(f"\n   {row[0]}:")
    print(f"      Total rows: {int(row[1]):,}")
    print(f"      Unique months: {row[2]}")
    print(f"      Date range: {row[3]} to {row[4]}")
    print(f"      Total balance: ${float(row[5]):.2f}B")

verify_loans_sql = """
SELECT
    'loan_portfolio_historical' as table_name,
    COUNT(*) as total_rows,
    COUNT(DISTINCT DATE_TRUNC('month', effective_date)) as unique_months,
    MIN(effective_date) as earliest_date,
    MAX(effective_date) as latest_date,
    SUM(current_balance) / 1e9 as total_balance_billions
FROM cfo_banking_demo.bronze_core_banking.loan_portfolio_historical
"""

result = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=verify_loans_sql,
    wait_timeout="50s"
)

if result.result and result.result.data_array:
    row = result.result.data_array[0]
    print(f"\n   {row[0]}:")
    print(f"      Total rows: {int(row[1]):,}")
    print(f"      Unique months: {row[2]}")
    print(f"      Date range: {row[3]} to {row[4]}")
    print(f"      Total balance: ${float(row[5]):.2f}B")

# Step 4: Test PPNR query CTEs
print("\n4. Testing PPNR query CTEs after backfill...")

test_ctes_sql = """
WITH deposit_metrics AS (
    SELECT
        DATE_TRUNC('month', effective_date) as month,
        COUNT(DISTINCT account_id) as active_deposit_accounts
    FROM cfo_banking_demo.bronze_core_banking.deposit_accounts_historical
    WHERE effective_date >= DATE_SUB(CURRENT_DATE(), 730)
    GROUP BY DATE_TRUNC('month', effective_date)
),
loan_metrics AS (
    SELECT
        DATE_TRUNC('month', effective_date) as month,
        COUNT(DISTINCT loan_id) as active_loans
    FROM cfo_banking_demo.bronze_core_banking.loan_portfolio_historical
    WHERE effective_date >= DATE_SUB(CURRENT_DATE(), 730)
    GROUP BY DATE_TRUNC('month', effective_date)
)
SELECT
    'deposit_metrics' as cte_name,
    COUNT(*) as row_count,
    MIN(month) as earliest_month,
    MAX(month) as latest_month
FROM deposit_metrics

UNION ALL

SELECT
    'loan_metrics' as cte_name,
    COUNT(*) as row_count,
    MIN(month) as earliest_month,
    MAX(month) as latest_month
FROM loan_metrics
"""

result = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=test_ctes_sql,
    wait_timeout="50s"
)

if result.result and result.result.data_array:
    print("\n   CTE Test Results:")
    print("   " + "-" * 70)
    for row in result.result.data_array:
        print(f"   {row[0]:<20} | Rows: {row[1]:<3} | Range: {row[2]} to {row[3]}")

print("\n" + "=" * 80)
print("BACKFILL COMPLETE")
print("=" * 80)
print("\nNext Steps:")
print("1. Re-run PPNR notebook diagnostic cells to verify 24 months of data")
print("2. Train Non-Interest Income model with full 24-month dataset")
print("3. Expected training/test split: 19 months train, 5 months test")
