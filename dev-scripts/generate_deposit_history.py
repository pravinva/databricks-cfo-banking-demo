"""
Generate synthetic historical time-series data for deposit accounts.

This script creates realistic monthly snapshots from account opening date to present,
including account closures and balance movements based on:
- Relationship category (Strategic/Tactical/Expendable)
- Product type (Checking/Savings/MMDA/NOW)
- Rate environment
- Account tenure
"""

from databricks.sdk import WorkspaceClient
from datetime import datetime, timedelta
import random

w = WorkspaceClient()
WAREHOUSE_ID = "4b9b953939869799"

print("=" * 80)
print("GENERATING SYNTHETIC DEPOSIT ACCOUNT HISTORY")
print("=" * 80)

# Step 1: Create historical snapshots table
print("\n1. Creating historical snapshots table structure...")

create_table_sql = """
CREATE TABLE IF NOT EXISTS cfo_banking_demo.bronze_core_banking.deposit_accounts_historical (
    account_id STRING,
    customer_id STRING,
    product_type STRING,
    customer_segment STRING,
    account_open_date DATE,
    effective_date DATE,
    current_balance DECIMAL(18,2),
    stated_rate DECIMAL(8,4),
    is_current BOOLEAN,
    is_closed BOOLEAN,
    closure_date DATE,
    months_since_open DECIMAL(10,2)
) USING DELTA
PARTITIONED BY (effective_date)
"""

result = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=create_table_sql,
    wait_timeout="50s"
)
print("   ✓ Table created")

# Step 2: Generate monthly snapshots with realistic behavior
print("\n2. Generating monthly snapshots (this will take 2-3 minutes)...")

generate_history_sql = """
INSERT OVERWRITE cfo_banking_demo.bronze_core_banking.deposit_accounts_historical
WITH current_accounts AS (
    SELECT
        account_id,
        customer_id,
        product_type,
        customer_segment,
        account_open_date,
        current_balance,
        stated_rate,
        -- Calculate relationship category
        CASE
            WHEN customer_id IN (
                SELECT customer_id
                FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
                WHERE is_current = TRUE
                GROUP BY customer_id
                HAVING COUNT(DISTINCT account_id) >= 3
                AND SUM(current_balance) >= 500000
            ) THEN 'Strategic'
            WHEN customer_id IN (
                SELECT customer_id
                FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
                WHERE is_current = TRUE
                GROUP BY customer_id
                HAVING COUNT(DISTINCT account_id) >= 2
                OR SUM(current_balance) >= 100000
            ) THEN 'Tactical'
            ELSE 'Expendable'
        END as relationship_category
    FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
    WHERE is_current = TRUE
),
month_sequence AS (
    -- Generate monthly dates from account open to present
    SELECT explode(sequence(
        date_trunc('month', add_months(current_date(), -36)),  -- 3 years back
        date_trunc('month', current_date()),
        interval 1 month
    )) as month_date
),
account_months AS (
    SELECT
        a.*,
        m.month_date as effective_date,
        months_between(m.month_date, a.account_open_date) as months_since_open
    FROM current_accounts a
    CROSS JOIN month_sequence m
    WHERE m.month_date >= a.account_open_date
),
closure_probabilities AS (
    -- Assign closure probability based on characteristics
    SELECT
        *,
        CASE relationship_category
            WHEN 'Strategic' THEN 0.02   -- 2% annual closure rate
            WHEN 'Tactical' THEN 0.06    -- 6% annual closure rate
            WHEN 'Expendable' THEN 0.18  -- 18% annual closure rate
        END / 12 as monthly_closure_prob,  -- Convert to monthly

        CASE product_type
            WHEN 'Checking' THEN 1.0
            WHEN 'NOW' THEN 1.2
            WHEN 'Savings' THEN 1.5
            WHEN 'MMDA' THEN 1.8
            ELSE 1.0
        END as product_multiplier
    FROM account_months
),
simulated_closures AS (
    SELECT
        *,
        -- Simulate closure using account_id hash for deterministic randomness
        CASE
            WHEN months_since_open < 3 THEN FALSE  -- No closures in first 3 months
            WHEN (cast(conv(substring(md5(account_id), 1, 8), 16, 10) as double) / 4294967296.0)
                 < (monthly_closure_prob * product_multiplier * months_since_open / 12) THEN TRUE
            ELSE FALSE
        END as should_close,

        -- Calculate closure date (first month where closure happens)
        CASE
            WHEN months_since_open < 3 THEN NULL
            WHEN (cast(conv(substring(md5(account_id), 1, 8), 16, 10) as double) / 4294967296.0)
                 < (monthly_closure_prob * product_multiplier * months_since_open / 12)
            THEN effective_date
            ELSE NULL
        END as potential_closure_date
    FROM closure_probabilities
),
account_with_closure AS (
    SELECT
        account_id,
        customer_id,
        product_type,
        customer_segment,
        account_open_date,
        effective_date,
        current_balance,
        stated_rate,
        relationship_category,
        months_since_open,
        MIN(potential_closure_date) OVER (PARTITION BY account_id) as closure_date
    FROM simulated_closures
),
balance_evolution AS (
    SELECT
        *,
        CASE
            -- If closed, zero balance after closure
            WHEN closure_date IS NOT NULL AND effective_date >= closure_date THEN 0.0

            -- Otherwise, apply monthly growth rate based on relationship
            ELSE current_balance * POWER(
                1 + CASE relationship_category
                    WHEN 'Strategic' THEN 0.03      -- 3% annual growth
                    WHEN 'Tactical' THEN 0.01       -- 1% annual growth
                    WHEN 'Expendable' THEN -0.05    -- -5% annual runoff
                END / 12,
                months_since_open
            ) * (
                -- Add random noise (±10%)
                0.9 + 0.2 * (cast(conv(substring(md5(concat(account_id, cast(effective_date as string))), 1, 8), 16, 10) as double) / 4294967296.0)
            )
        END as evolved_balance
    FROM account_with_closure
)
SELECT
    account_id,
    customer_id,
    product_type,
    customer_segment,
    account_open_date,
    effective_date,
    CAST(GREATEST(0, evolved_balance) AS DECIMAL(18,2)) as current_balance,
    stated_rate,
    CASE
        WHEN effective_date = date_trunc('month', current_date()) THEN TRUE
        ELSE FALSE
    END as is_current,
    CASE
        WHEN closure_date IS NOT NULL AND effective_date >= closure_date THEN TRUE
        ELSE FALSE
    END as is_closed,
    closure_date,
    CAST(months_since_open AS DECIMAL(10,2)) as months_since_open
FROM balance_evolution
WHERE evolved_balance >= 0  -- Filter out any negative balances
ORDER BY account_id, effective_date
"""

print("   Executing SQL (generating 36 months × 402,000 accounts)...")
result = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=generate_history_sql,
    wait_timeout="50s"
)
print("   ✓ Historical data generated")

# Step 3: Verify the generated data
print("\n3. Verifying generated historical data...")

verify_sql = """
SELECT
    COUNT(*) as total_rows,
    COUNT(DISTINCT account_id) as unique_accounts,
    COUNT(DISTINCT effective_date) as unique_months,
    SUM(CASE WHEN is_closed = TRUE THEN 1 ELSE 0 END) as closed_account_snapshots,
    COUNT(DISTINCT CASE WHEN is_closed = TRUE THEN account_id END) as unique_closed_accounts,
    MIN(effective_date) as earliest_date,
    MAX(effective_date) as latest_date,
    AVG(current_balance) as avg_balance
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts_historical
"""

result = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=verify_sql,
    wait_timeout="50s"
)

if result.result and result.result.data_array:
    row = result.result.data_array[0]
    print(f"   Total rows: {int(row[0]):,}")
    print(f"   Unique accounts: {int(row[1]):,}")
    print(f"   Unique months: {row[2]}")
    print(f"   Closed account snapshots: {int(row[3]):,}")
    print(f"   Unique closed accounts: {int(row[4]):,}")
    print(f"   Date range: {row[5]} to {row[6]}")
    print(f"   Avg balance: ${float(row[7]):,.2f}")

# Step 4: Show closure rates by segment
print("\n4. Closure rates by relationship category...")

closure_sql = """
SELECT
    CASE
        WHEN customer_id IN (
            SELECT customer_id
            FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
            WHERE is_current = TRUE
            GROUP BY customer_id
            HAVING COUNT(DISTINCT account_id) >= 3 AND SUM(current_balance) >= 500000
        ) THEN 'Strategic'
        WHEN customer_id IN (
            SELECT customer_id
            FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
            WHERE is_current = TRUE
            GROUP BY customer_id
            HAVING COUNT(DISTINCT account_id) >= 2 OR SUM(current_balance) >= 100000
        ) THEN 'Tactical'
        ELSE 'Expendable'
    END as relationship_category,
    COUNT(DISTINCT account_id) as total_accounts,
    COUNT(DISTINCT CASE WHEN is_closed = TRUE THEN account_id END) as closed_accounts,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN is_closed = TRUE THEN account_id END) / COUNT(DISTINCT account_id), 2) as closure_rate_pct
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts_historical
GROUP BY 1
ORDER BY 1
"""

result = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=closure_sql,
    wait_timeout="50s"
)

if result.result and result.result.data_array:
    print("   Category        | Total  | Closed | Rate")
    print("   " + "-" * 50)
    for row in result.result.data_array:
        print(f"   {row[0]:<15} | {int(row[1]):>6,} | {int(row[2]):>6,} | {row[3]:>5}%")

print("\n" + "=" * 80)
print("HISTORICAL DATA GENERATION COMPLETE")
print("=" * 80)
print("\nNext Steps:")
print("1. Update Phase 2 notebook to use deposit_accounts_historical table")
print("2. Re-run cohort analysis with historical data")
print("3. Component decay metrics should now show realistic λ and g values")
