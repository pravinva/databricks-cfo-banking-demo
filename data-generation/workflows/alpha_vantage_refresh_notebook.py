# Databricks notebook source
# MAGIC %md
# MAGIC # CFO Data Generation - AlphaVantage Refresh
# MAGIC Refreshes treasury curve data from AlphaVantage into workstream-prefixed silver treasury table.

# COMMAND ----------

import time
import requests
import csv
import io
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import sql as dbsql

dbutils.widgets.text("warehouse_id", "AUTO")
dbutils.widgets.text("catalog", "banking_cfo_treasury")
dbutils.widgets.text("schema_prefix", "deposit_ppnr")
dbutils.widgets.text("start_date", "2024-01-01")
dbutils.widgets.text("secret_scope", "cfo_demo")
dbutils.widgets.text("secret_key", "alpha_vantage_api_key")


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
print(f"Using SQL warehouse_id={warehouse_id}")
catalog = dbutils.widgets.get("catalog")
schema_prefix = dbutils.widgets.get("schema_prefix").strip().strip("_")
start_date = dbutils.widgets.get("start_date")
secret_scope = dbutils.widgets.get("secret_scope")
secret_key = dbutils.widgets.get("secret_key")

if not schema_prefix:
    raise ValueError("schema_prefix must not be empty")

target_schema = f"{schema_prefix}_silver_treasury"
target_table = f"{catalog}.{target_schema}.yield_curves"

api_key = dbutils.secrets.get(secret_scope, secret_key)
if not api_key:
    raise RuntimeError(f"Secret {secret_scope}/{secret_key} is empty")


def fetch_json(params):
    response = requests.get("https://www.alphavantage.co/query", params=params, timeout=45)
    response.raise_for_status()
    payload = response.json()
    if "Note" in payload:
        raise RuntimeError(f"AlphaVantage rate-limit note: {payload['Note']}")
    if "Error Message" in payload:
        raise RuntimeError(f"AlphaVantage error: {payload['Error Message']}")
    return payload


def _to_float(v):
    try:
        return float(v)
    except Exception:
        return None


def fetch_treasury_csv_rows(start_date_str: str):
    # Public U.S. Treasury daily rates CSV fallback (no API key required).
    year = int(start_date_str[:4])
    current_year = int(time.strftime("%Y"))
    out = {}

    for y in range(year, current_year + 1):
        url = (
            "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
            f"daily-treasury-rates.csv/{y}/all?type=daily_treasury_yield_curve"
        )
        response = requests.get(url, timeout=45)
        response.raise_for_status()
        reader = csv.DictReader(io.StringIO(response.text))
        for row in reader:
            dt_raw = row.get("Date")
            if not dt_raw:
                continue
            try:
                mm, dd, yyyy = dt_raw.split("/")
                dt = f"{yyyy}-{int(mm):02d}-{int(dd):02d}"
            except Exception:
                continue
            if dt < start_date_str:
                continue

            def _dec(col):
                v = (row.get(col) or "").strip()
                if not v:
                    return None
                parsed = _to_float(v)
                return None if parsed is None else (parsed / 100.0)

            vals = {
                "rate_3m": _dec("3 Mo"),
                "rate_2y": _dec("2 Yr"),
                "rate_5y": _dec("5 Yr"),
                "rate_10y": _dec("10 Yr"),
                "rate_30y": _dec("30 Yr"),
            }
            if any(vals.get(c) is not None for c in ["rate_3m", "rate_2y", "rate_5y", "rate_10y", "rate_30y"]):
                out.setdefault(dt, {}).update(vals)
    return out


# Build in-memory date-keyed records
rows_by_date = {}

try:
    fed = fetch_json({"function": "FEDERAL_FUNDS_RATE", "apikey": api_key}).get("data", [])
    for row in fed:
        dt = row.get("date")
        if not dt or dt < start_date:
            continue
        rows_by_date.setdefault(dt, {})["fed_funds_rate"] = _to_float(row.get("value"))
except Exception as e:
    print(f"FED funds fetch warning (continuing): {e}")

maturities = [
    ("3month", "rate_3m"),
    ("2year", "rate_2y"),
    ("5year", "rate_5y"),
    ("10year", "rate_10y"),
    ("30year", "rate_30y"),
]
treasury_loaded = False
try:
    for idx, (maturity, col_name) in enumerate(maturities):
        payload = fetch_json(
            {
                "function": "TREASURY_YIELD",
                "interval": "daily",
                "maturity": maturity,
                "apikey": api_key,
            }
        )
        for row in payload.get("data", []):
            dt = row.get("date")
            value = row.get("value")
            if not dt or dt < start_date or value in (None, "."):
                continue
            parsed = _to_float(value)
            if parsed is None:
                continue
            rows_by_date.setdefault(dt, {})[col_name] = parsed

        # Free-tier pacing: max 5 calls/minute
        if idx < len(maturities) - 1:
            time.sleep(12)
    treasury_loaded = True
except Exception as e:
    print(f"Treasury fetch via AlphaVantage warning: {e}")
    print("Falling back to U.S. Treasury CSV source for curve tenors.")
    csv_rows = fetch_treasury_csv_rows(start_date)
    for dt, vals in csv_rows.items():
        rows_by_date.setdefault(dt, {}).update(vals)
    treasury_loaded = True

curve_cols = ["rate_3m", "rate_2y", "rate_5y", "rate_10y", "rate_30y"]
dates = sorted([d for d, vals in rows_by_date.items() if any(vals.get(c) is not None for c in curve_cols)])
if not dates:
    raise RuntimeError("No treasury rows fetched from AlphaVantage")


def to_sql_number(v):
    return "NULL" if v is None else str(v)


values_sql = []
for dt in dates:
    vals = rows_by_date[dt]
    values_sql.append(
        "("
        + ", ".join(
            [
                f"'{dt}'",
                to_sql_number(vals.get("fed_funds_rate")),
                to_sql_number(vals.get("rate_3m")),
                to_sql_number(vals.get("rate_2y")),
                to_sql_number(vals.get("rate_5y")),
                to_sql_number(vals.get("rate_10y")),
                to_sql_number(vals.get("rate_30y")),
            ]
        )
        + ")"
    )

w = WorkspaceClient()


def exec_sql(statement: str, timeout: str = "20s"):
    response = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=statement,
        wait_timeout=timeout,
    )
    state = response.status.state
    if state in (dbsql.StatementState.PENDING, dbsql.StatementState.RUNNING):
        statement_id = response.statement_id
        while True:
            s = w.statement_execution.get_statement(statement_id)
            if s.status.state in (dbsql.StatementState.PENDING, dbsql.StatementState.RUNNING):
                time.sleep(1)
                continue
            if s.status.state != dbsql.StatementState.SUCCEEDED:
                raise RuntimeError(getattr(s.status.error, "message", "SQL failed"))
            return s
    if state != dbsql.StatementState.SUCCEEDED:
        raise RuntimeError(getattr(response.status.error, "message", "SQL failed"))
    return response


# Ensure target schema/table/columns exist
exec_sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{target_schema}")
exec_sql(
    f"""
CREATE TABLE IF NOT EXISTS {target_table} (
  date DATE,
  rate_3m DOUBLE,
  rate_2y DOUBLE,
  rate_5y DOUBLE,
  rate_10y DOUBLE,
  rate_30y DOUBLE,
  fed_funds_rate DOUBLE
)
"""
)

for col in ["fed_funds_rate"]:
    col_exists_stmt = f"""
SELECT COUNT(*)
FROM {catalog}.information_schema.columns
WHERE table_schema = '{target_schema}'
  AND table_name = 'yield_curves'
  AND column_name = '{col}'
"""
    col_exists = int((exec_sql(col_exists_stmt).result.data_array or [[0]])[0][0]) > 0
    if not col_exists:
        exec_sql(f"ALTER TABLE {target_table} ADD COLUMNS ({col} DOUBLE)")


chunk_size = 700
for i in range(0, len(values_sql), chunk_size):
    block = ",\n".join(values_sql[i : i + chunk_size])
    merge_stmt = f"""
MERGE INTO {target_table} AS target
USING (
  SELECT * FROM VALUES
  {block}
  AS tmp(date, fed_funds_rate, rate_3m, rate_2y, rate_5y, rate_10y, rate_30y)
) AS source
ON target.date = source.date
WHEN MATCHED THEN UPDATE SET
  target.fed_funds_rate = CASE WHEN source.fed_funds_rate > 1 THEN source.fed_funds_rate / 100.0 ELSE source.fed_funds_rate END,
  target.rate_3m = COALESCE(CASE WHEN source.rate_3m > 1 THEN source.rate_3m / 100.0 ELSE source.rate_3m END, target.rate_3m),
  target.rate_2y = COALESCE(CASE WHEN source.rate_2y > 1 THEN source.rate_2y / 100.0 ELSE source.rate_2y END, target.rate_2y),
  target.rate_5y = COALESCE(CASE WHEN source.rate_5y > 1 THEN source.rate_5y / 100.0 ELSE source.rate_5y END, target.rate_5y),
  target.rate_10y = COALESCE(CASE WHEN source.rate_10y > 1 THEN source.rate_10y / 100.0 ELSE source.rate_10y END, target.rate_10y),
  target.rate_30y = COALESCE(CASE WHEN source.rate_30y > 1 THEN source.rate_30y / 100.0 ELSE source.rate_30y END, target.rate_30y)
WHEN NOT MATCHED THEN INSERT (date, fed_funds_rate, rate_3m, rate_2y, rate_5y, rate_10y, rate_30y)
VALUES (
  source.date,
  CASE WHEN source.fed_funds_rate > 1 THEN source.fed_funds_rate / 100.0 ELSE source.fed_funds_rate END,
  CASE WHEN source.rate_3m > 1 THEN source.rate_3m / 100.0 ELSE source.rate_3m END,
  CASE WHEN source.rate_2y > 1 THEN source.rate_2y / 100.0 ELSE source.rate_2y END,
  CASE WHEN source.rate_5y > 1 THEN source.rate_5y / 100.0 ELSE source.rate_5y END,
  CASE WHEN source.rate_10y > 1 THEN source.rate_10y / 100.0 ELSE source.rate_10y END,
  CASE WHEN source.rate_30y > 1 THEN source.rate_30y / 100.0 ELSE source.rate_30y END
)
"""
    exec_sql(merge_stmt)

summary_stmt = f"SELECT MIN(date), MAX(date), COUNT(*), COUNT(fed_funds_rate) FROM {target_table}"
latest_stmt = f"SELECT date, fed_funds_rate, rate_3m, rate_2y, rate_10y, rate_30y FROM {target_table} ORDER BY date DESC LIMIT 5"

summary = (exec_sql(summary_stmt).result.data_array or [[None, None, None, None]])[0]
latest_rows = exec_sql(latest_stmt).result.data_array or []

print(f"Target table: {target_table}")
print(f"Source rows loaded: {len(values_sql)}")
print(f"Date range: {summary[0]} -> {summary[1]}")
print(f"Total rows: {summary[2]}, rows with fed funds: {summary[3]}")
print("Latest rows:")
for row in latest_rows:
    print("\t".join(str(x) for x in row))
