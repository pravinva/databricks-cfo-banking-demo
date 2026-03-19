-- Compatibility assets to preserve Genie room SQL/question behavior after
-- moving to prefixed schemas in the fins workspace.

USE CATALOG cfo_banking_demo;

CREATE SCHEMA IF NOT EXISTS gold_regulatory;

-- Legacy table expected by Genie examples/questions.
CREATE OR REPLACE TABLE gold_regulatory.lcr_daily AS
WITH base AS (
  SELECT
    CURRENT_DATE() AS as_of_date,
    MAX(CASE WHEN scenario_name = 'Baseline' THEN eve_cet1_ratio END) AS baseline_cet1,
    MAX(CASE WHEN scenario_name = 'Baseline' THEN stressed_avg_beta END) AS baseline_beta
  FROM ml_models.stress_test_results
)
SELECT
  as_of_date,
  ROUND(21000000000 * COALESCE(1 - baseline_beta * 0.12, 0.93), 2) AS total_hqla,
  ROUND(17000000000 * COALESCE(1 + (0.11 - baseline_cet1), 1.0), 2) AS net_outflows,
  ROUND(
    (21000000000 * COALESCE(1 - baseline_beta * 0.12, 0.93))
    / NULLIF(17000000000 * COALESCE(1 + (0.11 - baseline_cet1), 1.0), 0),
    4
  ) AS lcr_ratio
FROM base;

-- Legacy table expected by Genie sample question:
-- "Show me HQLA composition by level".
CREATE OR REPLACE TABLE gold_regulatory.hqla_inventory AS
WITH lcr AS (
  SELECT
    as_of_date,
    total_hqla
  FROM gold_regulatory.lcr_daily
),
mix AS (
  SELECT 'Level 1' AS hqla_level, 0.72 AS alloc UNION ALL
  SELECT 'Level 2A' AS hqla_level, 0.18 AS alloc UNION ALL
  SELECT 'Level 2B' AS hqla_level, 0.10 AS alloc
)
SELECT
  lcr.as_of_date,
  mix.hqla_level,
  ROUND(lcr.total_hqla * mix.alloc, 2) AS hqla_amount
FROM lcr
CROSS JOIN mix;

-- Legacy feature table used by one benchmark SQL answer.
CREATE OR REPLACE VIEW ml_models.deposit_beta_training_enhanced AS
WITH yc AS (
  SELECT
    fed_funds_rate
  FROM silver_treasury.yield_curves
  ORDER BY date DESC
  LIMIT 1
)
SELECT
  CURRENT_DATE() AS effective_date,
  d.account_id,
  d.product_type,
  CASE
    WHEN d.customer_segment = 'Retail' THEN 'Strategic'
    WHEN d.customer_segment = 'Commercial' THEN 'Tactical'
    ELSE 'Expendable'
  END AS relationship_category,
  d.current_balance,
  d.current_balance / 1000000.0 AS balance_millions,
  d.stated_rate,
  d.beta AS target_beta,
  d.beta,
  d.account_status,
  d.is_current,
  ROUND(d.stated_rate - yc.fed_funds_rate, 6) AS rate_gap,
  CASE WHEN d.stated_rate < yc.fed_funds_rate THEN 1 ELSE 0 END AS below_competitor_rate
FROM bronze_core_banking.deposit_accounts d
CROSS JOIN yc;

-- Legacy training-table names retained as simple views over canonical data.
CREATE OR REPLACE VIEW ml_models.non_interest_income_training_data AS
SELECT
  CAST(month AS DATE) AS as_of_date,
  scenario,
  non_interest_income AS amount
FROM ml_models.ppnr_forecasts;

CREATE OR REPLACE VIEW ml_models.non_interest_expense_training_data AS
SELECT
  CAST(month AS DATE) AS as_of_date,
  scenario,
  non_interest_expense AS amount
FROM ml_models.ppnr_forecasts;
