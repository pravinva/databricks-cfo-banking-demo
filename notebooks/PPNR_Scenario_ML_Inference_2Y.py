# Databricks notebook source
# MAGIC %md
# MAGIC # PPNR Scenario Planning (ML-Driven NonII/NonIE) — 2Y Driver
# MAGIC
# MAGIC This notebook upgrades scenario planning from simple multipliers to **model-driven** projections for:
# MAGIC - **Non-Interest Income** (fee income) via `models:/cfo_banking_demo.models.non_interest_income_model@champion`
# MAGIC - **Non-Interest Expense** via `models:/cfo_banking_demo.models.non_interest_expense_model@champion`
# MAGIC
# MAGIC The macro driver is still the **2Y path** (`rate_2y_pct`) from:
# MAGIC - `cfo_banking_demo.gold_finance.ppnr_scenario_drivers_quarterly`
# MAGIC
# MAGIC And NII is sourced from the **full repricing engine** output:
# MAGIC - `cfo_banking_demo.gold_finance.nii_projection_quarterly`
# MAGIC
# MAGIC ## Outputs
# MAGIC - `cfo_banking_demo.gold_finance.ppnr_ml_projection_monthly`
# MAGIC - `cfo_banking_demo.gold_finance.ppnr_projection_quarterly_ml`

# COMMAND ----------

import math
import decimal
from datetime import date

import mlflow
import pandas as pd

# COMMAND ----------

CATALOG = "cfo_banking_demo"
SCHEMA = "gold_finance"

SCENARIO_DRIVERS = f"{CATALOG}.{SCHEMA}.ppnr_scenario_drivers_quarterly"
NII_QTR = f"{CATALOG}.{SCHEMA}.nii_projection_quarterly"

NII_TRAIN = f"{CATALOG}.ml_models.non_interest_income_training_data"
NIE_TRAIN = f"{CATALOG}.ml_models.non_interest_expense_training_data"

OUT_MONTHLY = f"{CATALOG}.{SCHEMA}.ppnr_ml_projection_monthly"
OUT_QTR = f"{CATALOG}.{SCHEMA}.ppnr_projection_quarterly_ml"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Preconditions

# COMMAND ----------

for req in [SCENARIO_DRIVERS, NII_QTR, NII_TRAIN, NIE_TRAIN]:
    if not spark.catalog.tableExists(req):
        raise RuntimeError(f"Missing required table: {req}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Load champion models from Unity Catalog (MLflow)

# COMMAND ----------

mlflow.set_registry_uri("databricks-uc")

nii_model = mlflow.xgboost.load_model(f"models:/{CATALOG}.models.non_interest_income_model@champion")
nie_model = mlflow.xgboost.load_model(f"models:/{CATALOG}.models.non_interest_expense_model@champion")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2b: Feature coercion helpers (avoid XGBoost dtype errors)

# COMMAND ----------

def _model_feature_names(model) -> list[str] | None:
    """
    Return feature names expected by the model, if available.

    We rely on these names to:
    - drop non-feature columns like timestamps
    - keep column ordering stable for XGBoost inference
    """
    names = None
    # sklearn API
    if hasattr(model, "feature_names_in_"):
        try:
            names = list(getattr(model, "feature_names_in_"))
        except Exception:
            names = None
    if names:
        return names
    # xgboost booster
    try:
        booster = model.get_booster()
        if booster is not None and booster.feature_names:
            return list(booster.feature_names)
    except Exception:
        pass
    return None


def _normalize_scalar(v):
    if isinstance(v, decimal.Decimal):
        return float(v)
    return v


def _coerce_numeric_frame(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert Decimal/object columns to numeric floats when possible.
    """
    out = df.copy()
    for c in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[c]):
            # datetime columns are not valid XGBoost inputs; caller should drop them via feature selection
            continue
        if out[c].dtype == "object":
            out[c] = out[c].map(_normalize_scalar)
            out[c] = pd.to_numeric(out[c], errors="coerce")
    return out


def _build_X(feat_dict: dict, model) -> pd.DataFrame:
    """
    Build a clean, numeric feature frame for the given model.
    - Select only model feature columns if available.
    - Coerce object/Decimal columns to float.
    - Fill NaNs with 0.
    """
    df = pd.DataFrame([{k: _normalize_scalar(v) for k, v in feat_dict.items()}])
    names = _model_feature_names(model)
    if names:
        # Ensure every expected feature exists.
        for n in names:
            if n not in df.columns:
                df[n] = 0.0
        df = df[names]
    else:
        # Fall back: drop obvious non-features and keep numeric-only.
        drop = {"month"}
        df = df.drop(columns=[c for c in drop if c in df.columns], errors="ignore")
        df = _coerce_numeric_frame(df)
        df = df.select_dtypes(include=["number", "bool"])

    df = _coerce_numeric_frame(df).fillna(0.0)
    return df

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Build a small future-month feature set per scenario
# MAGIC
# MAGIC MVP approach:
# MAGIC - Take the **latest training row** as the “portfolio state”
# MAGIC - Roll forward **27 months** (9 quarters), updating seasonality fields + scenario `avg_2y_rate`
# MAGIC - For lag features (`prior_month_*`), use the prior **predicted** value within each scenario path

# COMMAND ----------

drivers_pdf = (
    spark.table(SCENARIO_DRIVERS)
    .select("scenario_id", "quarter_start", "rate_2y_pct")
    .orderBy("scenario_id", "quarter_start")
    .toPandas()
)

if drivers_pdf.empty:
    raise RuntimeError(f"No rows in {SCENARIO_DRIVERS}. Run the scenario planning setup first.")

qtrs = sorted(drivers_pdf["quarter_start"].unique().tolist())
start_qtr = pd.to_datetime(min(qtrs)).date()
months = pd.date_range(start=pd.Timestamp(start_qtr), periods=27, freq="MS")  # month-start timestamps

nii_last = spark.table(NII_TRAIN).orderBy("month", ascending=False).limit(1).toPandas()
nie_last = spark.table(NIE_TRAIN).orderBy("month", ascending=False).limit(1).toPandas()
if nii_last.empty or nie_last.empty:
    raise RuntimeError("Training tables are empty; run Train_PPNR_Models.py first.")

nii_last_row = nii_last.iloc[0].to_dict()
nie_last_row = nie_last.iloc[0].to_dict()

def month_sin_cos(m: int) -> tuple[float, float]:
    # m: 1..12
    return (math.sin(2 * math.pi * m / 12.0), math.cos(2 * math.pi * m / 12.0))

def quarter_num(dt: pd.Timestamp) -> int:
    return int(((dt.month - 1) // 3) + 1)

def scenario_rate_for_month(scenario_id: str, month_ts: pd.Timestamp) -> float:
    qtr_start = pd.Timestamp(month_ts.to_period("Q").start_time).date()
    row = drivers_pdf[(drivers_pdf["scenario_id"] == scenario_id) & (drivers_pdf["quarter_start"] == qtr_start)]
    if row.empty:
        # If scenario drivers are only defined for a subset, fail fast (no silent fallback).
        raise RuntimeError(f"Missing driver for scenario_id={scenario_id}, quarter_start={qtr_start} in {SCENARIO_DRIVERS}")
    return float(row.iloc[0]["rate_2y_pct"])

scenario_ids = sorted(drivers_pdf["scenario_id"].unique().tolist())

rows_out: list[dict] = []

for scenario_id in scenario_ids:
    prior_fee_income = float(nii_last_row.get("prior_month_fee_income") or 0.0)
    prior_transactions = float(nii_last_row.get("prior_month_transactions") or 0.0)
    prior_expense = float(nie_last_row.get("prior_month_expense") or 0.0)
    prior_accounts = float(nie_last_row.get("prior_month_accounts") or 0.0)

    for m_ts in months:
        m = int(m_ts.month)
        sin_m, cos_m = month_sin_cos(m)
        q = quarter_num(m_ts)

        # Build Non-Interest Income features
        nii_feat = dict(nii_last_row)
        nii_feat["month"] = pd.Timestamp(m_ts).to_pydatetime()
        nii_feat["quarter"] = q
        nii_feat["month_sin"] = sin_m
        nii_feat["month_cos"] = cos_m
        nii_feat["avg_2y_rate"] = scenario_rate_for_month(scenario_id, m_ts)
        # Keep 10Y constant; update slope deterministically
        if "avg_10y_rate" in nii_feat and "yield_curve_slope" in nii_feat:
            try:
                nii_feat["yield_curve_slope"] = float(nii_feat["avg_10y_rate"]) - float(nii_feat["avg_2y_rate"])
            except Exception:
                pass
        nii_feat["prior_month_fee_income"] = prior_fee_income
        nii_feat["prior_month_transactions"] = prior_transactions

        # Drop target column if present
        nii_feat.pop("target_fee_income", None)

        # Build Non-Interest Expense features
        nie_feat = dict(nie_last_row)
        nie_feat["month"] = pd.Timestamp(m_ts).to_pydatetime()
        nie_feat["quarter"] = q
        nie_feat["month_sin"] = sin_m
        nie_feat["month_cos"] = cos_m
        nie_feat["prior_month_expense"] = prior_expense
        nie_feat["prior_month_accounts"] = prior_accounts
        nie_feat.pop("target_operating_expense", None)

        # Predict
        nii_X = _build_X(nii_feat, nii_model)
        nie_X = _build_X(nie_feat, nie_model)
        nii_pred = float(nii_model.predict(nii_X)[0])
        nie_pred = float(nie_model.predict(nie_X)[0])

        rows_out.append(
            {
                "scenario_id": scenario_id,
                "month": m_ts.date(),
                "rate_2y_pct": float(nii_feat["avg_2y_rate"]),
                "predicted_non_interest_income_usd": nii_pred,
                "predicted_non_interest_expense_usd": nie_pred,
            }
        )

        prior_fee_income = nii_pred
        prior_expense = nie_pred
        # keep accounts/transactions constant (can be upgraded later)

ml_monthly_pdf = pd.DataFrame(rows_out)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Write results to Unity Catalog

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")

spark.sql(f"""
CREATE OR REPLACE TABLE {OUT_MONTHLY} (
  scenario_id STRING,
  month DATE,
  rate_2y_pct DOUBLE,
  predicted_non_interest_income_usd DOUBLE,
  predicted_non_interest_expense_usd DOUBLE
)
USING DELTA
""")

spark_df = spark.createDataFrame(ml_monthly_pdf)
spark_df.write.mode("overwrite").saveAsTable(OUT_MONTHLY)

spark.sql(f"""
CREATE OR REPLACE TABLE {OUT_QTR} (
  scenario_id STRING,
  quarter_start DATE,
  rate_2y_pct DOUBLE,
  rate_2y_delta_bps DOUBLE,
  nii_usd DOUBLE,
  non_interest_income_usd DOUBLE,
  non_interest_expense_usd DOUBLE,
  ppnr_usd DOUBLE,
  delta_ppnr_usd DOUBLE
)
USING DELTA
""")

spark.sql(f"TRUNCATE TABLE {OUT_QTR}")

spark.sql(f"""
WITH ml_qtr AS (
  SELECT
    scenario_id,
    DATE_TRUNC('quarter', month) AS quarter_start,
    MAX(rate_2y_pct) AS rate_2y_pct,
    SUM(predicted_non_interest_income_usd) AS non_interest_income_usd,
    SUM(predicted_non_interest_expense_usd) AS non_interest_expense_usd
  FROM {OUT_MONTHLY}
  GROUP BY scenario_id, DATE_TRUNC('quarter', month)
),
nii_qtr AS (
  SELECT
    scenario_id,
    quarter_start,
    MAX(rate_2y_pct) AS rate_2y_pct,
    MAX(rate_2y_delta_bps) AS rate_2y_delta_bps,
    MAX(nii_usd) AS nii_usd
  FROM {NII_QTR}
  GROUP BY scenario_id, quarter_start
),
base AS (
  SELECT
    quarter_start,
    MAX(ppnr) AS baseline_ppnr_usd
  FROM (
    SELECT
      q.quarter_start,
      (q.nii_usd + q.non_interest_income_usd - q.non_interest_expense_usd) AS ppnr
    FROM (
      SELECT
        n.quarter_start,
        n.nii_usd,
        m.non_interest_income_usd,
        m.non_interest_expense_usd
      FROM nii_qtr n
      JOIN ml_qtr m
        ON n.scenario_id = m.scenario_id
       AND n.quarter_start = m.quarter_start
      WHERE n.scenario_id = 'baseline'
    ) q
  ) x
  GROUP BY quarter_start
)
INSERT INTO {OUT_QTR}
SELECT
  n.scenario_id,
  n.quarter_start,
  n.rate_2y_pct,
  n.rate_2y_delta_bps,
  n.nii_usd,
  m.non_interest_income_usd,
  m.non_interest_expense_usd,
  (n.nii_usd + m.non_interest_income_usd - m.non_interest_expense_usd) AS ppnr_usd,
  (
    (n.nii_usd + m.non_interest_income_usd - m.non_interest_expense_usd)
    - b.baseline_ppnr_usd
  ) AS delta_ppnr_usd
FROM nii_qtr n
JOIN ml_qtr m
  ON n.scenario_id = m.scenario_id
 AND n.quarter_start = m.quarter_start
JOIN base b
  ON n.quarter_start = b.quarter_start
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Sanity checks

# COMMAND ----------

display(spark.sql(f"""
SELECT scenario_id, COUNT(*) quarters, MIN(quarter_start) min_qtr, MAX(quarter_start) max_qtr
FROM {OUT_QTR}
GROUP BY scenario_id
ORDER BY scenario_id
"""))

display(spark.sql(f"""
SELECT quarter_start, scenario_id, rate_2y_delta_bps, ppnr_usd, delta_ppnr_usd
FROM {OUT_QTR}
ORDER BY quarter_start, scenario_id
LIMIT 60
"""))

