# Databricks notebook source
# MAGIC %md
# MAGIC # PPNR Scenario Planning Engine (2Y Driver)
# MAGIC
# MAGIC This notebook adds a **scenario planning layer** on top of the existing PPNR outputs.
# MAGIC
# MAGIC ## Macro driver (decision)
# MAGIC - **We standardize on the 2Y rate** (`cfo_banking_demo.silver_treasury.yield_curves.rate_2y`) as the primary macro driver.
# MAGIC
# MAGIC ## What this creates (Unity Catalog)
# MAGIC - `cfo_banking_demo.gold_finance.ppnr_scenario_catalog`
# MAGIC - `cfo_banking_demo.gold_finance.ppnr_scenario_drivers_quarterly`
# MAGIC - `cfo_banking_demo.gold_finance.ppnr_sensitivity_assumptions`
# MAGIC - `cfo_banking_demo.gold_finance.ppnr_projection_quarterly`
# MAGIC
# MAGIC ## How it works (MVP logic)
# MAGIC - Baseline PPNR comes from existing `cfo_banking_demo.ml_models.ppnr_forecasts` (monthly) aggregated to **quarterly**.
# MAGIC - Scenario paths are defined as quarterly drivers (including **rate_2y**) and simple multipliers.
# MAGIC - The **rate → NII** effect uses a transparent first-cut approximation derived from the current deposit book:
# MAGIC   - Compute weighted balance exposure: \( \sum balance \times predicted\_beta \)
# MAGIC   - Convert a **100 bps** move into incremental quarterly deposit interest expense:
# MAGIC     \[
# MAGIC       \Delta IE_{qtr,100bps} = \frac{\sum(balance \times beta)\times 0.01}{4}
# MAGIC     \]
# MAGIC   - Apply that to baseline NII as: \( NII_{scenario} = NII_{baseline} - \Delta IE \times \frac{\Delta rate_{bps}}{100} \)
# MAGIC
# MAGIC This is intentionally simple and auditable; you can later replace it with a more granular ALM cashflow model or learned elasticities.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 0: Preconditions (existing demo tables)
# MAGIC This notebook assumes these already exist (they do in the CFO demo):
# MAGIC - `cfo_banking_demo.ml_models.ppnr_forecasts` (monthly PPNR forecast series)
# MAGIC - `cfo_banking_demo.ml_models.deposit_beta_predictions` (account-level predicted_beta + balances)
# MAGIC - `cfo_banking_demo.silver_treasury.yield_curves` (daily rates incl. `rate_2y`)

# COMMAND ----------

CATALOG = "cfo_banking_demo"
SCHEMA = "gold_finance"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Create schema + scenario planning tables

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")

spark.sql(f"""
CREATE OR REPLACE TABLE {CATALOG}.{SCHEMA}.ppnr_scenario_catalog (
  scenario_id STRING,
  scenario_name STRING,
  scenario_type STRING,         -- e.g., baseline / custom / stress
  description STRING,
  created_at TIMESTAMP,
  created_by STRING
)
USING DELTA
""")

spark.sql(f"""
CREATE OR REPLACE TABLE {CATALOG}.{SCHEMA}.ppnr_scenario_drivers_quarterly (
  scenario_id STRING,
  quarter_start DATE,

  -- Macro driver: 2Y rate path (in percent, e.g., 3.53)
  rate_2y_pct DOUBLE,

  -- Simple planning levers (multipliers; 1.0 = baseline)
  fee_income_multiplier DOUBLE,
  expense_multiplier DOUBLE
)
USING DELTA
""")

spark.sql(f"""
CREATE OR REPLACE TABLE {CATALOG}.{SCHEMA}.ppnr_sensitivity_assumptions (
  assumption_set STRING,
  as_of_date DATE,

  -- Derived from current deposit exposure (sum(balance * predicted_beta))
  deposit_exposure_usd DOUBLE,

  -- Incremental quarterly deposit interest expense for a +100bps move in rates
  delta_deposit_interest_expense_qtr_100bps_usd DOUBLE,

  -- Notes for auditability
  notes STRING
)
USING DELTA
""")

spark.sql(f"""
CREATE OR REPLACE TABLE {CATALOG}.{SCHEMA}.ppnr_projection_quarterly (
  scenario_id STRING,
  quarter_start DATE,

  -- Drivers (copied for dashboarding / joins)
  rate_2y_pct DOUBLE,
  rate_2y_delta_bps DOUBLE,
  fee_income_multiplier DOUBLE,
  expense_multiplier DOUBLE,

  -- Baseline quarterly (from ml_models.ppnr_forecasts)
  baseline_nii_usd DOUBLE,
  baseline_non_interest_income_usd DOUBLE,
  baseline_non_interest_expense_usd DOUBLE,
  baseline_ppnr_usd DOUBLE,

  -- Scenario quarterly (after applying drivers)
  scenario_nii_usd DOUBLE,
  scenario_non_interest_income_usd DOUBLE,
  scenario_non_interest_expense_usd DOUBLE,
  scenario_ppnr_usd DOUBLE,

  -- Deltas
  delta_ppnr_usd DOUBLE
)
USING DELTA
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Seed a minimal scenario catalog

# COMMAND ----------

spark.sql(f"TRUNCATE TABLE {CATALOG}.{SCHEMA}.ppnr_scenario_catalog")

spark.sql(f"""
INSERT INTO {CATALOG}.{SCHEMA}.ppnr_scenario_catalog
VALUES
  ('baseline', 'Baseline (2Y unchanged)', 'baseline', 'No 2Y shock; multipliers = 1.0', current_timestamp(), current_user()),
  ('rate_hike_100', '+100 bps 2Y shock', 'custom', '2Y +100bps constant; multipliers = 1.0', current_timestamp(), current_user()),
  ('rate_cut_100',  '-100 bps 2Y shock', 'custom', '2Y -100bps constant; multipliers = 1.0', current_timestamp(), current_user())
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Compute sensitivity assumptions (deposit exposure → quarterly NII impact)
# MAGIC We derive a transparent NII sensitivity from the **current deposit exposure** using predicted betas.

# COMMAND ----------

spark.sql(f"TRUNCATE TABLE {CATALOG}.{SCHEMA}.ppnr_sensitivity_assumptions")

spark.sql(f"""
WITH latest_pred AS (
  SELECT
    current_balance,
    predicted_beta
  FROM {CATALOG}.ml_models.deposit_beta_predictions
  WHERE prediction_timestamp = (
    SELECT MAX(prediction_timestamp) FROM {CATALOG}.ml_models.deposit_beta_predictions
  )
),
exposure AS (
  SELECT
    SUM(COALESCE(current_balance, 0) * COALESCE(predicted_beta, 0)) AS deposit_exposure_usd
  FROM latest_pred
),
asof AS (
  SELECT MAX(date) AS as_of_date FROM {CATALOG}.silver_treasury.yield_curves
)
INSERT INTO {CATALOG}.{SCHEMA}.ppnr_sensitivity_assumptions
SELECT
  'default_2y' AS assumption_set,
  asof.as_of_date,
  exposure.deposit_exposure_usd,
  (exposure.deposit_exposure_usd * 0.01) / 4.0 AS delta_deposit_interest_expense_qtr_100bps_usd,
  'Derived from sum(current_balance * predicted_beta) at latest prediction_timestamp. Assumes 100bps = 1% move; quarterly impact = annual/4. Asset repricing not modeled in MVP.' AS notes
FROM exposure
CROSS JOIN asof
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Build a 9-quarter baseline from the existing monthly PPNR series
# MAGIC
# MAGIC In some demo runs, `ml_models.ppnr_forecasts` may only contain a limited number of months.
# MAGIC For scenario planning we still want a stable **next 9 quarters** window.
# MAGIC
# MAGIC MVP approach:
# MAGIC - Anchor to the latest available month in `ml_models.ppnr_forecasts`
# MAGIC - Use that latest month’s values as a flat monthly baseline for the next **27 months**
# MAGIC - Aggregate monthly → quarterly for a 9-quarter baseline curve

# COMMAND ----------

baseline_qtr_df = spark.sql(f"""
WITH anchor_row AS (
  SELECT
    TO_DATE(month) AS anchor_month,
    COALESCE(net_interest_income, 0) AS net_interest_income,
    COALESCE(non_interest_income, 0) AS non_interest_income,
    COALESCE(non_interest_expense, 0) AS non_interest_expense,
    COALESCE(ppnr, 0) AS ppnr
  FROM {CATALOG}.ml_models.ppnr_forecasts
  ORDER BY TO_DATE(month) DESC
  LIMIT 1
),
months AS (
  SELECT
    -- Start at quarter boundary so 27 months = exactly 9 quarters
    ADD_MONTHS(DATE_TRUNC('quarter', (SELECT anchor_month FROM anchor_row)), i) AS month,
    (SELECT net_interest_income FROM anchor_row) AS net_interest_income,
    (SELECT non_interest_income FROM anchor_row) AS non_interest_income,
    (SELECT non_interest_expense FROM anchor_row) AS non_interest_expense,
    (SELECT ppnr FROM anchor_row) AS ppnr
  FROM (SELECT EXPLODE(SEQUENCE(0, 26)) AS i)
),
qtr AS (
  SELECT
    DATE_TRUNC('quarter', month) AS quarter_start,
    SUM(net_interest_income) AS baseline_nii_usd,
    SUM(non_interest_income) AS baseline_non_interest_income_usd,
    SUM(non_interest_expense) AS baseline_non_interest_expense_usd,
    SUM(ppnr) AS baseline_ppnr_usd
  FROM months
  GROUP BY DATE_TRUNC('quarter', month)
)
SELECT * FROM qtr
ORDER BY quarter_start
""")

baseline_qtr_df.createOrReplaceTempView("baseline_ppnr_quarterly")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Generate quarterly driver paths (2Y) for each scenario
# MAGIC We use the latest observed 2Y level as baseline and apply constant shocks for the sample scenarios.

# COMMAND ----------

spark.sql(f"TRUNCATE TABLE {CATALOG}.{SCHEMA}.ppnr_scenario_drivers_quarterly")

spark.sql(f"""
WITH base_quarters AS (
  SELECT DISTINCT quarter_start FROM baseline_ppnr_quarterly
),
latest_rates AS (
  SELECT
    MAX(date) AS as_of_date,
    FIRST(rate_2y, TRUE) AS latest_rate_2y
  FROM {CATALOG}.silver_treasury.yield_curves
  QUALIFY ROW_NUMBER() OVER (ORDER BY date DESC) = 1
),
scenarios AS (
  SELECT scenario_id FROM {CATALOG}.{SCHEMA}.ppnr_scenario_catalog
),
scenario_shocks AS (
  SELECT 'baseline' AS scenario_id, 0.0 AS shock_bps UNION ALL
  SELECT 'rate_hike_100', 100.0 UNION ALL
  SELECT 'rate_cut_100', -100.0
)
INSERT INTO {CATALOG}.{SCHEMA}.ppnr_scenario_drivers_quarterly
SELECT
  s.scenario_id,
  q.quarter_start,
  (r.latest_rate_2y + (ss.shock_bps / 100.0)) AS rate_2y_pct,
  1.0 AS fee_income_multiplier,
  1.0 AS expense_multiplier
FROM scenarios s
JOIN scenario_shocks ss
  ON s.scenario_id = ss.scenario_id
CROSS JOIN base_quarters q
CROSS JOIN latest_rates r
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6: Produce `ppnr_projection_quarterly` (baseline vs scenario)

# COMMAND ----------

spark.sql(f"TRUNCATE TABLE {CATALOG}.{SCHEMA}.ppnr_projection_quarterly")

spark.sql(f"""
WITH baseline AS (
  SELECT * FROM baseline_ppnr_quarterly
),
assumptions AS (
  SELECT *
  FROM {CATALOG}.{SCHEMA}.ppnr_sensitivity_assumptions
  WHERE assumption_set = 'default_2y'
  ORDER BY as_of_date DESC
  LIMIT 1
),
drivers AS (
  SELECT d.*
  FROM {CATALOG}.{SCHEMA}.ppnr_scenario_drivers_quarterly d
),
baseline_rate AS (
  SELECT
    MAX(CASE WHEN scenario_id = 'baseline' THEN rate_2y_pct END) AS baseline_rate_2y_pct
  FROM drivers
)
INSERT INTO {CATALOG}.{SCHEMA}.ppnr_projection_quarterly
SELECT
  d.scenario_id,
  b.quarter_start,

  d.rate_2y_pct,
  (d.rate_2y_pct - br.baseline_rate_2y_pct) * 100.0 AS rate_2y_delta_bps,
  d.fee_income_multiplier,
  d.expense_multiplier,

  b.baseline_nii_usd,
  b.baseline_non_interest_income_usd,
  b.baseline_non_interest_expense_usd,
  b.baseline_ppnr_usd,

  -- Scenario NII: apply deposit-driven interest expense sensitivity
  (b.baseline_nii_usd
    - (a.delta_deposit_interest_expense_qtr_100bps_usd * ((d.rate_2y_pct - br.baseline_rate_2y_pct) * 100.0 / 100.0))
  ) AS scenario_nii_usd,

  -- Scenario NonII / NonIE: multipliers (MVP)
  (b.baseline_non_interest_income_usd * d.fee_income_multiplier) AS scenario_non_interest_income_usd,
  (b.baseline_non_interest_expense_usd * d.expense_multiplier) AS scenario_non_interest_expense_usd,

  -- Scenario PPNR identity
  (
    (b.baseline_nii_usd
      - (a.delta_deposit_interest_expense_qtr_100bps_usd * ((d.rate_2y_pct - br.baseline_rate_2y_pct) * 100.0 / 100.0))
    )
    + (b.baseline_non_interest_income_usd * d.fee_income_multiplier)
    - (b.baseline_non_interest_expense_usd * d.expense_multiplier)
  ) AS scenario_ppnr_usd,

  (
    (
      (b.baseline_nii_usd
        - (a.delta_deposit_interest_expense_qtr_100bps_usd * ((d.rate_2y_pct - br.baseline_rate_2y_pct) * 100.0 / 100.0))
      )
      + (b.baseline_non_interest_income_usd * d.fee_income_multiplier)
      - (b.baseline_non_interest_expense_usd * d.expense_multiplier)
    ) - b.baseline_ppnr_usd
  ) AS delta_ppnr_usd
FROM baseline b
JOIN drivers d
  ON b.quarter_start = d.quarter_start
CROSS JOIN assumptions a
CROSS JOIN baseline_rate br
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 7: Quick sanity checks

# COMMAND ----------

display(spark.sql(f"""
SELECT
  scenario_id,
  COUNT(*) AS quarters,
  MIN(quarter_start) AS min_qtr,
  MAX(quarter_start) AS max_qtr,
  SUM(delta_ppnr_usd) AS total_delta_ppnr_usd
FROM {CATALOG}.{SCHEMA}.ppnr_projection_quarterly
GROUP BY scenario_id
ORDER BY scenario_id
"""))

display(spark.sql(f"""
SELECT *
FROM {CATALOG}.{SCHEMA}.ppnr_projection_quarterly
WHERE scenario_id IN ('baseline', 'rate_hike_100', 'rate_cut_100')
ORDER BY quarter_start, scenario_id
LIMIT 50
"""))

