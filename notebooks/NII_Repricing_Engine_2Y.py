# Databricks notebook source
# MAGIC %md
# MAGIC # Full NII Repricing Engine (2Y Driver)
# MAGIC
# MAGIC This notebook produces a **quarterly Net Interest Income (NII)** projection under the same **scenario curve paths**
# MAGIC used elsewhere in the demo (Fed Funds, SOFR/Prime proxies, 2Y, 10Y).
# MAGIC
# MAGIC ## Drivers (standard)
# MAGIC - Source: `cfo_banking_demo.silver_treasury.yield_curves` (includes `fed_funds_rate`, `rate_2y`, `rate_10y`)
# MAGIC - Scenario grid: `cfo_banking_demo.gold_finance.ppnr_scenario_drivers_quarterly`
# MAGIC
# MAGIC ## Outputs (Unity Catalog)
# MAGIC - `cfo_banking_demo.gold_finance.deposit_repricing_assumptions`
# MAGIC - `cfo_banking_demo.gold_finance.loan_repricing_assumptions`
# MAGIC - `cfo_banking_demo.gold_finance.nii_projection_quarterly`
# MAGIC
# MAGIC ## Repricing logic (auditable MVP)
# MAGIC - **Volume dynamics**:
# MAGIC   - Deposits: use `ml_models.deposit_runoff_forecasts` to project balances (monthly → sampled at quarter horizons)
# MAGIC   - Loans: simple linear amortization to `maturity_date` (no new origination in MVP)
# MAGIC - **Deposit repricing**: product-level beta (from latest predictions) applied to a chosen driver (default `rate_2y_pct`)
# MAGIC - **Loan repricing**:
# MAGIC   - Prime/SOFR/FF indexed: rate = index + margin (from `rate_margin`)
# MAGIC   - ARM: base-rate reprices vs `rate_2y_pct` with lag/pass-through
# MAGIC - **Lags / caps / floors**: governed by UC assumption tables (seeded with defaults).
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
  driver STRING, -- which scenario driver to use (e.g., rate_2y_pct)
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
  rate_index STRING,             -- Prime / SOFR / NULL
  driver STRING,                 -- fed_funds_pct / prime_pct / sofr_pct / rate_2y_pct
  lag_quarters INT,              -- 0/1/2 supported in this MVP
  pass_through DOUBLE,           -- apply to 2Y delta (0 for fixed)
  use_index_plus_margin BOOLEAN, -- if true, rate := index + margin
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

  fed_funds_pct DOUBLE,
  sofr_pct DOUBLE,
  prime_pct DOUBLE,
  rate_2y_pct DOUBLE,
  rate_10y_pct DOUBLE,
  curve_slope DOUBLE,
  rate_2y_delta_bps DOUBLE,

  loan_interest_income_usd DOUBLE,
  deposit_interest_expense_usd DOUBLE,
  nii_usd DOUBLE,

  projected_loan_balance_usd DOUBLE,
  projected_deposit_balance_usd DOUBLE,

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
  ('DDA',     'rate_2y_pct', 1, 1.0, 0.0, 20.0, 'Lag 1Q for non-maturity deposits; beta vs 2Y'),
  ('NOW',     'rate_2y_pct', 1, 1.0, 0.0, 20.0, 'Lag 1Q; beta vs 2Y'),
  ('Savings', 'rate_2y_pct', 1, 1.0, 0.0, 20.0, 'Lag 1Q; beta vs 2Y'),
  ('MMDA',    'rate_2y_pct', 1, 1.0, 0.0, 20.0, 'Lag 1Q; beta vs 2Y'),
  ('CD',      'rate_2y_pct', 2, 1.0, 0.0, 20.0, 'Lag 2Q (reprices at rollover); beta vs 2Y')
""")

spark.sql(f"TRUNCATE TABLE {CATALOG}.{SCHEMA}.loan_repricing_assumptions")
spark.sql(f"""
INSERT INTO {CATALOG}.{SCHEMA}.loan_repricing_assumptions
VALUES
  ('Fixed',    NULL,   NULL,           0, 0.00, FALSE, 0.0, 30.0, 'Fixed-rate: no repricing in MVP'),
  ('Fixed',    'SOFR', NULL,           0, 0.00, FALSE, 0.0, 30.0, 'Fixed-rate (SOFR labeled): treated as fixed'),
  ('Variable', 'Prime','prime_pct',    0, 1.00, TRUE,  0.0, 30.0, 'Prime indexed: rate = Prime + margin'),
  ('Variable', 'SOFR', 'sofr_pct',     0, 1.00, TRUE,  0.0, 30.0, 'SOFR indexed: rate = SOFR + margin'),
  ('Variable', NULL,   'fed_funds_pct',0, 1.00, TRUE,  0.0, 30.0, 'Unlabeled variable: rate = FedFunds + margin'),
  ('ARM',      NULL,   'rate_2y_pct',  1, 0.75, FALSE, 0.0, 30.0, 'ARM: base rate reprices vs 2Y with lag 1Q')
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
    fed_funds_pct,
    sofr_pct,
    prime_pct,
    rate_2y_pct,
    rate_10y_pct,
    curve_slope
  FROM {SCENARIO_DRIVERS_TABLE}
),
baseline_drivers AS (
  SELECT
    quarter_start,
    fed_funds_pct AS b_fed_funds_pct,
    sofr_pct AS b_sofr_pct,
    prime_pct AS b_prime_pct,
    rate_2y_pct AS b_rate_2y_pct,
    rate_10y_pct AS b_rate_10y_pct
  FROM drivers
  WHERE scenario_id = 'baseline'
),
driver_deltas AS (
  SELECT
    d.*,
    bd.b_fed_funds_pct,
    bd.b_sofr_pct,
    bd.b_prime_pct,
    bd.b_rate_2y_pct,
    bd.b_rate_10y_pct,
    (d.fed_funds_pct - bd.b_fed_funds_pct) AS d_fed_funds_pct,
    (d.sofr_pct - bd.b_sofr_pct) AS d_sofr_pct,
    (d.prime_pct - bd.b_prime_pct) AS d_prime_pct,
    (d.rate_2y_pct - bd.b_rate_2y_pct) AS d_rate_2y_pct,
    (d.rate_10y_pct - bd.b_rate_10y_pct) AS d_rate_10y_pct,
    LAG((d.fed_funds_pct - bd.b_fed_funds_pct), 1) OVER (PARTITION BY d.scenario_id ORDER BY d.quarter_start) AS d_fed_funds_pct_lag1,
    LAG((d.fed_funds_pct - bd.b_fed_funds_pct), 2) OVER (PARTITION BY d.scenario_id ORDER BY d.quarter_start) AS d_fed_funds_pct_lag2,
    LAG((d.sofr_pct - bd.b_sofr_pct), 1) OVER (PARTITION BY d.scenario_id ORDER BY d.quarter_start) AS d_sofr_pct_lag1,
    LAG((d.sofr_pct - bd.b_sofr_pct), 2) OVER (PARTITION BY d.scenario_id ORDER BY d.quarter_start) AS d_sofr_pct_lag2,
    LAG((d.prime_pct - bd.b_prime_pct), 1) OVER (PARTITION BY d.scenario_id ORDER BY d.quarter_start) AS d_prime_pct_lag1,
    LAG((d.prime_pct - bd.b_prime_pct), 2) OVER (PARTITION BY d.scenario_id ORDER BY d.quarter_start) AS d_prime_pct_lag2,
    LAG((d.rate_2y_pct - bd.b_rate_2y_pct), 1) OVER (PARTITION BY d.scenario_id ORDER BY d.quarter_start) AS d_rate_2y_pct_lag1,
    LAG((d.rate_2y_pct - bd.b_rate_2y_pct), 2) OVER (PARTITION BY d.scenario_id ORDER BY d.quarter_start) AS d_rate_2y_pct_lag2,
    LAG((d.rate_10y_pct - bd.b_rate_10y_pct), 1) OVER (PARTITION BY d.scenario_id ORDER BY d.quarter_start) AS d_rate_10y_pct_lag1,
    LAG((d.rate_10y_pct - bd.b_rate_10y_pct), 2) OVER (PARTITION BY d.scenario_id ORDER BY d.quarter_start) AS d_rate_10y_pct_lag2
  FROM drivers d
  JOIN baseline_drivers bd
    ON d.quarter_start = bd.quarter_start
),
asof_quarter AS (
  SELECT DATE_TRUNC('quarter', (SELECT effective_date FROM asof_deposits)) AS asof_qtr
),
driver_months AS (
  SELECT
    dd.*,
    CAST(MONTHS_BETWEEN(dd.quarter_start, (SELECT asof_qtr FROM asof_quarter)) AS INT) AS months_ahead
  FROM driver_deltas dd
),
deposit_base AS (
  SELECT
    product_type,
    AVG(CAST(stated_rate AS DOUBLE)) AS base_rate_pct,
    SUM(CAST(current_balance AS DOUBLE)) AS base_balance_usd
  FROM {CATALOG}.bronze_core_banking.deposit_accounts_historical
  WHERE effective_date = (SELECT effective_date FROM asof_deposits)
  GROUP BY product_type
),
deposit_beta_by_product AS (
  SELECT
    p.product_type,
    SUM(CAST(p.current_balance AS DOUBLE) * COALESCE(CAST(b.predicted_beta AS DOUBLE), 0.0)) / NULLIF(SUM(CAST(p.current_balance AS DOUBLE)), 0) AS beta_wavg
  FROM {CATALOG}.ml_models.deposit_beta_predictions b
  JOIN {CATALOG}.bronze_core_banking.deposit_accounts_historical p
    ON b.account_id = p.account_id
   AND p.effective_date = (SELECT effective_date FROM asof_deposits)
  WHERE b.prediction_timestamp = (SELECT MAX(prediction_timestamp) FROM {CATALOG}.ml_models.deposit_beta_predictions)
  GROUP BY p.product_type
),
deposit_runoff AS (
  SELECT
    product_type,
    months_ahead,
    SUM(projected_balance_billions) * 1e9 AS projected_balance_usd
  FROM {CATALOG}.ml_models.deposit_runoff_forecasts
  GROUP BY product_type, months_ahead
),
deposit_assumptions AS (
  SELECT * FROM {CATALOG}.{SCHEMA}.deposit_repricing_assumptions
),
deposit_interest_qtr AS (
  SELECT
    dm.scenario_id,
    dm.quarter_start,
    MAX(dm.fed_funds_pct) AS fed_funds_pct,
    MAX(dm.sofr_pct) AS sofr_pct,
    MAX(dm.prime_pct) AS prime_pct,
    MAX(dm.rate_2y_pct) AS rate_2y_pct,
    MAX(dm.rate_10y_pct) AS rate_10y_pct,
    MAX(dm.curve_slope) AS curve_slope,
    MAX((dm.rate_2y_pct - dm.b_rate_2y_pct) * 100.0) AS rate_2y_delta_bps,
    SUM(COALESCE(dr.projected_balance_usd, db.base_balance_usd)) AS projected_deposit_balance_usd,
    SUM(
      COALESCE(dr.projected_balance_usd, db.base_balance_usd)
      * (
        LEAST(da.rate_cap_pct, GREATEST(da.rate_floor_pct,
          db.base_rate_pct + (COALESCE(beta.beta_wavg, 0.0) * da.beta_multiplier) * (
            CASE
              WHEN da.driver = 'rate_2y_pct' AND da.lag_quarters = 0 THEN dm.d_rate_2y_pct
              WHEN da.driver = 'rate_2y_pct' AND da.lag_quarters = 1 THEN COALESCE(dm.d_rate_2y_pct_lag1, 0.0)
              WHEN da.driver = 'rate_2y_pct' AND da.lag_quarters = 2 THEN COALESCE(dm.d_rate_2y_pct_lag2, 0.0)
              WHEN da.driver = 'fed_funds_pct' AND da.lag_quarters = 0 THEN dm.d_fed_funds_pct
              WHEN da.driver = 'fed_funds_pct' AND da.lag_quarters = 1 THEN COALESCE(dm.d_fed_funds_pct_lag1, 0.0)
              WHEN da.driver = 'fed_funds_pct' AND da.lag_quarters = 2 THEN COALESCE(dm.d_fed_funds_pct_lag2, 0.0)
              ELSE dm.d_rate_2y_pct
            END
          )
        ))
      ) / 100.0 / 4.0
    ) AS deposit_interest_expense_usd
  FROM driver_months dm
  JOIN deposit_base db
    ON 1=1
  JOIN deposit_assumptions da
    ON db.product_type = da.product_type
  LEFT JOIN deposit_beta_by_product beta
    ON db.product_type = beta.product_type
  LEFT JOIN deposit_runoff dr
    ON db.product_type = dr.product_type
   AND dm.months_ahead = dr.months_ahead
  GROUP BY dm.scenario_id, dm.quarter_start
),
loan_base AS (
  SELECT
    loan_id,
    rate_type,
    rate_index,
    CAST(current_balance AS DOUBLE) AS current_balance_usd,
    CAST(interest_rate AS DOUBLE) AS base_rate_pct,
    CAST(rate_margin AS DOUBLE) AS rate_margin_pct,
    maturity_date
  FROM {CATALOG}.bronze_core_banking.loan_portfolio_historical
  WHERE effective_date = (SELECT effective_date FROM asof_loans)
),
loan_assumptions AS (
  SELECT * FROM {CATALOG}.{SCHEMA}.loan_repricing_assumptions
),
loan_proj AS (
  SELECT
    dm.scenario_id,
    dm.quarter_start,
    dm.fed_funds_pct,
    dm.sofr_pct,
    dm.prime_pct,
    dm.rate_2y_pct,
    dm.rate_10y_pct,
    dm.curve_slope,
    ((dm.rate_2y_pct - dm.b_rate_2y_pct) * 100.0) AS rate_2y_delta_bps,
    dm.months_ahead,
    dm.d_fed_funds_pct,
    dm.d_fed_funds_pct_lag1,
    dm.d_fed_funds_pct_lag2,
    dm.d_sofr_pct,
    dm.d_sofr_pct_lag1,
    dm.d_sofr_pct_lag2,
    dm.d_prime_pct,
    dm.d_prime_pct_lag1,
    dm.d_prime_pct_lag2,
    dm.d_rate_2y_pct,
    dm.d_rate_2y_pct_lag1,
    dm.d_rate_2y_pct_lag2,
    lb.loan_id,
    lb.rate_type,
    lb.rate_index,
    lb.current_balance_usd,
    lb.base_rate_pct,
    lb.rate_margin_pct,
    lb.maturity_date,
    COALESCE(la.driver, 'rate_2y_pct') AS driver,
    COALESCE(la.lag_quarters, 0) AS lag_quarters,
    COALESCE(la.pass_through, 0.0) AS pass_through,
    COALESCE(la.use_index_plus_margin, FALSE) AS use_index_plus_margin,
    COALESCE(la.rate_floor_pct, 0.0) AS rate_floor_pct,
    COALESCE(la.rate_cap_pct, 40.0) AS rate_cap_pct,
    CASE
      WHEN lb.maturity_date IS NULL THEN lb.current_balance_usd
      ELSE (
        lb.current_balance_usd
        * GREATEST(
            0.0,
            (GREATEST(1.0, MONTHS_BETWEEN(lb.maturity_date, (SELECT effective_date FROM asof_loans))) - dm.months_ahead)
            / GREATEST(1.0, MONTHS_BETWEEN(lb.maturity_date, (SELECT effective_date FROM asof_loans)))
          )
      )
    END AS projected_balance_usd
  FROM driver_months dm
  CROSS JOIN loan_base lb
  LEFT JOIN loan_assumptions la
    ON lb.rate_type = la.rate_type
   AND ( (lb.rate_index = la.rate_index) OR (lb.rate_index IS NULL AND la.rate_index IS NULL) )
),
loan_interest_qtr AS (
  SELECT
    scenario_id,
    quarter_start,
    MAX(fed_funds_pct) AS fed_funds_pct,
    MAX(sofr_pct) AS sofr_pct,
    MAX(prime_pct) AS prime_pct,
    MAX(rate_2y_pct) AS rate_2y_pct,
    MAX(rate_10y_pct) AS rate_10y_pct,
    MAX(curve_slope) AS curve_slope,
    MAX(rate_2y_delta_bps) AS rate_2y_delta_bps,
    SUM(projected_balance_usd) AS projected_loan_balance_usd,
    SUM(
      projected_balance_usd
      * (
        LEAST(rate_cap_pct, GREATEST(rate_floor_pct,
          CASE
            WHEN use_index_plus_margin THEN
              (
                CASE
                  WHEN driver = 'prime_pct' THEN prime_pct
                  WHEN driver = 'sofr_pct' THEN sofr_pct
                  WHEN driver = 'fed_funds_pct' THEN fed_funds_pct
                  ELSE rate_2y_pct
                END
                + COALESCE(rate_margin_pct, 0.0)
              )
            ELSE
              (
                base_rate_pct
                + pass_through * (
                  CASE
                    WHEN driver = 'prime_pct' AND lag_quarters = 0 THEN d_prime_pct
                    WHEN driver = 'prime_pct' AND lag_quarters = 1 THEN COALESCE(d_prime_pct_lag1, 0.0)
                    WHEN driver = 'prime_pct' AND lag_quarters = 2 THEN COALESCE(d_prime_pct_lag2, 0.0)
                    WHEN driver = 'sofr_pct' AND lag_quarters = 0 THEN d_sofr_pct
                    WHEN driver = 'sofr_pct' AND lag_quarters = 1 THEN COALESCE(d_sofr_pct_lag1, 0.0)
                    WHEN driver = 'sofr_pct' AND lag_quarters = 2 THEN COALESCE(d_sofr_pct_lag2, 0.0)
                    WHEN driver = 'fed_funds_pct' AND lag_quarters = 0 THEN d_fed_funds_pct
                    WHEN driver = 'fed_funds_pct' AND lag_quarters = 1 THEN COALESCE(d_fed_funds_pct_lag1, 0.0)
                    WHEN driver = 'fed_funds_pct' AND lag_quarters = 2 THEN COALESCE(d_fed_funds_pct_lag2, 0.0)
                    WHEN driver = 'rate_2y_pct' AND lag_quarters = 0 THEN d_rate_2y_pct
                    WHEN driver = 'rate_2y_pct' AND lag_quarters = 1 THEN COALESCE(d_rate_2y_pct_lag1, 0.0)
                    WHEN driver = 'rate_2y_pct' AND lag_quarters = 2 THEN COALESCE(d_rate_2y_pct_lag2, 0.0)
                    ELSE d_rate_2y_pct
                  END
                )
              )
          END
        ))
      ) / 100.0 / 4.0
    ) AS loan_interest_income_usd
  FROM loan_proj
  GROUP BY scenario_id, quarter_start
)
INSERT INTO {CATALOG}.{SCHEMA}.nii_projection_quarterly
SELECT
  li.scenario_id,
  li.quarter_start,
  li.fed_funds_pct,
  li.sofr_pct,
  li.prime_pct,
  li.rate_2y_pct,
  li.rate_10y_pct,
  li.curve_slope,
  li.rate_2y_delta_bps,
  li.loan_interest_income_usd,
  di.deposit_interest_expense_usd,
  (li.loan_interest_income_usd - di.deposit_interest_expense_usd) AS nii_usd,
  li.projected_loan_balance_usd,
  di.projected_deposit_balance_usd,
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

