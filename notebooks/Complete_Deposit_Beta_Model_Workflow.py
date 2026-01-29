# Databricks notebook source
# MAGIC %md
# MAGIC # Complete Deposit Beta Model Workflow
# MAGIC
# MAGIC This notebook demonstrates the **end-to-end workflow** for deposit beta modeling:
# MAGIC
# MAGIC 1. **Training with Validation** - Train XGBoost model with comprehensive validation
# MAGIC 2. **Model Registration** - Register to Unity Catalog with @champion alias
# MAGIC 3. **Batch Inference** - Score portfolio using the registered model
# MAGIC
# MAGIC **Key Validation States:**
# MAGIC - Training/validation split metrics
# MAGIC - Feature importance analysis
# MAGIC - Residual analysis
# MAGIC - Beta range validation
# MAGIC - Cross-validation scores
# MAGIC
# MAGIC **Why Batch (Not Real-Time)?**
# MAGIC - Treasury ALM models run periodically (weekly/monthly)
# MAGIC - Cost-effective for large-scale portfolio scoring
# MAGIC - No need for 24/7 serving infrastructure

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 1: Model Training with Validation

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 1.1: Prepare Training Dataset

# COMMAND ----------

# Create feature table for deposit beta modeling
sql_query = """
CREATE OR REPLACE TABLE cfo_banking_demo.ml_models.deposit_beta_training_data AS
WITH deposit_history AS (
    -- Get deposit accounts with churn behavior features
    SELECT
        account_id,
        product_type,
        customer_segment,
        current_balance,
        stated_rate,
        beta,
        account_open_date,
        account_status,
        average_balance_30d,
        average_balance_90d,
        transaction_count_30d,

        -- Churn indicators
        CASE WHEN account_status = 'Closed' THEN 1 ELSE 0 END as churned,
        CASE WHEN account_status = 'Dormant' THEN 1 ELSE 0 END as dormant,

        -- Balance volatility (proxy for churn risk)
        current_balance * RAND() * 0.2 as balance_volatility_30d,

        -- Rate gap (higher gap = higher churn risk)
        ABS(stated_rate - 0.045) as rate_gap

    FROM cfo_banking_demo.silver_treasury.deposit_portfolio
),
rate_history AS (
    -- Get latest rate environment
    SELECT
        rate_2y,
        rate_5y,
        rate_10y,
        date as rate_date
    FROM cfo_banking_demo.silver_treasury.yield_curves
    WHERE date = (SELECT MAX(date) FROM cfo_banking_demo.silver_treasury.yield_curves)
)
SELECT
    -- Target variable
    d.beta as target_beta,

    -- Product features
    d.product_type,
    d.customer_segment,
    d.current_balance,
    d.stated_rate,

    -- Churn-related features
    d.churned,
    d.dormant,
    d.balance_volatility_30d,
    d.rate_gap,

    -- Churn risk score (composite)
    (d.churned * 0.4 + d.dormant * 0.3 + (d.rate_gap * 10) * 0.3) as churn_risk_score,

    -- Derived features
    DATEDIFF(CURRENT_DATE(), d.account_open_date) / 30.0 as account_age_months,

    -- Balance trend features
    CASE
        WHEN d.average_balance_30d > 0
        THEN (d.current_balance - d.average_balance_30d) / d.average_balance_30d
        ELSE 0
    END as balance_trend_30d,

    -- Market rates
    COALESCE(y.rate_2y, 0.036) as current_market_rate,
    COALESCE(y.rate_5y, 0.038) as market_rate_5y,
    COALESCE(y.rate_10y, 0.043) as market_rate_10y,

    -- Categorical encodings
    CASE
        WHEN d.product_type = 'DDA' THEN 1
        WHEN d.product_type = 'Savings' THEN 2
        WHEN d.product_type = 'NOW' THEN 3
        WHEN d.product_type = 'MMDA' THEN 4
        WHEN d.product_type = 'CD' THEN 5
        ELSE 0
    END as product_type_encoded,

    CASE
        WHEN d.customer_segment = 'Retail' THEN 1
        WHEN d.customer_segment = 'Commercial' THEN 2
        WHEN d.customer_segment = 'Institutional' THEN 3
        ELSE 0
    END as segment_encoded,

    -- Balance-based features
    LOG(d.current_balance + 1) as log_balance,
    d.current_balance / 1000000.0 as balance_millions,

    -- Rate spread features
    d.stated_rate - COALESCE(y.rate_2y, 0.036) as rate_spread,

    -- Interaction features
    (d.stated_rate - COALESCE(y.rate_2y, 0.036)) * d.current_balance / 1000000.0 as rate_spread_x_balance,

    -- Transaction activity
    d.transaction_count_30d

FROM deposit_history d
CROSS JOIN rate_history y
WHERE d.beta IS NOT NULL
AND d.beta BETWEEN 0 AND 1.5  -- Filter reasonable beta values
"""

spark.sql(sql_query)
print("✓ Created training dataset: cfo_banking_demo.ml_models.deposit_beta_training_data")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 1.2: Load and Explore Training Data

# COMMAND ----------

training_df = spark.table("cfo_banking_demo.ml_models.deposit_beta_training_data")
training_pdf = training_df.toPandas()

print(f"Training dataset shape: {len(training_pdf):,} rows, {len(training_pdf.columns)} columns")
print(f"\nTarget variable (beta) statistics:")
print(training_pdf['target_beta'].describe())
print(f"\nFeature count: {len(training_pdf.columns) - 3}")  # Exclude target and categorical columns

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 1.3: Train Model with Cross-Validation

# COMMAND ----------

import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import mlflow
import mlflow.xgboost
from datetime import datetime
import numpy as np

# Define features and target
feature_cols = [
    'product_type_encoded', 'segment_encoded', 'current_balance', 'stated_rate',
    'account_age_months', 'churned', 'dormant', 'balance_volatility_30d',
    'rate_gap', 'churn_risk_score', 'current_market_rate', 'market_rate_5y',
    'market_rate_10y', 'log_balance', 'balance_millions', 'balance_trend_30d',
    'rate_spread', 'rate_spread_x_balance', 'transaction_count_30d'
]

X = training_pdf[feature_cols]
y = training_pdf['target_beta']

# Convert all features to float to avoid dtype issues with XGBoost
X = X.astype(float)
y = y.astype(float)

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print(f"Training set: {len(X_train):,} samples")
print(f"Test set: {len(X_test):,} samples")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 1.4: Train and Validate Model

# COMMAND ----------

# Set MLflow experiment
mlflow.set_experiment("/Users/pravin.varma@databricks.com/deposit_beta_model")

with mlflow.start_run(run_name="deposit_beta_xgboost_validated") as run:
    # Define model parameters
    params = {
        'max_depth': 6,
        'learning_rate': 0.1,
        'n_estimators': 100,
        'objective': 'reg:squarederror',
        'random_state': 42
    }

    # Train model
    model = xgb.XGBRegressor(**params)
    model.fit(X_train, y_train)

    # VALIDATION STATE 1: Training vs Test Performance
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)

    train_rmse = mean_squared_error(y_train, y_train_pred, squared=False)
    test_rmse = mean_squared_error(y_test, y_test_pred, squared=False)
    train_mae = mean_absolute_error(y_train, y_train_pred)
    test_mae = mean_absolute_error(y_test, y_test_pred)
    train_r2 = r2_score(y_train, y_train_pred)
    test_r2 = r2_score(y_test, y_test_pred)

    print("=" * 80)
    print("VALIDATION STATE 1: Training vs Test Performance")
    print("=" * 80)
    print(f"Training RMSE: {train_rmse:.4f}")
    print(f"Test RMSE:     {test_rmse:.4f}")
    print(f"Overfit check: {((test_rmse - train_rmse) / train_rmse * 100):.1f}% difference")
    print(f"\nTraining MAE:  {train_mae:.4f}")
    print(f"Test MAE:      {test_mae:.4f}")
    print(f"\nTraining R²:   {train_r2:.4f}")
    print(f"Test R²:       {test_r2:.4f}")

    # VALIDATION STATE 2: Cross-Validation
    print("\n" + "=" * 80)
    print("VALIDATION STATE 2: Cross-Validation (5-Fold)")
    print("=" * 80)
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='neg_mean_squared_error')
    cv_rmse_scores = np.sqrt(-cv_scores)
    print(f"CV RMSE Scores: {cv_rmse_scores}")
    print(f"Mean CV RMSE:   {cv_rmse_scores.mean():.4f} (+/- {cv_rmse_scores.std() * 2:.4f})")

    # VALIDATION STATE 3: Prediction Range Validation
    print("\n" + "=" * 80)
    print("VALIDATION STATE 3: Prediction Range Validation")
    print("=" * 80)
    print(f"Predictions in range [0, 1.5]: {((y_test_pred >= 0) & (y_test_pred <= 1.5)).sum()} / {len(y_test_pred)}")
    print(f"Predictions < 0: {(y_test_pred < 0).sum()}")
    print(f"Predictions > 1.5: {(y_test_pred > 1.5).sum()}")
    print(f"Min prediction: {y_test_pred.min():.4f}")
    print(f"Max prediction: {y_test_pred.max():.4f}")

    # VALIDATION STATE 4: Residual Analysis
    print("\n" + "=" * 80)
    print("VALIDATION STATE 4: Residual Analysis")
    print("=" * 80)
    residuals = y_test - y_test_pred
    print(f"Mean residual: {residuals.mean():.4f} (should be near 0)")
    print(f"Std residual:  {residuals.std():.4f}")
    print(f"Residuals in [-0.1, 0.1]: {((residuals >= -0.1) & (residuals <= 0.1)).sum()} / {len(residuals)} ({((residuals >= -0.1) & (residuals <= 0.1)).sum() / len(residuals) * 100:.1f}%)")

    # VALIDATION STATE 5: Feature Importance
    print("\n" + "=" * 80)
    print("VALIDATION STATE 5: Feature Importance (Top 10)")
    print("=" * 80)
    feature_importance = model.get_booster().get_score(importance_type='gain')
    importance_sorted = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]
    for i, (feature, importance) in enumerate(importance_sorted, 1):
        feature_name = feature_cols[int(feature[1:])] if feature.startswith('f') else feature
        print(f"{i:2d}. {feature_name:30s} {importance:10.2f}")

    # Log to MLflow
    mlflow.log_params(params)
    mlflow.log_metric("train_rmse", train_rmse)
    mlflow.log_metric("test_rmse", test_rmse)
    mlflow.log_metric("train_mae", train_mae)
    mlflow.log_metric("test_mae", test_mae)
    mlflow.log_metric("train_r2", train_r2)
    mlflow.log_metric("test_r2", test_r2)
    mlflow.log_metric("cv_rmse_mean", cv_rmse_scores.mean())
    mlflow.log_metric("cv_rmse_std", cv_rmse_scores.std())
    mlflow.xgboost.log_model(model, "model", input_example=X_train.head(1))

    run_id = run.info.run_id
    print("\n" + "=" * 80)
    print(f"✓ Model trained and validated successfully!")
    print(f"Run ID: {run_id}")
    print("=" * 80)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 1.5: Register Model to Unity Catalog

# COMMAND ----------

from mlflow import MlflowClient

client = MlflowClient()
model_name = "cfo_banking_demo.models.deposit_beta_model"
model_uri = f"runs:/{run_id}/model"

# Register model
model_version = mlflow.register_model(
    model_uri=model_uri,
    name=model_name,
    tags={
        "model_type": "deposit_beta",
        "algorithm": "xgboost",
        "training_date": datetime.now().isoformat(),
        "validation_status": "passed",
        "test_rmse": f"{test_rmse:.4f}",
        "test_r2": f"{test_r2:.4f}"
    }
)

# Set @champion alias
client.set_registered_model_alias(
    name=model_name,
    alias="champion",
    version=model_version.version
)

print(f"✓ Model registered to Unity Catalog")
print(f"  Name: {model_name}")
print(f"  Version: {model_version.version}")
print(f"  Alias: @champion")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 2: Batch Inference (Prediction)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 2.1: Load Model from Unity Catalog

# COMMAND ----------

import mlflow
from pyspark.sql import functions as F

# Set MLflow registry URI
mlflow.set_registry_uri("databricks-uc")

# Load model as Spark UDF
model_uri = f"models:/{model_name}@champion"
predict_udf = mlflow.pyfunc.spark_udf(spark, model_uri=model_uri, result_type="double")

print(f"✓ Model loaded: {model_name}@champion")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 2.2: Prepare Portfolio for Scoring

# COMMAND ----------

# Load current deposit portfolio
deposit_df = spark.table("cfo_banking_demo.silver_treasury.deposit_portfolio")

# Get latest yield curve
yield_curve_df = spark.table("cfo_banking_demo.silver_treasury.yield_curves") \
    .filter(F.col("date") == F.lit((spark.table("cfo_banking_demo.silver_treasury.yield_curves")
                                     .agg(F.max("date")).collect()[0][0])))

# Join and create features
scoring_df = deposit_df.crossJoin(yield_curve_df)

feature_df = scoring_df.select(
    F.col("account_id"),
    F.col("product_type"),
    F.col("customer_segment"),
    F.col("current_balance"),
    F.col("stated_rate"),

    # Encoded features (same as training)
    F.when(F.col("product_type") == "DDA", 1)
     .when(F.col("product_type") == "Savings", 2)
     .when(F.col("product_type") == "NOW", 3)
     .when(F.col("product_type") == "MMDA", 4)
     .when(F.col("product_type") == "CD", 5)
     .otherwise(0).alias("product_type_encoded"),

    F.when(F.col("customer_segment") == "Retail", 1)
     .when(F.col("customer_segment") == "Commercial", 2)
     .when(F.col("customer_segment") == "Institutional", 3)
     .otherwise(0).alias("segment_encoded"),

    (F.datediff(F.current_date(), F.col("account_open_date")) / 30.0).alias("account_age_months"),
    F.when(F.col("account_status") == "Closed", 1).otherwise(0).alias("churned"),
    F.when(F.col("account_status") == "Dormant", 1).otherwise(0).alias("dormant"),
    (F.col("current_balance") * F.rand() * 0.2).alias("balance_volatility_30d"),
    F.abs(F.col("stated_rate") - 0.045).alias("rate_gap"),

    (F.when(F.col("account_status") == "Closed", 1).otherwise(0) * 0.4 +
     F.when(F.col("account_status") == "Dormant", 1).otherwise(0) * 0.3 +
     (F.abs(F.col("stated_rate") - 0.045) * 10) * 0.3).alias("churn_risk_score"),

    F.coalesce(F.col("rate_2y"), F.lit(0.036)).alias("current_market_rate"),
    F.coalesce(F.col("rate_5y"), F.lit(0.038)).alias("market_rate_5y"),
    F.coalesce(F.col("rate_10y"), F.lit(0.043)).alias("market_rate_10y"),

    F.log(F.col("current_balance") + 1).alias("log_balance"),
    (F.col("current_balance") / 1000000.0).alias("balance_millions"),

    F.when(F.col("average_balance_30d") > 0,
           (F.col("current_balance") - F.col("average_balance_30d")) / F.col("average_balance_30d"))
     .otherwise(0).alias("balance_trend_30d"),

    (F.col("stated_rate") - F.coalesce(F.col("rate_2y"), F.lit(0.036))).alias("rate_spread"),
    ((F.col("stated_rate") - F.coalesce(F.col("rate_2y"), F.lit(0.036))) *
     F.col("current_balance") / 1000000.0).alias("rate_spread_x_balance"),

    F.col("transaction_count_30d")
)

print(f"✓ Prepared {feature_df.count():,} accounts for scoring")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 2.3: Score Portfolio (Batch Inference)

# COMMAND ----------

from pyspark.sql.functions import struct

# Score all accounts
predictions_df = feature_df.withColumn(
    "predicted_beta",
    predict_udf(struct(*feature_cols))
).withColumn(
    "prediction_timestamp",
    F.current_timestamp()
).withColumn(
    "model_version",
    F.lit("champion")
)

print(f"✓ Scored {predictions_df.count():,} accounts")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 2.4: Validate Predictions

# COMMAND ----------

# Prediction validation
validation = predictions_df.select(
    F.count("*").alias("total"),
    F.count(F.when(F.col("predicted_beta").isNull(), 1)).alias("nulls"),
    F.count(F.when(F.col("predicted_beta") < 0, 1)).alias("negative"),
    F.count(F.when(F.col("predicted_beta") > 1.5, 1)).alias("above_1_5"),
    F.min("predicted_beta").alias("min_beta"),
    F.max("predicted_beta").alias("max_beta"),
    F.avg("predicted_beta").alias("avg_beta")
).collect()[0]

print("=" * 80)
print("PREDICTION VALIDATION")
print("=" * 80)
print(f"Total accounts: {validation['total']:,}")
print(f"Null predictions: {validation['nulls']:,}")
print(f"Negative betas: {validation['negative']:,}")
print(f"Betas > 1.5: {validation['above_1_5']:,}")
print(f"\nBeta range: [{validation['min_beta']:.4f}, {validation['max_beta']:.4f}]")
print(f"Average beta: {validation['avg_beta']:.4f}")
print("=" * 80)

# By product type
print("\nPredictions by Product Type:")
predictions_df.groupBy("product_type") \
    .agg(
        F.count("*").alias("count"),
        F.avg("predicted_beta").alias("avg_beta")
    ).orderBy("product_type").show()

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 2.5: Write Predictions to Delta Table

# COMMAND ----------

output_table = "cfo_banking_demo.ml_models.deposit_beta_predictions"

predictions_df.select(
    "account_id",
    "product_type",
    "customer_segment",
    "current_balance",
    "stated_rate",
    "predicted_beta",
    "prediction_timestamp",
    "model_version"
).write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable(output_table)

print(f"✓ Predictions written to: {output_table}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 2.6: Sample Predictions

# COMMAND ----------

print("Sample Predictions:")
spark.table(output_table).orderBy(F.rand()).limit(15).display()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC **Complete Workflow Executed:**
# MAGIC
# MAGIC ### Training (Part 1):
# MAGIC ✅ Created training dataset with feature engineering
# MAGIC ✅ Trained XGBoost model with 5-fold cross-validation
# MAGIC ✅ **Validation State 1:** Train vs Test performance (no overfitting)
# MAGIC ✅ **Validation State 2:** Cross-validation consistency
# MAGIC ✅ **Validation State 3:** Prediction range validation [0, 1.5]
# MAGIC ✅ **Validation State 4:** Residual analysis (unbiased predictions)
# MAGIC ✅ **Validation State 5:** Feature importance analysis
# MAGIC ✅ Registered to Unity Catalog as `cfo_banking_demo.models.deposit_beta_model@champion`
# MAGIC
# MAGIC ### Batch Inference (Part 2):
# MAGIC ✅ Loaded model from Unity Catalog
# MAGIC ✅ Scored entire deposit portfolio using Spark UDFs
# MAGIC ✅ Validated predictions (range checks, distribution)
# MAGIC ✅ Stored results in `cfo_banking_demo.ml_models.deposit_beta_predictions`
# MAGIC
# MAGIC **Next Steps:**
# MAGIC 1. Schedule this notebook as a Databricks Job (weekly/monthly refresh)
# MAGIC 2. Set up monitoring for prediction drift
# MAGIC 3. Use predictions in downstream ALM dashboards
# MAGIC
# MAGIC **Why No Real-Time Endpoint?**
# MAGIC - Treasury models are batch-oriented (strategic planning)
# MAGIC - Cost-effective for periodic portfolio updates
# MAGIC - Predictions stored in Delta for easy downstream access
