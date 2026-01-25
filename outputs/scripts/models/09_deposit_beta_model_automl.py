#!/usr/bin/env python3
"""
WS3-01: Deposit Beta Model with Databricks AutoML
Train ML model to predict deposit sensitivity to interest rate changes
Uses Databricks AutoML for production-grade model training
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import time
from datetime import datetime
import json

def log_message(message, level="INFO"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

# Constants
WAREHOUSE_ID = "4b9b953939869799"
CATALOG = "cfo_banking_demo"
SCHEMA = "ml_models"
MODEL_NAME = "deposit_beta_predictor"

def execute_sql(w, sql_statement, warehouse_id=WAREHOUSE_ID):
    """Execute SQL statement with extended timeout"""
    statement = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql_statement,
        wait_timeout="50s"
    )

    # Wait for completion
    max_wait_time = 600
    elapsed = 0
    while statement.status.state in [StatementState.PENDING, StatementState.RUNNING] and elapsed < max_wait_time:
        time.sleep(3)
        elapsed += 3
        statement = w.statement_execution.get_statement(statement.statement_id)

    if statement.status.state == StatementState.FAILED:
        error_msg = statement.status.error.message if statement.status.error else "Unknown error"
        raise Exception(f"SQL execution failed: {error_msg}")

    return statement

def create_ml_schema(w):
    """Create schema for ML models"""
    log_message("Creating ML models schema...")
    execute_sql(w, f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")
    log_message(f"  ✓ Created {CATALOG}.{SCHEMA}")

def create_training_dataset(w):
    """
    Create training dataset for deposit beta prediction
    Target: balance_change_pct (deposit sensitivity)
    Features: rate_change, product_type, customer_segment, balances, etc.
    """
    log_message("Creating training dataset...")

    # First, create deposit behavior history if it doesn't exist
    create_history_sql = """
    CREATE TABLE IF NOT EXISTS cfo_banking_demo.bronze_core_banking.deposit_behavior_history (
        account_id STRING,
        period_date DATE,
        beginning_balance DECIMAL(18,2),
        ending_balance DECIMAL(18,2),
        balance_change DECIMAL(18,2),
        balance_change_pct DECIMAL(8,4),
        fed_funds_rate DECIMAL(8,4),
        rate_change DECIMAL(8,4),
        product_type STRING,
        customer_segment STRING,
        has_online_banking BOOLEAN
    )
    """
    execute_sql(w, create_history_sql)

    # Generate synthetic historical data (12 months)
    log_message("  Generating synthetic deposit behavior history...")
    generate_history_sql = """
    INSERT OVERWRITE TABLE cfo_banking_demo.bronze_core_banking.deposit_behavior_history
    SELECT
        da.account_id,
        ADD_MONTHS(CURRENT_DATE(), -seq.month_offset) as period_date,
        da.current_balance * (1 + (RAND() * 0.1 - 0.05)) as beginning_balance,
        da.current_balance * (1 + (RAND() * 0.1 - 0.05)) as ending_balance,
        da.current_balance * (RAND() * 0.1 - 0.05) as balance_change,
        (RAND() * 10 - 5) as balance_change_pct,
        CASE
            WHEN seq.month_offset >= 10 THEN 2.5 + (RAND() * 0.5)
            WHEN seq.month_offset >= 6 THEN 3.5 + (RAND() * 0.5)
            ELSE 4.5 + (RAND() * 0.5)
        END as fed_funds_rate,
        CASE
            WHEN seq.month_offset = 11 THEN 0.0
            WHEN seq.month_offset >= 10 THEN 0.25
            WHEN seq.month_offset >= 6 THEN 0.5
            ELSE 0.25
        END as rate_change,
        da.product_type,
        da.customer_segment,
        da.has_online_banking
    FROM cfo_banking_demo.bronze_core_banking.deposit_accounts da
    CROSS JOIN (
        SELECT EXPLODE(SEQUENCE(0, 11)) as month_offset
    ) seq
    WHERE da.account_status = 'Active'
    """
    execute_sql(w, generate_history_sql)

    # Create ML training table with engineered features
    log_message("  Creating ML training table with features...")
    create_training_sql = f"""
    CREATE OR REPLACE TABLE {CATALOG}.{SCHEMA}.deposit_beta_training_data AS
    SELECT
        account_id,
        period_date,

        -- Target variable: balance change percentage
        balance_change_pct as target,

        -- Interest rate features
        fed_funds_rate,
        rate_change,
        CASE
            WHEN rate_change > 0 THEN 'INCREASE'
            WHEN rate_change < 0 THEN 'DECREASE'
            ELSE 'STABLE'
        END as rate_direction,

        -- Balance features
        beginning_balance,
        ending_balance,
        balance_change,
        CASE
            WHEN beginning_balance < 10000 THEN 'SMALL'
            WHEN beginning_balance < 100000 THEN 'MEDIUM'
            ELSE 'LARGE'
        END as balance_tier,

        -- Product and customer features
        product_type,
        customer_segment,
        has_online_banking,

        -- Time features
        MONTH(period_date) as month,
        QUARTER(period_date) as quarter,

        -- Interaction features
        rate_change * beginning_balance as rate_balance_interaction,

        -- Historical volatility (lag features would be calculated here in production)
        ABS(balance_change_pct) as balance_volatility

    FROM cfo_banking_demo.bronze_core_banking.deposit_behavior_history
    WHERE balance_change_pct IS NOT NULL
    AND ABS(balance_change_pct) < 50  -- Remove outliers
    """
    execute_sql(w, create_training_sql)

    # Get dataset stats
    stats = execute_sql(w, f"""
        SELECT
            COUNT(*) as record_count,
            COUNT(DISTINCT account_id) as unique_accounts,
            AVG(target) as avg_balance_change_pct,
            STDDEV(target) as stddev_balance_change_pct,
            MIN(rate_change) as min_rate_change,
            MAX(rate_change) as max_rate_change
        FROM {CATALOG}.{SCHEMA}.deposit_beta_training_data
    """)

    if stats.result and stats.result.data_array and stats.result.data_array[0]:
        row = stats.result.data_array[0]
        log_message(f"  ✓ Training dataset created:")
        log_message(f"    - Records: {int(row[0]):,}")
        log_message(f"    - Unique accounts: {int(row[1]):,}")
        log_message(f"    - Avg balance change: {float(row[2]):.2f}%")
        log_message(f"    - Std dev: {float(row[3]):.2f}%")
        log_message(f"    - Rate change range: {float(row[4]):.2f}% to {float(row[5]):.2f}%")

def create_automl_notebook(w):
    """Create notebook to run AutoML training"""
    log_message("Creating AutoML training notebook...")

    notebook_content = """# Databricks notebook source
# MAGIC %md
# MAGIC # Deposit Beta Model Training with AutoML
# MAGIC
# MAGIC Train ML model to predict deposit balance sensitivity to interest rate changes

# COMMAND ----------

import databricks.automl as automl

# COMMAND ----------

# MAGIC %md
# MAGIC ## Run AutoML Regression
# MAGIC
# MAGIC Predicting `target` (balance_change_pct) using deposit and rate features

# COMMAND ----------

summary = automl.regress(
    dataset="cfo_banking_demo.ml_models.deposit_beta_training_data",
    target_col="target",
    primary_metric="r2",
    timeout_minutes=30,
    max_trials=20,
    experiment_name="/Users/pravin.varma@databricks.com/deposit_beta_automl"
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## AutoML Results

# COMMAND ----------

print(f"Best trial R²: {summary.best_trial.metrics['val_r2_score']:.4f}")
print(f"Best trial MSE: {summary.best_trial.metrics['val_mse']:.4f}")
print(f"Best model: {summary.best_trial.model_description}")
print(f"Model path: {summary.best_trial.model_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Register Best Model to Unity Catalog

# COMMAND ----------

import mlflow

mlflow.set_registry_uri("databricks-uc")

# Register model to Unity Catalog
model_name = "cfo_banking_demo.ml_models.deposit_beta_predictor"

model_version = mlflow.register_model(
    model_uri=f"runs:/{summary.best_trial.mlflow_run_id}/model",
    name=model_name
)

print(f"Model registered: {model_name} (version {model_version.version})")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Set Model Alias to Champion

# COMMAND ----------

from mlflow.tracking import MlflowClient

client = MlflowClient()

# Set the @champion alias
client.set_registered_model_alias(
    name=model_name,
    alias="champion",
    version=model_version.version
)

print(f"Model {model_name} version {model_version.version} set as @champion")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test Model Predictions

# COMMAND ----------

import mlflow.pyfunc

# Load model using champion alias
champion_model = mlflow.pyfunc.load_model(f"models:/{model_name}@champion")

# Test with sample data
test_data = spark.table("cfo_banking_demo.ml_models.deposit_beta_training_data").limit(10).toPandas()
test_features = test_data.drop(columns=['target', 'account_id', 'period_date'])

predictions = champion_model.predict(test_features)

print("Sample predictions:")
for i, pred in enumerate(predictions[:5]):
    actual = test_data.iloc[i]['target']
    print(f"  Predicted: {pred:.2f}%, Actual: {actual:.2f}%")
"""

    # Upload notebook to workspace
    import base64
    content_b64 = base64.b64encode(notebook_content.encode('utf-8')).decode('utf-8')

    from databricks.sdk.service.workspace import ImportFormat, Language

    w.workspace.import_(
        path="/Users/pravin.varma@databricks.com/Deposit_Beta_AutoML_Training",
        format=ImportFormat.SOURCE,
        language=Language.PYTHON,
        content=content_b64,
        overwrite=True
    )

    log_message("  ✓ AutoML training notebook created: /Users/pravin.varma@databricks.com/Deposit_Beta_AutoML_Training")

def main():
    log_message("=" * 80)
    log_message("WS3-01: Deposit Beta Model with Databricks AutoML")
    log_message("=" * 80)

    # Initialize Databricks client
    w = WorkspaceClient()
    log_message("✓ Connected to Databricks")

    log_message("")
    log_message("-" * 80)

    # Step 1: Create ML schema
    create_ml_schema(w)

    log_message("")
    log_message("-" * 80)

    # Step 2: Create training dataset
    create_training_dataset(w)

    log_message("")
    log_message("-" * 80)

    # Step 3: Create AutoML notebook
    create_automl_notebook(w)

    log_message("")
    log_message("=" * 80)
    log_message("✅ WS3-01 Complete: Training Data Prepared")
    log_message("=" * 80)
    log_message("")
    log_message("Next Steps:")
    log_message("  1. Open notebook: /Users/pravin.varma@databricks.com/Deposit_Beta_AutoML_Training")
    log_message("  2. Attach to a cluster with ML Runtime")
    log_message("  3. Run all cells to train model with AutoML")
    log_message("  4. AutoML will automatically:")
    log_message("     - Train multiple models (XGBoost, LightGBM, Random Forest, etc.)")
    log_message("     - Perform hyperparameter tuning")
    log_message("     - Select best model based on R² score")
    log_message("     - Register model to Unity Catalog")
    log_message("     - Set @champion alias for production use")
    log_message("")

if __name__ == "__main__":
    main()
