-- One realtime "tick": mutate balances/rates, append snapshots, refresh model outputs.
-- Run repeatedly (for example every 60 seconds) for near-real-time simulation.

USE CATALOG cfo_banking_demo;

-- 1) Maintain deterministic tick counter
CREATE TABLE IF NOT EXISTS ml_models.realtime_generation_state (
  id INT,
  tick BIGINT
);

MERGE INTO ml_models.realtime_generation_state AS t
USING (SELECT 1 AS id, 0 AS tick) AS s
ON t.id = s.id
WHEN NOT MATCHED THEN INSERT (id, tick) VALUES (s.id, s.tick);

UPDATE ml_models.realtime_generation_state
SET tick = tick + 1
WHERE id = 1;

-- 2) Micro-move balances and rates using deterministic hash noise per tick
UPDATE bronze_core_banking.deposit_accounts
SET
  current_balance = ROUND(
    GREATEST(
      1000.0,
      current_balance * (
        1 + (
          (
            PMOD(ABS(HASH(account_id, (SELECT tick FROM ml_models.realtime_generation_state WHERE id = 1), 101)), 1000000) / 1000000.0
            - 0.5
          ) * 0.006
        )
      )
    ),
    2
  ),
  stated_rate = ROUND(
    LEAST(
      0.09,
      GREATEST(
        0.0005,
        stated_rate + (
          (
            PMOD(ABS(HASH(account_id, (SELECT tick FROM ml_models.realtime_generation_state WHERE id = 1), 202)), 1000000) / 1000000.0
            - 0.5
          ) * 0.0009
        )
      )
    ),
    6
  ),
  beta = ROUND(
    LEAST(
      0.99,
      GREATEST(
        0.05,
        beta + (
          (
            PMOD(ABS(HASH(account_id, (SELECT tick FROM ml_models.realtime_generation_state WHERE id = 1), 303)), 1000000) / 1000000.0
            - 0.5
          ) * 0.01
        )
      )
    ),
    6
  )
WHERE is_current = true AND account_status = 'Active';

-- 3) Append daily snapshots for trend visuals
INSERT INTO bronze_core_banking.deposit_accounts_history
SELECT
  account_id,
  customer_name,
  product_type,
  customer_segment,
  CURRENT_DATE() AS snapshot_date,
  current_balance,
  stated_rate,
  beta,
  account_status
FROM bronze_core_banking.deposit_accounts
WHERE is_current = true;

-- 4) Refresh beta predictions from latest account state
CREATE OR REPLACE TABLE ml_models.deposit_beta_predictions AS
SELECT
  d.account_id,
  d.product_type,
  d.current_balance,
  d.stated_rate,
  ROUND(LEAST(0.99, GREATEST(0.06, d.beta + ((RAND() - 0.5) * 0.04))), 6) AS predicted_beta,
  CASE
    WHEN d.beta < 0.35 THEN 'Strategic'
    WHEN d.beta < 0.60 THEN 'Tactical'
    ELSE 'Expendable'
  END AS relationship_category,
  CURRENT_TIMESTAMP() AS prediction_timestamp
FROM bronze_core_banking.deposit_accounts d
WHERE d.is_current = true;

-- 5) Preserve externally sourced curve data (AlphaVantage).
-- Do not synthesize intraday curve moves here. If the current date row is
-- missing, carry forward the latest available market snapshot.
MERGE INTO silver_treasury.yield_curves AS t
USING (
  SELECT
    CURRENT_DATE() AS date,
    rate_3m,
    rate_2y,
    rate_5y,
    rate_10y,
    rate_30y,
    fed_funds_rate
  FROM silver_treasury.yield_curves
  ORDER BY date DESC
  LIMIT 1
) AS s
ON t.date = s.date
WHEN NOT MATCHED THEN INSERT *;

-- 6) Keep current month PPNR synced to latest economic state
MERGE INTO ml_models.ppnr_forecasts AS t
USING (
  WITH base AS (
    SELECT
      DATE_TRUNC('month', CURRENT_DATE()) AS month,
      (108000000 + (SUM(current_balance) * 0.000025)) AS net_interest_income_raw,
      (90500000 + (AVG(stated_rate) * 45000000)) AS non_interest_expense_raw
    FROM bronze_core_banking.deposit_accounts
    WHERE is_current = true
  )
  SELECT
    month,
    ROUND(net_interest_income_raw, 2) AS net_interest_income,
    -- Maintain non-interest income near 10% of NII.
    ROUND(net_interest_income_raw * 0.10, 2) AS non_interest_income,
    ROUND(non_interest_expense_raw, 2) AS non_interest_expense,
    'baseline' AS scenario
  FROM base
) AS s
ON t.month = s.month
WHEN MATCHED THEN UPDATE SET
  t.net_interest_income = s.net_interest_income,
  t.non_interest_income = s.non_interest_income,
  t.non_interest_expense = s.non_interest_expense,
  t.ppnr = ROUND(s.net_interest_income + s.non_interest_income - s.non_interest_expense, 2),
  t.scenario = s.scenario
WHEN NOT MATCHED THEN INSERT (
  month,
  net_interest_income,
  non_interest_income,
  non_interest_expense,
  ppnr,
  scenario
) VALUES (
  s.month,
  s.net_interest_income,
  s.non_interest_income,
  s.non_interest_expense,
  ROUND(s.net_interest_income + s.non_interest_income - s.non_interest_expense, 2),
  s.scenario
);
