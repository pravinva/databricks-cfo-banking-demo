"""
Create or update a Databricks Job that runs the Executive Treasury report notebook
twice daily and writes HTML + PDF to the UC Volume.

Usage example:
  python scripts/setup_executive_report_job.py \
    --notebook-path "/Repos/you@databricks.com/databricks-cfo-banking-demo/notebooks/Generate_Report_Executive_Layout" \
    --existing-cluster-id "0123-456789-abcde" \
    --timezone "UTC"

By default this schedules at 09:00 and 21:00 (twice daily) in the provided timezone.
"""

from __future__ import annotations

import argparse
import os

from databricks.sdk import WorkspaceClient


DEFAULT_CRON_TWICE_DAILY = "0 0 9,21 ? * *"  # sec min hour day-of-month month day-of-week


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--job-name", default="CFO Demo - Executive Treasury Report (ALCO PDF)")
    p.add_argument("--notebook-path", required=True, help="Workspace notebook path to run")
    p.add_argument(
        "--existing-cluster-id",
        required=True,
        help="Cluster ID to run the notebook on (existing cluster).",
    )
    p.add_argument("--timezone", default="UTC", help="Schedule timezone (Quartz)")
    p.add_argument(
        "--cron",
        default=DEFAULT_CRON_TWICE_DAILY,
        help="Quartz cron. Default runs twice daily at 09:00 and 21:00.",
    )
    p.add_argument(
        "--job-id",
        type=int,
        default=None,
        help="If provided, updates (resets) this job id instead of creating a new job.",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    w = WorkspaceClient()

    job_settings = {
        "name": args.job_name,
        "tasks": [
            {
                "task_key": "generate_executive_report",
                "existing_cluster_id": args.existing_cluster_id,
                "notebook_task": {
                    "notebook_path": args.notebook_path,
                },
                # Allow the notebook's %pip to run
                "timeout_seconds": 3600,
            }
        ],
        "schedule": {
            "quartz_cron_expression": args.cron,
            "timezone_id": args.timezone,
            "pause_status": "UNPAUSED",
        },
        # Let multiple runs queue rather than fail if a cluster is busy
        "max_concurrent_runs": 1,
    }

    if args.job_id is not None:
        w.jobs.reset(job_id=args.job_id, new_settings=job_settings)
        print(f"Updated job_id={args.job_id}")
        job_id = args.job_id
    else:
        created = w.jobs.create(**job_settings)
        job_id = created.job_id
        print(f"Created job_id={job_id}")

    host = os.getenv("DATABRICKS_HOST")
    if host:
        print(f"Job URL: {host}/#job/{job_id}")
    else:
        print("Tip: set DATABRICKS_HOST to print a clickable job URL.")


if __name__ == "__main__":
    main()

