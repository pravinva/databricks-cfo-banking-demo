# Databricks notebook source
# MAGIC %md
# MAGIC # CFO Data Generation - Realtime Tick
# MAGIC Executes one synthetic realtime update tick.

# COMMAND ----------

from databricks.sdk import WorkspaceClient
import re
import time

dbutils.widgets.text("warehouse_id", "192fe959f141d27c")
dbutils.widgets.text("catalog", "banking_cfo_treasury")
dbutils.widgets.text("schema_prefix", "deposit_ppnr")
dbutils.widgets.text("sql_file_path", "dbfs:/FileStore/cfo-data-generation/sql/50_realtime_tick.sql")

warehouse_id = dbutils.widgets.get("warehouse_id")
catalog = dbutils.widgets.get("catalog")
schema_prefix = dbutils.widgets.get("schema_prefix")
sql_file_path = dbutils.widgets.get("sql_file_path")


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


def wait_execute_sql(client: WorkspaceClient, sql_warehouse_id: str, statement: str, timeout_s: int = 300) -> None:
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


rows = spark.read.text(sql_file_path).collect()
sql_text = "\n".join(r.value for r in rows)
sql_text = rewrite_catalog_references(sql_text, catalog, schema_prefix)
statements = split_sql_statements(sql_text)
if not statements:
    raise RuntimeError(f"No statements found in {sql_file_path}")

client = WorkspaceClient()
print(f"Target catalog: {catalog}")
print(f"Schema prefix: {schema_prefix}")
print(f"Warehouse: {warehouse_id}")
print(f"Tick statements: {len(statements)}")

for idx, statement in enumerate(statements, start=1):
    print(f"[{idx}/{len(statements)}] Executing")
    wait_execute_sql(client, warehouse_id, statement)

print("Realtime tick complete.")
