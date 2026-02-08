#!/usr/bin/env python3
"""
Backfill deposit subledger + GL (headers + lines) for ALL active deposits.

Why:
- Drill-down UI expects:
  - cfo_banking_demo.silver_finance.deposit_subledger
  - cfo_banking_demo.silver_finance.gl_entries
  - cfo_banking_demo.silver_finance.gl_entry_lines
- Existing demo data often only had activity for a small subset (e.g., Savings).

What this script does:
1) Rebuilds `silver_finance.deposit_subledger` with ONE synthetic "OPEN" transaction per active deposit account.
2) Upserts corresponding GL headers into `silver_finance.gl_entries`.
3) Upserts corresponding double-entry GL lines into `silver_finance.gl_entry_lines`.

Notes:
- This is warehouse-executed, set-based SQL (fast and scalable for 402k accounts).
- It is synthetic demo data (not accounting-grade).
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import os
import time


CATALOG = "cfo_banking_demo"
WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID", "4b9b953939869799")


def run_sql(w: WorkspaceClient, sql: str, title: str, timeout_s: int = 900) -> None:
    print("\n" + "=" * 100)
    print(title)
    print("=" * 100)
    stmt = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        statement=sql,
        wait_timeout=f"{min(timeout_s, 50)}s",
    )

    start = time.time()
    while stmt.status.state in (StatementState.PENDING, StatementState.RUNNING):
        if time.time() - start > timeout_s:
            raise TimeoutError(f"Timed out waiting for statement: {title}")
        time.sleep(2)
        stmt = w.statement_execution.get_statement(stmt.statement_id)

    if stmt.status.state != StatementState.SUCCEEDED:
        err = (stmt.status.error.message if stmt.status and stmt.status.error else "Unknown error")
        raise RuntimeError(f"Statement failed for {title}: {err}")

    print("✓ Success")


def main() -> None:
    w = WorkspaceClient()

    # 1) Rebuild deposit_subledger (OPEN transaction per active deposit)
    # We use `current_balance` as opening amount to guarantee non-empty, consistent drill-down.
    # `gl_entry_id` is deterministic so GL can be upserted idempotently.
    rebuild_subledger = f"""
    CREATE OR REPLACE TABLE {CATALOG}.silver_finance.deposit_subledger AS
    WITH deposits AS (
        SELECT
            account_id,
            customer_name,
            product_type,
            account_open_date,
            CAST(current_balance AS DECIMAL(18,2)) AS opening_amount
        FROM {CATALOG}.bronze_core_banking.deposit_accounts
        WHERE is_current = true
          AND account_status = 'Active'
    )
    SELECT
        CONCAT('DST-', d.account_id, '-OPEN') AS transaction_id,
        TO_TIMESTAMP(d.account_open_date) AS transaction_timestamp,
        d.account_open_date AS posting_date,
        d.account_id AS account_id,
        'OPEN' AS transaction_type,
        d.opening_amount AS amount,
        CAST(0.00 AS DECIMAL(18,2)) AS balance_before,
        d.opening_amount AS balance_after,
        CONCAT('GLE-DEP-', d.account_id) AS gl_entry_id,
        'Branch' AS channel,
        CONCAT('Deposit account opening - ', d.customer_name) AS description,
        CURRENT_TIMESTAMP() AS effective_timestamp
    FROM deposits d
    """
    run_sql(w, rebuild_subledger, "1/3 Rebuild deposit_subledger (OPEN txns for all active deposits)", timeout_s=1800)

    # 2) Upsert GL headers for deposit OPEN events
    # Default bookkeeping metadata is filled with simple constants.
    upsert_gl_entries = f"""
    MERGE INTO {CATALOG}.silver_finance.gl_entries AS t
    USING (
        SELECT
            s.gl_entry_id AS entry_id,
            CAST(s.posting_date AS DATE) AS entry_date,
            CAST(s.transaction_timestamp AS TIMESTAMP) AS entry_timestamp,
            CAST(s.posting_date AS DATE) AS posting_date,
            DATE_FORMAT(s.posting_date, 'yyyy-MM') AS accounting_period,
            'DEPOSIT_SUBLEDGER' AS entry_type,
            'core_banking' AS source_system,
            s.account_id AS source_transaction_id,
            'deposit_open_backfill' AS batch_id,
            'POSTED' AS entry_status,
            s.description AS description,
            CAST(s.amount AS DECIMAL(18,2)) AS total_debits,
            CAST(s.amount AS DECIMAL(18,2)) AS total_credits,
            'system' AS created_by,
            NULL AS approved_by,
            true AS is_balanced,
            false AS is_reversed,
            NULL AS reversed_by_entry_id,
            CURRENT_TIMESTAMP() AS effective_timestamp
        FROM {CATALOG}.silver_finance.deposit_subledger s
        WHERE s.transaction_type = 'OPEN'
    ) AS s
    ON t.entry_id = s.entry_id
    WHEN MATCHED THEN UPDATE SET
        t.entry_date = s.entry_date,
        t.entry_timestamp = s.entry_timestamp,
        t.posting_date = s.posting_date,
        t.accounting_period = s.accounting_period,
        t.entry_type = s.entry_type,
        t.source_system = s.source_system,
        t.source_transaction_id = s.source_transaction_id,
        t.batch_id = s.batch_id,
        t.entry_status = s.entry_status,
        t.description = s.description,
        t.total_debits = s.total_debits,
        t.total_credits = s.total_credits,
        t.created_by = s.created_by,
        t.approved_by = s.approved_by,
        t.is_balanced = s.is_balanced,
        t.is_reversed = s.is_reversed,
        t.reversed_by_entry_id = s.reversed_by_entry_id,
        t.effective_timestamp = s.effective_timestamp
    WHEN NOT MATCHED THEN INSERT (
        entry_id, entry_date, entry_timestamp, posting_date, accounting_period, entry_type, source_system,
        source_transaction_id, batch_id, entry_status, description, total_debits, total_credits, created_by,
        approved_by, is_balanced, is_reversed, reversed_by_entry_id, effective_timestamp
    ) VALUES (
        s.entry_id, s.entry_date, s.entry_timestamp, s.posting_date, s.accounting_period, s.entry_type, s.source_system,
        s.source_transaction_id, s.batch_id, s.entry_status, s.description, s.total_debits, s.total_credits, s.created_by,
        s.approved_by, s.is_balanced, s.is_reversed, s.reversed_by_entry_id, s.effective_timestamp
    )
    """
    run_sql(w, upsert_gl_entries, "2/3 Upsert GL headers (gl_entries) for deposit OPEN txns", timeout_s=1800)

    # 3) Upsert GL lines (double-entry) for deposit OPEN events
    # Line 1: Debit cash (1000)
    # Line 2: Credit deposits payable (2020)
    upsert_gl_lines = f"""
    MERGE INTO {CATALOG}.silver_finance.gl_entry_lines AS t
    USING (
        WITH open_txns AS (
            SELECT
                s.gl_entry_id AS entry_id,
                s.account_id AS account_id,
                s.transaction_id AS txn_id,
                s.posting_date AS posting_date,
                s.amount AS amount,
                d.product_type AS product_code,
                d.customer_segment AS customer_segment
            FROM {CATALOG}.silver_finance.deposit_subledger s
            LEFT JOIN {CATALOG}.bronze_core_banking.deposit_accounts d
              ON d.account_id = s.account_id AND d.is_current = true
            WHERE s.transaction_type = 'OPEN'
        ),
        lines AS (
            SELECT
                CONCAT(entry_id, '-L1') AS line_id,
                entry_id,
                1 AS line_number,
                '1000' AS account_number,
                CAST(amount AS DECIMAL(18,2)) AS debit_amount,
                CAST(0.00 AS DECIMAL(18,2)) AS credit_amount,
                'Deposit opening - cash debit' AS line_description,
                'TREASURY' AS cost_center,
                'DEPOSITS' AS department,
                product_code AS product_code,
                account_id AS customer_id,
                account_id AS reference_number,
                CURRENT_TIMESTAMP() AS effective_timestamp
            FROM open_txns

            UNION ALL

            SELECT
                CONCAT(entry_id, '-L2') AS line_id,
                entry_id,
                2 AS line_number,
                '2020' AS account_number,
                CAST(0.00 AS DECIMAL(18,2)) AS debit_amount,
                CAST(amount AS DECIMAL(18,2)) AS credit_amount,
                'Deposit opening - deposits payable credit' AS line_description,
                'TREASURY' AS cost_center,
                'DEPOSITS' AS department,
                product_code AS product_code,
                account_id AS customer_id,
                account_id AS reference_number,
                CURRENT_TIMESTAMP() AS effective_timestamp
            FROM open_txns
        )
        SELECT * FROM lines
    ) AS s
    ON t.line_id = s.line_id
    WHEN MATCHED THEN UPDATE SET
        t.entry_id = s.entry_id,
        t.line_number = s.line_number,
        t.account_number = s.account_number,
        t.debit_amount = s.debit_amount,
        t.credit_amount = s.credit_amount,
        t.line_description = s.line_description,
        t.cost_center = s.cost_center,
        t.department = s.department,
        t.product_code = s.product_code,
        t.customer_id = s.customer_id,
        t.reference_number = s.reference_number,
        t.effective_timestamp = s.effective_timestamp
    WHEN NOT MATCHED THEN INSERT (
        line_id, entry_id, line_number, account_number, debit_amount, credit_amount, line_description,
        cost_center, department, product_code, customer_id, reference_number, effective_timestamp
    ) VALUES (
        s.line_id, s.entry_id, s.line_number, s.account_number, s.debit_amount, s.credit_amount, s.line_description,
        s.cost_center, s.department, s.product_code, s.customer_id, s.reference_number, s.effective_timestamp
    )
    """
    run_sql(w, upsert_gl_lines, "3/3 Upsert GL lines (gl_entry_lines) for deposit OPEN txns", timeout_s=1800)

    # Quick counts for sanity
    verify = f"""
    SELECT
      (SELECT COUNT(*) FROM {CATALOG}.bronze_core_banking.deposit_accounts WHERE is_current=true AND account_status='Active') AS active_deposits,
      (SELECT COUNT(*) FROM {CATALOG}.silver_finance.deposit_subledger) AS subledger_rows,
      (SELECT COUNT(*) FROM {CATALOG}.silver_finance.gl_entries WHERE entry_type='DEPOSIT_SUBLEDGER') AS gl_entries_rows,
      (SELECT COUNT(*) FROM {CATALOG}.silver_finance.gl_entry_lines WHERE department='DEPOSITS') AS gl_lines_rows
    """
    run_sql(w, verify, "Verification query executed (check warehouse results UI for counts)", timeout_s=300)
    print("\nDone.")


if __name__ == "__main__":
    main()

