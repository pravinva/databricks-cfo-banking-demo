#!/usr/bin/env python3
"""
Clone a Genie room from one workspace/profile into another workspace/profile,
rewriting table references to the target catalog + schema prefix.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from databricks.sdk import WorkspaceClient


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--source-profile", default="DEFAULT")
    p.add_argument("--target-profile", default="fins")
    p.add_argument("--source-space-id", required=True)
    p.add_argument("--target-space-id", default="")
    p.add_argument("--target-title", default="Treasury Modeling - Deposits & Fee Income")
    p.add_argument("--target-description", default="Migrated from Field Engg workspace.")
    p.add_argument("--target-warehouse-id", required=True)
    p.add_argument("--target-catalog", default="banking_cfo_treasury")
    p.add_argument("--schema-prefix", default="deposit_ppnr")
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def _schema_map(prefix: str) -> dict[str, str]:
    clean = prefix.strip().strip("_")
    return {
        "bronze_core_banking": f"{clean}_bronze_core_banking",
        "silver_finance": f"{clean}_silver_finance",
        "silver_treasury": f"{clean}_silver_treasury",
        "ml_models": f"{clean}_ml_models",
        "gold_finance": f"{clean}_gold_finance",
        "gold_regulatory": f"{clean}_gold_regulatory",
    }


def _legacy_table_map(target_catalog: str, prefix: str) -> dict[str, str]:
    sm = _schema_map(prefix)
    return {
        "cfo_banking_demo.bronze_core_banking.deposit_accounts": f"{target_catalog}.{sm['bronze_core_banking']}.deposit_accounts",
        "cfo_banking_demo.bronze_core_banking.deposit_accounts_historical": f"{target_catalog}.{sm['bronze_core_banking']}.deposit_accounts_history",
        "cfo_banking_demo.silver_treasury.yield_curves": f"{target_catalog}.{sm['silver_treasury']}.yield_curves",
        "cfo_banking_demo.ml_models.deposit_beta_predictions": f"{target_catalog}.{sm['ml_models']}.deposit_beta_predictions",
        "cfo_banking_demo.ml_models.deposit_beta_training_enhanced": f"{target_catalog}.{sm['ml_models']}.deposit_beta_training_enhanced",
        "cfo_banking_demo.ml_models.cohort_survival_rates": f"{target_catalog}.{sm['ml_models']}.cohort_survival_rates",
        "cfo_banking_demo.ml_models.component_decay_metrics": f"{target_catalog}.{sm['ml_models']}.component_decay_metrics",
        "cfo_banking_demo.ml_models.deposit_runoff_forecasts": f"{target_catalog}.{sm['ml_models']}.deposit_runoff_forecasts",
        "cfo_banking_demo.ml_models.dynamic_beta_parameters": f"{target_catalog}.{sm['ml_models']}.dynamic_beta_parameters",
        "cfo_banking_demo.ml_models.non_interest_income_training_data": f"{target_catalog}.{sm['ml_models']}.non_interest_income_training_data",
        "cfo_banking_demo.ml_models.non_interest_expense_training_data": f"{target_catalog}.{sm['ml_models']}.non_interest_expense_training_data",
        "cfo_banking_demo.ml_models.ppnr_forecasts": f"{target_catalog}.{sm['ml_models']}.ppnr_forecasts",
        "cfo_banking_demo.ml_models.stress_test_results": f"{target_catalog}.{sm['ml_models']}.stress_test_results",
        "cfo_banking_demo.gold_regulatory.lcr_daily": f"{target_catalog}.{sm['gold_regulatory']}.lcr_daily",
        "cfo_banking_demo.gold_regulatory.hqla_inventory": f"{target_catalog}.{sm['gold_regulatory']}.hqla_inventory",
    }


def _rewrite_text(value: str, replacements: dict[str, str]) -> str:
    out = value
    # Longest-key-first prevents partial replacements colliding.
    for src in sorted(replacements.keys(), key=len, reverse=True):
        out = out.replace(src, replacements[src])
    return out


def _rewrite_recursive(obj: Any, replacements: dict[str, str]) -> Any:
    if isinstance(obj, dict):
        return {k: _rewrite_recursive(v, replacements) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_rewrite_recursive(v, replacements) for v in obj]
    if isinstance(obj, str):
        return _rewrite_text(obj, replacements)
    return obj


def _load_space(w: WorkspaceClient, space_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    raw = w.api_client.do(
        "GET",
        f"/api/2.0/genie/spaces/{space_id}",
        query={"include_serialized_space": "true"},
    )
    serialized = json.loads(raw.get("serialized_space") or "{}")
    return raw, serialized


def _patch_space(w: WorkspaceClient, space_id: str, serialized_space: dict[str, Any]) -> None:
    w.api_client.do(
        "PATCH",
        f"/api/2.0/genie/spaces/{space_id}",
        body={"serialized_space": json.dumps(serialized_space)},
    )


def _create_space(
    w: WorkspaceClient,
    title: str,
    description: str,
    warehouse_id: str,
    serialized_space: dict[str, Any],
) -> str:
    created = w.api_client.do(
        "POST",
        "/api/2.0/genie/spaces",
        body={
            "title": title,
            "description": description,
            "warehouse_id": warehouse_id,
            "serialized_space": json.dumps(serialized_space),
        },
    )
    return created["space_id"]


def _find_space_id_by_title(w: WorkspaceClient, title: str) -> str:
    page_token = None
    while True:
        query = {}
        if page_token:
            query["page_token"] = page_token
        resp = w.api_client.do("GET", "/api/2.0/genie/spaces", query=query)
        for space in resp.get("spaces") or []:
            if (space.get("title") or "").strip() == title.strip():
                return space.get("space_id") or ""
        page_token = resp.get("next_page_token")
        if not page_token:
            return ""


def main() -> None:
    args = parse_args()
    src = WorkspaceClient(profile=args.source_profile)
    dst = WorkspaceClient(profile=args.target_profile)

    _, src_serialized = _load_space(src, args.source_space_id)
    replacements = _legacy_table_map(args.target_catalog, args.schema_prefix)
    migrated_serialized = _rewrite_recursive(src_serialized, replacements)

    if args.dry_run:
        print("Dry run complete.")
        print(f"Source space: {args.source_space_id}")
        print(f"Target title: {args.target_title}")
        print(f"Replacements applied: {len(replacements)}")
        return

    target_space_id = args.target_space_id.strip()
    if not target_space_id:
        target_space_id = _find_space_id_by_title(dst, args.target_title)

    if target_space_id:
        _patch_space(dst, target_space_id, migrated_serialized)
        print(f"Updated existing target space: {target_space_id}")
    else:
        target_space_id = _create_space(
            dst,
            title=args.target_title,
            description=args.target_description,
            warehouse_id=args.target_warehouse_id,
            serialized_space=migrated_serialized,
        )
        print(f"Created target space: {target_space_id}")

    print("Migration complete.")


if __name__ == "__main__":
    main()
