#!/usr/bin/env python3
"""
Execute data generation SQL scripts in sequence.
"""

from __future__ import annotations

import argparse
import os
import re
import time
from pathlib import Path
from typing import List

from databricks.sdk import WorkspaceClient


DEFAULT_SCRIPT_ORDER = [
    "00_create_schemas.sql",
    "10_seed_core_banking.sql",
    "20_seed_finance_ledgers.sql",
    "30_seed_treasury_and_models.sql",
    "40_genie_compatibility_assets.sql",
]


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
            rf"CREATE\s+SCHEMA\s+IF\s+NOT\s+EXISTS\s+{schema}\b",
            f"CREATE SCHEMA IF NOT EXISTS {catalog}.{prefixed_schema}",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(
            rf"USE\s+SCHEMA\s+{schema}\b",
            f"USE SCHEMA {catalog}.{prefixed_schema}",
            text,
            flags=re.IGNORECASE,
        )
    return text


def _split_sql_statements(sql_text: str) -> List[str]:
    statements: List[str] = []
    current: List[str] = []
    for line in sql_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        current.append(line)
        if stripped.endswith(";"):
            stmt = "\n".join(current).strip().rstrip(";").strip()
            if stmt:
                statements.append(stmt)
            current = []
    trailing = "\n".join(current).strip()
    if trailing:
        statements.append(trailing)
    return [s for s in statements if s]


def _execute_statement(
    client: WorkspaceClient, warehouse_id: str, statement: str, timeout_s: int
) -> None:
    resp = client.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=statement,
        wait_timeout="5s",
    )
    statement_id = resp.statement_id
    start = time.time()

    while True:
        state_obj = client.statement_execution.get_statement(statement_id)
        state = state_obj.status.state.value
        if state in ("PENDING", "RUNNING"):
            if time.time() - start > timeout_s:
                raise TimeoutError(f"Timed out waiting for statement {statement_id}")
            time.sleep(1)
            continue
        if state != "SUCCEEDED":
            err = state_obj.status.error
            raise RuntimeError(
                f"Statement failed [{state}] code={getattr(err, 'error_code', 'UNKNOWN')} "
                f"message={getattr(err, 'message', 'Unknown error')}"
            )
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Run all on-demand data generation SQL scripts.")
    parser.add_argument("--warehouse-id", default=os.getenv("DATABRICKS_WAREHOUSE_ID"), required=False)
    parser.add_argument("--profile", default=os.getenv("DATABRICKS_CONFIG_PROFILE", "DEFAULT"))
    parser.add_argument("--catalog", default=os.getenv("DATABRICKS_CATALOG", "banking_cfo_treasury"))
    parser.add_argument("--schema-prefix", default=os.getenv("DATABRICKS_SCHEMA_PREFIX", "deposit_ppnr"))
    parser.add_argument("--sql-dir", default=str(Path(__file__).parent))
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.warehouse_id:
        raise SystemExit("Missing --warehouse-id (or set DATABRICKS_WAREHOUSE_ID).")

    os.environ["DATABRICKS_CONFIG_PROFILE"] = args.profile
    sql_dir = Path(args.sql_dir)

    for script_name in DEFAULT_SCRIPT_ORDER:
        script_path = sql_dir / script_name
        if not script_path.exists():
            raise FileNotFoundError(f"Missing SQL script: {script_path}")

    statements = []
    for script_name in DEFAULT_SCRIPT_ORDER:
        script_path = sql_dir / script_name
        sql_text = script_path.read_text(encoding="utf-8")
        sql_text = _rewrite_catalog_references(sql_text, args.catalog, args.schema_prefix)
        script_statements = _split_sql_statements(sql_text)
        if not script_statements:
            raise RuntimeError(f"No executable SQL statements found in {script_path}")
        statements.extend((script_name, s) for s in script_statements)

    if args.dry_run:
        print(f"Dry run: {len(statements)} statements across {len(DEFAULT_SCRIPT_ORDER)} files.")
        for i, (script_name, stmt) in enumerate(statements, 1):
            first_line = stmt.splitlines()[0][:120]
            print(f"[{i:03d}] {script_name} :: {first_line}")
        return

    client = WorkspaceClient()
    total = len(statements)
    print(f"Target catalog: {args.catalog}")
    print(f"Schema prefix: {args.schema_prefix}")
    for i, (script_name, statement) in enumerate(statements, 1):
        print(f"[{i}/{total}] {script_name}")
        _execute_statement(client, args.warehouse_id, statement, args.timeout_seconds)

    print("Done. Full data generation completed.")


if __name__ == "__main__":
    main()
