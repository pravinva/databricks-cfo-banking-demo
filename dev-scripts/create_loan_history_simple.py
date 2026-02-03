"""
Simple script to create loan_portfolio_historical table.
Uses CTAS (CREATE TABLE AS SELECT) to generate 36 months of history.
"""

from databricks.sdk import WorkspaceClient
import time

w = WorkspaceClient()
WAREHOUSE_ID = "4b9b953939869799"

print("=" * 80)
print("CREATING LOAN_PORTFOLIO_HISTORICAL TABLE")
print("=" * 80)

create_sql = """
CREATE OR REPLACE TABLE cfo_banking_demo.bronze_core_banking.loan_portfolio_historical
USING DELTA
AS
WITH current_loans AS (
    SELECT * FROM cfo_banking_demo.bronze_core_banking.loan_portfolio
    WHERE is_current = TRUE
),
month_sequence AS (
    SELECT explode(sequence(
        date_trunc('month', add_months(current_date(), -36)),
        date_trunc('month', current_date()),
        interval 1 month
    )) as month_date
),
loan_months AS (
    SELECT
        l.*,
        m.month_date as snapshot_month,
        months_between(m.month_date, l.origination_date) as months_since_origination
    FROM current_loans l
    CROSS JOIN month_sequence m
    WHERE m.month_date >= date_trunc('month', l.origination_date)
),
evolved AS (
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
        -- Amortize balance backwards
        CASE
            WHEN months_since_origination >= original_term_months THEN 0.0
            ELSE current_balance * (1.0 - (months_since_origination / NULLIF(original_term_months, 0)))
        END as current_balance,
        principal_balance,
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
        snapshot_month as effective_date,
        (snapshot_month = date_trunc('month', current_date())) as is_current
    FROM loan_months
)
SELECT * FROM evolved
WHERE current_balance >= 0
"""

print("\n1. Executing CREATE TABLE (this will take 2-3 minutes)...")
result = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=create_sql,
    wait_timeout="0s"
)

statement_id = result.statement_id
print(f"   Statement ID: {statement_id}")
print("   Waiting for completion...")

# Poll for completion
max_wait = 300
waited = 0
while waited < max_wait:
    status = w.statement_execution.get_statement(statement_id)
    if status.status.state.value in ['SUCCEEDED', 'CLOSED']:
        print("   ✓ Table created successfully")
        break
    elif status.status.state.value in ['FAILED', 'CANCELED']:
        print(f"   ✗ Failed: {status.status.error}")
        exit(1)
    time.sleep(5)
    waited += 5
    if waited % 30 == 0:
        print(f"   ...still running ({waited}s elapsed)...")

# Verify
print("\n2. Verifying table...")
verify_sql = """
SELECT
    COUNT(*) as total_rows,
    COUNT(DISTINCT loan_id) as unique_loans,
    COUNT(DISTINCT DATE_TRUNC('month', effective_date)) as unique_months,
    MIN(effective_date) as earliest_date,
    MAX(effective_date) as latest_date
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

print("\n" + "=" * 80)
print("COMPLETE")
print("=" * 80)
print("\nNext step: Re-run PPNR notebook - should now have 24+ months of training data")
