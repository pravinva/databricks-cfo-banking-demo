#!/usr/bin/env python3
"""
Create/refresh PPNR Scenario Planning (2Y) assets in Unity Catalog using a SQL Warehouse.

This script is intentionally simple: it executes the same core SQL steps used in
`notebooks/PPNR_Scenario_Planning_Engine.py`, but from your laptop/CI via the Databricks SDK.

Usage:
  DATABRICKS_CONFIG_PROFILE=DEFAULT python scripts/setup_ppnr_scenario_planning.py --warehouse-id 4b9b953939869799
"""

from __future__ import annotations

import argparse
import os
import time
from typing import Iterable, Optional

from databricks.sdk import WorkspaceClient


def _wait_execute_sql(w: WorkspaceClient, warehouse_id: str, statement: str, timeout_s: int = 300) -> None:
    resp = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=statement,
        wait_timeout="5s",
    )
    statement_id = resp.statement_id

    start = time.time()
    while True:
        s = w.statement_execution.get_statement(statement_id)
        state = s.status.state.value
        if state in ("PENDING", "RUNNING"):
            if time.time() - start > timeout_s:
                raise TimeoutError(f"Timed out after {timeout_s}s for statement_id={statement_id}")
            time.sleep(1)
            continue

        if state != "SUCCEEDED":
            err = s.status.error
            msg = err.message if err else "Unknown error"
            code = err.error_code if err else "UNKNOWN"
            raise RuntimeError(f"SQL failed: state={state} code={code} message={msg}")

        return


def _statements(catalog: str, schema: str, use_full_nii_repricing: bool) -> Iterable[str]:
    qname = lambda t: f"{catalog}.{schema}.{t}"

    yield f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}"

    yield f"""
CREATE OR REPLACE TABLE {qname('ppnr_scenario_catalog')} (
  scenario_id STRING,
  scenario_name STRING,
  scenario_type STRING,
  description STRING,
  created_at TIMESTAMP,
  created_by STRING
)
USING DELTA
""".strip()

    yield f"""
CREATE OR REPLACE TABLE {qname('ppnr_scenario_drivers_quarterly')} (
  scenario_id STRING,
  quarter_start DATE,
  fed_funds_pct DOUBLE,
  sofr_pct DOUBLE,
  prime_pct DOUBLE,
  rate_2y_pct DOUBLE,
  rate_10y_pct DOUBLE,
  curve_slope DOUBLE,
  fee_income_multiplier DOUBLE,
  expense_multiplier DOUBLE
)
USING DELTA
""".strip()

    yield f"""
CREATE OR REPLACE TABLE {qname('ppnr_sensitivity_assumptions')} (
  assumption_set STRING,
  as_of_date DATE,
  deposit_exposure_usd DOUBLE,
  delta_deposit_interest_expense_qtr_100bps_usd DOUBLE,
  notes STRING
)
USING DELTA
""".strip()

    yield f"""
CREATE OR REPLACE TABLE {qname('ppnr_projection_quarterly')} (
  scenario_id STRING,
  quarter_start DATE,
  rate_2y_pct DOUBLE,
  rate_2y_delta_bps DOUBLE,
  fee_income_multiplier DOUBLE,
  expense_multiplier DOUBLE,
  baseline_nii_usd DOUBLE,
  baseline_non_interest_income_usd DOUBLE,
  baseline_non_interest_expense_usd DOUBLE,
  baseline_ppnr_usd DOUBLE,
  scenario_nii_usd DOUBLE,
  scenario_non_interest_income_usd DOUBLE,
  scenario_non_interest_expense_usd DOUBLE,
  scenario_ppnr_usd DOUBLE,
  delta_ppnr_usd DOUBLE
)
USING DELTA
""".strip()

    yield f"TRUNCATE TABLE {qname('ppnr_scenario_catalog')}"
    yield f"""
INSERT INTO {qname('ppnr_scenario_catalog')}
VALUES
  ('baseline', 'Baseline (2Y unchanged)', 'baseline', 'No 2Y shock; multipliers = 1.0', current_timestamp(), current_user()),
  ('rate_hike_100', '+100 bps 2Y shock', 'custom', '2Y +100bps constant; multipliers = 1.0', current_timestamp(), current_user()),
  ('rate_cut_100',  '-100 bps 2Y shock', 'custom', '2Y -100bps constant; multipliers = 1.0', current_timestamp(), current_user()),
  ('market_shock', 'Market shock (non-rate)', 'stress', 'Equity down, spreads wider, USD stronger, elevated runoff', current_timestamp(), current_user())
""".strip()

    yield f"TRUNCATE TABLE {qname('ppnr_sensitivity_assumptions')}"
    yield f"""
WITH latest_pred AS (
  SELECT current_balance, predicted_beta
  FROM {catalog}.ml_models.deposit_beta_predictions
  WHERE prediction_timestamp = (SELECT MAX(prediction_timestamp) FROM {catalog}.ml_models.deposit_beta_predictions)
),
exposure AS (
  SELECT SUM(COALESCE(current_balance, 0) * COALESCE(predicted_beta, 0)) AS deposit_exposure_usd
  FROM latest_pred
),
asof AS (
  SELECT MAX(date) AS as_of_date FROM {catalog}.silver_treasury.yield_curves
)
INSERT INTO {qname('ppnr_sensitivity_assumptions')}
SELECT
  'default_2y' AS assumption_set,
  asof.as_of_date,
  exposure.deposit_exposure_usd,
  (exposure.deposit_exposure_usd * 0.01) / 4.0 AS delta_deposit_interest_expense_qtr_100bps_usd,
  'Derived from sum(current_balance * predicted_beta) at latest prediction_timestamp. Assumes 100bps = 1% move; quarterly impact = annual/4. Asset repricing not modeled in MVP.' AS notes
FROM exposure
CROSS JOIN asof
""".strip()

    # Drivers and projections are generated in one go (no temp views in warehouse context).
    yield f"TRUNCATE TABLE {qname('ppnr_scenario_drivers_quarterly')}"
    yield f"""
WITH anchor_row AS (
  SELECT
    TO_DATE(month) AS anchor_month,
    COALESCE(net_interest_income, 0) AS net_interest_income,
    COALESCE(non_interest_income, 0) AS non_interest_income,
    COALESCE(non_interest_expense, 0) AS non_interest_expense,
    COALESCE(ppnr, 0) AS ppnr
  FROM {catalog}.ml_models.ppnr_forecasts
  ORDER BY TO_DATE(month) DESC
  LIMIT 1
),
months AS (
  SELECT
    -- Start at quarter boundary so 27 months = exactly 9 quarters
    ADD_MONTHS(DATE_TRUNC('quarter', (SELECT anchor_month FROM anchor_row)), i) AS month
  FROM (SELECT EXPLODE(SEQUENCE(0, 26)) AS i)
),
base_quarters AS (
  SELECT DISTINCT DATE_TRUNC('quarter', month) AS quarter_start
  FROM months
),
latest_rate AS (
  SELECT rate_2y AS latest_rate_2y,
         rate_10y AS latest_rate_10y,
         fed_funds_rate AS latest_fed_funds
  FROM {catalog}.silver_treasury.yield_curves
  ORDER BY date DESC
  LIMIT 1
),
scenario_shocks AS (
  SELECT 'baseline' AS scenario_id, 0.0 AS shock_bps UNION ALL
  SELECT 'rate_hike_100', 100.0 UNION ALL
  SELECT 'rate_cut_100', -100.0
)
INSERT INTO {qname('ppnr_scenario_drivers_quarterly')}
SELECT
  ss.scenario_id,
  q.quarter_start,
  (r.latest_fed_funds + (ss.shock_bps / 100.0)) AS fed_funds_pct,
  ((r.latest_fed_funds + (ss.shock_bps / 100.0)) - 0.05) AS sofr_pct,
  ((r.latest_fed_funds + (ss.shock_bps / 100.0)) + 3.00) AS prime_pct,
  (r.latest_rate_2y + (ss.shock_bps / 100.0)) AS rate_2y_pct,
  (r.latest_rate_10y + (ss.shock_bps / 100.0)) AS rate_10y_pct,
  ((r.latest_rate_10y + (ss.shock_bps / 100.0)) - (r.latest_rate_2y + (ss.shock_bps / 100.0))) AS curve_slope,
  1.0 AS fee_income_multiplier,
  1.0 AS expense_multiplier
FROM base_quarters q
CROSS JOIN latest_rate r
JOIN scenario_shocks ss
  ON 1 = 1
""".strip()

    yield f"TRUNCATE TABLE {qname('ppnr_projection_quarterly')}"
    if use_full_nii_repricing:
        yield f"""
WITH anchor_row AS (
  SELECT
    TO_DATE(month) AS anchor_month,
    COALESCE(net_interest_income, 0) AS net_interest_income,
    COALESCE(non_interest_income, 0) AS non_interest_income,
    COALESCE(non_interest_expense, 0) AS non_interest_expense,
    COALESCE(ppnr, 0) AS ppnr
  FROM {catalog}.ml_models.ppnr_forecasts
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
baseline AS (
  SELECT
    DATE_TRUNC('quarter', month) AS quarter_start,
    SUM(net_interest_income) AS baseline_nii_usd,
    SUM(non_interest_income) AS baseline_non_interest_income_usd,
    SUM(non_interest_expense) AS baseline_non_interest_expense_usd,
    SUM(ppnr) AS baseline_ppnr_usd
  FROM months
  GROUP BY DATE_TRUNC('quarter', month)
),
drivers AS (
  SELECT * FROM {qname('ppnr_scenario_drivers_quarterly')}
),
baseline_rate AS (
  SELECT
    MAX(CASE WHEN scenario_id = 'baseline' THEN rate_2y_pct END) AS baseline_rate_2y_pct
  FROM drivers
),
nii_repricing AS (
  SELECT scenario_id, quarter_start, nii_usd
  FROM {qname('nii_projection_quarterly')}
),
nii_baseline AS (
  SELECT quarter_start, nii_usd
  FROM nii_repricing
  WHERE scenario_id = 'baseline'
)
INSERT INTO {qname('ppnr_projection_quarterly')}
SELECT
  d.scenario_id,
  b.quarter_start,
  d.rate_2y_pct,
  (d.rate_2y_pct - br.baseline_rate_2y_pct) * 100.0 AS rate_2y_delta_bps,
  d.fee_income_multiplier,
  d.expense_multiplier,
  nb.nii_usd AS baseline_nii_usd,
  b.baseline_non_interest_income_usd,
  b.baseline_non_interest_expense_usd,
  (nb.nii_usd + b.baseline_non_interest_income_usd - b.baseline_non_interest_expense_usd) AS baseline_ppnr_usd,
  ns.nii_usd AS scenario_nii_usd,
  (b.baseline_non_interest_income_usd * d.fee_income_multiplier) AS scenario_non_interest_income_usd,
  (b.baseline_non_interest_expense_usd * d.expense_multiplier) AS scenario_non_interest_expense_usd,
  (ns.nii_usd + (b.baseline_non_interest_income_usd * d.fee_income_multiplier) - (b.baseline_non_interest_expense_usd * d.expense_multiplier)) AS scenario_ppnr_usd,
  (
    (ns.nii_usd + (b.baseline_non_interest_income_usd * d.fee_income_multiplier) - (b.baseline_non_interest_expense_usd * d.expense_multiplier))
    - (nb.nii_usd + b.baseline_non_interest_income_usd - b.baseline_non_interest_expense_usd)
  ) AS delta_ppnr_usd
FROM baseline b
JOIN drivers d
  ON b.quarter_start = d.quarter_start
CROSS JOIN baseline_rate br
JOIN nii_repricing ns
  ON ns.scenario_id = d.scenario_id
 AND ns.quarter_start = b.quarter_start
JOIN nii_baseline nb
  ON nb.quarter_start = b.quarter_start
""".strip()
    else:
        yield f"""
WITH anchor_row AS (
  SELECT
    TO_DATE(month) AS anchor_month,
    COALESCE(net_interest_income, 0) AS net_interest_income,
    COALESCE(non_interest_income, 0) AS non_interest_income,
    COALESCE(non_interest_expense, 0) AS non_interest_expense,
    COALESCE(ppnr, 0) AS ppnr
  FROM {catalog}.ml_models.ppnr_forecasts
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
baseline AS (
  SELECT
    DATE_TRUNC('quarter', month) AS quarter_start,
    SUM(net_interest_income) AS baseline_nii_usd,
    SUM(non_interest_income) AS baseline_non_interest_income_usd,
    SUM(non_interest_expense) AS baseline_non_interest_expense_usd,
    SUM(ppnr) AS baseline_ppnr_usd
  FROM months
  GROUP BY DATE_TRUNC('quarter', month)
),
assumptions AS (
  SELECT *
  FROM {qname('ppnr_sensitivity_assumptions')}
  WHERE assumption_set = 'default_2y'
  ORDER BY as_of_date DESC
  LIMIT 1
),
drivers AS (
  SELECT * FROM {qname('ppnr_scenario_drivers_quarterly')}
),
baseline_rate AS (
  SELECT
    MAX(CASE WHEN scenario_id = 'baseline' THEN rate_2y_pct END) AS baseline_rate_2y_pct
  FROM drivers
)
INSERT INTO {qname('ppnr_projection_quarterly')}
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
  (b.baseline_nii_usd
    - (a.delta_deposit_interest_expense_qtr_100bps_usd * ((d.rate_2y_pct - br.baseline_rate_2y_pct) * 100.0 / 100.0))
  ) AS scenario_nii_usd,
  (b.baseline_non_interest_income_usd * d.fee_income_multiplier) AS scenario_non_interest_income_usd,
  (b.baseline_non_interest_expense_usd * d.expense_multiplier) AS scenario_non_interest_expense_usd,
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
""".strip()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--warehouse-id", required=False, default=os.getenv("DATABRICKS_WAREHOUSE_ID"))
    p.add_argument("--catalog", default="cfo_banking_demo")
    p.add_argument("--schema", default="gold_finance")
    p.add_argument(
        "--use-full-nii-repricing",
        action="store_true",
        help="Use gold_finance.nii_projection_quarterly for scenario NII (requires running setup_nii_repricing_2y.py).",
    )
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if not args.warehouse_id:
        raise SystemExit("Missing --warehouse-id (or set DATABRICKS_WAREHOUSE_ID)")

    w = WorkspaceClient()
    stmts = list(_statements(args.catalog, args.schema, args.use_full_nii_repricing))

    if args.dry_run:
        print("\n\n".join(stmts))
        return

    for i, stmt in enumerate(stmts, 1):
        print(f"[{i}/{len(stmts)}] Executing...")
        _wait_execute_sql(w, args.warehouse_id, stmt)

    print("Done. Scenario planning tables refreshed.")


if __name__ == "__main__":
    main()

