# Databricks notebook source
# MAGIC %md
# MAGIC # Approach 1: Deposit Beta Model (Static)
# MAGIC
# MAGIC **Objective:** Train a static deposit beta model for portfolio-level rate sensitivity.
# MAGIC
# MAGIC **Outputs**
# MAGIC - Training table: `cfo_banking_demo.ml_models.deposit_beta_training_data`
# MAGIC - Registered model: `cfo_banking_demo.models.deposit_beta_model@champion`

# COMMAND ----------

import mlflow
import pandas as pd
from pyspark.sql import functions as F

mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Build canonical training dataset
# MAGIC
# MAGIC This is the canonical feature set used by `Batch_Inference_Deposit_Beta_Model.py`.

# COMMAND ----------

# Latest yield curve snapshot (single row)
yield_curve_latest = (
    spark.table("cfo_banking_demo.silver_treasury.yield_curves")
    .filter(
        F.col("date")
        == spark.table("cfo_banking_demo.silver_treasury.yield_curves")
        .agg(F.max("date").alias("max_date"))
        .collect()[0]["max_date"]
    )
)

deposits = (
    spark.table("cfo_banking_demo.bronze_core_banking.deposit_accounts")
    .filter((F.col("is_current") == True) & F.col("beta").isNotNull())
)

base_df = deposits.crossJoin(yield_curve_latest)

training_df = (
    base_df.select(
        F.col("account_id"),
        F.col("customer_id"),
        F.col("product_type"),
        F.col("customer_segment"),
        F.col("account_open_date"),
        F.col("current_balance"),
        F.col("average_balance_30d"),
        F.col("stated_rate"),
        F.col("transaction_count_30d"),
        F.col("account_status"),
        F.col("effective_date"),
        # Encoded features
        F.when(F.col("product_type") == "DDA", 1)
        .when(F.col("product_type") == "Savings", 2)
        .when(F.col("product_type") == "NOW", 3)
        .when(F.col("product_type") == "MMDA", 4)
        .when(F.col("product_type") == "CD", 5)
        .otherwise(0)
        .alias("product_type_encoded"),
        F.when(F.col("customer_segment") == "Retail", 1)
        .when(F.col("customer_segment") == "Commercial", 2)
        .when(F.col("customer_segment") == "Institutional", 3)
        .otherwise(0)
        .alias("segment_encoded"),
        # Account features
        (F.datediff(F.current_date(), F.col("account_open_date")) / 30.0).alias("account_age_months"),
        # Churn flags
        F.when(F.col("account_status") == "Closed", 1).otherwise(0).alias("churned"),
        F.when(F.col("account_status") == "Dormant", 1).otherwise(0).alias("dormant"),
        # Volatility / gaps
        F.when(
            F.col("average_balance_30d").isNotNull() & (F.col("average_balance_30d") > 0),
            F.abs(F.col("current_balance") - F.col("average_balance_30d")) / F.col("average_balance_30d"),
        )
        .otherwise(0.0)
        .alias("balance_volatility_30d"),
        # Market rates
        F.coalesce(F.col("rate_2y"), F.lit(0.036)).alias("current_market_rate"),
        F.coalesce(F.col("rate_5y"), F.lit(0.038)).alias("market_rate_5y"),
        F.coalesce(F.col("rate_10y"), F.lit(0.043)).alias("market_rate_10y"),
        # Rate gap/spreads
        F.abs(F.col("stated_rate") - F.coalesce(F.col("rate_2y"), F.lit(0.036))).alias("rate_gap"),
        (F.col("stated_rate") - F.coalesce(F.col("rate_2y"), F.lit(0.036))).alias("rate_spread"),
        (
            (F.col("stated_rate") - F.coalesce(F.col("rate_2y"), F.lit(0.036)))
            * F.col("current_balance")
            / 1_000_000.0
        ).alias("rate_spread_x_balance"),
        # Balance transforms
        F.log(F.col("current_balance") + F.lit(1.0)).alias("log_balance"),
        (F.col("current_balance") / 1_000_000.0).alias("balance_millions"),
        F.when(
            F.col("average_balance_30d").isNotNull() & (F.col("average_balance_30d") > 0),
            (F.col("current_balance") - F.col("average_balance_30d")) / F.col("average_balance_30d"),
        )
        .otherwise(0.0)
        .alias("balance_trend_30d"),
        # Composite churn risk score (simple, interpretable)
        (
            F.when(F.col("account_status") == "Closed", 1).otherwise(0) * F.lit(0.4)
            + F.when(F.col("account_status") == "Dormant", 1).otherwise(0) * F.lit(0.3)
            + (F.abs(F.col("stated_rate") - F.coalesce(F.col("rate_2y"), F.lit(0.036))) * F.lit(10.0)) * F.lit(0.3)
        ).alias("churn_risk_score"),
        # Target
        F.col("beta").cast("double").alias("target_beta"),
    )
    .withColumn("dataset_timestamp", F.current_timestamp())
)

training_df.write.mode("overwrite").saveAsTable("cfo_banking_demo.ml_models.deposit_beta_training_data")
print(f"✓ Wrote training data: {training_df.count():,} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Train XGBoost model + register to Unity Catalog

# COMMAND ----------

import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import mlflow.xgboost

training_pdf = spark.table("cfo_banking_demo.ml_models.deposit_beta_training_data").toPandas()

feature_cols = [
    "product_type_encoded",
    "segment_encoded",
    "current_balance",
    "stated_rate",
    "account_age_months",
    "churned",
    "dormant",
    "balance_volatility_30d",
    "rate_gap",
    "churn_risk_score",
    "current_market_rate",
    "market_rate_5y",
    "market_rate_10y",
    "log_balance",
    "balance_millions",
    "balance_trend_30d",
    "rate_spread",
    "rate_spread_x_balance",
    "transaction_count_30d",
]

X = training_pdf[feature_cols].fillna(0).astype(float)
y = training_pdf["target_beta"].fillna(0).astype(float)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model_name = "cfo_banking_demo.models.deposit_beta_model"

with mlflow.start_run(run_name="approach1_deposit_beta_model") as run:
    params = {
        "max_depth": 6,
        "learning_rate": 0.1,
        "n_estimators": 100,
        "objective": "reg:squarederror",
        "random_state": 42,
    }

    model = xgb.XGBRegressor(**params)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    rmse = mean_squared_error(y_test, y_pred, squared=False)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    mlflow.log_params(params)
    mlflow.log_metric("rmse", float(rmse))
    mlflow.log_metric("mae", float(mae))
    mlflow.log_metric("r2", float(r2))
    mlflow.xgboost.log_model(model, "model", input_example=X_train.head(1))

    run_id = run.info.run_id

print(f"✓ Training complete. run_id={run_id}")

# Register and set @champion alias
from mlflow import MlflowClient

client = MlflowClient()
model_uri = f"runs:/{run_id}/model"

model_version = mlflow.register_model(model_uri=model_uri, name=model_name)
client.set_registered_model_alias(model_name, "champion", model_version.version)

print(f"✓ Model registered: {model_name}@champion (v{model_version.version})")

