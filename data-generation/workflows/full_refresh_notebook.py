# Databricks notebook source
# MAGIC %md
# MAGIC # CFO Data Generation - Full Refresh
# MAGIC Rebuilds all synthetic demo tables from SQL assets.

# COMMAND ----------

from databricks.sdk import WorkspaceClient
import re
import time

dbutils.widgets.text("warehouse_id", "AUTO")
dbutils.widgets.text("catalog", "banking_cfo_treasury")
dbutils.widgets.text("schema_prefix", "deposit_ppnr")
dbutils.widgets.text("sql_base_path", "dbfs:/FileStore/cfo-data-generation/sql")


def _resolve_sql_warehouse(raw: str) -> str:
    """Use widget value, or first existing warehouse among FINS-Apps then Serverless Starter."""
    raw = (raw or "").strip()
    if raw.upper() != "AUTO":
        return raw
    candidates = (
        "d5080ca821238922",  # FINS-Apps (fevm-fins-demo)
        "05dad35197134270",  # Serverless Starter Warehouse
    )
    ws = WorkspaceClient()
    for wid in candidates:
        try:
            ws.warehouses.get(wid)
            return wid
        except Exception:
            continue
    raise RuntimeError(
        "Could not resolve SQL warehouse: set warehouse_id explicitly or ensure "
        "FINS-Apps or Serverless Starter Warehouse exists in this workspace."
    )


warehouse_id = _resolve_sql_warehouse(dbutils.widgets.get("warehouse_id"))
catalog = dbutils.widgets.get("catalog")
schema_prefix = dbutils.widgets.get("schema_prefix")
sql_base_path = dbutils.widgets.get("sql_base_path").rstrip("/")

SCRIPT_ORDER = [
    "00_create_schemas.sql",
    "10_seed_core_banking.sql",
    "20_seed_finance_ledgers.sql",
    "30_seed_treasury_and_models.sql",
    "40_genie_compatibility_assets.sql",
]


def schema_map(prefix: str) -> dict[str, str]:
    clean_prefix = prefix.strip().strip("_")
    if not clean_prefix:
        raise ValueError("schema_prefix must not be empty")
    return {
        "bronze_core_banking": f"{clean_prefix}_bronze_core_banking",
        "silver_finance": f"{clean_prefix}_silver_finance",
        "silver_treasury": f"{clean_prefix}_silver_treasury",
        "ml_models": f"{clean_prefix}_ml_models",
        "gold_finance": f"{clean_prefix}_gold_finance",
        "gold_regulatory": f"{clean_prefix}_gold_regulatory",
    }


def rewrite_catalog_references(sql_text: str, target_catalog: str, prefix: str) -> str:
    text = sql_text.replace("cfo_banking_demo.", f"{target_catalog}.")
    text = text.replace("USE CATALOG cfo_banking_demo", f"USE CATALOG {target_catalog}")
    for schema, prefixed_schema in schema_map(prefix).items():
        text = text.replace(f".{schema}.", f".{prefixed_schema}.")
        text = re.sub(
            rf"(?<![\w\.]){schema}\.",
            f"{target_catalog}.{prefixed_schema}.",
            text,
        )
        text = re.sub(
            rf"CREATE\s+SCHEMA\s+IF\s+NOT\s+EXISTS\s+{schema}\b",
            f"CREATE SCHEMA IF NOT EXISTS {target_catalog}.{prefixed_schema}",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(
            rf"USE\s+SCHEMA\s+{schema}\b",
            f"USE SCHEMA {target_catalog}.{prefixed_schema}",
            text,
            flags=re.IGNORECASE,
        )
    return text


def split_sql_statements(sql_text: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    for line in sql_text.splitlines():
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


def wait_execute_sql(client: WorkspaceClient, sql_warehouse_id: str, statement: str, timeout_s: int = 900) -> None:
    resp = client.statement_execution.execute_statement(
        warehouse_id=sql_warehouse_id,
        statement=statement,
        wait_timeout="5s",
    )
    statement_id = resp.statement_id
    started = time.time()
    while True:
        state_obj = client.statement_execution.get_statement(statement_id)
        state = state_obj.status.state.value
        if state in ("PENDING", "RUNNING"):
            if time.time() - started > timeout_s:
                raise TimeoutError(f"Timed out waiting for statement {statement_id}")
            time.sleep(1)
            continue
        if state != "SUCCEEDED":
            err = state_obj.status.error
            raise RuntimeError(
                f"SQL failed: state={state} "
                f"code={getattr(err, 'error_code', 'UNKNOWN')} "
                f"message={getattr(err, 'message', 'Unknown error')}"
            )
        return


def assert_ppnr_income_ratio_guard(
    client: WorkspaceClient,
    sql_warehouse_id: str,
    target_catalog: str,
    prefix: str,
) -> None:
    schema = schema_map(prefix)["ml_models"]
    query = f"""
    SELECT
      MIN(non_interest_income / NULLIF(net_interest_income, 0.0)) AS min_ratio,
      MAX(non_interest_income / NULLIF(net_interest_income, 0.0)) AS max_ratio,
      AVG(non_interest_income / NULLIF(net_interest_income, 0.0)) AS avg_ratio
    FROM {target_catalog}.{schema}.ppnr_forecasts
    WHERE scenario = 'baseline'
      AND net_interest_income IS NOT NULL
      AND non_interest_income IS NOT NULL
    """
    resp = client.api_client.do(
        "POST",
        "/api/2.0/sql/statements",
        body={
            "statement": query,
            "warehouse_id": sql_warehouse_id,
            "wait_timeout": "30s",
        },
    )
    result = ((resp.get("result") or {}).get("data_array")) or []
    if not result:
        raise RuntimeError("QA guard failed: no baseline PPNR rows found.")

    min_ratio, max_ratio, avg_ratio = result[0]
    if min_ratio is None or max_ratio is None:
        raise RuntimeError("QA guard failed: unable to compute non-interest income ratio.")

    min_v = float(min_ratio)
    max_v = float(max_ratio)
    avg_v = float(avg_ratio)
    if min_v < 0.08 or max_v > 0.12:
        raise RuntimeError(
            "QA guard failed: non_interest_income/net_interest_income ratio is out of range "
            f"(min={min_v:.4f}, max={max_v:.4f}, avg={avg_v:.4f}; expected within [0.08, 0.12])."
        )

    print(
        "QA guard passed: non_interest_income/net_interest_income baseline ratio "
        f"within [0.08, 0.12] (min={min_v:.4f}, max={max_v:.4f}, avg={avg_v:.4f})."
    )


client = WorkspaceClient()
statement_queue: list[tuple[str, str]] = []

for script_name in SCRIPT_ORDER:
    path = f"{sql_base_path}/{script_name}"
    rows = spark.read.text(path).collect()
    sql_text = "\n".join(r.value for r in rows)
    sql_text = rewrite_catalog_references(sql_text, catalog, schema_prefix)
    statements = split_sql_statements(sql_text)
    if not statements:
        raise RuntimeError(f"No statements found in {path}")
    statement_queue.extend((script_name, s) for s in statements)

print(f"Target catalog: {catalog}")
print(f"Schema prefix: {schema_prefix}")
print(f"Warehouse: {warehouse_id}")
print(f"Statements to execute: {len(statement_queue)}")

for idx, (script_name, statement) in enumerate(statement_queue, start=1):
    print(f"[{idx}/{len(statement_queue)}] {script_name}")
    wait_execute_sql(client, warehouse_id, statement)

assert_ppnr_income_ratio_guard(client, warehouse_id, catalog, schema_prefix)

print("Full refresh complete.")
