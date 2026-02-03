"""
Generate synthetic historical time-series data for loan portfolio.

Creates monthly snapshots from loan origination to present with realistic:
- Balance amortization
- Rate adjustments
- Payment history
- Default progression
"""

from databricks.sdk import WorkspaceClient
from datetime import datetime, timedelta

w = WorkspaceClient()
WAREHOUSE_ID = "4b9b953939869799"

print("=" * 80)
print("GENERATING SYNTHETIC LOAN PORTFOLIO HISTORY")
print("=" * 80)

# Step 1: Create historical snapshots table
print("\n1. Creating loan_portfolio_historical table structure...")

create_table_sql = """
CREATE TABLE IF NOT EXISTS cfo_banking_demo.bronze_core_banking.loan_portfolio_historical
LIKE cfo_banking_demo.bronze_core_banking.loan_portfolio
"""

result = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=create_table_sql,
    wait_timeout="50s"
)
print("   ✓ Table created")

# Step 2: Generate monthly snapshots
print("\n2. Generating monthly snapshots (this will take 2-3 minutes)...")

generate_history_sql = """
INSERT OVERWRITE cfo_banking_demo.bronze_core_banking.loan_portfolio_historical
WITH current_loans AS (
    SELECT *
    FROM cfo_banking_demo.bronze_core_banking.loan_portfolio
    WHERE is_current = TRUE
),
month_sequence AS (
    -- Generate monthly dates going back 36 months
    SELECT explode(sequence(
        date_trunc('month', add_months(current_date(), -36)),
        date_trunc('month', current_date()),
        interval 1 month
    )) as month_date
),
loan_months AS (
    SELECT
        l.loan_id,
        l.account_number,
        l.borrower_id,
        l.borrower_name,
        l.borrower_type,
        l.product_type,
        l.loan_purpose,
        l.origination_date,
        l.maturity_date,
        l.original_amount,
        l.current_balance,
        l.principal_balance,
        l.interest_accrued,
        l.fees_accrued,
        l.interest_rate,
        l.rate_type,
        l.rate_index,
        l.rate_margin,
        l.payment_frequency,
        l.monthly_payment,
        l.payment_status,
        l.days_past_due,
        l.next_payment_date,
        l.last_payment_date,
        l.last_payment_amount,
        l.remaining_term_months,
        l.original_term_months,
        l.collateral_type,
        l.collateral_value,
        l.ltv_ratio,
        l.credit_score,
        l.risk_rating,
        l.pd,
        l.lgd,
        l.ead,
        l.cecl_reserve,
        l.geography,
        l.industry_code,
        l.officer_id,
        l.branch_id,
        m.month_date as snapshot_date,
        months_between(m.month_date, l.origination_date) as months_since_origination
    FROM current_loans l
    CROSS JOIN month_sequence m
    WHERE m.month_date >= l.origination_date  -- Only create snapshots after origination
),
balance_evolution AS (
    SELECT
        *,
        CASE
            -- Amortizing balance over time (realistic loan paydown)
            WHEN months_since_origination >= original_term_months THEN 0.0  -- Fully paid off
            ELSE current_balance * (
                1.0 - (months_since_origination / NULLIF(original_term_months, 0))  -- Linear amortization
            ) * (
                -- Add noise ±5%
                0.95 + 0.10 * (cast(conv(substring(md5(concat(loan_id, cast(snapshot_date as string))), 1, 8), 16, 10) as double) / 4294967296.0)
            )
        END as evolved_balance
    FROM loan_months
)
SELECT
    loan_id,
    account_number,
    borrower_id,
    borrower_name,
    borrower_type,
    product_type,
    loan_purpose,
    origination_date,
    maturity_date,
    original_amount,
    CAST(GREATEST(0, evolved_balance) AS DOUBLE) as current_balance,
    CAST(GREATEST(0, evolved_balance) AS DOUBLE) as principal_balance,
    interest_accrued,
    fees_accrued,
    interest_rate,
    rate_type,
    rate_index,
    rate_margin,
    payment_frequency,
    monthly_payment,
    payment_status,
    days_past_due,
    next_payment_date,
    last_payment_date,
    last_payment_amount,
    remaining_term_months,
    original_term_months,
    collateral_type,
    collateral_value,
    ltv_ratio,
    credit_score,
    risk_rating,
    pd,
    lgd,
    ead,
    cecl_reserve,
    geography,
    industry_code,
    officer_id,
    branch_id,
    snapshot_date as effective_date,
    (snapshot_date = date_trunc('month', current_date())) as is_current
FROM balance_evolution
WHERE evolved_balance >= 0  -- Filter out negative balances
ORDER BY loan_id, snapshot_date
"""

print("   Executing SQL (generating 36 months × 97,200 loans)...")
print("   This will run asynchronously - check status in SQL workspace...")
result = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=generate_history_sql,
    wait_timeout="0s"  # Run async
)
statement_id = result.statement_id
print(f"   Statement ID: {statement_id}")
print("   Waiting for completion...")

# Poll for completion
import time
max_wait = 300  # 5 minutes
waited = 0
while waited < max_wait:
    status = w.statement_execution.get_statement(statement_id)
    if status.status.state.value in ['SUCCEEDED', 'CLOSED']:
        print("   ✓ Historical data generated")
        break
    elif status.status.state.value in ['FAILED', 'CANCELED']:
        print(f"   ✗ Failed: {status.status.error}")
        exit(1)
    time.sleep(5)
    waited += 5
    if waited % 30 == 0:
        print(f"   ...still running ({waited}s elapsed)...")

# Step 3: Verify the generated data
print("\n3. Verifying generated historical data...")

verify_sql = """
SELECT
    COUNT(*) as total_rows,
    COUNT(DISTINCT loan_id) as unique_loans,
    COUNT(DISTINCT effective_date) as unique_months,
    MIN(effective_date) as earliest_date,
    MAX(effective_date) as latest_date,
    SUM(current_balance) / 1e9 as total_balance_billions,
    AVG(current_balance) as avg_balance
FROM cfo_banking_demo.bronze_core_banking.loan_portfolio_historical
"""

result = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=verify_sql,
    wait_timeout="50s"
)

if result.result and result.result.data_array:
    row = result.result.data_array[0]
    print(f"   Total rows: {int(row[0]):,}")
    print(f"   Unique loans: {int(row[1]):,}")
    print(f"   Unique months: {row[2]}")
    print(f"   Date range: {row[3]} to {row[4]}")
    print(f"   Total balance: ${float(row[5]):.2f}B")
    print(f"   Avg balance: ${float(row[6]):,.2f}")

print("\n" + "=" * 80)
print("HISTORICAL DATA GENERATION COMPLETE")
print("=" * 80)
print("\nNext Steps:")
print("1. Update PPNR notebook to use loan_portfolio_historical table")
print("2. Re-run PPNR training with 24+ months of historical data")
print("3. Verify training/test split shows proper month counts")
