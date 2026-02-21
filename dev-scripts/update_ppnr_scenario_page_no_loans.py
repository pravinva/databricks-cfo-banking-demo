#!/usr/bin/env python3
"""
Ensure the "PPNR Scenario Planning" page in the Portfolio Suite dashboard contains
no loan references (titles/queries) and republish.

This script is safe to run multiple times.

Usage:
  DATABRICKS_CONFIG_PROFILE=DEFAULT python dev-scripts/update_ppnr_scenario_page_no_loans.py
"""

from __future__ import annotations

import json

from databricks.sdk import WorkspaceClient


DASHBOARD_ID = "01f0fea1adbb1e97a3142da3a87f7cb8"
PAGE_NAME = "ppnr_scenario_planning"


def _set_dataset_sql(serialized: dict, dataset_name: str, sql: str) -> None:
    datasets = serialized.get("datasets", [])
    for d in datasets:
        if d.get("name") == dataset_name:
            d["queryLines"] = [line for line in sql.strip().splitlines(True)] or [sql]
            return
    raise RuntimeError(f"Dataset not found: {dataset_name}")


def _assert_no_loan_strings(serialized: dict) -> None:
    """
    Enforce: no widget titles/frames contain the substring 'loan' (case-insensitive)
    on the scenario planning page.
    """
    pages = serialized.get("pages", [])
    page = next((p for p in pages if p.get("name") == PAGE_NAME), None)
    if not page:
        raise RuntimeError(f"Page not found: {PAGE_NAME}")

    for item in page.get("layout", []):
        w = item.get("widget", {})
        spec = w.get("spec", {}) or {}
        frame = spec.get("frame", {}) or {}
        title = frame.get("title") or ""
        if "loan" in str(title).lower():
            raise RuntimeError(f"Loan reference found in widget title: {title}")


def main() -> None:
    w = WorkspaceClient()
    dash = w.api_client.do("GET", f"/api/2.0/lakeview/dashboards/{DASHBOARD_ID}")
    etag = dash["etag"]
    serialized = json.loads(dash["serialized_dashboard"])

    # Update NII trend dataset to source NII from the ML PPNR table (no loan-related columns).
    _set_dataset_sql(
        serialized,
        "ppnr_ds_nii_trend",
        """
SELECT
  quarter_start,
  scenario_id,
  nii_usd / 1e6 AS nii_m
FROM cfo_banking_demo.gold_finance.ppnr_projection_quarterly_ml
ORDER BY quarter_start, scenario_id
""",
    )

    # Keep volumes dataset explicitly deposit-only (already), but make it crystal clear.
    _set_dataset_sql(
        serialized,
        "ppnr_ds_volumes",
        """
SELECT
  quarter_start,
  scenario_id,
  projected_deposit_balance_usd / 1e9 AS deposits_b
FROM cfo_banking_demo.gold_finance.nii_projection_quarterly
ORDER BY quarter_start, scenario_id
""",
    )

    _assert_no_loan_strings(serialized)

    # PATCH draft + publish.
    w.api_client.do(
        "PATCH",
        f"/api/2.0/lakeview/dashboards/{DASHBOARD_ID}",
        body={"etag": etag, "serialized_dashboard": json.dumps(serialized)},
    )
    w.api_client.do(
        "POST",
        f"/api/2.0/lakeview/dashboards/{DASHBOARD_ID}/published",
        body={"embed_credentials": True},
    )

    print("Done. Scenario page updated to exclude loans and republished.")


if __name__ == "__main__":
    main()

