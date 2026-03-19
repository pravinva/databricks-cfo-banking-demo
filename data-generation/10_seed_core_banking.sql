-- Seeds synthetic core banking datasets used by the API.
-- Safe to rerun: tables are recreated each run.

USE CATALOG cfo_banking_demo;

CREATE OR REPLACE TABLE bronze_core_banking.deposit_accounts AS
WITH ids AS (
  SELECT EXPLODE(SEQUENCE(1, 2500)) AS n
),
base AS (
  SELECT
    CONCAT('D', LPAD(CAST(n AS STRING), 7, '0')) AS account_id,
    CONCAT('Customer_', LPAD(CAST(n AS STRING), 6, '0')) AS customer_name,
    CASE n % 6
      WHEN 0 THEN 'MMDA'
      WHEN 1 THEN 'Savings'
      WHEN 2 THEN 'DDA'
      WHEN 3 THEN 'NOW'
      WHEN 4 THEN 'CD'
      ELSE 'Business Checking'
    END AS product_type,
    CASE n % 5
      WHEN 0 THEN 'Consumer'
      WHEN 1 THEN 'Affluent'
      WHEN 2 THEN 'SMB'
      WHEN 3 THEN 'Commercial'
      ELSE 'Corporate'
    END AS customer_segment,
    DATE_SUB(CURRENT_DATE(), CAST(30 + RAND() * 2200 AS INT)) AS account_open_date,
    CASE
      WHEN n % 6 = 4 THEN 250000 + RAND() * 2500000
      WHEN n % 5 = 4 THEN 500000 + RAND() * 8000000
      ELSE 25000 + RAND() * 750000
    END AS current_balance,
    CASE
      WHEN n % 6 = 4 THEN 0.0375 + RAND() * 0.011
      WHEN n % 6 = 0 THEN 0.0190 + RAND() * 0.012
      WHEN n % 6 = 1 THEN 0.0140 + RAND() * 0.011
      ELSE 0.0040 + RAND() * 0.008
    END AS stated_rate,
    CASE
      WHEN n % 5 IN (0, 1) THEN 0.16 + RAND() * 0.16
      WHEN n % 5 IN (2, 3) THEN 0.34 + RAND() * 0.20
      ELSE 0.62 + RAND() * 0.24
    END AS beta
  FROM ids
)
SELECT
  account_id,
  customer_name,
  product_type,
  customer_segment,
  account_open_date,
  ROUND(current_balance, 2) AS current_balance,
  ROUND(stated_rate, 6) AS stated_rate,
  ROUND(LEAST(0.98, GREATEST(0.05, beta)), 6) AS beta,
  'Active' AS account_status,
  true AS is_current
FROM base;

CREATE OR REPLACE TABLE bronze_core_banking.deposit_accounts_history AS
SELECT
  account_id,
  customer_name,
  product_type,
  customer_segment,
  DATE_SUB(CURRENT_DATE(), day_back) AS snapshot_date,
  ROUND(current_balance * (1.0 + ((RAND() - 0.5) * 0.08)), 2) AS current_balance,
  ROUND(stated_rate + ((RAND() - 0.5) * 0.004), 6) AS stated_rate,
  beta,
  account_status
FROM bronze_core_banking.deposit_accounts
CROSS JOIN (SELECT EXPLODE(SEQUENCE(0, 180)) AS day_back);

CREATE OR REPLACE TABLE bronze_core_banking.loan_portfolio AS
WITH ids AS (
  SELECT EXPLODE(SEQUENCE(1, 1200)) AS n
)
SELECT
  CONCAT('L', LPAD(CAST(n AS STRING), 7, '0')) AS loan_id,
  CONCAT('Borrower_', LPAD(CAST(n AS STRING), 6, '0')) AS borrower_name,
  CASE n % 5
    WHEN 0 THEN 'Commercial Real Estate'
    WHEN 1 THEN 'C&I'
    WHEN 2 THEN 'Residential Mortgage'
    WHEN 3 THEN 'Auto'
    ELSE 'Small Business'
  END AS product_type,
  ROUND(90000 + RAND() * 4800000, 2) AS current_balance,
  ROUND(120000 + RAND() * 5600000, 2) AS original_amount,
  ROUND(0.035 + RAND() * 0.055, 6) AS interest_rate,
  DATE_SUB(CURRENT_DATE(), CAST(90 + RAND() * 2200 AS INT)) AS origination_date,
  DATE_ADD(CURRENT_DATE(), CAST(365 + RAND() * 3000 AS INT)) AS maturity_date,
  CASE
    WHEN RAND() < 0.92 THEN 'Current'
    WHEN RAND() < 0.98 THEN '30DPD'
    ELSE '90+DPD'
  END AS payment_status,
  CAST(
    CASE
      WHEN RAND() < 0.90 THEN 0
      WHEN RAND() < 0.98 THEN 30 + RAND() * 60
      ELSE 90 + RAND() * 120
    END AS INT
  ) AS days_past_due,
  ROUND((90000 + RAND() * 4800000) * (0.005 + RAND() * 0.022), 2) AS cecl_reserve,
  ROUND(0.008 + RAND() * 0.055, 6) AS pd,
  ROUND(0.15 + RAND() * 0.55, 6) AS lgd,
  CASE n % 4
    WHEN 0 THEN 'Real Estate'
    WHEN 1 THEN 'Cash'
    WHEN 2 THEN 'Equipment'
    ELSE 'Receivables'
  END AS collateral_type,
  ROUND((120000 + RAND() * 5600000) * (0.75 + RAND() * 0.45), 2) AS collateral_value,
  ROUND(0.45 + RAND() * 0.45, 6) AS ltv_ratio,
  CONCAT('OFF', LPAD(CAST((n % 40) + 1 AS STRING), 3, '0')) AS officer_id,
  CONCAT('BR', LPAD(CAST((n % 25) + 1 AS STRING), 3, '0')) AS branch_id,
  true AS is_current
FROM ids;
