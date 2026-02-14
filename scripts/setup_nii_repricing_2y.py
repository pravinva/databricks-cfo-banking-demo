#!/usr/bin/env python3
"""
Create/refresh the Full NII Repricing (2Y) assets in Unity Catalog using a SQL Warehouse.

Depends on:
  - cfo_banking_demo.gold_finance.ppnr_scenario_drivers_quarterly
    (run scripts/setup_ppnr_scenario_planning.py first)

Usage:
  DATABRICKS_CONFIG_PROFILE=DEFAULT python scripts/setup_nii_repricing_2y.py --warehouse-id 4b9b953939869799
"""

from __future__ import annotations

import argparse
import os
import time
from typing import Iterable

from databricks.sdk import WorkspaceClient


def _wait_execute_sql(w: WorkspaceClient, warehouse_id: str, statement: str, timeout_s: int = 600) -> None:
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


def _statements(catalog: str, schema: str) -> Iterable[str]:
    q = lambda t: f"{catalog}.{schema}.{t}"
    scenario_drivers = q("ppnr_scenario_drivers_quarterly")

    yield f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}"

    yield f"""
CREATE OR REPLACE TABLE {q('deposit_repricing_assumptions')} (
  product_type STRING,
  lag_quarters INT,
  beta_multiplier DOUBLE,
  rate_floor_pct DOUBLE,
  rate_cap_pct DOUBLE,
  notes STRING
)
USING DELTA
""".strip()

    yield f"""
CREATE OR REPLACE TABLE {q('loan_repricing_assumptions')} (
  rate_type STRING,
  lag_quarters INT,
  pass_through DOUBLE,
  rate_floor_pct DOUBLE,
  rate_cap_pct DOUBLE,
  notes STRING
)
USING DELTA
""".strip()

    yield f"""
CREATE OR REPLACE TABLE {q('nii_projection_quarterly')} (
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
""".strip()

    yield f"TRUNCATE TABLE {q('deposit_repricing_assumptions')}"
    yield f"""
INSERT INTO {q('deposit_repricing_assumptions')}
VALUES
  ('DDA',     1, 1.0, 0.0, 20.0, 'Lag 1Q for non-maturity deposits; account-level predicted_beta'),
  ('NOW',     1, 1.0, 0.0, 20.0, 'Lag 1Q; account-level predicted_beta'),
  ('Savings', 1, 1.0, 0.0, 20.0, 'Lag 1Q; account-level predicted_beta'),
  ('MMDA',    1, 1.0, 0.0, 20.0, 'Lag 1Q; account-level predicted_beta'),
  ('CD',      2, 1.0, 0.0, 20.0, 'Lag 2Q (reprices at rollover); predicted_beta used as a simplification')
""".strip()

    yield f"TRUNCATE TABLE {q('loan_repricing_assumptions')}"
    yield f"""
INSERT INTO {q('loan_repricing_assumptions')}
VALUES
  ('Fixed',    0, 0.00, 0.0, 30.0, 'Fixed-rate: no repricing to 2Y in MVP'),
  ('Variable', 0, 0.85, 0.0, 30.0, 'Variable-rate: 85% pass-through to 2Y; no lag in MVP'),
  ('ARM',      1, 0.75, 0.0, 30.0, 'ARM: 75% pass-through; lag 1Q in MVP')
""".strip()

    yield f"TRUNCATE TABLE {q('nii_projection_quarterly')}"
    yield f"""
WITH asof_deposits AS (
  SELECT MAX(effective_date) AS effective_date
  FROM {catalog}.bronze_core_banking.deposit_accounts_historical
),
asof_loans AS (
  SELECT MAX(effective_date) AS effective_date
  FROM {catalog}.bronze_core_banking.loan_portfolio_historical
),
asof_yc AS (
  SELECT MAX(date) AS as_of_yield_curve_date
  FROM {catalog}.silver_treasury.yield_curves
),
drivers AS (
  SELECT scenario_id, quarter_start, rate_2y_pct
  FROM {scenario_drivers}
),
baseline_rate AS (
  SELECT MAX(CASE WHEN scenario_id = 'baseline' THEN rate_2y_pct END) AS baseline_rate_2y_pct
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
  FROM {catalog}.bronze_core_banking.deposit_accounts_historical dah
  WHERE dah.effective_date = (SELECT effective_date FROM asof_deposits)
),
deposit_betas AS (
  SELECT
    account_id,
    COALESCE(CAST(predicted_beta AS DOUBLE), 0.0) AS predicted_beta
  FROM {catalog}.ml_models.deposit_beta_predictions
  WHERE prediction_timestamp = (SELECT MAX(prediction_timestamp) FROM {catalog}.ml_models.deposit_beta_predictions)
),
deposit_assumptions AS (
  SELECT * FROM {q('deposit_repricing_assumptions')}
),
deposit_interest AS (
  SELECT
    dd.scenario_id,
    dd.quarter_start,
    dd.rate_2y_pct,
    dd.baseline_rate_2y_pct,
    dd.delta_rate_bps,
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
  FROM {catalog}.bronze_core_banking.loan_portfolio_historical lph
  WHERE lph.effective_date = (SELECT effective_date FROM asof_loans)
),
loan_assumptions AS (
  SELECT * FROM {q('loan_repricing_assumptions')}
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
INSERT INTO {q('nii_projection_quarterly')}
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
""".strip()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--warehouse-id", required=False, default=os.getenv("DATABRICKS_WAREHOUSE_ID"))
    p.add_argument("--catalog", default="cfo_banking_demo")
    p.add_argument("--schema", default="gold_finance")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if not args.warehouse_id:
        raise SystemExit("Missing --warehouse-id (or set DATABRICKS_WAREHOUSE_ID)")

    w = WorkspaceClient()
    stmts = list(_statements(args.catalog, args.schema))

    if args.dry_run:
        print("\n\n".join(stmts))
        return

    for i, stmt in enumerate(stmts, 1):
        print(f"[{i}/{len(stmts)}] Executing...")
        _wait_execute_sql(w, args.warehouse_id, stmt)

    print("Done. NII repricing tables refreshed.")


if __name__ == "__main__":
    main()

