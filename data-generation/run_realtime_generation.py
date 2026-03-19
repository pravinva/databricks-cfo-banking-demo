#!/usr/bin/env python3
"""
Continuously execute realtime synthetic data ticks.
"""

from __future__ import annotations

import argparse
import os
import re
import time
from pathlib import Path

from databricks.sdk import WorkspaceClient


def _schema_map(schema_prefix: str) -> dict[str, str]:
    prefix = schema_prefix.strip().strip("_")
    if not prefix:
        raise ValueError("schema_prefix must not be empty")
    return {
        "bronze_core_banking": f"{prefix}_bronze_core_banking",
        "silver_finance": f"{prefix}_silver_finance",
        "silver_treasury": f"{prefix}_silver_treasury",
        "ml_models": f"{prefix}_ml_models",
        "gold_finance": f"{prefix}_gold_finance",
        "gold_regulatory": f"{prefix}_gold_regulatory",
    }


def _rewrite_catalog_references(sql_text: str, catalog: str, schema_prefix: str) -> str:
    text = sql_text.replace("cfo_banking_demo.", f"{catalog}.")
    text = text.replace("USE CATALOG cfo_banking_demo", f"USE CATALOG {catalog}")
    for schema, prefixed_schema in _schema_map(schema_prefix).items():
        text = text.replace(f".{schema}.", f".{prefixed_schema}.")
        text = re.sub(
            rf"(?<![\w\.]){schema}\.",
            f"{catalog}.{prefixed_schema}.",
            text,
        )
        text = re.sub(
            rf"USE\s+SCHEMA\s+{schema}\b",
            f"USE SCHEMA {catalog}.{prefixed_schema}",
            text,
            flags=re.IGNORECASE,
        )
    return text


def _load_tick_statements(sql_file: Path, catalog: str, schema_prefix: str) -> list[str]:
    raw = _rewrite_catalog_references(sql_file.read_text(encoding="utf-8"), catalog, schema_prefix)
    statements: list[str] = []
    current: list[str] = []
    for line in raw.splitlines():
        if line.strip().startswith("--"):
            continue
        current.append(line)
        if line.strip().endswith(";"):
            statement = "\n".join(current).strip().rstrip(";").strip()
            if statement:
                statements.append(statement)
            current = []
    trailing = "\n".join(current).strip()
    if trailing:
        statements.append(trailing)
    return statements


def _exec_sql(client: WorkspaceClient, warehouse_id: str, statement: str) -> None:
    resp = client.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=statement,
        wait_timeout="20s",
    )
    state = resp.status.state.value if resp.status and resp.status.state else "UNKNOWN"
    if state not in ("SUCCEEDED", "PENDING", "RUNNING"):
        err = resp.status.error if resp.status else None
        raise RuntimeError(
            f"Statement start failed: code={getattr(err, 'error_code', 'UNKNOWN')} "
            f"message={getattr(err, 'message', 'Unknown error')}"
        )

    if state == "SUCCEEDED":
        return

    statement_id = resp.statement_id
    while True:
        s = client.statement_execution.get_statement(statement_id)
        current_state = s.status.state.value
        if current_state in ("PENDING", "RUNNING"):
            time.sleep(1)
            continue
        if current_state != "SUCCEEDED":
            err = s.status.error
            raise RuntimeError(
                f"Statement failed: state={current_state} "
                f"code={getattr(err, 'error_code', 'UNKNOWN')} "
                f"message={getattr(err, 'message', 'Unknown error')}"
            )
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Run realtime synthetic data updates in a loop.")
    parser.add_argument("--warehouse-id", default=os.getenv("DATABRICKS_WAREHOUSE_ID"))
    parser.add_argument("--profile", default=os.getenv("DATABRICKS_CONFIG_PROFILE", "DEFAULT"))
    parser.add_argument("--catalog", default=os.getenv("DATABRICKS_CATALOG", "banking_cfo_treasury"))
    parser.add_argument("--schema-prefix", default=os.getenv("DATABRICKS_SCHEMA_PREFIX", "deposit_ppnr"))
    parser.add_argument("--interval-seconds", type=int, default=60)
    parser.add_argument("--ticks", type=int, default=0, help="0 means run forever")
    parser.add_argument("--sql-file", default=str(Path(__file__).parent / "50_realtime_tick.sql"))
    args = parser.parse_args()

    if not args.warehouse_id:
        raise SystemExit("Missing --warehouse-id (or set DATABRICKS_WAREHOUSE_ID).")
    if args.interval_seconds < 5:
        raise SystemExit("--interval-seconds must be >= 5 to avoid runaway load.")

    os.environ["DATABRICKS_CONFIG_PROFILE"] = args.profile
    tick_sql_path = Path(args.sql_file)
    if not tick_sql_path.exists():
        raise FileNotFoundError(f"Tick SQL file not found: {tick_sql_path}")

    tick_statements = _load_tick_statements(tick_sql_path, args.catalog, args.schema_prefix)
    if not tick_statements:
        raise RuntimeError(f"No executable statements found in {tick_sql_path}")

    client = WorkspaceClient()
    tick = 0

    print(
        f"Starting realtime generation loop "
        f"(profile={args.profile}, warehouse={args.warehouse_id}, catalog={args.catalog}, schema_prefix={args.schema_prefix}, interval={args.interval_seconds}s)"
    )
    try:
        while True:
            tick += 1
            print(f"\nTick #{tick} at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            for idx, statement in enumerate(tick_statements, 1):
                print(f"  - statement {idx}/{len(tick_statements)}")
                _exec_sql(client, args.warehouse_id, statement)

            if args.ticks > 0 and tick >= args.ticks:
                print("Requested tick count reached. Exiting.")
                return

            time.sleep(args.interval_seconds)
    except KeyboardInterrupt:
        print("\nStopped by user.")


if __name__ == "__main__":
    main()
