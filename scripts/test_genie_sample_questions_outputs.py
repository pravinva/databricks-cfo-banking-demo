"""
Execute all Genie sample questions' intended SQL and print outputs.

This does NOT call the Genie LLM. It runs representative "gold" SQL for each
sample question against the Genie space's SQL warehouse, so we can validate
tables/columns exist and show what the outputs look like.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import re

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import Disposition


WAREHOUSE_ID = "4b9b953939869799"


@dataclass(frozen=True)
class SampleQuery:
    question: str
    sql: str
    max_rows: int = 20


SAMPLE_QUERIES: list[SampleQuery] = [
    SampleQuery(
        question="For deposit_accounts_historical, show total current_balance by effective_date for the last 12 months.",
        sql="""
SELECT
  effective_date,
  SUM(current_balance)/1e9 AS total_balance_b
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts_historical
WHERE effective_date >= add_months(current_date(), -12)
GROUP BY effective_date
ORDER BY effective_date DESC
""".strip(),
    ),
    SampleQuery(
        question="What are the last 6 months of non_interest_income vs non_interest_expense trends?",
        sql="""
WITH latest AS (
  SELECT MAX(month) AS max_month
  FROM cfo_banking_demo.ml_models.ppnr_forecasts
)
SELECT
  date_trunc('month', month) AS month,
  non_interest_income/1e6 AS non_interest_income_m,
  non_interest_expense/1e6 AS non_interest_expense_m
FROM cfo_banking_demo.ml_models.ppnr_forecasts
WHERE month >= add_months((SELECT max_month FROM latest), -6)
ORDER BY month
""".strip(),
    ),
    SampleQuery(
        question="For a +200 bps shock, what is the stressed_avg_beta and delta_nii_millions?",
        sql="""
SELECT
  scenario_name,
  rate_shock_bps,
  stressed_avg_beta,
  delta_nii_millions,
  sot_status
FROM cfo_banking_demo.ml_models.stress_test_results
WHERE rate_shock_bps = 200
ORDER BY calculation_date DESC
LIMIT 5
""".strip(),
    ),
    SampleQuery(
        question="Which stress scenario breaches the Standard Outlier Test (sot_status not OK)?",
        sql="""
SELECT
  scenario_name,
  rate_shock_bps,
  stressed_avg_beta,
  delta_nii_millions,
  sot_status
FROM cfo_banking_demo.ml_models.stress_test_results
WHERE sot_status IS NOT NULL
  AND UPPER(sot_status) <> 'OK'
ORDER BY rate_shock_bps
""".strip(),
    ),
    SampleQuery(
        question="Summarize stress_test_results: scenario_name, rate_shock_bps, stressed_avg_beta, delta_nii_millions.",
        sql="""
SELECT
  scenario_name,
  rate_shock_bps,
  stressed_avg_beta,
  delta_nii_millions,
  sot_status
FROM cfo_banking_demo.ml_models.stress_test_results
ORDER BY rate_shock_bps
""".strip(),
    ),
    SampleQuery(
        question="Show the latest 12 months of ppnr (ppnr_forecasts) with net_interest_income, non_interest_income, non_interest_expense.",
        sql="""
SELECT
  date_trunc('month', month) AS month,
  net_interest_income/1e6 AS net_interest_income_m,
  non_interest_income/1e6 AS non_interest_income_m,
  non_interest_expense/1e6 AS non_interest_expense_m,
  ppnr/1e6 AS ppnr_m
FROM cfo_banking_demo.ml_models.ppnr_forecasts
ORDER BY month DESC
LIMIT 12
""".strip(),
    ),
    SampleQuery(
        question="What is the latest yield curve snapshot (rate_2y, rate_5y, rate_10y) and date?",
        sql="""
SELECT
  date,
  rate_2y,
  rate_5y,
  rate_10y
FROM cfo_banking_demo.silver_treasury.yield_curves
WHERE date = (SELECT MAX(date) FROM cfo_banking_demo.silver_treasury.yield_curves)
""".strip(),
    ),
    SampleQuery(
        question="Show me PPNR projections for the last 9 quarters with NII, non-interest income, and expenses.",
        sql="""
WITH q AS (
  SELECT
    date_trunc('quarter', month) AS quarter,
    SUM(net_interest_income)/1e6 AS nii_m,
    SUM(non_interest_income)/1e6 AS nonii_m,
    SUM(non_interest_expense)/1e6 AS nonie_m,
    SUM(ppnr)/1e6 AS ppnr_m
  FROM cfo_banking_demo.ml_models.ppnr_forecasts
  GROUP BY date_trunc('quarter', month)
),
ranked AS (
  SELECT
    quarter,
    nii_m,
    nonii_m,
    nonie_m,
    ppnr_m,
    ROW_NUMBER() OVER (ORDER BY quarter DESC) AS rn
  FROM q
)
SELECT quarter, nii_m, nonii_m, nonie_m, ppnr_m
FROM ranked
WHERE rn <= 9
ORDER BY quarter DESC
""".strip(),
    ),
    SampleQuery(
        question="Show me delta NII, delta EVE, and LCR ratio across all stress scenarios.",
        sql="""
SELECT
  scenario_name,
  rate_shock_bps,
  delta_nii_millions,
  delta_eve_billions,
  (SELECT lcr_ratio FROM cfo_banking_demo.gold_regulatory.lcr_daily LIMIT 1) AS lcr_ratio_latest
FROM cfo_banking_demo.ml_models.stress_test_results
ORDER BY rate_shock_bps
""".strip(),
    ),
    SampleQuery(
        question="What is the CET1 ratio under baseline, adverse, and severely adverse scenarios?",
        sql="""
SELECT
  scenario_name,
  eve_cet1_ratio
FROM cfo_banking_demo.ml_models.stress_test_results
WHERE LOWER(scenario_name) LIKE '%baseline%'
   OR LOWER(scenario_name) LIKE '%adverse%'
ORDER BY scenario_name
""".strip(),
    ),
    SampleQuery(
        question="Show me at-risk accounts by relationship category with total balances and rate gaps.",
        sql="""
WITH latest AS (
  SELECT MAX(effective_date) AS effective_date
  FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
)
SELECT
  relationship_category,
  SUM(balance_millions) AS balance_m,
  AVG(rate_gap) AS avg_rate_gap,
  COUNT(*) AS accounts
FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
WHERE effective_date = (SELECT effective_date FROM latest)
  AND below_competitor_rate = 1
GROUP BY relationship_category
ORDER BY balance_m DESC
""".strip(),
    ),
    SampleQuery(
        question="What is the average deposit beta by relationship category and product type?",
        sql="""
SELECT
  relationship_category,
  product_type,
  SUM(balance_millions)/1000.0 AS balance_b,
  SUM(balance_millions * target_beta) / NULLIF(SUM(balance_millions), 0) AS avg_beta_weighted
FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
WHERE relationship_category IS NOT NULL
  AND product_type IS NOT NULL
GROUP BY relationship_category, product_type
ORDER BY balance_b DESC
""".strip(),
    ),
    SampleQuery(
        question="Show me account survival rates at 12, 24, and 36 months by relationship category.",
        sql="""
SELECT
  relationship_category,
  CAST(months_since_open AS INT) AS months_since_open,
  AVG(account_survival_rate) AS account_survival_rate_raw,
  LEAST(AVG(account_survival_rate), 1.0) AS account_retention_rate_capped,
  AVG(CAST(balance_survival_rate AS DOUBLE)) AS balance_survival_rate_raw,
  LEAST(AVG(CAST(balance_survival_rate AS DOUBLE)), 1.0) AS balance_retention_rate_capped
FROM cfo_banking_demo.ml_models.cohort_survival_rates
WHERE CAST(months_since_open AS INT) IN (12, 24, 36)
GROUP BY relationship_category, CAST(months_since_open AS INT)
ORDER BY relationship_category, months_since_open
""".strip(),
    ),
    SampleQuery(
        question="What is the projected deposit runoff over 36 months by relationship category?",
        sql="""
SELECT
  relationship_category,
  SUM(current_balance_billions) AS current_balance_b,
  SUM(projected_balance_billions) AS projected_balance_b,
  SUM(current_balance_billions - projected_balance_billions) AS projected_runoff_b
FROM cfo_banking_demo.ml_models.deposit_runoff_forecasts
WHERE months_ahead = 36
GROUP BY relationship_category
ORDER BY projected_runoff_b DESC
""".strip(),
    ),
]


def _run_sql(w: WorkspaceClient, sql: str, max_rows: int) -> dict[str, Any]:
    # Only append LIMIT if the query doesn't already contain a LIMIT clause.
    has_limit = re.search(r"\blimit\b", sql, flags=re.IGNORECASE) is not None
    statement = f"{sql}\nLIMIT {max_rows}" if not has_limit else sql
    st = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        statement=statement,
        disposition=Disposition.INLINE,
        wait_timeout="30s",
    )
    state = st.status.state.value if st.status and st.status.state else "UNKNOWN"
    if state != "SUCCEEDED":
        err = st.status.error.message if st.status and st.status.error else "unknown_error"
        return {"state": state, "error": err, "statement": statement}

    res = w.statement_execution.get_statement_result_chunk_n(st.statement_id, 0)
    # Column names in manifest
    cols = []
    if st.manifest and st.manifest.schema and st.manifest.schema.columns:
        cols = [c.name for c in st.manifest.schema.columns]
    rows = res.data_array or []
    return {"state": state, "columns": cols, "rows": rows, "statement": statement}


def main() -> None:
    w = WorkspaceClient()
    for i, sq in enumerate(SAMPLE_QUERIES, 1):
        print(f"\n## {i}. {sq.question}")
        out = _run_sql(w, sq.sql, sq.max_rows)
        print("SQL:", out.get("statement"))
        if out["state"] != "SUCCEEDED":
            print("STATE:", out["state"])
            print("ERROR:", out.get("error"))
            continue
        cols = out.get("columns") or []
        rows = out.get("rows") or []
        print("COLUMNS:", cols)
        for r in rows[:10]:
            print("ROW:", r)


if __name__ == "__main__":
    main()

