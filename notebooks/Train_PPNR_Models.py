# Databricks notebook source
# MAGIC %md
# MAGIC # PPNR Model Training - Non-Interest Income & Expense
# MAGIC
# MAGIC **Pre-Provision Net Revenue (PPNR)** is a key stress testing metric used by regulators and banks.
# MAGIC
# MAGIC **PPNR = Net Interest Income + Non-Interest Income - Non-Interest Expense**
# MAGIC
# MAGIC This notebook builds ML models for:
# MAGIC 1. **Non-Interest Income (Fee Revenue)** - Predicts fee income based on economic conditions
# MAGIC 2. **Non-Interest Expense (Operating Costs)** - Predicts operating expenses based on business volume
# MAGIC
# MAGIC ## Use Cases:
# MAGIC - **Stress Testing:** CCAR, DFAST scenarios
# MAGIC - **Financial Planning:** Annual budgeting, strategic planning
# MAGIC - **Performance Forecasting:** Quarterly projections
# MAGIC - **Scenario Analysis:** Recession, boom, baseline scenarios
# MAGIC
# MAGIC ## Regulatory Context:
# MAGIC - **Fed CCAR:** Comprehensive Capital Analysis and Review
# MAGIC - **DFAST:** Dodd-Frank Act Stress Testing
# MAGIC - **Basel III:** Capital planning requirements

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 1: Non-Interest Income Model

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 1.1: Create Training Dataset for Non-Interest Income

# COMMAND ----------

# MAGIC %md
# MAGIC #### Diagnostic: Check Data Availability

# COMMAND ----------

# Check if source data exists
print("Checking data availability in source tables...\n")

# Check deposit accounts
deposit_check = spark.sql("""
    SELECT
        COUNT(*) as total_rows,
        MIN(effective_date) as earliest_date,
        MAX(effective_date) as latest_date,
        COUNT(DISTINCT DATE_TRUNC('month', effective_date)) as unique_months
    FROM cfo_banking_demo.bronze_core_banking.deposit_accounts_historical
    WHERE effective_date >= DATE_SUB(CURRENT_DATE(), 730)
""")
print("Deposit Accounts (last 730 days):")
deposit_check.show()

# Check loan portfolio
loan_check = spark.sql("""
    SELECT
        COUNT(*) as total_rows,
        MIN(effective_date) as earliest_date,
        MAX(effective_date) as latest_date,
        COUNT(DISTINCT DATE_TRUNC('month', effective_date)) as unique_months
    FROM cfo_banking_demo.bronze_core_banking.loan_portfolio_historical
    WHERE effective_date >= DATE_SUB(CURRENT_DATE(), 730)
""")
print("Loan Portfolio Historical (last 730 days):")
loan_check.show()

# Check yield curves
yield_check = spark.sql("""
    SELECT
        COUNT(*) as total_rows,
        MIN(date) as earliest_date,
        MAX(date) as latest_date,
        COUNT(DISTINCT DATE_TRUNC('month', date)) as unique_months
    FROM cfo_banking_demo.silver_treasury.yield_curves
    WHERE date >= DATE_SUB(CURRENT_DATE(), 730)
""")
print("Yield Curves (last 730 days):")
yield_check.show()

# Check GL data
gl_check = spark.sql("""
    SELECT
        COUNT(*) as total_rows,
        MIN(e.entry_date) as earliest_date,
        MAX(e.entry_date) as latest_date,
        COUNT(DISTINCT DATE_TRUNC('month', e.entry_date)) as unique_months
    FROM cfo_banking_demo.silver_finance.gl_entry_lines l
    JOIN cfo_banking_demo.silver_finance.gl_entries e ON l.entry_id = e.entry_id
    WHERE e.entry_date >= DATE_SUB(CURRENT_DATE(), 730)
    AND l.account_number LIKE '41%'
""")
print("GL Fee Income (last 730 days):")
gl_check.show()

# COMMAND ----------

# Non-Interest Income includes:
# - Service charges on deposits
# - Card interchange fees
# - Wealth management fees
# - Investment banking fees
# - Trading revenue
# - Mortgage servicing fees

sql_query_nii = """
CREATE OR REPLACE TABLE cfo_banking_demo.ml_models.non_interest_income_training_data AS
WITH deposit_metrics AS (
    -- Aggregate deposits by month first (avoids Cartesian product)
    -- deposit_accounts_historical has simplified schema: account_id, customer_id, product_type,
    -- customer_segment, account_open_date, effective_date, current_balance, stated_rate, is_current, is_closed
    SELECT
        DATE_TRUNC('month', effective_date) as month,
        COUNT(DISTINCT account_id) as active_deposit_accounts,
        SUM(CASE WHEN product_type IN ('Checking', 'DDA') THEN 1 ELSE 0 END) as checking_accounts,
        SUM(current_balance) as total_deposits,
        -- Estimated transaction metrics (not in historical table)
        COUNT(DISTINCT account_id) * 25 as total_transactions,  -- Est 25 txns/account/month
        12.50 as avg_monthly_fee,  -- Static average
        SUM(CASE WHEN customer_segment = 'Retail' THEN current_balance ELSE 0 END) / NULLIF(SUM(current_balance), 0) as retail_deposit_pct,
        SUM(CASE WHEN customer_segment = 'Commercial' THEN current_balance ELSE 0 END) / NULLIF(SUM(current_balance), 0) as commercial_deposit_pct,
        -- Estimated digital vs branch (not in historical table)
        COUNT(DISTINCT account_id) * 20 as digital_transactions,  -- Est 80% digital
        COUNT(DISTINCT account_id) * 5 as branch_transactions  -- Est 20% branch
    FROM cfo_banking_demo.bronze_core_banking.deposit_accounts_historical
    WHERE effective_date >= DATE_SUB(CURRENT_DATE(), 730)
    GROUP BY DATE_TRUNC('month', effective_date)
),
loan_metrics AS (
    -- Aggregate loans by month separately
    SELECT
        DATE_TRUNC('month', effective_date) as month,
        COUNT(DISTINCT loan_id) as active_loans,
        SUM(current_balance) as total_loan_balance,
        COUNT(CASE WHEN origination_date >= DATE_SUB(CURRENT_DATE(), 30) THEN 1 END) as new_loans_30d,
        SUM(CASE WHEN product_type IN ('Mortgage', 'Home_Equity', 'Residential_Mortgage', 'Commercial_Mortgage') THEN current_balance ELSE 0 END) as mortgage_balance
    FROM cfo_banking_demo.bronze_core_banking.loan_portfolio_historical
    WHERE effective_date >= DATE_SUB(CURRENT_DATE(), 730)
    GROUP BY DATE_TRUNC('month', effective_date)
),
monthly_metrics AS (
    -- Join aggregated metrics (much smaller datasets)
    SELECT
        d.month,
        d.active_deposit_accounts,
        d.checking_accounts,
        d.total_deposits,
        d.total_transactions,
        d.avg_monthly_fee,
        d.retail_deposit_pct,
        d.commercial_deposit_pct,
        d.digital_transactions,
        d.branch_transactions,
        COALESCE(l.active_loans, 0) as active_loans,
        COALESCE(l.total_loan_balance, 0) as total_loan_balance,
        COALESCE(l.new_loans_30d, 0) as new_loans_30d,
        COALESCE(l.mortgage_balance, 0) as mortgage_balance
    FROM deposit_metrics d
    LEFT JOIN loan_metrics l ON d.month = l.month
),
market_conditions AS (
    -- Economic indicators that affect fee income
    SELECT
        DATE_TRUNC('month', date) as month,
        AVG(rate_10y) as avg_10y_rate,
        AVG(rate_2y) as avg_2y_rate,
        (MAX(rate_10y) - MIN(rate_10y)) as rate_volatility,
        AVG(rate_10y - rate_2y) as yield_curve_slope
    FROM cfo_banking_demo.silver_treasury.yield_curves
    WHERE date >= DATE_SUB(CURRENT_DATE(), 730)
    GROUP BY DATE_TRUNC('month', date)
),
fee_income_actual AS (
    -- Actual fee income from GL (target variable)
    SELECT
        DATE_TRUNC('month', e.entry_date) as month,
        SUM(CASE
            WHEN l.account_number LIKE '4100%' THEN l.credit_amount  -- Service charges
            WHEN l.account_number LIKE '4110%' THEN l.credit_amount  -- Card fees
            WHEN l.account_number LIKE '4120%' THEN l.credit_amount  -- Loan fees
            WHEN l.account_number LIKE '4130%' THEN l.credit_amount  -- Wealth mgmt fees
            ELSE 0
        END) as total_fee_income,

        SUM(CASE WHEN l.account_number LIKE '4100%' THEN l.credit_amount ELSE 0 END) as service_charge_income,
        SUM(CASE WHEN l.account_number LIKE '4110%' THEN l.credit_amount ELSE 0 END) as card_fee_income,
        SUM(CASE WHEN l.account_number LIKE '4120%' THEN l.credit_amount ELSE 0 END) as loan_fee_income,
        SUM(CASE WHEN l.account_number LIKE '4130%' THEN l.credit_amount ELSE 0 END) as wealth_fee_income

    FROM cfo_banking_demo.silver_finance.gl_entry_lines l
    JOIN cfo_banking_demo.silver_finance.gl_entries e ON l.entry_id = e.entry_id
    WHERE e.entry_date >= DATE_SUB(CURRENT_DATE(), 730)
    AND l.account_number LIKE '41%'  -- Revenue accounts
    GROUP BY DATE_TRUNC('month', e.entry_date)
)
SELECT
    m.month,

    -- Target variable
    COALESCE(f.total_fee_income, 45000000) as target_fee_income,  -- Default if missing

    -- Business volume features
    m.active_deposit_accounts,
    m.checking_accounts,
    m.total_deposits / 1e9 as total_deposits_billions,
    m.total_transactions / 1000000.0 as total_transactions_millions,
    m.avg_monthly_fee,
    m.retail_deposit_pct,
    m.commercial_deposit_pct,

    m.active_loans,
    m.total_loan_balance / 1e9 as total_loan_balance_billions,
    m.new_loans_30d,
    m.mortgage_balance / 1e9 as mortgage_balance_billions,

    m.digital_transactions / 1000000.0 as digital_transactions_millions,
    m.branch_transactions / 1000000.0 as branch_transactions_millions,

    -- Economic features
    mc.avg_10y_rate,
    mc.avg_2y_rate,
    mc.rate_volatility,
    mc.yield_curve_slope,

    -- Derived features
    m.checking_accounts / NULLIF(m.active_deposit_accounts, 0) as checking_account_pct,
    m.digital_transactions / NULLIF(m.total_transactions, 0) as digital_transaction_pct,
    m.new_loans_30d / NULLIF(m.active_loans, 0) as new_loan_rate,

    -- Time features (seasonality)
    MONTH(m.month) as month_of_year,
    QUARTER(m.month) as quarter,
    YEAR(m.month) as year,

    -- Lagged features (prior month trend)
    LAG(COALESCE(f.total_fee_income, 45000000), 1) OVER (ORDER BY m.month) as prior_month_fee_income,
    LAG(m.total_transactions, 1) OVER (ORDER BY m.month) as prior_month_transactions

FROM monthly_metrics m
LEFT JOIN market_conditions mc ON m.month = mc.month
LEFT JOIN fee_income_actual f ON m.month = f.month
WHERE m.month IS NOT NULL
ORDER BY m.month
"""

spark.sql(sql_query_nii)
print("✓ Created Non-Interest Income training dataset")

# COMMAND ----------

# MAGIC %md
# MAGIC #### Diagnostic: Check CTE Results

# COMMAND ----------

# Check how many rows each CTE produces
print("Checking intermediate CTE results...\n")

# Check deposit_metrics CTE
deposit_metrics_check = spark.sql("""
    WITH deposit_metrics AS (
        SELECT
            DATE_TRUNC('month', effective_date) as month,
            COUNT(DISTINCT account_id) as active_deposit_accounts
        FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
        WHERE effective_date >= DATE_SUB(CURRENT_DATE(), 730)
        GROUP BY DATE_TRUNC('month', effective_date)
    )
    SELECT COUNT(*) as row_count, MIN(month) as earliest_month, MAX(month) as latest_month
    FROM deposit_metrics
""")
print("deposit_metrics CTE:")
deposit_metrics_check.show()

# Check loan_metrics CTE
loan_metrics_check = spark.sql("""
    WITH loan_metrics AS (
        SELECT
            DATE_TRUNC('month', effective_date) as month,
            COUNT(DISTINCT loan_id) as active_loans
        FROM cfo_banking_demo.bronze_core_banking.loan_portfolio
        WHERE effective_date >= DATE_SUB(CURRENT_DATE(), 730)
        GROUP BY DATE_TRUNC('month', effective_date)
    )
    SELECT COUNT(*) as row_count, MIN(month) as earliest_month, MAX(month) as latest_month
    FROM loan_metrics
""")
print("loan_metrics CTE:")
loan_metrics_check.show()

# Check market_conditions CTE
market_check = spark.sql("""
    WITH market_conditions AS (
        SELECT
            DATE_TRUNC('month', date) as month,
            AVG(rate_10y) as avg_10y_rate
        FROM cfo_banking_demo.silver_treasury.yield_curves
        WHERE date >= DATE_SUB(CURRENT_DATE(), 730)
        GROUP BY DATE_TRUNC('month', date)
    )
    SELECT COUNT(*) as row_count, MIN(month) as earliest_month, MAX(month) as latest_month
    FROM market_conditions
""")
print("market_conditions CTE:")
market_check.show()

# Check fee_income_actual CTE
fee_check = spark.sql("""
    WITH fee_income_actual AS (
        SELECT
            DATE_TRUNC('month', e.entry_date) as month,
            SUM(l.credit_amount) as total_fee_income
        FROM cfo_banking_demo.silver_finance.gl_entry_lines l
        JOIN cfo_banking_demo.silver_finance.gl_entries e ON l.entry_id = e.entry_id
        WHERE e.entry_date >= DATE_SUB(CURRENT_DATE(), 730)
        AND l.account_number LIKE '41%'
        GROUP BY DATE_TRUNC('month', e.entry_date)
    )
    SELECT COUNT(*) as row_count, MIN(month) as earliest_month, MAX(month) as latest_month
    FROM fee_income_actual
""")
print("fee_income_actual CTE:")
fee_check.show()

# Check final result set row count
final_check = spark.sql("""
    SELECT COUNT(*) as final_row_count
    FROM cfo_banking_demo.ml_models.non_interest_income_training_data
""")
print("\nFinal training table:")
final_check.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 1.2: Train Non-Interest Income Model

# COMMAND ----------

import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, mean_absolute_percentage_error
import mlflow
import mlflow.xgboost
import numpy as np
import pandas as pd
from datetime import datetime

# Load training data
nii_training_df = spark.table("cfo_banking_demo.ml_models.non_interest_income_training_data")
nii_training_pdf = nii_training_df.toPandas()

print(f"Non-Interest Income training data: {len(nii_training_pdf):,} months")
print(f"\nTarget variable statistics:")
print(nii_training_pdf['target_fee_income'].describe())

# Define features
nii_feature_cols = [
    'active_deposit_accounts', 'checking_accounts', 'total_deposits_billions',
    'total_transactions_millions', 'avg_monthly_fee', 'retail_deposit_pct',
    'commercial_deposit_pct', 'active_loans', 'total_loan_balance_billions',
    'new_loans_30d', 'mortgage_balance_billions', 'digital_transactions_millions',
    'branch_transactions_millions', 'avg_10y_rate', 'avg_2y_rate', 'rate_volatility',
    'yield_curve_slope', 'checking_account_pct', 'digital_transaction_pct',
    'new_loan_rate', 'month_of_year', 'quarter', 'prior_month_fee_income',
    'prior_month_transactions'
]

X_nii = nii_training_pdf[nii_feature_cols].fillna(0)
y_nii = nii_training_pdf['target_fee_income']

# Convert to float
X_nii = X_nii.astype(float)
y_nii = y_nii.astype(float)

# Train/test split (time-based)
split_idx = int(len(X_nii) * 0.8)
X_nii_train, X_nii_test = X_nii[:split_idx], X_nii[split_idx:]
y_nii_train, y_nii_test = y_nii[:split_idx], y_nii[split_idx:]

print(f"\nTraining set: {len(X_nii_train)} months")
print(f"Test set: {len(X_nii_test)} months (most recent)")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 1.3: Train and Validate Non-Interest Income Model

# COMMAND ----------

mlflow.set_experiment("/Users/pravin.varma@databricks.com/ppnr_non_interest_income")

with mlflow.start_run(run_name="non_interest_income_xgboost") as run:
    # Model parameters
    params_nii = {
        'max_depth': 5,
        'learning_rate': 0.05,
        'n_estimators': 150,
        'objective': 'reg:squarederror',
        'random_state': 42
    }

    # Train model
    model_nii = xgb.XGBRegressor(**params_nii)
    model_nii.fit(X_nii_train, y_nii_train)

    # Predictions
    y_nii_train_pred = model_nii.predict(X_nii_train)
    y_nii_test_pred = model_nii.predict(X_nii_test)

    # Validation State 1: Train vs Test
    train_rmse = mean_squared_error(y_nii_train, y_nii_train_pred, squared=False)
    test_rmse = mean_squared_error(y_nii_test, y_nii_test_pred, squared=False)
    train_mape = mean_absolute_percentage_error(y_nii_train, y_nii_train_pred)
    test_mape = mean_absolute_percentage_error(y_nii_test, y_nii_test_pred)
    train_r2 = r2_score(y_nii_train, y_nii_train_pred)
    test_r2 = r2_score(y_nii_test, y_nii_test_pred)

    print("=" * 80)
    print("NON-INTEREST INCOME MODEL VALIDATION")
    print("=" * 80)
    print("\nVALIDATION STATE 1: Train vs Test Performance")
    print(f"Training RMSE: ${train_rmse:,.0f}")
    print(f"Test RMSE:     ${test_rmse:,.0f}")
    print(f"Training MAPE: {train_mape:.2%}")
    print(f"Test MAPE:     {test_mape:.2%}  {'✓' if test_mape < 0.10 else '⚠️'}")
    print(f"Training R²:   {train_r2:.4f}")
    print(f"Test R²:       {test_r2:.4f}")

    # Validation State 2: Prediction Range
    print("\nVALIDATION STATE 2: Prediction Range")
    print(f"Min prediction: ${y_nii_test_pred.min():,.0f}")
    print(f"Max prediction: ${y_nii_test_pred.max():,.0f}")
    print(f"Mean prediction: ${y_nii_test_pred.mean():,.0f}")
    print(f"Actual mean: ${y_nii_test.mean():,.0f}")

    # Validation State 3: Feature Importance
    print("\nVALIDATION STATE 3: Feature Importance (Top 10)")
    feature_importance_nii = model_nii.get_booster().get_score(importance_type='gain')
    importance_sorted_nii = sorted(feature_importance_nii.items(), key=lambda x: x[1], reverse=True)[:10]
    for i, (feature, importance) in enumerate(importance_sorted_nii, 1):
        feature_name = nii_feature_cols[int(feature[1:])] if feature.startswith('f') else feature
        print(f"{i:2d}. {feature_name:35s} {importance:10.0f}")

    # Log to MLflow
    mlflow.log_params(params_nii)
    mlflow.log_metric("train_rmse", train_rmse)
    mlflow.log_metric("test_rmse", test_rmse)
    mlflow.log_metric("train_mape", train_mape)
    mlflow.log_metric("test_mape", test_mape)
    mlflow.log_metric("train_r2", train_r2)
    mlflow.log_metric("test_r2", test_r2)
    mlflow.xgboost.log_model(model_nii, "model", input_example=X_nii_train.head(1))

    run_id_nii = run.info.run_id
    print(f"\n✓ Non-Interest Income model trained successfully!")
    print(f"Run ID: {run_id_nii}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 1.4: Register Non-Interest Income Model

# COMMAND ----------

from mlflow import MlflowClient

client = MlflowClient()
model_name_nii = "cfo_banking_demo.models.non_interest_income_model"
model_uri_nii = f"runs:/{run_id_nii}/model"

model_version_nii = mlflow.register_model(
    model_uri=model_uri_nii,
    name=model_name_nii,
    tags={
        "model_type": "ppnr_non_interest_income",
        "algorithm": "xgboost",
        "training_date": datetime.now().isoformat(),
        "test_mape": f"{test_mape:.4f}",
        "test_r2": f"{test_r2:.4f}"
    }
)

client.set_registered_model_alias(
    name=model_name_nii,
    alias="champion",
    version=model_version_nii.version
)

print(f"✓ Model registered: {model_name_nii}@champion")
print(f"  Version: {model_version_nii.version}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 2: Non-Interest Expense Model

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 2.1: Create Training Dataset for Non-Interest Expense

# COMMAND ----------

# Non-Interest Expense includes:
# - Salaries and benefits
# - Occupancy costs (rent, utilities)
# - Technology expenses
# - Marketing and advertising
# - Professional fees
# - FDIC insurance

sql_query_nie = """
CREATE OR REPLACE TABLE cfo_banking_demo.ml_models.non_interest_expense_training_data AS
WITH deposit_summary AS (
    -- Aggregate deposits first to avoid Cartesian product
    SELECT
        DATE_TRUNC('month', effective_date) as month,
        COUNT(DISTINCT account_id) as active_accounts,
        SUM(current_balance) as total_assets_proxy,
        -- Estimated transaction count (historical table doesn't have transaction_count_30d)
        COUNT(DISTINCT account_id) * 25 as total_transactions,
        -- Estimated digital users (80% of active accounts)
        CAST(COUNT(DISTINCT account_id) * 0.8 AS INT) as digital_users,
        COUNT(CASE WHEN account_open_date >= DATE_SUB(CURRENT_DATE(), 30) THEN 1 END) as new_accounts_30d
    FROM cfo_banking_demo.bronze_core_banking.deposit_accounts_historical
    WHERE effective_date >= DATE_SUB(CURRENT_DATE(), 730)
    GROUP BY DATE_TRUNC('month', effective_date)
),
loan_summary AS (
    -- Aggregate loans separately
    SELECT
        DATE_TRUNC('month', effective_date) as month,
        COUNT(DISTINCT loan_id) as loan_count,
        SUM(current_balance) as total_loan_balance,
        COUNT(CASE WHEN days_past_due > 0 THEN 1 END) as delinquent_loans,
        COUNT(CASE WHEN origination_date >= DATE_SUB(CURRENT_DATE(), 30) THEN 1 END) as new_loans_30d
    FROM cfo_banking_demo.bronze_core_banking.loan_portfolio_historical
    WHERE effective_date >= DATE_SUB(CURRENT_DATE(), 730)
    GROUP BY DATE_TRUNC('month', effective_date)
),
monthly_metrics AS (
    -- Join pre-aggregated summaries
    SELECT
        d.month,
        d.active_accounts,
        d.total_assets_proxy,
        d.total_transactions,
        25 as active_branches,  -- Static estimate
        d.digital_users,
        COALESCE(l.loan_count, 0) as loan_count,
        COALESCE(l.total_loan_balance, 0) as total_loan_balance,
        COALESCE(l.delinquent_loans, 0) as delinquent_loans,
        d.new_accounts_30d,
        COALESCE(l.new_loans_30d, 0) as new_loans_30d
    FROM deposit_summary d
    LEFT JOIN loan_summary l ON d.month = l.month
),
market_conditions AS (
    SELECT
        DATE_TRUNC('month', date) as month,
        AVG(rate_10y) as avg_10y_rate
    FROM cfo_banking_demo.silver_treasury.yield_curves
    WHERE date >= DATE_SUB(CURRENT_DATE(), 730)
    GROUP BY DATE_TRUNC('month', date)
),
expense_actual AS (
    -- Actual operating expenses from GL (target variable)
    SELECT
        DATE_TRUNC('month', e.entry_date) as month,
        SUM(CASE
            WHEN l.account_number LIKE '61%' THEN l.debit_amount  -- Personnel costs
            WHEN l.account_number LIKE '62%' THEN l.debit_amount  -- Occupancy
            WHEN l.account_number LIKE '63%' THEN l.debit_amount  -- Technology
            WHEN l.account_number LIKE '64%' THEN l.debit_amount  -- Marketing
            WHEN l.account_number LIKE '65%' THEN l.debit_amount  -- Professional fees
            WHEN l.account_number LIKE '66%' THEN l.debit_amount  -- Other operating
            ELSE 0
        END) as total_operating_expense,

        SUM(CASE WHEN l.account_number LIKE '61%' THEN l.debit_amount ELSE 0 END) as personnel_expense,
        SUM(CASE WHEN l.account_number LIKE '62%' THEN l.debit_amount ELSE 0 END) as occupancy_expense,
        SUM(CASE WHEN l.account_number LIKE '63%' THEN l.debit_amount ELSE 0 END) as technology_expense

    FROM cfo_banking_demo.silver_finance.gl_entry_lines l
    JOIN cfo_banking_demo.silver_finance.gl_entries e ON l.entry_id = e.entry_id
    WHERE e.entry_date >= DATE_SUB(CURRENT_DATE(), 730)
    AND l.account_number LIKE '6%'  -- Expense accounts
    GROUP BY DATE_TRUNC('month', e.entry_date)
)
SELECT
    m.month,

    -- Target variable
    COALESCE(e.total_operating_expense, 125000000) as target_operating_expense,

    -- Business volume features
    m.active_accounts,
    m.total_assets_proxy / 1e9 as total_assets_billions,
    m.total_transactions / 1000000.0 as total_transactions_millions,
    m.active_branches,
    m.digital_users,
    m.loan_count,
    m.total_loan_balance / 1e9 as total_loan_balance_billions,
    m.delinquent_loans,
    m.new_accounts_30d,
    m.new_loans_30d,

    -- Efficiency ratios
    m.digital_users / NULLIF(m.active_accounts, 0) as digital_adoption_rate,
    m.total_transactions / NULLIF(m.active_accounts, 0) as transactions_per_account,
    m.delinquent_loans / NULLIF(m.loan_count, 0) as delinquency_rate,

    -- Market conditions
    mc.avg_10y_rate,

    -- Time features
    MONTH(m.month) as month_of_year,
    QUARTER(m.month) as quarter,
    YEAR(m.month) as year,

    -- Lagged features
    LAG(COALESCE(e.total_operating_expense, 125000000), 1) OVER (ORDER BY m.month) as prior_month_expense,
    LAG(m.active_accounts, 1) OVER (ORDER BY m.month) as prior_month_accounts

FROM monthly_metrics m
LEFT JOIN market_conditions mc ON m.month = mc.month
LEFT JOIN expense_actual e ON m.month = e.month
WHERE m.month IS NOT NULL
ORDER BY m.month
"""

spark.sql(sql_query_nie)
print("✓ Created Non-Interest Expense training dataset")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 2.2: Train Non-Interest Expense Model

# COMMAND ----------

# Load training data
nie_training_df = spark.table("cfo_banking_demo.ml_models.non_interest_expense_training_data")
nie_training_pdf = nie_training_df.toPandas()

print(f"Non-Interest Expense training data: {len(nie_training_pdf):,} months")
print(f"\nTarget variable statistics:")
print(nie_training_pdf['target_operating_expense'].describe())

# Define features
nie_feature_cols = [
    'active_accounts', 'total_assets_billions', 'total_transactions_millions',
    'active_branches', 'digital_users', 'loan_count', 'total_loan_balance_billions',
    'delinquent_loans', 'new_accounts_30d', 'new_loans_30d', 'digital_adoption_rate',
    'transactions_per_account', 'delinquency_rate', 'avg_10y_rate',
    'month_of_year', 'quarter', 'prior_month_expense', 'prior_month_accounts'
]

X_nie = nie_training_pdf[nie_feature_cols].fillna(0)
y_nie = nie_training_pdf['target_operating_expense']

# Convert to float
X_nie = X_nie.astype(float)
y_nie = y_nie.astype(float)

# Train/test split (time-based)
split_idx = int(len(X_nie) * 0.8)
X_nie_train, X_nie_test = X_nie[:split_idx], X_nie[split_idx:]
y_nie_train, y_nie_test = y_nie[:split_idx], y_nie[split_idx:]

print(f"\nTraining set: {len(X_nie_train)} months")
print(f"Test set: {len(X_nie_test)} months (most recent)")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 2.3: Train and Validate Non-Interest Expense Model

# COMMAND ----------

mlflow.set_experiment("/Users/pravin.varma@databricks.com/ppnr_non_interest_expense")

with mlflow.start_run(run_name="non_interest_expense_xgboost") as run:
    # Model parameters
    params_nie = {
        'max_depth': 5,
        'learning_rate': 0.05,
        'n_estimators': 150,
        'objective': 'reg:squarederror',
        'random_state': 42
    }

    # Train model
    model_nie = xgb.XGBRegressor(**params_nie)
    model_nie.fit(X_nie_train, y_nie_train)

    # Predictions
    y_nie_train_pred = model_nie.predict(X_nie_train)
    y_nie_test_pred = model_nie.predict(X_nie_test)

    # Validation State 1: Train vs Test
    train_rmse = mean_squared_error(y_nie_train, y_nie_train_pred, squared=False)
    test_rmse = mean_squared_error(y_nie_test, y_nie_test_pred, squared=False)
    train_mape = mean_absolute_percentage_error(y_nie_train, y_nie_train_pred)
    test_mape = mean_absolute_percentage_error(y_nie_test, y_nie_test_pred)
    train_r2 = r2_score(y_nie_train, y_nie_train_pred)
    test_r2 = r2_score(y_nie_test, y_nie_test_pred)

    print("=" * 80)
    print("NON-INTEREST EXPENSE MODEL VALIDATION")
    print("=" * 80)
    print("\nVALIDATION STATE 1: Train vs Test Performance")
    print(f"Training RMSE: ${train_rmse:,.0f}")
    print(f"Test RMSE:     ${test_rmse:,.0f}")
    print(f"Training MAPE: {train_mape:.2%}")
    print(f"Test MAPE:     {test_mape:.2%}  {'✓' if test_mape < 0.10 else '⚠️'}")
    print(f"Training R²:   {train_r2:.4f}")
    print(f"Test R²:       {test_r2:.4f}")

    # Validation State 2: Prediction Range
    print("\nVALIDATION STATE 2: Prediction Range")
    print(f"Min prediction: ${y_nie_test_pred.min():,.0f}")
    print(f"Max prediction: ${y_nie_test_pred.max():,.0f}")
    print(f"Mean prediction: ${y_nie_test_pred.mean():,.0f}")
    print(f"Actual mean: ${y_nie_test.mean():,.0f}")

    # Validation State 3: Feature Importance
    print("\nVALIDATION STATE 3: Feature Importance (Top 10)")
    feature_importance_nie = model_nie.get_booster().get_score(importance_type='gain')
    importance_sorted_nie = sorted(feature_importance_nie.items(), key=lambda x: x[1], reverse=True)[:10]
    for i, (feature, importance) in enumerate(importance_sorted_nie, 1):
        feature_name = nie_feature_cols[int(feature[1:])] if feature.startswith('f') else feature
        print(f"{i:2d}. {feature_name:35s} {importance:10.0f}")

    # Log to MLflow
    mlflow.log_params(params_nie)
    mlflow.log_metric("train_rmse", train_rmse)
    mlflow.log_metric("test_rmse", test_rmse)
    mlflow.log_metric("train_mape", train_mape)
    mlflow.log_metric("test_mape", test_mape)
    mlflow.log_metric("train_r2", train_r2)
    mlflow.log_metric("test_r2", test_r2)
    mlflow.xgboost.log_model(model_nie, "model", input_example=X_nie_train.head(1))

    run_id_nie = run.info.run_id
    print(f"\n✓ Non-Interest Expense model trained successfully!")
    print(f"Run ID: {run_id_nie}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 2.4: Register Non-Interest Expense Model

# COMMAND ----------

model_name_nie = "cfo_banking_demo.models.non_interest_expense_model"
model_uri_nie = f"runs:/{run_id_nie}/model"

model_version_nie = mlflow.register_model(
    model_uri=model_uri_nie,
    name=model_name_nie,
    tags={
        "model_type": "ppnr_non_interest_expense",
        "algorithm": "xgboost",
        "training_date": datetime.now().isoformat(),
        "test_mape": f"{test_mape:.4f}",
        "test_r2": f"{test_r2:.4f}"
    }
)

client.set_registered_model_alias(
    name=model_name_nie,
    alias="champion",
    version=model_version_nie.version
)

print(f"✓ Model registered: {model_name_nie}@champion")
print(f"  Version: {model_version_nie.version}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 3: PPNR Forecasting (Combined)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 3.1: Generate PPNR Forecasts

# COMMAND ----------

# Load both models for PPNR calculation
mlflow.set_registry_uri("databricks-uc")

model_nii_loaded = mlflow.xgboost.load_model(f"models:/{model_name_nii}@champion")
model_nie_loaded = mlflow.xgboost.load_model(f"models:/{model_name_nie}@champion")

# Use test set for demonstration
nii_forecast = model_nii_loaded.predict(X_nii_test)
nie_forecast = model_nie_loaded.predict(X_nie_test)

# Calculate PPNR (simplified: NII not modeled here, using placeholder)
# In full implementation: PPNR = Net Interest Income + Non-Interest Income - Non-Interest Expense
net_interest_income_placeholder = 250_000_000  # Monthly NII from separate model

ppnr_forecast = net_interest_income_placeholder + nii_forecast - nie_forecast

# Create forecast table
forecast_results = pd.DataFrame({
    'month': nie_training_pdf['month'].iloc[split_idx:].values,
    'net_interest_income': net_interest_income_placeholder,
    'non_interest_income': nii_forecast,
    'non_interest_expense': nie_forecast,
    'ppnr': ppnr_forecast,
    'actual_nii': nii_training_pdf['target_fee_income'].iloc[split_idx:].values,
    'actual_nie': nie_training_pdf['target_operating_expense'].iloc[split_idx:].values
})

print("=" * 80)
print("PPNR FORECAST SUMMARY (Test Period)")
print("=" * 80)
print(f"\nAverage Monthly PPNR: ${ppnr_forecast.mean():,.0f}")
print(f"Min Monthly PPNR:     ${ppnr_forecast.min():,.0f}")
print(f"Max Monthly PPNR:     ${ppnr_forecast.max():,.0f}")
print(f"\nAnnualized PPNR:      ${ppnr_forecast.mean() * 12:,.0f}")

print("\n" + "=" * 80)
print("Forecast vs Actual Comparison")
print("=" * 80)
display(forecast_results)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 3.2: Save PPNR Forecasts

# COMMAND ----------

# Convert to Spark DataFrame and save
forecast_spark_df = spark.createDataFrame(forecast_results)

forecast_spark_df.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable("cfo_banking_demo.ml_models.ppnr_forecasts")

print(f"✓ PPNR forecasts saved to: cfo_banking_demo.ml_models.ppnr_forecasts")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC **Models Trained:**
# MAGIC 1. ✅ **Non-Interest Income Model**
# MAGIC    - Model: `cfo_banking_demo.models.non_interest_income_model@champion`
# MAGIC    - Predicts: Monthly fee income based on business volume
# MAGIC    - Use: Stress testing, financial planning
# MAGIC
# MAGIC 2. ✅ **Non-Interest Expense Model**
# MAGIC    - Model: `cfo_banking_demo.models.non_interest_expense_model@champion`
# MAGIC    - Predicts: Monthly operating expenses based on scale
# MAGIC    - Use: Budgeting, cost forecasting
# MAGIC
# MAGIC 3. ✅ **PPNR Forecast**
# MAGIC    - Table: `cfo_banking_demo.ml_models.ppnr_forecasts`
# MAGIC    - Formula: NII + Non-Interest Income - Non-Interest Expense
# MAGIC    - Use: CCAR/DFAST stress testing, strategic planning
# MAGIC
# MAGIC **Key Drivers:**
# MAGIC - **Non-Interest Income:** Transaction volume, account count, loan originations
# MAGIC - **Non-Interest Expense:** Business scale (accounts, branches), digital adoption
# MAGIC
# MAGIC **Next Steps:**
# MAGIC 1. Schedule as monthly batch jobs
# MAGIC 2. Integrate with stress testing scenarios
# MAGIC 3. Feed into capital planning models
# MAGIC 4. Create PPNR dashboard for executive reporting
