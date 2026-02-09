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
import os
import time


def resolve_warehouse_id(w: WorkspaceClient) -> str:
    """
    Resolve a SQL Warehouse ID for Statement Execution.

    Root cause fix:
    - The previous version hard-coded a warehouse ID that doesn't exist in all workspaces.
    - This resolver prefers an explicit env var, otherwise discovers an available warehouse.
    """
    explicit = os.getenv("DATABRICKS_WAREHOUSE_ID")
    if explicit:
        return explicit

    try:
        warehouses = list(w.warehouses.list())
    except Exception as e:
        raise RuntimeError(
            "Could not list SQL warehouses. Set DATABRICKS_WAREHOUSE_ID to a valid warehouse id."
        ) from e

    if not warehouses:
        raise RuntimeError(
            "No SQL warehouses found in this workspace. Create one, or set DATABRICKS_WAREHOUSE_ID."
        )

    # Prefer common defaults if present (case-insensitive exact match).
    preferred_names = [
        "Serverless Starter Warehouse",
        "Starter Warehouse",
        "Serverless",
        "Shared Warehouse",
    ]
    for pref in preferred_names:
        for wh in warehouses:
            if (getattr(wh, "name", "") or "").strip().lower() == pref.lower():
                return wh.id

    # Otherwise prefer a running/starting warehouse, else just pick the first.
    for wh in warehouses:
        if getattr(wh, "state", None) in ("RUNNING", "STARTING"):
            return wh.id

    return warehouses[0].id


def execute_sql(
    w: WorkspaceClient,
    warehouse_id: str,
    statement: str,
    *,
    label: str = "sql",
    wait_timeout: str = "50s",
    poll_interval_s: float = 1.0,
    max_wait_s: float = 900.0,
):
    """
    Execute SQL via Statement Execution and wait for completion.

    Note: `execute_statement(..., wait_timeout=...)` may return before completion.
    This helper ensures we only proceed once the statement is SUCCEEDED.
    """
    resp = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=statement,
        wait_timeout=wait_timeout,
    )
    statement_id = resp.statement_id
    if not statement_id:
        raise RuntimeError("Statement execution did not return a statement_id.")

    def normalize_state(s):
        # databricks-sdk may return an enum (e.g. StatementState.SUCCEEDED) or a string.
        if s is None:
            return None
        return getattr(s, "value", str(s))

    state = normalize_state(getattr(getattr(resp, "status", None), "state", None))
    print(f"   → submitted {label}: statement_id={statement_id} initial_state={state}")
    start = time.time()
    last_print = start
    while state not in ("SUCCEEDED", "FAILED", "CANCELED"):
        if time.time() - start > max_wait_s:
            raise TimeoutError(f"Timed out waiting for statement_id={statement_id} state={state}")
        time.sleep(poll_interval_s)
        resp = w.statement_execution.get_statement(statement_id)
        state = normalize_state(getattr(getattr(resp, "status", None), "state", None))
        now = time.time()
        if now - last_print >= 10:
            print(f"     … {label} still {state} (elapsed={int(now-start)}s)")
            last_print = now

    if state != "SUCCEEDED":
        err = getattr(getattr(resp, "status", None), "error", None)
        raise RuntimeError(f"SQL failed: statement_id={statement_id} state={state} error={err}")

    return resp

w = WorkspaceClient()
WAREHOUSE_ID = resolve_warehouse_id(w)
print(f"Using SQL warehouse_id={WAREHOUSE_ID}")

print("=" * 80)
print("GENERATING SYNTHETIC DEPOSIT ACCOUNT HISTORY")
print("=" * 80)

# Step 1: Create historical snapshots table
print("\n1. Creating historical snapshots table structure...")

create_table_sql = """
CREATE OR REPLACE TABLE cfo_banking_demo.bronze_core_banking.deposit_accounts_historical (
    account_id STRING,
    customer_id STRING,
    product_type STRING,
    customer_segment STRING,
    account_open_date DATE,
    effective_date DATE,
    current_balance DECIMAL(18,2),
    average_balance_30d DECIMAL(18,2),
    average_balance_90d DECIMAL(18,2),
    stated_rate DECIMAL(8,4),
    transaction_count_30d INT,
    account_status STRING,
    is_current BOOLEAN,
    is_closed BOOLEAN,
    closure_date DATE,
    months_since_open DECIMAL(10,2)
) USING DELTA
PARTITIONED BY (effective_date)
"""

result = execute_sql(w, WAREHOUSE_ID, create_table_sql, label="create_table", wait_timeout="50s")
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
),
with_features AS (
    SELECT
        *,
        GREATEST(0, evolved_balance) AS evolved_balance_pos,
        -- Deterministic pseudo-random in [0, 1) based on (account_id, effective_date)
        (cast(conv(substring(md5(concat(account_id, '|txn|', cast(effective_date as string))), 1, 8), 16, 10) as double) / 4294967296.0) AS txn_u,
        CAST(
            CASE
                WHEN closure_date IS NOT NULL AND effective_date >= closure_date THEN 0
                ELSE
                    GREATEST(
                        0,
                        CAST(
                            (
                                -- base activity by relationship category
                                CASE relationship_category
                                    WHEN 'Strategic' THEN 60
                                    WHEN 'Tactical' THEN 35
                                    ELSE 15
                                END
                                -- product effect
                                * CASE product_type
                                    WHEN 'Checking' THEN 1.2
                                    WHEN 'NOW' THEN 1.0
                                    WHEN 'Savings' THEN 0.8
                                    WHEN 'MMDA' THEN 0.6
                                    ELSE 1.0
                                END
                                -- random variation (±35%)
                                * (0.65 + 0.70 * (cast(conv(substring(md5(concat(account_id, '|txnvar|', cast(effective_date as string))), 1, 8), 16, 10) as double) / 4294967296.0))
                            ) AS INT
                        )
                    )
            END AS INT
        ) AS transaction_count_30d,
        -- Approximate 30d/90d averages from monthly snapshots via rolling windows.
        CAST(
            AVG(GREATEST(0, evolved_balance)) OVER (
                PARTITION BY account_id
                ORDER BY effective_date
                ROWS BETWEEN 1 PRECEDING AND CURRENT ROW
            ) AS DECIMAL(18,2)
        ) AS average_balance_30d,
        CAST(
            AVG(GREATEST(0, evolved_balance)) OVER (
                PARTITION BY account_id
                ORDER BY effective_date
                ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
            ) AS DECIMAL(18,2)
        ) AS average_balance_90d
    FROM balance_evolution
),
with_status AS (
    SELECT
        *,
        CASE
            WHEN closure_date IS NOT NULL AND effective_date >= closure_date THEN 'Closed'
            WHEN transaction_count_30d <= 2 THEN 'Dormant'
            ELSE 'Active'
        END AS account_status
    FROM with_features
)
SELECT
    account_id,
    customer_id,
    product_type,
    customer_segment,
    account_open_date,
    effective_date,
    CAST(evolved_balance_pos AS DECIMAL(18,2)) as current_balance,
    average_balance_30d,
    average_balance_90d,
    stated_rate,
    transaction_count_30d,
    account_status,
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
FROM with_status
WHERE evolved_balance_pos >= 0  -- Filter out any negative balances
ORDER BY account_id, effective_date
"""

print("   Executing SQL (generating 36 months × 402,000 accounts)...")
result = execute_sql(
    w,
    WAREHOUSE_ID,
    generate_history_sql,
    label="generate_history",
    wait_timeout="50s",
    max_wait_s=3600.0,
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

result = execute_sql(w, WAREHOUSE_ID, verify_sql, label="verify", wait_timeout="50s")

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

result = execute_sql(w, WAREHOUSE_ID, closure_sql, label="closure_rates", wait_timeout="50s")

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
