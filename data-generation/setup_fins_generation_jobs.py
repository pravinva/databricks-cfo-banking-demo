#!/usr/bin/env python3
"""
Create/update Databricks Jobs in the fins workspace for:
1) Daily full synthetic data refresh
2) Frequent realtime synthetic tick updates
"""

from __future__ import annotations

import argparse
import os

from databricks.sdk import WorkspaceClient


def upsert_job(w: WorkspaceClient, existing_job_id: int | None, settings: dict) -> int:
    if existing_job_id:
        w.api_client.do(
            "POST",
            "/api/2.2/jobs/reset",
            body={"job_id": existing_job_id, "new_settings": settings},
        )
        return existing_job_id

    created = w.api_client.do("POST", "/api/2.2/jobs/create", body=settings)
    return int(created["job_id"])


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--profile", default=os.getenv("DATABRICKS_CONFIG_PROFILE", "fins"))
    p.add_argument("--warehouse-id", required=True)
    p.add_argument("--catalog", default="banking_cfo_treasury")
    p.add_argument("--schema-prefix", default="deposit_ppnr")
    p.add_argument(
        "--workspace-base",
        default="/Workspace/Users/pravin.varma@databricks.com/cfo-data-generation",
        help="Workspace folder where generation notebooks were imported.",
    )
    p.add_argument("--full-refresh-job-id", type=int, default=None)
    p.add_argument("--realtime-job-id", type=int, default=None)
    p.add_argument("--timezone", default="UTC")
    args = p.parse_args()

    os.environ["DATABRICKS_CONFIG_PROFILE"] = args.profile
    w = WorkspaceClient()

    full_refresh_notebook = f"{args.workspace_base}/full_refresh_notebook"
    realtime_tick_notebook = f"{args.workspace_base}/realtime_tick_notebook"
    alpha_vantage_notebook = f"{args.workspace_base}/alpha_vantage_refresh_notebook"

    full_refresh_job_settings = {
        "name": f"CFO Demo - Daily Data Generation Full Refresh ({args.schema_prefix})",
        "tasks": [
            {
                "task_key": "alpha_vantage_refresh",
                "notebook_task": {
                    "notebook_path": alpha_vantage_notebook,
                    "base_parameters": {
                        "warehouse_id": args.warehouse_id,
                        "catalog": args.catalog,
                        "schema_prefix": args.schema_prefix,
                        "start_date": "2024-01-01",
                        "secret_scope": "cfo_demo",
                        "secret_key": "alpha_vantage_api_key",
                    },
                },
                "timeout_seconds": 1800,
            },
            {
                "task_key": "full_refresh",
                "notebook_task": {
                    "notebook_path": full_refresh_notebook,
                    "base_parameters": {
                        "warehouse_id": args.warehouse_id,
                        "catalog": args.catalog,
                        "schema_prefix": args.schema_prefix,
                        "sql_base_path": "dbfs:/FileStore/cfo-data-generation/sql",
                    },
                },
                "depends_on": [{"task_key": "alpha_vantage_refresh"}],
                "timeout_seconds": 7200,
            }
        ],
        "schedule": {
            "quartz_cron_expression": "0 0 2 ? * *",  # 02:00 daily
            "timezone_id": args.timezone,
            "pause_status": "UNPAUSED",
        },
        "max_concurrent_runs": 1,
    }

    realtime_tick_job_settings = {
        "name": f"CFO Demo - Realtime Data Generation Tick ({args.schema_prefix})",
        "tasks": [
            {
                "task_key": "realtime_tick",
                "notebook_task": {
                    "notebook_path": realtime_tick_notebook,
                    "base_parameters": {
                        "warehouse_id": args.warehouse_id,
                        "catalog": args.catalog,
                        "schema_prefix": args.schema_prefix,
                        "sql_file_path": "dbfs:/FileStore/cfo-data-generation/sql/50_realtime_tick.sql",
                    },
                },
                "timeout_seconds": 1800,
            }
        ],
        "schedule": {
            "quartz_cron_expression": "0 0/15 * ? * *",  # every 15 minutes
            "timezone_id": args.timezone,
            "pause_status": "UNPAUSED",
        },
        "max_concurrent_runs": 1,
    }

    full_job_id = upsert_job(w, args.full_refresh_job_id, full_refresh_job_settings)
    realtime_job_id = upsert_job(w, args.realtime_job_id, realtime_tick_job_settings)

    print(f"Full refresh job id: {full_job_id}")
    print(f"Realtime tick job id: {realtime_job_id}")

    # Kick off one immediate run of each so user can validate.
    full_run = w.api_client.do("POST", "/api/2.2/jobs/run-now", body={"job_id": full_job_id})
    tick_run = w.api_client.do("POST", "/api/2.2/jobs/run-now", body={"job_id": realtime_job_id})
    print(f"Triggered full refresh run_id: {full_run.get('run_id')}")
    print(f"Triggered realtime tick run_id: {tick_run.get('run_id')}")


if __name__ == "__main__":
    main()
