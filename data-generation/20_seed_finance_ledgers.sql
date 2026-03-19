-- Seeds synthetic subledger + general ledger tables.
-- Depends on bronze_core_banking tables from 10_seed_core_banking.sql.

USE CATALOG cfo_banking_demo;
CREATE SCHEMA IF NOT EXISTS silver_finance;

CREATE OR REPLACE TABLE silver_finance.deposit_subledger AS
WITH base AS (
  SELECT
    d.account_id,
    d.current_balance,
    d.account_open_date,
    EXPLODE(SEQUENCE(1, 12)) AS txn_idx
  FROM bronze_core_banking.deposit_accounts d
),
rows AS (
  SELECT
    CONCAT('DSTXN_', account_id, '_', LPAD(CAST(txn_idx AS STRING), 2, '0')) AS transaction_id,
    account_id,
    TIMESTAMP(DATE_ADD(account_open_date, txn_idx * 30)) AS transaction_timestamp,
    CASE WHEN txn_idx % 4 = 0 THEN 'Withdrawal' ELSE 'Deposit' END AS transaction_type,
    ROUND(CASE WHEN txn_idx % 4 = 0 THEN -(250 + RAND() * 25000) ELSE (500 + RAND() * 42000) END, 2) AS amount,
    CONCAT('GLD_', account_id, '_', LPAD(CAST(txn_idx AS STRING), 2, '0')) AS gl_entry_id,
    CASE
      WHEN txn_idx % 5 = 0 THEN 'ACH'
      WHEN txn_idx % 5 = 1 THEN 'Online'
      WHEN txn_idx % 5 = 2 THEN 'Branch'
      WHEN txn_idx % 5 = 3 THEN 'Wire'
      ELSE 'ATM'
    END AS channel
  FROM base
)
SELECT
  transaction_id,
  account_id,
  transaction_timestamp,
  transaction_type,
  amount,
  ROUND(12000 + (RAND() * 900000), 2) AS balance_after,
  gl_entry_id,
  channel,
  CONCAT(transaction_type, ' event on ', account_id) AS description
FROM rows;

CREATE OR REPLACE TABLE silver_finance.loan_subledger AS
WITH base AS (
  SELECT
    l.loan_id,
    l.current_balance,
    l.origination_date,
    l.interest_rate,
    EXPLODE(SEQUENCE(1, 18)) AS txn_idx
  FROM bronze_core_banking.loan_portfolio l
),
rows AS (
  SELECT
    CONCAT('LSTXN_', loan_id, '_', LPAD(CAST(txn_idx AS STRING), 2, '0')) AS transaction_id,
    loan_id,
    TIMESTAMP(DATE_ADD(origination_date, txn_idx * 30)) AS transaction_timestamp,
    CASE WHEN txn_idx % 9 = 0 THEN 'Fee' ELSE 'Payment' END AS transaction_type,
    ROUND(600 + RAND() * 26000, 2) AS principal_amount,
    ROUND((600 + RAND() * 26000) * (0.08 + RAND() * 0.22), 2) AS interest_amount
  FROM base
)
SELECT
  transaction_id,
  loan_id,
  transaction_timestamp,
  transaction_type,
  principal_amount,
  interest_amount,
  ROUND(2000 + (RAND() * 3500000), 2) AS balance_after
FROM rows;

CREATE OR REPLACE TABLE silver_finance.gl_entries AS
SELECT
  gl_entry_id AS entry_id,
  account_id AS source_transaction_id,
  DATE(transaction_timestamp) AS entry_date,
  transaction_timestamp AS entry_timestamp,
  ROUND(ABS(amount), 2) AS total_debits,
  ROUND(ABS(amount), 2) AS total_credits,
  true AS is_balanced,
  description
FROM silver_finance.deposit_subledger
UNION ALL
SELECT
  CONCAT('GLL_', transaction_id) AS entry_id,
  loan_id AS source_transaction_id,
  DATE(transaction_timestamp) AS entry_date,
  transaction_timestamp AS entry_timestamp,
  ROUND(principal_amount + interest_amount, 2) AS total_debits,
  ROUND(principal_amount + interest_amount, 2) AS total_credits,
  true AS is_balanced,
  CONCAT(transaction_type, ' event on ', loan_id) AS description
FROM silver_finance.loan_subledger;

CREATE OR REPLACE TABLE silver_finance.gl_entry_lines AS
SELECT
  e.entry_id,
  CASE WHEN side.n = 1 THEN '1110-CASH' ELSE '2210-DEPOSITS' END AS account_number,
  CASE WHEN side.n = 1 THEN e.total_debits ELSE e.total_credits END AS amount,
  side.n = 1 AS is_debit,
  e.source_transaction_id AS customer_id,
  e.source_transaction_id AS reference_number
FROM silver_finance.gl_entries e
CROSS JOIN (SELECT EXPLODE(ARRAY(1, 2)) AS n) side;
