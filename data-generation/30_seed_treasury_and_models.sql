-- Seeds treasury curves and ML output tables used by frontend + backend.
-- Depends on seeded core banking tables.

USE CATALOG cfo_banking_demo;
CREATE SCHEMA IF NOT EXISTS silver_treasury;
CREATE SCHEMA IF NOT EXISTS ml_models;
CREATE SCHEMA IF NOT EXISTS gold_finance;

CREATE TABLE IF NOT EXISTS silver_treasury.yield_curves (
  date DATE,
  rate_3m DOUBLE,
  rate_2y DOUBLE,
  rate_5y DOUBLE,
  rate_10y DOUBLE,
  rate_30y DOUBLE,
  fed_funds_rate DOUBLE
);

-- Seed synthetic curve history only if the table is empty.
-- If AlphaVantage has already populated this table, preserve those values.
INSERT INTO silver_treasury.yield_curves
WITH ds AS (
  SELECT EXPLODE(SEQUENCE(DATE_SUB(CURRENT_DATE(), 540), CURRENT_DATE(), INTERVAL 1 DAY)) AS dt
)
SELECT
  dt AS date,
  ROUND(0.030 + (SIN(DATEDIFF(dt, DATE'2024-01-01') / 25.0) * 0.002) + (RAND() * 0.0012), 6) AS rate_3m,
  ROUND(0.034 + (SIN(DATEDIFF(dt, DATE'2024-01-01') / 35.0) * 0.0022) + (RAND() * 0.0015), 6) AS rate_2y,
  ROUND(0.036 + (SIN(DATEDIFF(dt, DATE'2024-01-01') / 45.0) * 0.0018) + (RAND() * 0.0013), 6) AS rate_5y,
  ROUND(0.038 + (SIN(DATEDIFF(dt, DATE'2024-01-01') / 55.0) * 0.0016) + (RAND() * 0.0012), 6) AS rate_10y,
  ROUND(0.040 + (SIN(DATEDIFF(dt, DATE'2024-01-01') / 70.0) * 0.0014) + (RAND() * 0.0011), 6) AS rate_30y,
  ROUND(0.033 + (SIN(DATEDIFF(dt, DATE'2024-01-01') / 30.0) * 0.0020) + (RAND() * 0.0012), 6) AS fed_funds_rate
FROM ds
WHERE NOT EXISTS (SELECT 1 FROM silver_treasury.yield_curves LIMIT 1);

CREATE OR REPLACE TABLE ml_models.deposit_beta_predictions AS
SELECT
  d.account_id,
  d.product_type,
  d.current_balance,
  d.stated_rate,
  ROUND(LEAST(0.99, GREATEST(0.06, d.beta + ((RAND() - 0.5) * 0.08))), 6) AS predicted_beta,
  CASE
    WHEN d.beta < 0.35 THEN 'Strategic'
    WHEN d.beta < 0.60 THEN 'Tactical'
    ELSE 'Expendable'
  END AS relationship_category,
  CURRENT_TIMESTAMP() AS prediction_timestamp
FROM bronze_core_banking.deposit_accounts d
WHERE d.is_current = true;

CREATE OR REPLACE TABLE ml_models.ppnr_forecasts AS
WITH months AS (
  SELECT EXPLODE(SEQUENCE(DATE_TRUNC('month', ADD_MONTHS(CURRENT_DATE(), -18)), DATE_TRUNC('month', ADD_MONTHS(CURRENT_DATE(), 18)), INTERVAL 1 MONTH)) AS month_start
),
base_nii AS (
  SELECT
    month_start,
    112000000 + (SIN(MONTH(month_start) / 2.0) * 2500000) + (RAND() * 1800000) AS nii
  FROM months
),
base AS (
  SELECT
    month_start,
    nii,
    -- Keep non-interest income near 10% of NII for a well-run bank profile.
    (nii * (0.10 + ((RAND() - 0.5) * 0.02))) AS nonii,
    91000000 + (SIN(MONTH(month_start) / 2.2) * 1700000) + (RAND() * 1300000) AS nonexp
  FROM base_nii
)
SELECT
  month_start AS month,
  ROUND(nii, 2) AS net_interest_income,
  ROUND(nonii, 2) AS non_interest_income,
  ROUND(nonexp, 2) AS non_interest_expense,
  ROUND(nii + nonii - nonexp, 2) AS ppnr,
  'baseline' AS scenario
FROM base;

CREATE OR REPLACE TABLE ml_models.component_decay_metrics AS
SELECT * FROM VALUES
  ('Strategic', 0.020, 0.004),
  ('Strategic', 0.022, 0.003),
  ('Tactical', 0.045, -0.002),
  ('Tactical', 0.049, -0.003),
  ('Expendable', 0.090, -0.010),
  ('Expendable', 0.096, -0.012)
AS t(relationship_category, lambda_closure_rate, g_abgr);

CREATE OR REPLACE TABLE ml_models.cohort_survival_rates AS
WITH months AS (
  SELECT EXPLODE(SEQUENCE(0, 36)) AS m
),
cats AS (
  SELECT * FROM VALUES
    ('Strategic', 0.985),
    ('Tactical', 0.970),
    ('Expendable', 0.940)
  AS c(relationship_category, monthly_retention)
)
SELECT
  c.relationship_category,
  m.m AS months_since_open,
  ROUND(POW(c.monthly_retention, m.m), 6) AS account_survival_rate
FROM cats c
CROSS JOIN months m;

CREATE OR REPLACE TABLE ml_models.deposit_runoff_forecasts AS
SELECT * FROM VALUES
  ('Strategic', 12, 22.50, 22.05),
  ('Strategic', 24, 22.50, 21.35),
  ('Strategic', 36, 22.50, 20.60),
  ('Tactical', 12, 15.40, 14.82),
  ('Tactical', 24, 15.40, 14.10),
  ('Tactical', 36, 15.40, 13.28),
  ('Expendable', 12, 9.60, 8.72),
  ('Expendable', 24, 9.60, 7.96),
  ('Expendable', 36, 9.60, 7.15)
AS t(relationship_category, months_ahead, current_balance_billions, projected_balance_billions);

CREATE OR REPLACE TABLE ml_models.dynamic_beta_parameters AS
SELECT * FROM VALUES
  ('Strategic', 0.08, 0.38, 0.70, 2.50),
  ('Tactical', 0.22, 0.68, 0.95, 3.20),
  ('Expendable', 0.40, 0.95, 1.15, 3.90)
AS t(relationship_category, beta_min, beta_max, k_steepness, R0_inflection);

CREATE OR REPLACE TABLE ml_models.stress_test_results AS
SELECT * FROM VALUES
  ('baseline', 'Baseline (No Shock)', 0,   0.00,  0.00,  0.00, 'PASS', 0.32),
  ('adverse', 'Adverse (+200 bps)', 200, -42.50, -0.35, -0.75, 'PASS', 0.48),
  ('severely_adverse', 'Severely Adverse (+300 bps)', 300, -95.00, -0.95, -1.65, 'PASS', 0.62)
AS t(scenario_id, scenario_name, rate_shock_bps, delta_nii_millions, delta_eve_billions, eve_cet1_ratio, sot_status, stressed_avg_beta);

CREATE OR REPLACE TABLE gold_finance.ppnr_projection_quarterly AS
WITH quarters AS (
  SELECT EXPLODE(SEQUENCE(DATE_TRUNC('quarter', CURRENT_DATE()), DATE_TRUNC('quarter', ADD_MONTHS(CURRENT_DATE(), 24)), INTERVAL 3 MONTH)) AS qtr
),
scenarios AS (
  SELECT * FROM VALUES
    ('rate_cut_100', -100.0, 0.04, -35.0, 0.02, -0.03),
    ('rate_cut_50',  -50.0, 0.02, -15.0, 0.01, -0.01),
    ('baseline',       0.0, 0.00,   0.0, 0.00,  0.00),
    ('rate_hike_50',  50.0, -0.02, 20.0, -0.01, 0.03),
    ('rate_hike_100',100.0, -0.05, 45.0, -0.02, 0.06)
  AS s(scenario_id, rate_2y_delta_bps, equity_shock_pct, credit_spread_shock_bps, fx_shock_pct, liquidity_runoff_shock_pct)
),
base AS (
  SELECT
    qtr,
    63000000 + (ROW_NUMBER() OVER (ORDER BY qtr) * 1100000) AS baseline_ppnr
  FROM quarters
)
SELECT
  s.scenario_id,
  b.qtr AS quarter_start,
  s.rate_2y_delta_bps,
  s.equity_shock_pct,
  s.credit_spread_shock_bps,
  s.fx_shock_pct,
  s.liquidity_runoff_shock_pct,
  ROUND(-s.rate_2y_delta_bps * 16000, 2) AS delta_ppnr_rate_usd,
  ROUND(s.equity_shock_pct * 9000000 - s.credit_spread_shock_bps * 8000, 2) AS delta_ppnr_market_usd,
  ROUND(-s.liquidity_runoff_shock_pct * 12000000, 2) AS delta_ppnr_liquidity_usd,
  ROUND((b.baseline_ppnr + (-s.rate_2y_delta_bps * 16000) + (s.equity_shock_pct * 9000000 - s.credit_spread_shock_bps * 8000) + (-s.liquidity_runoff_shock_pct * 12000000)), 2) AS scenario_ppnr_usd,
  ROUND(((-s.rate_2y_delta_bps * 16000) + (s.equity_shock_pct * 9000000 - s.credit_spread_shock_bps * 8000) + (-s.liquidity_runoff_shock_pct * 12000000)), 2) AS delta_ppnr_usd
FROM base b
CROSS JOIN scenarios s
ORDER BY s.scenario_id, b.qtr;

CREATE OR REPLACE TABLE gold_finance.ppnr_projection_quarterly_ml AS
SELECT
  scenario_id,
  quarter_start,
  rate_2y_delta_bps,
  equity_shock_pct,
  credit_spread_shock_bps,
  fx_shock_pct,
  liquidity_runoff_shock_pct,
  delta_ppnr_rate_usd,
  delta_ppnr_market_usd,
  delta_ppnr_liquidity_usd,
  scenario_ppnr_usd AS ppnr_usd,
  delta_ppnr_usd
FROM gold_finance.ppnr_projection_quarterly;
