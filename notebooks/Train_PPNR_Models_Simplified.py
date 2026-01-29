# Databricks notebook source
# MAGIC %md
# MAGIC # PPNR Model Training - Simplified (Using Available Data)
# MAGIC
# MAGIC **Pre-Provision Net Revenue (PPNR)** models using available gold-layer aggregates.
# MAGIC
# MAGIC **PPNR = Net Interest Income + Non-Interest Income - Non-Interest Expense**
# MAGIC
# MAGIC This notebook builds simplified ML models based on available data:
# MAGIC 1. **Non-Interest Income (Fee Revenue)** - Based on profitability metrics
# MAGIC 2. **Non-Interest Expense (Operating Costs)** - Based on business volume indicators
# MAGIC
# MAGIC ## Data Sources:
# MAGIC - `gold_finance.profitability_metrics` - Current fee revenue, expenses
# MAGIC - `bronze_core_banking.deposit_accounts` - Business volume indicators
# MAGIC - `bronze_core_banking.loan_portfolio` - Loan volume
# MAGIC - `silver_treasury.yield_curves` - Economic environment

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Create Synthetic Training Data for PPNR
# MAGIC
# MAGIC Since we don't have historical monthly GL data, we'll create a synthetic time series
# MAGIC based on current metrics and reasonable assumptions

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window
from datetime import datetime, timedelta
import random

# Generate 24 months of historical data
months_back = 24
base_date = datetime.now()

# Get current snapshot metrics
current_metrics = spark.sql("""
    SELECT
        -- Profitability (from gold_finance)
        COALESCE(MAX(fee_revenue), 45000000) as current_fee_revenue,
        COALESCE(MAX(operating_expenses), 125000000) as current_operating_expenses,
        COALESCE(MAX(net_interest_margin), 0.0325) as current_nim,

        -- Business volume
        COUNT(DISTINCT d.account_id) as current_accounts,
        SUM(d.current_balance) / 1e9 as current_deposits_billions,
        COUNT(DISTINCT l.loan_id) as current_loans,
        SUM(l.current_balance) / 1e9 as current_loan_balance_billions

    FROM cfo_banking_demo.bronze_core_banking.deposit_accounts d
    LEFT JOIN cfo_banking_demo.bronze_core_banking.loan_portfolio l ON 1=1
    CROSS JOIN cfo_banking_demo.gold_finance.profitability_metrics p
    WHERE d.is_current = TRUE
""").collect()[0]

print("Current Snapshot:")
print(f"  Fee Revenue: ${current_metrics['current_fee_revenue']:,.0f}")
print(f"  Operating Expenses: ${current_metrics['current_operating_expenses']:,.0f}")
print(f"  Deposit Accounts: {current_metrics['current_accounts']:,}")
print(f"  Total Deposits: ${current_metrics['current_deposits_billions']:.2f}B")

# COMMAND ----------

# Generate synthetic monthly time series
sql_synthetic = f"""
CREATE OR REPLACE TABLE cfo_banking_demo.ml_models.ppnr_training_data_synthetic AS
WITH month_sequence AS (
    -- Generate 24 months of history
    SELECT
        ADD_MONTHS(CURRENT_DATE(), -sequence.month_offset) as month,
        sequence.month_offset
    FROM (
        SELECT explode(sequence(0, 23)) as month_offset
    ) sequence
),
market_rates AS (
    -- Get actual historical rates
    SELECT
        DATE_TRUNC('month', date) as month,
        AVG(rate_10y) as avg_10y_rate,
        AVG(rate_2y) as avg_2y_rate,
        (MAX(rate_10y) - MIN(rate_10y)) as rate_volatility
    FROM cfo_banking_demo.silver_treasury.yield_curves
    GROUP BY DATE_TRUNC('month', date)
),
synthetic_data AS (
    SELECT
        m.month,
        m.month_offset,

        -- Current values with growth trend and seasonality
        {current_metrics['current_accounts']} * (1 + 0.01 * m.month_offset) * (1 + 0.05 * SIN(MONTH(m.month) * 3.14159 / 6)) as active_accounts,
        {current_metrics['current_deposits_billions']} * (1 + 0.015 * m.month_offset) * (1 + 0.03 * SIN(MONTH(m.month) * 3.14159 / 6)) as deposits_billions,
        {current_metrics['current_loans']} * (1 + 0.008 * m.month_offset) as loan_count,
        {current_metrics['current_loan_balance_billions']} * (1 + 0.012 * m.month_offset) as loan_balance_billions,

        -- Fee income with volume and seasonality
        {current_metrics['current_fee_revenue']} * (1 + 0.01 * m.month_offset) * (1 + 0.08 * SIN(MONTH(m.month) * 3.14159 / 6)) * (1 + (RAND() - 0.5) * 0.05) as target_fee_income,

        -- Operating expense with scale and inflation
        {current_metrics['current_operating_expenses']} * (1 + 0.015 * m.month_offset) * (1 + (RAND() - 0.5) * 0.03) as target_operating_expense,

        -- Market rates
        COALESCE(r.avg_10y_rate, 0.04) as avg_10y_rate,
        COALESCE(r.avg_2y_rate, 0.035) as avg_2y_rate,
        COALESCE(r.rate_volatility, 0.002) as rate_volatility,

        -- Time features
        MONTH(m.month) as month_of_year,
        QUARTER(m.month) as quarter

    FROM month_sequence m
    LEFT JOIN market_rates r ON m.month = r.month
)
SELECT
    month,

    -- Target variables
    target_fee_income,
    target_operating_expense,

    -- Features
    active_accounts,
    deposits_billions,
    loan_count,
    loan_balance_billions,
    avg_10y_rate,
    avg_2y_rate,
    rate_volatility,
    month_of_year,
    quarter,

    -- Derived features
    deposits_billions / NULLIF(active_accounts, 0) * 1e9 as deposits_per_account,
    loan_balance_billions / NULLIF(loan_count, 0) * 1e9 as avg_loan_size,

    -- Lagged features
    LAG(target_fee_income, 1) OVER (ORDER BY month) as prior_month_fee_income,
    LAG(target_operating_expense, 1) OVER (ORDER BY month) as prior_month_expense,
    LAG(active_accounts, 1) OVER (ORDER BY month) as prior_month_accounts

FROM synthetic_data
ORDER BY month DESC
"""

spark.sql(sql_synthetic)
print("\n✓ Created synthetic PPNR training data (24 months)")

# Display sample
display(spark.table("cfo_banking_demo.ml_models.ppnr_training_data_synthetic").limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Train Non-Interest Income Model

# COMMAND ----------

import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, mean_absolute_percentage_error
import mlflow
import mlflow.xgboost
import pandas as pd
import numpy as np

# Load training data
training_df = spark.table("cfo_banking_demo.ml_models.ppnr_training_data_synthetic")
training_pdf = training_df.toPandas()

print(f"Training data: {len(training_pdf)} months")
print(f"\nFee Income range: ${training_pdf['target_fee_income'].min():,.0f} - ${training_pdf['target_fee_income'].max():,.0f}")
print(f"Operating Expense range: ${training_pdf['target_operating_expense'].min():,.0f} - ${training_pdf['target_operating_expense'].max():,.0f}")

# COMMAND ----------

# Train Non-Interest Income Model
mlflow.set_experiment("/Users/pravin.varma@databricks.com/ppnr_non_interest_income")

nii_feature_cols = [
    'active_accounts', 'deposits_billions', 'loan_count', 'loan_balance_billions',
    'avg_10y_rate', 'avg_2y_rate', 'rate_volatility', 'month_of_year', 'quarter',
    'deposits_per_account', 'avg_loan_size', 'prior_month_fee_income'
]

X_nii = training_pdf[nii_feature_cols].fillna(training_pdf[nii_feature_cols].mean())
y_nii = training_pdf['target_fee_income']

# Convert to float
X_nii = X_nii.astype(float)
y_nii = y_nii.astype(float)

# Time-based split (train on older, test on recent)
split_idx = int(len(X_nii) * 0.75)
X_nii_train, X_nii_test = X_nii.iloc[:split_idx], X_nii.iloc[split_idx:]
y_nii_train, y_nii_test = y_nii.iloc[:split_idx], y_nii.iloc[split_idx:]

print(f"Non-Interest Income - Train: {len(X_nii_train)} months, Test: {len(X_nii_test)} months")

with mlflow.start_run(run_name="non_interest_income_xgboost") as run:
    params_nii = {
        'max_depth': 4,
        'learning_rate': 0.1,
        'n_estimators': 100,
        'objective': 'reg:squarederror',
        'random_state': 42
    }

    model_nii = xgb.XGBRegressor(**params_nii)
    model_nii.fit(X_nii_train, y_nii_train)

    y_nii_train_pred = model_nii.predict(X_nii_train)
    y_nii_test_pred = model_nii.predict(X_nii_test)

    train_rmse = mean_squared_error(y_nii_train, y_nii_train_pred, squared=False)
    test_rmse = mean_squared_error(y_nii_test, y_nii_test_pred, squared=False)
    test_mape = mean_absolute_percentage_error(y_nii_test, y_nii_test_pred)
    test_r2 = r2_score(y_nii_test, y_nii_test_pred)

    print("\n" + "=" * 80)
    print("NON-INTEREST INCOME MODEL")
    print("=" * 80)
    print(f"Training RMSE: ${train_rmse:,.0f}")
    print(f"Test RMSE:     ${test_rmse:,.0f}")
    print(f"Test MAPE:     {test_mape:.2%}")
    print(f"Test R²:       {test_r2:.4f}")

    print("\nFeature Importance (Top 5):")
    feature_importance = model_nii.get_booster().get_score(importance_type='gain')
    importance_sorted = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
    for i, (feature, importance) in enumerate(importance_sorted, 1):
        feat_name = nii_feature_cols[int(feature[1:])] if feature.startswith('f') else feature
        print(f"  {i}. {feat_name:30s} {importance:8.0f}")

    mlflow.log_params(params_nii)
    mlflow.log_metrics({"test_rmse": test_rmse, "test_mape": test_mape, "test_r2": test_r2})
    mlflow.xgboost.log_model(model_nii, "model", input_example=X_nii_train.head(1))

    run_id_nii = run.info.run_id

# Register model
from mlflow import MlflowClient
client = MlflowClient()

model_name_nii = "cfo_banking_demo.models.non_interest_income_model"
model_version_nii = mlflow.register_model(
    model_uri=f"runs:/{run_id_nii}/model",
    name=model_name_nii,
    tags={"model_type": "ppnr", "test_mape": f"{test_mape:.4f}"}
)

client.set_registered_model_alias(
    name=model_name_nii,
    alias="champion",
    version=model_version_nii.version
)

print(f"\n✓ Model registered: {model_name_nii}@champion (version {model_version_nii.version})")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Train Non-Interest Expense Model

# COMMAND ----------

mlflow.set_experiment("/Users/pravin.varma@databricks.com/ppnr_non_interest_expense")

nie_feature_cols = [
    'active_accounts', 'deposits_billions', 'loan_count', 'loan_balance_billions',
    'avg_10y_rate', 'month_of_year', 'quarter',
    'deposits_per_account', 'avg_loan_size', 'prior_month_expense', 'prior_month_accounts'
]

X_nie = training_pdf[nie_feature_cols].fillna(training_pdf[nie_feature_cols].mean())
y_nie = training_pdf['target_operating_expense']

# Convert to float
X_nie = X_nie.astype(float)
y_nie = y_nie.astype(float)

# Time-based split
X_nie_train, X_nie_test = X_nie.iloc[:split_idx], X_nie.iloc[split_idx:]
y_nie_train, y_nie_test = y_nie.iloc[:split_idx], y_nie.iloc[split_idx:]

print(f"Non-Interest Expense - Train: {len(X_nie_train)} months, Test: {len(X_nie_test)} months")

with mlflow.start_run(run_name="non_interest_expense_xgboost") as run:
    params_nie = {
        'max_depth': 4,
        'learning_rate': 0.1,
        'n_estimators': 100,
        'objective': 'reg:squarederror',
        'random_state': 42
    }

    model_nie = xgb.XGBRegressor(**params_nie)
    model_nie.fit(X_nie_train, y_nie_train)

    y_nie_train_pred = model_nie.predict(X_nie_train)
    y_nie_test_pred = model_nie.predict(X_nie_test)

    train_rmse = mean_squared_error(y_nie_train, y_nie_train_pred, squared=False)
    test_rmse = mean_squared_error(y_nie_test, y_nie_test_pred, squared=False)
    test_mape = mean_absolute_percentage_error(y_nie_test, y_nie_test_pred)
    test_r2 = r2_score(y_nie_test, y_nie_test_pred)

    print("\n" + "=" * 80)
    print("NON-INTEREST EXPENSE MODEL")
    print("=" * 80)
    print(f"Training RMSE: ${train_rmse:,.0f}")
    print(f"Test RMSE:     ${test_rmse:,.0f}")
    print(f"Test MAPE:     {test_mape:.2%}")
    print(f"Test R²:       {test_r2:.4f}")

    print("\nFeature Importance (Top 5):")
    feature_importance = model_nie.get_booster().get_score(importance_type='gain')
    importance_sorted = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
    for i, (feature, importance) in enumerate(importance_sorted, 1):
        feat_name = nie_feature_cols[int(feature[1:])] if feature.startswith('f') else feature
        print(f"  {i}. {feat_name:30s} {importance:8.0f}")

    mlflow.log_params(params_nie)
    mlflow.log_metrics({"test_rmse": test_rmse, "test_mape": test_mape, "test_r2": test_r2})
    mlflow.xgboost.log_model(model_nie, "model", input_example=X_nie_train.head(1))

    run_id_nie = run.info.run_id

# Register model
model_name_nie = "cfo_banking_demo.models.non_interest_expense_model"
model_version_nie = mlflow.register_model(
    model_uri=f"runs:/{run_id_nie}/model",
    name=model_name_nie,
    tags={"model_type": "ppnr", "test_mape": f"{test_mape:.4f}"}
)

client.set_registered_model_alias(
    name=model_name_nie,
    alias="champion",
    version=model_version_nie.version
)

print(f"\n✓ Model registered: {model_name_nie}@champion (version {model_version_nie.version})")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Generate PPNR Forecast

# COMMAND ----------

# Load models
mlflow.set_registry_uri("databricks-uc")
model_nii_loaded = mlflow.xgboost.load_model(f"models:/{model_name_nii}@champion")
model_nie_loaded = mlflow.xgboost.load_model(f"models:/{model_name_nie}@champion")

# Generate forecasts on test set
nii_forecast = model_nii_loaded.predict(X_nii_test)
nie_forecast = model_nie_loaded.predict(X_nie_test)

# Calculate PPNR
# PPNR = NII + Non-Interest Income - Non-Interest Expense
# Using current NIM and deposits as proxy for NII
test_months = training_pdf.iloc[split_idx:]
nii_proxy = (test_months['deposits_billions'].values * 1e9 * {current_metrics['current_nim']}) / 12
ppnr_forecast = nii_proxy + nii_forecast - nie_forecast

# Create results dataframe
results_df = pd.DataFrame({
    'month': test_months['month'].values,
    'net_interest_income_proxy': nii_proxy,
    'non_interest_income_forecast': nii_forecast,
    'non_interest_expense_forecast': nie_forecast,
    'ppnr_forecast': ppnr_forecast,
    'actual_fee_income': test_months['target_fee_income'].values,
    'actual_operating_expense': test_months['target_operating_expense'].values
})

print("=" * 80)
print("PPNR FORECAST SUMMARY")
print("=" * 80)
print(f"Average Monthly PPNR: ${ppnr_forecast.mean():,.0f}")
print(f"Annualized PPNR:      ${ppnr_forecast.mean() * 12:,.0f}")
print(f"\nComponents (Monthly Average):")
print(f"  Net Interest Income:      ${nii_proxy.mean():,.0f}")
print(f"  Non-Interest Income:      ${nii_forecast.mean():,.0f}")
print(f"  Non-Interest Expense:    -${nie_forecast.mean():,.0f}")
print(f"  ----------------------------------------")
print(f"  PPNR:                     ${ppnr_forecast.mean():,.0f}")

# Display results
display(results_df)

# COMMAND ----------

# Save forecasts
spark.createDataFrame(results_df).write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable("cfo_banking_demo.ml_models.ppnr_forecasts")

print("\n✓ PPNR forecasts saved to: cfo_banking_demo.ml_models.ppnr_forecasts")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC **✅ Models Trained & Registered:**
# MAGIC
# MAGIC 1. **Non-Interest Income Model**
# MAGIC    - `cfo_banking_demo.models.non_interest_income_model@champion`
# MAGIC    - Predicts monthly fee revenue based on business volume
# MAGIC    - Key drivers: Account count, deposits, transactions
# MAGIC
# MAGIC 2. **Non-Interest Expense Model**
# MAGIC    - `cfo_banking_demo.models.non_interest_expense_model@champion`
# MAGIC    - Predicts monthly operating expenses based on scale
# MAGIC    - Key drivers: Business volume, prior expenses
# MAGIC
# MAGIC 3. **PPNR Forecasts**
# MAGIC    - `cfo_banking_demo.ml_models.ppnr_forecasts`
# MAGIC    - Monthly PPNR projections for stress testing
# MAGIC
# MAGIC **Use Cases:**
# MAGIC - CCAR/DFAST stress testing
# MAGIC - Annual budgeting and financial planning
# MAGIC - Quarterly earnings forecasts
# MAGIC - Scenario analysis (recession, baseline, boom)
# MAGIC
# MAGIC **Next Steps:**
# MAGIC 1. Integrate with stress testing scenarios
# MAGIC 2. Create PPNR dashboard
# MAGIC 3. Schedule monthly batch scoring
# MAGIC 4. Feed into capital planning models
