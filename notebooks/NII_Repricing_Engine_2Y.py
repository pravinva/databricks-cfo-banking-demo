# Databricks notebook source
# MAGIC %md
# MAGIC # Full NII Repricing Engine (2Y Driver)
# MAGIC
# MAGIC This notebook produces a **quarterly Net Interest Income (NII)** projection under the same **2Y scenario paths**
# MAGIC used elsewhere in the demo.
# MAGIC
# MAGIC ## Macro driver (standard)
# MAGIC - `cfo_banking_demo.silver_treasury.yield_curves.rate_2y` (percent)
# MAGIC
# MAGIC ## Outputs (Unity Catalog)
# MAGIC - `cfo_banking_demo.gold_finance.deposit_repricing_assumptions`
# MAGIC - `cfo_banking_demo.gold_finance.loan_repricing_assumptions`
# MAGIC - `cfo_banking_demo.gold_finance.nii_projection_quarterly`
# MAGIC
# MAGIC ## Repricing logic (auditable MVP)
# MAGIC - **Balances**: held constant at the latest `effective_date` snapshot for deposits and loans.
# MAGIC - **Deposit repricing**: account-level `predicted_beta` pass-through applied to `stated_rate`.
# MAGIC - **Loan repricing**: `rate_type`-based pass-through applied to `interest_rate`.
# MAGIC - **Lags / caps / floors**: governed by the assumption tables (seeded with defaults).
# MAGIC
# MAGIC This is the “full NII” layer (assets + liabilities). It replaces the deposit-only NII sensitivity used earlier.

# COMMAND ----------

CATALOG = "cfo_banking_demo"
SCHEMA = "gold_finance"

# Required upstream scenario driver table (created by PPNR scenario planning engine)
SCENARIO_DRIVERS_TABLE = f"{CATALOG}.{SCHEMA}.ppnr_scenario_drivers_quarterly"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Create schema + tables

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")

spark.sql(f"""
CREATE OR REPLACE TABLE {CATALOG}.{SCHEMA}.deposit_repricing_assumptions (
  product_type STRING,
  lag_quarters INT,              -- 0/1/2 supported in this MVP
  beta_multiplier DOUBLE,        -- multiply predicted_beta
  rate_floor_pct DOUBLE,
  rate_cap_pct DOUBLE,
  notes STRING
)
USING DELTA
""")

spark.sql(f"""
CREATE OR REPLACE TABLE {CATALOG}.{SCHEMA}.loan_repricing_assumptions (
  rate_type STRING,              -- Fixed / Variable / ARM
  lag_quarters INT,              -- 0/1/2 supported in this MVP
  pass_through DOUBLE,           -- apply to 2Y delta (0 for fixed)
  rate_floor_pct DOUBLE,
  rate_cap_pct DOUBLE,
  notes STRING
)
USING DELTA
""")

spark.sql(f"""
CREATE OR REPLACE TABLE {CATALOG}.{SCHEMA}.nii_projection_quarterly (
  scenario_id STRING,
  quarter_start DATE,

  rate_2y_pct DOUBLE,
  baseline_rate_2y_pct DOUBLE,
  rate_2y_delta_bps DOUBLE,

  loan_interest_income_usd DOUBLE,
  deposit_interest_expense_usd DOUBLE,
  nii_usd DOUBLE,

  as_of_deposit_effective_date DATE,
  as_of_loan_effective_date DATE,
  as_of_yield_curve_date DATE
)
USING DELTA
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Seed default repricing assumptions
# MAGIC These defaults are intended to be **reasonable demo settings** and easy to tweak in UC.

# COMMAND ----------

spark.sql(f"TRUNCATE TABLE {CATALOG}.{SCHEMA}.deposit_repricing_assumptions")
spark.sql(f"""
INSERT INTO {CATALOG}.{SCHEMA}.deposit_repricing_assumptions
VALUES
  ('DDA',     1, 1.0, 0.0, 20.0, 'Lag 1Q for non-maturity deposits; account-level predicted_beta'),
  ('NOW',     1, 1.0, 0.0, 20.0, 'Lag 1Q; account-level predicted_beta'),
  ('Savings', 1, 1.0, 0.0, 20.0, 'Lag 1Q; account-level predicted_beta'),
  ('MMDA',    1, 1.0, 0.0, 20.0, 'Lag 1Q; account-level predicted_beta'),
  ('CD',      2, 1.0, 0.0, 20.0, 'Lag 2Q (reprices at rollover); predicted_beta used as a simplification')
""")

spark.sql(f"TRUNCATE TABLE {CATALOG}.{SCHEMA}.loan_repricing_assumptions")
spark.sql(f"""
INSERT INTO {CATALOG}.{SCHEMA}.loan_repricing_assumptions
VALUES
  ('Fixed',    0, 0.00, 0.0, 30.0, 'Fixed-rate: no repricing to 2Y in MVP'),
  ('Variable', 0, 0.85, 0.0, 30.0, 'Variable-rate: 85% pass-through to 2Y; no lag in MVP'),
  ('ARM',      1, 0.75, 0.0, 30.0, 'ARM: 75% pass-through; lag 1Q in MVP')
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Compute quarterly NII under scenario 2Y paths
# MAGIC Requires: `gold_finance.ppnr_scenario_drivers_quarterly` to exist.

# COMMAND ----------

if not spark.catalog.tableExists(SCENARIO_DRIVERS_TABLE):
    raise RuntimeError(
        f"Missing required scenario drivers table: {SCENARIO_DRIVERS_TABLE}. "
        "Run notebooks/PPNR_Scenario_Planning_Engine.py (or scripts/setup_ppnr_scenario_planning.py) first."
    )

spark.sql(f"TRUNCATE TABLE {CATALOG}.{SCHEMA}.nii_projection_quarterly")

spark.sql(f"""
WITH asof_deposits AS (
  SELECT MAX(effective_date) AS effective_date
  FROM {CATALOG}.bronze_core_banking.deposit_accounts_historical
),
asof_loans AS (
  SELECT MAX(effective_date) AS effective_date
  FROM {CATALOG}.bronze_core_banking.loan_portfolio_historical
),
asof_yc AS (
  SELECT MAX(date) AS as_of_yield_curve_date
  FROM {CATALOG}.silver_treasury.yield_curves
),
drivers AS (
  SELECT
    scenario_id,
    quarter_start,
    rate_2y_pct
  FROM {SCENARIO_DRIVERS_TABLE}
),
baseline_rate AS (
  SELECT
    MAX(CASE WHEN scenario_id = 'baseline' THEN rate_2y_pct END) AS baseline_rate_2y_pct
  FROM drivers
),
driver_deltas AS (
  SELECT
    d.*,
    br.baseline_rate_2y_pct,
    (d.rate_2y_pct - br.baseline_rate_2y_pct) AS delta_rate_pct,
    (d.rate_2y_pct - br.baseline_rate_2y_pct) * 100.0 AS delta_rate_bps,
    LAG((d.rate_2y_pct - br.baseline_rate_2y_pct), 1) OVER (PARTITION BY d.scenario_id ORDER BY d.quarter_start) AS delta_rate_pct_lag1,
    LAG((d.rate_2y_pct - br.baseline_rate_2y_pct), 2) OVER (PARTITION BY d.scenario_id ORDER BY d.quarter_start) AS delta_rate_pct_lag2
  FROM drivers d
  CROSS JOIN baseline_rate br
),
deposit_book AS (
  SELECT
    dah.account_id,
    dah.product_type,
    CAST(dah.current_balance AS DOUBLE) AS current_balance_usd,
    CAST(dah.stated_rate AS DOUBLE) AS base_rate_pct
  FROM {CATALOG}.bronze_core_banking.deposit_accounts_historical dah
  WHERE dah.effective_date = (SELECT effective_date FROM asof_deposits)
),
deposit_betas AS (
  SELECT
    account_id,
    COALESCE(CAST(predicted_beta AS DOUBLE), 0.0) AS predicted_beta
  FROM {CATALOG}.ml_models.deposit_beta_predictions
  WHERE prediction_timestamp = (SELECT MAX(prediction_timestamp) FROM {CATALOG}.ml_models.deposit_beta_predictions)
),
deposit_assumptions AS (
  SELECT * FROM {CATALOG}.{SCHEMA}.deposit_repricing_assumptions
),
deposit_interest AS (
  SELECT
    dd.scenario_id,
    dd.quarter_start,
    dd.rate_2y_pct,
    dd.baseline_rate_2y_pct,
    dd.delta_rate_bps,
    -- lagged delta per product (0/1/2 supported)
    CASE
      WHEN da.lag_quarters = 0 THEN dd.delta_rate_pct
      WHEN da.lag_quarters = 1 THEN COALESCE(dd.delta_rate_pct_lag1, 0.0)
      WHEN da.lag_quarters = 2 THEN COALESCE(dd.delta_rate_pct_lag2, 0.0)
      ELSE 0.0
    END AS effective_delta_rate_pct,
    db.current_balance_usd,
    db.base_rate_pct,
    COALESCE(b.predicted_beta, 0.0) AS predicted_beta,
    COALESCE(da.beta_multiplier, 1.0) AS beta_multiplier,
    COALESCE(da.rate_floor_pct, 0.0) AS rate_floor_pct,
    COALESCE(da.rate_cap_pct, 30.0) AS rate_cap_pct
  FROM driver_deltas dd
  CROSS JOIN deposit_book db
  LEFT JOIN deposit_betas b
    ON db.account_id = b.account_id
  LEFT JOIN deposit_assumptions da
    ON db.product_type = da.product_type
),
deposit_interest_qtr AS (
  SELECT
    scenario_id,
    quarter_start,
    MAX(rate_2y_pct) AS rate_2y_pct,
    MAX(baseline_rate_2y_pct) AS baseline_rate_2y_pct,
    MAX(delta_rate_bps) AS rate_2y_delta_bps,
    SUM(
      current_balance_usd
      * (LEAST(rate_cap_pct, GREATEST(rate_floor_pct, base_rate_pct + (predicted_beta * beta_multiplier * effective_delta_rate_pct))))
      / 100.0
      / 4.0
    ) AS deposit_interest_expense_usd
  FROM deposit_interest
  GROUP BY scenario_id, quarter_start
),
loan_book AS (
  SELECT
    lph.loan_id,
    lph.rate_type,
    CAST(lph.current_balance AS DOUBLE) AS current_balance_usd,
    CAST(lph.interest_rate AS DOUBLE) AS base_rate_pct
  FROM {CATALOG}.bronze_core_banking.loan_portfolio_historical lph
  WHERE lph.effective_date = (SELECT effective_date FROM asof_loans)
),
loan_assumptions AS (
  SELECT * FROM {CATALOG}.{SCHEMA}.loan_repricing_assumptions
),
loan_interest AS (
  SELECT
    dd.scenario_id,
    dd.quarter_start,
    dd.rate_2y_pct,
    dd.baseline_rate_2y_pct,
    dd.delta_rate_bps,
    CASE
      WHEN la.lag_quarters = 0 THEN dd.delta_rate_pct
      WHEN la.lag_quarters = 1 THEN COALESCE(dd.delta_rate_pct_lag1, 0.0)
      WHEN la.lag_quarters = 2 THEN COALESCE(dd.delta_rate_pct_lag2, 0.0)
      ELSE 0.0
    END AS effective_delta_rate_pct,
    lb.current_balance_usd,
    lb.base_rate_pct,
    COALESCE(la.pass_through, 0.0) AS pass_through,
    COALESCE(la.rate_floor_pct, 0.0) AS rate_floor_pct,
    COALESCE(la.rate_cap_pct, 40.0) AS rate_cap_pct
  FROM driver_deltas dd
  CROSS JOIN loan_book lb
  LEFT JOIN loan_assumptions la
    ON lb.rate_type = la.rate_type
),
loan_interest_qtr AS (
  SELECT
    scenario_id,
    quarter_start,
    MAX(rate_2y_pct) AS rate_2y_pct,
    MAX(baseline_rate_2y_pct) AS baseline_rate_2y_pct,
    MAX(delta_rate_bps) AS rate_2y_delta_bps,
    SUM(
      current_balance_usd
      * (LEAST(rate_cap_pct, GREATEST(rate_floor_pct, base_rate_pct + (pass_through * effective_delta_rate_pct))))
      / 100.0
      / 4.0
    ) AS loan_interest_income_usd
  FROM loan_interest
  GROUP BY scenario_id, quarter_start
)
INSERT INTO {CATALOG}.{SCHEMA}.nii_projection_quarterly
SELECT
  li.scenario_id,
  li.quarter_start,
  li.rate_2y_pct,
  li.baseline_rate_2y_pct,
  li.rate_2y_delta_bps,
  li.loan_interest_income_usd,
  di.deposit_interest_expense_usd,
  (li.loan_interest_income_usd - di.deposit_interest_expense_usd) AS nii_usd,
  (SELECT effective_date FROM asof_deposits) AS as_of_deposit_effective_date,
  (SELECT effective_date FROM asof_loans) AS as_of_loan_effective_date,
  (SELECT as_of_yield_curve_date FROM asof_yc) AS as_of_yield_curve_date
FROM loan_interest_qtr li
JOIN deposit_interest_qtr di
  ON li.scenario_id = di.scenario_id
 AND li.quarter_start = di.quarter_start
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Sanity checks

# COMMAND ----------

display(spark.sql(f"""
SELECT
  scenario_id,
  COUNT(*) AS quarters,
  MIN(quarter_start) AS min_qtr,
  MAX(quarter_start) AS max_qtr,
  AVG(nii_usd) AS avg_nii_usd
FROM {CATALOG}.{SCHEMA}.nii_projection_quarterly
GROUP BY scenario_id
ORDER BY scenario_id
"""))

display(spark.sql(f"""
SELECT
  quarter_start,
  scenario_id,
  rate_2y_delta_bps,
  loan_interest_income_usd,
  deposit_interest_expense_usd,
  nii_usd
FROM {CATALOG}.{SCHEMA}.nii_projection_quarterly
ORDER BY quarter_start, scenario_id
LIMIT 60
"""))

