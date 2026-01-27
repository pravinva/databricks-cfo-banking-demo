# Databricks notebook source
# MAGIC %md
# MAGIC # Deposit Beta Model Training with Databricks Assistant (Data Science Agent)
# MAGIC
# MAGIC This notebook uses **Databricks Assistant** (the AI-powered data science agent) to train a deposit beta model through natural language instructions.
# MAGIC
# MAGIC ## How to Use Databricks Assistant:
# MAGIC
# MAGIC 1. **Enable Assistant**: Click the 🤖 Assistant icon in the top-right of your notebook
# MAGIC 2. **Provide Context**: First, run the cells below to create the training dataset
# MAGIC 3. **Use Natural Language**: In the Assistant chat, type instructions like:
# MAGIC    - "Train a regression model to predict target_beta from the deposit_beta_training_data table"
# MAGIC    - "Use XGBoost with 100 estimators and max_depth of 6"
# MAGIC    - "Evaluate the model using RMSE, MAE, and R²"
# MAGIC    - "Register the model to Unity Catalog as cfo_banking_demo.models.deposit_beta_model"
# MAGIC
# MAGIC The Assistant will generate and execute the code for you!

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Prepare Training Dataset
# MAGIC
# MAGIC First, let's create the feature table that the Assistant will use:

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
    -- Get latest rate environment (use 2-year as proxy for deposit rates)
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

    -- Historical rate environment (use 2Y rate as deposit rate proxy)
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

    -- Rate spread features (critical for beta prediction)
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
# MAGIC ## Step 2: Verify Training Data

# COMMAND ----------

# Check data quality
training_df = spark.table("cfo_banking_demo.ml_models.deposit_beta_training_data")

print(f"Training dataset shape: {training_df.count()} rows, {len(training_df.columns)} columns")
print("\nFeatures:")
for col in training_df.columns:
    print(f"  - {col}")

print("\nTarget variable distribution:")
training_df.select("target_beta").summary().show()

print("\nProduct type distribution:")
training_df.groupBy("product_type").count().orderBy("count", ascending=False).show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Use Databricks Assistant to Train the Model
# MAGIC
# MAGIC **🤖 Now use Databricks Assistant!**
# MAGIC
# MAGIC 1. Click the **Assistant** icon (🤖) in the top-right corner of this notebook
# MAGIC 2. In the Assistant chat, paste this prompt:
# MAGIC
# MAGIC ```
# MAGIC Train a regression model to predict target_beta using the table cfo_banking_demo.ml_models.deposit_beta_training_data.
# MAGIC
# MAGIC Use these features:
# MAGIC - product_type_encoded, segment_encoded, current_balance, stated_rate, account_age_months
# MAGIC - churned, dormant, balance_volatility_30d, rate_gap, churn_risk_score
# MAGIC - current_market_rate, market_rate_5y, market_rate_10y
# MAGIC - log_balance, balance_millions, balance_trend_30d
# MAGIC - rate_spread, rate_spread_x_balance, transaction_count_30d
# MAGIC
# MAGIC Use XGBoost with these parameters:
# MAGIC - max_depth: 6
# MAGIC - learning_rate: 0.1
# MAGIC - n_estimators: 100
# MAGIC
# MAGIC Split the data 80/20 for train/test, evaluate using RMSE, MAE, and R², log everything with MLflow, and register the best model to Unity Catalog as cfo_banking_demo.models.deposit_beta_model with alias @champion.
# MAGIC ```
# MAGIC
# MAGIC 3. The Assistant will generate the training code and execute it
# MAGIC 4. Review the generated code and results
# MAGIC 5. The model will be registered and ready for inference!

# COMMAND ----------

# MAGIC %md
# MAGIC ## Alternative: Example Code Generated by Assistant
# MAGIC
# MAGIC Below is example code that the Assistant might generate (for reference):

# COMMAND ----------

# This cell shows what the Assistant would generate
# You can run this directly OR use the Assistant to generate it for you

import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import mlflow
import mlflow.xgboost
from datetime import datetime

# Load training data
training_df = spark.table("cfo_banking_demo.ml_models.deposit_beta_training_data")
training_pdf = training_df.toPandas()

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

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Start MLflow run
with mlflow.start_run(run_name="deposit_beta_xgboost_assistant") as run:
    # Train XGBoost model
    params = {
        'max_depth': 6,
        'learning_rate': 0.1,
        'n_estimators': 100,
        'objective': 'reg:squarederror',
        'random_state': 42
    }

    model = xgb.XGBRegressor(**params)
    model.fit(X_train, y_train)

    # Predict and evaluate
    y_pred = model.predict(X_test)
    rmse = mean_squared_error(y_test, y_pred, squared=False)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    # Log to MLflow
    mlflow.log_params(params)
    mlflow.log_metric("rmse", rmse)
    mlflow.log_metric("mae", mae)
    mlflow.log_metric("r2", r2)
    mlflow.xgboost.log_model(model, "model", input_example=X_train.head(1))

    run_id = run.info.run_id

    print(f"\n✓ Training complete!")
    print(f"Run ID: {run_id}")
    print(f"RMSE: {rmse:.4f}")
    print(f"MAE: {mae:.4f}")
    print(f"R²: {r2:.4f}")

# Register to Unity Catalog
from mlflow import MlflowClient

client = MlflowClient()
model_name = "cfo_banking_demo.models.deposit_beta_model"
model_uri = f"runs:/{run_id}/model"

model_version = mlflow.register_model(
    model_uri=model_uri,
    name=model_name,
    tags={
        "model_type": "deposit_beta",
        "algorithm": "xgboost",
        "training_date": datetime.now().isoformat(),
        "trained_with": "databricks_assistant"
    }
)

# Set @champion alias
client.set_registered_model_alias(
    name=model_name,
    alias="champion",
    version=model_version.version
)

print(f"\n✓ Registered model: {model_name}")
print(f"  Version: {model_version.version}")
print(f"  Alias: @champion")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC **Using Databricks Assistant (Data Science Agent):**
# MAGIC
# MAGIC ✅ **What you did:**
# MAGIC 1. Created training dataset with feature engineering
# MAGIC 2. Used natural language prompts in Databricks Assistant
# MAGIC 3. Assistant generated training code automatically
# MAGIC 4. Model trained, evaluated, and registered to Unity Catalog
# MAGIC
# MAGIC **Model Location:** `cfo_banking_demo.models.deposit_beta_model@champion`
# MAGIC
# MAGIC **Key Benefit:** You used natural language to describe what you wanted, and the AI agent wrote the code for you!
