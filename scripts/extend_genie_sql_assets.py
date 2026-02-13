"""
Extend the Treasury Modeling Genie space with additional example SQL queries and reusable SQL snippets
(filters / expressions / measures) to improve response quality and benchmark accuracy.

This updates the Genie space `serialized_space` (no table changes).

Run:
  DATABRICKS_CONFIG_PROFILE=DEFAULT python3 scripts/extend_genie_sql_assets.py --apply
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from databricks.sdk import WorkspaceClient


SPACE_ID_DEFAULT = "01f101adda151c09835a99254d4c308c"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--space-id", default=SPACE_ID_DEFAULT)
    p.add_argument("--apply", action="store_true", help="Patch the Genie space (otherwise dry-run).")
    return p.parse_args()


def _load_space(w: WorkspaceClient, space_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    resp = w.api_client._perform(
        "GET",
        f"/api/2.0/genie/spaces/{space_id}",
        query={"include_serialized_space": "true"},
    )
    space = json.loads(resp.get("serialized_space") or "{}")
    return resp, space


def _patch_space(w: WorkspaceClient, space_id: str, space: dict[str, Any]) -> None:
    w.api_client._perform(
        "PATCH",
        f"/api/2.0/genie/spaces/{space_id}",
        body={"serialized_space": json.dumps(space)},
    )


def _to_single_line_sql(sql: str) -> str:
    s = " ".join([line.strip() for line in sql.splitlines() if line.strip()])
    while "  " in s:
        s = s.replace("  ", " ")
    return s.strip()


def _ensure_list(container: dict[str, Any], key: str) -> list[dict[str, Any]]:
    v = container.get(key)
    if v is None:
        container[key] = []
        v = container[key]
    if not isinstance(v, list):
        container[key] = []
        v = container[key]
    return v


def _has_question(example_sqls: list[dict[str, Any]], question_text: str) -> bool:
    for ex in example_sqls:
        q = (ex.get("question") or [""])[0]
        if isinstance(q, str) and q.strip() == question_text.strip():
            return True
    return False


def _upsert_expr_or_measure(
    snips: list[dict[str, Any]],
    *,
    id: str,
    alias: str,
    sql: str,
    display_name: str,
    synonyms: list[str],
) -> bool:
    for s in snips:
        if s.get("id") == id or s.get("alias") == alias:
            s["id"] = id
            s["alias"] = alias
            s["sql"] = [_to_single_line_sql(sql)]
            s["display_name"] = display_name
            s["synonyms"] = synonyms
            return True
    snips.append(
        {
            "id": id,
            "alias": alias,
            "sql": [_to_single_line_sql(sql)],
            "display_name": display_name,
            "synonyms": synonyms,
        }
    )
    return True


def _upsert_filter(
    snips: list[dict[str, Any]],
    *,
    id: str,
    sql: str,
    display_name: str,
    synonyms: list[str],
) -> bool:
    # NOTE: Filter proto does NOT include "alias" (unlike expressions/measures).
    for s in snips:
        if s.get("id") == id or s.get("display_name") == display_name:
            s["id"] = id
            s["sql"] = [_to_single_line_sql(sql)]
            s["display_name"] = display_name
            s["synonyms"] = synonyms
            # remove invalid fields if present
            if "alias" in s:
                s.pop("alias", None)
            return True
    snips.append(
        {
            "id": id,
            "sql": [_to_single_line_sql(sql)],
            "display_name": display_name,
            "synonyms": synonyms,
        }
    )
    return True


def extend(space: dict[str, Any]) -> int:
    changed = 0

    instructions = space.get("instructions") or {}
    space["instructions"] = instructions

    # --- Example SQL queries ---
    example_sqls = _ensure_list(instructions, "example_question_sqls")

    new_examples: list[dict[str, Any]] = [
        {
            "id": "55555555555555555555555555555555",
            "question": ["Show total deposits ($B) by month for the last 12 months (current portfolio only)."],
            "sql": [
                _to_single_line_sql(
                    """
WITH monthly AS (
  SELECT
    date_trunc('month', effective_date) AS month,
    SUM(current_balance) AS bal
  FROM cfo_banking_demo.bronze_core_banking.deposit_accounts_historical
  WHERE effective_date >= add_months(current_date(), -12)
  GROUP BY date_trunc('month', effective_date)
)
SELECT
  month,
  bal/1e9 AS total_deposits_b
FROM monthly
ORDER BY month
"""
                )
            ],
        },
        {
            "id": "66666666666666666666666666666666",
            "question": ["Show total deposits ($B) by month vs prior year (YoY) for the last 12 months."],
            "sql": [
                _to_single_line_sql(
                    """
WITH m AS (
  SELECT
    date_trunc('month', effective_date) AS month,
    SUM(current_balance) AS bal
  FROM cfo_banking_demo.bronze_core_banking.deposit_accounts_historical
  WHERE effective_date >= add_months(current_date(), -24)
  GROUP BY date_trunc('month', effective_date)
),
yoy AS (
  SELECT
    month,
    bal/1e9 AS total_deposits_b,
    LAG(bal/1e9, 12) OVER (ORDER BY month) AS prior_year_deposits_b
  FROM m
)
SELECT
  month,
  total_deposits_b,
  prior_year_deposits_b,
  ROUND((total_deposits_b - prior_year_deposits_b) / NULLIF(prior_year_deposits_b, 0) * 100, 2) AS yoy_pct
FROM yoy
WHERE month >= add_months(date_trunc('month', current_date()), -12)
ORDER BY month
"""
                )
            ],
        },
        {
            "id": "77777777777777777777777777777777",
            "question": ["What is the balance-weighted portfolio beta by product_type (current portfolio)?"],
            "sql": [
                _to_single_line_sql(
                    """
WITH scored AS (
  SELECT
    d.product_type,
    d.current_balance,
    COALESCE(p.predicted_beta, d.beta) AS beta_used
  FROM cfo_banking_demo.bronze_core_banking.deposit_accounts d
  LEFT JOIN cfo_banking_demo.ml_models.deposit_beta_predictions p
    ON d.account_id = p.account_id
  WHERE d.is_current = TRUE
)
SELECT
  product_type,
  SUM(current_balance)/1e9 AS balance_b,
  SUM(current_balance * beta_used) / NULLIF(SUM(current_balance), 0) AS portfolio_beta
FROM scored
WHERE product_type IS NOT NULL
GROUP BY product_type
ORDER BY balance_b DESC
"""
                )
            ],
        },
        {
            "id": "88888888888888888888888888888888",
            "question": ["At 36 months, show runoff ($B) by relationship_category and product_type."],
            "sql": [
                _to_single_line_sql(
                    """
SELECT
  relationship_category,
  product_type,
  SUM(current_balance_billions) AS current_balance_b,
  SUM(projected_balance_billions) AS projected_balance_b,
  SUM(current_balance_billions - projected_balance_billions) AS projected_runoff_b
FROM cfo_banking_demo.ml_models.deposit_runoff_forecasts
WHERE months_ahead = 36
GROUP BY relationship_category, product_type
ORDER BY projected_runoff_b DESC
"""
                )
            ],
        },
        {
            "id": "99999999999999999999999999999999",
            "question": ["Show the last 6 months of average predicted beta (balance-weighted) by month."],
            "sql": [
                _to_single_line_sql(
                    """
WITH m AS (
  SELECT
    date_trunc('month', h.effective_date) AS month,
    SUM(h.current_balance) AS bal,
    SUM(h.current_balance * COALESCE(p.predicted_beta, h.beta)) AS bal_beta
  FROM cfo_banking_demo.bronze_core_banking.deposit_accounts_historical h
  LEFT JOIN cfo_banking_demo.ml_models.deposit_beta_predictions p
    ON h.account_id = p.account_id
  WHERE h.effective_date >= add_months(current_date(), -6)
  GROUP BY date_trunc('month', h.effective_date)
)
SELECT
  month,
  (bal_beta / NULLIF(bal, 0)) AS portfolio_beta
FROM m
ORDER BY month
"""
                )
            ],
        },
    ]

    for ex in new_examples:
        if not _has_question(example_sqls, ex["question"][0]):
            example_sqls.append(ex)
            changed += 1

    # proto requires example_question_sqls sorted by id
    example_sqls.sort(key=lambda x: (x.get("id") or ""))

    # --- SQL snippets (filters/expressions/measures) ---
    sql_snips = instructions.get("sql_snippets") or {}
    instructions["sql_snippets"] = sql_snips

    filters = _ensure_list(sql_snips, "filters")
    expressions = _ensure_list(sql_snips, "expressions")
    measures = _ensure_list(sql_snips, "measures")

    if _upsert_expr_or_measure(
        measures,
        id="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        alias="balance_b",
        sql="SUM(current_balance) / 1e9",
        display_name="Balance ($B)",
        synonyms=["balance_b", "balance in billions", "total balance $b"],
    ):
        changed += 1

    if _upsert_expr_or_measure(
        measures,
        id="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        alias="portfolio_beta_weighted_fallback",
        sql="SUM(current_balance * COALESCE(predicted_beta, beta)) / NULLIF(SUM(current_balance), 0)",
        display_name="Portfolio Beta (Balance-Weighted, with fallback)",
        synonyms=["portfolio beta", "weighted beta", "beta weighted"],
    ):
        changed += 1

    if _upsert_expr_or_measure(
        expressions,
        id="cccccccccccccccccccccccccccccccc",
        alias="beta_used",
        sql="COALESCE(predicted_beta, beta)",
        display_name="Beta Used (Predicted with Fallback)",
        synonyms=["beta used", "effective beta", "beta fallback"],
    ):
        changed += 1

    if _upsert_expr_or_measure(
        expressions,
        id="dddddddddddddddddddddddddddddddd",
        alias="month",
        sql="date_trunc('month', effective_date)",
        display_name="Month (from effective_date)",
        synonyms=["month", "monthly bucket", "month bucket"],
    ):
        changed += 1

    if _upsert_filter(
        filters,
        id="eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        sql="is_current = TRUE",
        display_name="Current Portfolio Only",
        synonyms=["current", "current portfolio", "active accounts"],
    ):
        changed += 1

    # Deterministic ordering for export proto validation
    filters.sort(key=lambda x: (x.get("id") or ""))
    expressions.sort(key=lambda x: (x.get("id") or ""))
    measures.sort(key=lambda x: (x.get("id") or ""))

    return changed


def main() -> None:
    args = parse_args()
    w = WorkspaceClient()
    _, space = _load_space(w, args.space_id)

    changed = extend(space)
    print(f"Space {args.space_id}: would update {changed} item(s).")

    if not args.apply:
        print("Dry run only. Re-run with --apply to patch the Genie space.")
        return

    if changed == 0:
        print("No changes needed.")
        return

    _patch_space(w, args.space_id, space)
    print("✓ Patched Genie space serialized_space.")


if __name__ == "__main__":
    main()

