# Databricks notebook source
# MAGIC %md
# MAGIC # Deposit Beta Model - Batch Inference
# MAGIC
# MAGIC This notebook demonstrates **batch inference** for the deposit beta model using the registered model from Unity Catalog.
# MAGIC
# MAGIC **Why Batch Inference (Not Real-Time Endpoint)?**
# MAGIC - Deposit beta models are used for strategic ALM planning, not real-time transactions
# MAGIC - Updated periodically (weekly/monthly) based on portfolio changes
# MAGIC - Batch inference is more cost-effective for large-scale scoring
# MAGIC - No need for 24/7 serving infrastructure
# MAGIC
# MAGIC **Workflow:**
# MAGIC 1. Load the registered model from Unity Catalog
# MAGIC 2. Load current deposit portfolio data
# MAGIC 3. Score all accounts in parallel using Spark
# MAGIC 4. Validate predictions against expected ranges
# MAGIC 5. Write results to Delta table for downstream consumption

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Load Model from Unity Catalog

# COMMAND ----------

import mlflow
import pandas as pd
from pyspark.sql import functions as F
from datetime import datetime

# Set MLflow registry URI to Unity Catalog
mlflow.set_registry_uri("databricks-uc")

# Load the champion model
model_name = "cfo_banking_demo.models.deposit_beta_model"
model_alias = "champion"

print(f"Loading model: {model_name}@{model_alias}")

# Load as Spark UDF for distributed scoring
model_uri = f"models:/{model_name}@{model_alias}"
predict_udf = mlflow.pyfunc.spark_udf(spark, model_uri=model_uri, result_type="double")

print(f"✓ Model loaded successfully")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Prepare Input Features
# MAGIC
# MAGIC Load current deposit portfolio and create the same features used during training

# COMMAND ----------

# Canonical scoring source: current deposit accounts (matches Approach 1 training feature engineering)
deposit_df = (
    spark.table("cfo_banking_demo.bronze_core_banking.deposit_accounts")
    .filter((F.col("is_current") == True) & (F.col("account_status") == "Active"))
)

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

scoring_df = deposit_df.crossJoin(yield_curve_latest)

# Create features (aligned to Approach 1 canonical feature set)
feature_df = (
    scoring_df.select(
        F.col("account_id"),
        F.col("product_type"),
        F.col("customer_segment"),
        F.col("account_open_date"),
        F.col("current_balance"),
        F.col("average_balance_30d"),
        F.col("stated_rate"),
        F.col("transaction_count_30d"),
        F.col("account_status"),
        F.col("beta").alias("actual_beta"),  # if available, used for validation only
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
        # Churn flags (batch scoring should produce interpretable risk flags even if churn is rare)
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
    )
)

print(f"✓ Prepared {feature_df.count():,} accounts for scoring")
print(f"\nFeature columns:")
for col in feature_df.columns:
    print(f"  - {col}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Score All Accounts (Batch Inference)

# COMMAND ----------

# Define feature columns for model input
model_features = [
    'product_type_encoded', 'segment_encoded', 'current_balance', 'stated_rate',
    'account_age_months', 'churned', 'dormant', 'balance_volatility_30d',
    'rate_gap', 'churn_risk_score', 'current_market_rate', 'market_rate_5y',
    'market_rate_10y', 'log_balance', 'balance_millions', 'balance_trend_30d',
    'rate_spread', 'rate_spread_x_balance', 'transaction_count_30d'
]

# Create struct for model input
from pyspark.sql.functions import struct

predictions_df = feature_df.withColumn(
    "predicted_beta",
    predict_udf(struct(*model_features))
).withColumn(
    "prediction_timestamp",
    F.current_timestamp()
).withColumn(
    "model_version",
    F.lit(model_alias)
)

print(f"✓ Scored {predictions_df.count():,} accounts")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Validate Predictions
# MAGIC
# MAGIC **Validation checks:**
# MAGIC 1. Beta values in expected range [0, 1.5]
# MAGIC 2. No null predictions
# MAGIC 3. Distribution aligns with product types
# MAGIC 4. Compare with actual beta if available

# COMMAND ----------

# Validation metrics
validation_results = predictions_df.select(
    F.count("*").alias("total_accounts"),
    F.count(F.when(F.col("predicted_beta").isNull(), 1)).alias("null_predictions"),
    F.count(F.when(F.col("predicted_beta") < 0, 1)).alias("negative_betas"),
    F.count(F.when(F.col("predicted_beta") > 1.5, 1)).alias("betas_above_1_5"),
    F.min("predicted_beta").alias("min_beta"),
    F.max("predicted_beta").alias("max_beta"),
    F.avg("predicted_beta").alias("avg_beta"),
    F.stddev("predicted_beta").alias("stddev_beta")
).collect()[0]

print("=" * 80)
print("PREDICTION VALIDATION RESULTS")
print("=" * 80)
print(f"Total accounts scored: {validation_results['total_accounts']:,}")
print(f"Null predictions: {validation_results['null_predictions']:,}")
print(f"Negative betas: {validation_results['negative_betas']:,}")
print(f"Betas > 1.5: {validation_results['betas_above_1_5']:,}")
print(f"\nBeta Distribution:")
print(f"  Min: {validation_results['min_beta']:.4f}")
print(f"  Max: {validation_results['max_beta']:.4f}")
print(f"  Avg: {validation_results['avg_beta']:.4f}")
print(f"  StdDev: {validation_results['stddev_beta']:.4f}")
print("=" * 80)

# Validation by product type
print("\nPredicted Beta by Product Type:")
predictions_df.groupBy("product_type") \
    .agg(
        F.count("*").alias("count"),
        F.avg("predicted_beta").alias("avg_beta"),
        F.min("predicted_beta").alias("min_beta"),
        F.max("predicted_beta").alias("max_beta")
    ) \
    .orderBy("product_type") \
    .show()

# If actual beta is available, calculate prediction error
if "actual_beta" in predictions_df.columns:
    error_df = predictions_df.filter(F.col("actual_beta").isNotNull()) \
        .select(
            F.count("*").alias("validated_count"),
            F.avg(F.abs(F.col("predicted_beta") - F.col("actual_beta"))).alias("mae"),
            F.sqrt(F.avg(F.pow(F.col("predicted_beta") - F.col("actual_beta"), 2))).alias("rmse")
        ).collect()[0]

    print(f"\nPrediction Accuracy (vs Actual Beta):")
    print(f"  Accounts with actual beta: {error_df['validated_count']:,}")
    print(f"  MAE: {error_df['mae']:.4f}")
    print(f"  RMSE: {error_df['rmse']:.4f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Write Predictions to Delta Table

# COMMAND ----------

# Select final output columns
output_df = predictions_df.select(
    "account_id",
    "product_type",
    "customer_segment",
    "current_balance",
    "stated_rate",
    "predicted_beta",
    "actual_beta",  # Keep for validation if available
    "prediction_timestamp",
    "model_version"
)

# Write to Delta table (overwrite mode for full refresh, append for incremental)
output_table = "cfo_banking_demo.ml_models.deposit_beta_predictions"

output_df.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable(output_table)

print(f"✓ Predictions written to: {output_table}")
print(f"  Total records: {output_df.count():,}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6: Sample Predictions

# COMMAND ----------

print("Sample Predictions:")
predictions_df.select(
    "account_id",
    "product_type",
    "customer_segment",
    F.col("current_balance").alias("balance"),
    "stated_rate",
    "predicted_beta",
    "actual_beta"
).orderBy(F.rand()).limit(20).show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC **Batch Inference Complete!**
# MAGIC
# MAGIC ✅ Loaded model from Unity Catalog: `cfo_banking_demo.models.deposit_beta_model@champion`
# MAGIC ✅ Scored all deposit accounts using distributed Spark UDFs
# MAGIC ✅ Validated predictions (range checks, distribution analysis)
# MAGIC ✅ Written results to: `cfo_banking_demo.ml_models.deposit_beta_predictions`
# MAGIC
# MAGIC **Next Steps:**
# MAGIC 1. Schedule this notebook as a Databricks Job (weekly/monthly)
# MAGIC 2. Set up alerts for validation failures
# MAGIC 3. Use predictions in downstream ALM analysis and dashboards
# MAGIC 4. Monitor prediction drift over time
# MAGIC
# MAGIC **Why No Serving Endpoint?**
# MAGIC - Batch scoring is more cost-effective for periodic updates
# MAGIC - No need for real-time inference in treasury ALM use cases
# MAGIC - Predictions stored in Delta table for easy access by downstream consumers
