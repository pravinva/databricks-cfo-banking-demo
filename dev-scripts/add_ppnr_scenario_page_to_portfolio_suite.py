#!/usr/bin/env python3
"""
Add a new "PPNR Scenario Planning" page to the existing Lakeview dashboard:
  CFO Deposit Portfolio Suite (dashboard_id = 01f0fea1adbb1e97a3142da3a87f7cb8)

This script:
1) GETs the current dashboard draft
2) Updates serialized_dashboard by adding:
   - datasets (SQL queries)
   - a new PAGE_TYPE_CANVAS page with widgets
3) PATCHes the draft (etag-protected)
4) Publishes the dashboard (embed_credentials=true)

Usage:
  DATABRICKS_CONFIG_PROFILE=DEFAULT python dev-scripts/add_ppnr_scenario_page_to_portfolio_suite.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List

from databricks.sdk import WorkspaceClient


DASHBOARD_ID = "01f0fea1adbb1e97a3142da3a87f7cb8"


@dataclass(frozen=True)
class DatasetDef:
    name: str
    display_name: str
    sql: str

    def as_serialized(self) -> dict:
        # Lakeview serialized_dashboard expects queryLines list-of-strings.
        lines = []
        for line in self.sql.strip().splitlines(True):
            lines.append(line)
        if not lines:
            lines = [self.sql]
        return {"name": self.name, "displayName": self.display_name, "queryLines": lines}


def _widget_line(widget_name: str, title: str, dataset: str, x: str, y: str, color: str | None = None) -> dict:
    enc: dict = {
        "x": {"fieldName": x, "scale": {"type": "temporal"}, "displayName": x},
        "y": {"fieldName": y, "scale": {"type": "quantitative"}, "displayName": y},
    }
    if color:
        enc["color"] = {"fieldName": color, "scale": {"type": "categorical"}, "displayName": color}

    return {
        "name": widget_name,
        "queries": [
            {
                "name": "main_query",
                "query": {
                    "datasetName": dataset,
                    "fields": [{"name": x, "expression": f"`{x}`"}, {"name": y, "expression": f"`{y}`"}]
                    + ([{"name": color, "expression": f"`{color}`"}] if color else []),
                    "disaggregated": False,
                },
            }
        ],
        "spec": {"version": 3, "frame": {"title": title, "showTitle": True}, "widgetType": "line", "encodings": enc},
    }


def _widget_bar(widget_name: str, title: str, dataset: str, x: str, y: str, color: str | None = None) -> dict:
    enc: dict = {
        "x": {"fieldName": x, "scale": {"type": "temporal"}, "displayName": x},
        "y": {"fieldName": y, "scale": {"type": "quantitative"}, "displayName": y},
    }
    if color:
        enc["color"] = {"fieldName": color, "scale": {"type": "categorical"}, "displayName": color}

    return {
        "name": widget_name,
        "queries": [
            {
                "name": "main_query",
                "query": {
                    "datasetName": dataset,
                    "fields": [{"name": x, "expression": f"`{x}`"}, {"name": y, "expression": f"`{y}`"}]
                    + ([{"name": color, "expression": f"`{color}`"}] if color else []),
                    "disaggregated": False,
                },
            }
        ],
        "spec": {"version": 3, "frame": {"title": title, "showTitle": True}, "widgetType": "bar", "encodings": enc},
    }


def _ensure_unique_page(pages: list[dict], page_name: str) -> None:
    for p in pages:
        if p.get("name") == page_name:
            raise RuntimeError(f"Page already exists in dashboard: {page_name}")


def main() -> None:
    w = WorkspaceClient()

    dash = w.api_client.do("GET", f"/api/2.0/lakeview/dashboards/{DASHBOARD_ID}")
    etag = dash["etag"]
    serialized = json.loads(dash["serialized_dashboard"])

    datasets: list[dict] = serialized.get("datasets", [])
    pages: list[dict] = serialized.get("pages", [])

    page_name = "ppnr_scenario_planning"
    _ensure_unique_page(pages, page_name)

    # Datasets (keep names unique and stable)
    new_datasets = [
        DatasetDef(
            name="ppnr_ds_ppnr_trend",
            display_name="PPNR Trend (Scenario)",
            sql="""
SELECT
  quarter_start,
  scenario_id,
  ppnr_usd / 1e6 AS ppnr_m
FROM cfo_banking_demo.gold_finance.ppnr_projection_quarterly_ml
ORDER BY quarter_start, scenario_id
""",
        ),
        DatasetDef(
            name="ppnr_ds_nii_trend",
            display_name="NII Trend (Scenario)",
            sql="""
SELECT
  quarter_start,
  scenario_id,
  nii_usd / 1e6 AS nii_m
FROM cfo_banking_demo.gold_finance.nii_projection_quarterly
ORDER BY quarter_start, scenario_id
""",
        ),
        DatasetDef(
            name="ppnr_ds_component_delta",
            display_name="ΔPPNR Component Attribution (vs Baseline)",
            sql="""
WITH base AS (
  SELECT
    quarter_start,
    nii_usd AS b_nii,
    non_interest_income_usd AS b_nonii,
    non_interest_expense_usd AS b_nonie,
    ppnr_usd AS b_ppnr
  FROM cfo_banking_demo.gold_finance.ppnr_projection_quarterly_ml
  WHERE scenario_id = 'baseline'
),
scn AS (
  SELECT *
  FROM cfo_banking_demo.gold_finance.ppnr_projection_quarterly_ml
  WHERE scenario_id <> 'baseline'
),
d AS (
  SELECT
    s.quarter_start,
    s.scenario_id,
    (s.nii_usd - b.b_nii) / 1e6 AS delta_nii_m,
    (s.non_interest_income_usd - b.b_nonii) / 1e6 AS delta_nonii_m,
    (s.non_interest_expense_usd - b.b_nonie) / 1e6 AS delta_nonie_m,
    (s.ppnr_usd - b.b_ppnr) / 1e6 AS delta_ppnr_m
  FROM scn s
  JOIN base b
    ON s.quarter_start = b.quarter_start
)
SELECT quarter_start, scenario_id, 'ΔNII' AS component, delta_nii_m AS delta_m FROM d
UNION ALL
SELECT quarter_start, scenario_id, 'ΔNonII' AS component, delta_nonii_m AS delta_m FROM d
UNION ALL
SELECT quarter_start, scenario_id, '−ΔNonIE' AS component, (-delta_nonie_m) AS delta_m FROM d
UNION ALL
SELECT quarter_start, scenario_id, 'ΔPPNR (check)' AS component, delta_ppnr_m AS delta_m FROM d
ORDER BY quarter_start, scenario_id, component
""",
        ),
        DatasetDef(
            name="ppnr_ds_volumes",
            display_name="Projected Balances ($B)",
            sql="""
SELECT
  quarter_start,
  scenario_id,
  projected_deposit_balance_usd / 1e9 AS deposits_b
FROM cfo_banking_demo.gold_finance.nii_projection_quarterly
ORDER BY quarter_start, scenario_id
""",
        ),
    ]

    existing_dataset_names = {d.get("name") for d in datasets}
    for ds in new_datasets:
        if ds.name in existing_dataset_names:
            raise RuntimeError(f"Dataset already exists in dashboard: {ds.name}")
        datasets.append(ds.as_serialized())

    # New page + widgets
    new_page = {
        "name": page_name,
        "displayName": "PPNR Scenario Planning",
        "pageType": "PAGE_TYPE_CANVAS",
        "layoutVersion": "GRID_V1",
        "layout": [
            {
                "position": {"x": 0, "y": 0, "width": 12, "height": 5},
                "widget": _widget_line(
                    widget_name="ppnr_ppnr_trend_line",
                    title="PPNR — 9Q Projection ($M)",
                    dataset="ppnr_ds_ppnr_trend",
                    x="quarter_start",
                    y="ppnr_m",
                    color="scenario_id",
                ),
            },
            {
                "position": {"x": 12, "y": 0, "width": 12, "height": 5},
                "widget": _widget_line(
                    widget_name="ppnr_nii_trend_line",
                    title="NII — 9Q Projection ($M)",
                    dataset="ppnr_ds_nii_trend",
                    x="quarter_start",
                    y="nii_m",
                    color="scenario_id",
                ),
            },
            {
                "position": {"x": 0, "y": 5, "width": 12, "height": 5},
                "widget": _widget_bar(
                    widget_name="ppnr_component_delta_bar",
                    title="ΔPPNR Attribution vs Baseline ($M)",
                    dataset="ppnr_ds_component_delta",
                    x="quarter_start",
                    y="delta_m",
                    color="component",
                ),
            },
            {
                "position": {"x": 12, "y": 5, "width": 12, "height": 5},
                "widget": _widget_line(
                    widget_name="ppnr_deposits_volume_line",
                    title="Projected Deposits Balance ($B)",
                    dataset="ppnr_ds_volumes",
                    x="quarter_start",
                    y="deposits_b",
                    color="scenario_id",
                ),
            },
        ],
    }

    pages.append(new_page)

    serialized["datasets"] = datasets
    serialized["pages"] = pages

    # Update dashboard draft (etag protected)
    update_body = {
        "etag": etag,
        "serialized_dashboard": json.dumps(serialized),
    }
    w.api_client.do("PATCH", f"/api/2.0/lakeview/dashboards/{DASHBOARD_ID}", body=update_body)

    # Publish (embed credentials) so the published link updates
    w.api_client.do(
        "POST",
        f"/api/2.0/lakeview/dashboards/{DASHBOARD_ID}/published",
        body={"embed_credentials": True},
    )

    print("Done. Added page and published dashboard.")


if __name__ == "__main__":
    main()

