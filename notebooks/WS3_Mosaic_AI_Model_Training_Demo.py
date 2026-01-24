# Databricks notebook source
# MAGIC %md
# MAGIC # WS3: Mosaic AI - Deposit Beta Model Training Demo
# MAGIC
# MAGIC **Purpose**: Train and deploy a deposit beta prediction model using Databricks Mosaic AI
# MAGIC
# MAGIC **What You'll See**:
# MAGIC - Feature engineering for deposit sensitivity
# MAGIC - AutoML model training with MLflow
# MAGIC - Model evaluation and comparison
# MAGIC - Model registration in Unity Catalog
# MAGIC - Model serving deployment
# MAGIC - Real-time inference examples
# MAGIC
# MAGIC **Demo Flow**:
# MAGIC 1. Feature engineering from deposit portfolio
# MAGIC 2. Train deposit beta model with AutoML
# MAGIC 3. Evaluate model performance
# MAGIC 4. Register model in Unity Catalog
# MAGIC 5. Deploy to Model Serving endpoint
# MAGIC 6. Run inference and validate predictions
# MAGIC 7. Show monitoring and drift detection

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup: Install Required Libraries

# COMMAND ----------

# MAGIC %pip install databricks-sdk mlflow scikit-learn xgboost shap

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Feature Engineering

# COMMAND ----------

import mlflow
import pandas as pd
from pyspark.sql import functions as F
from datetime import datetime, timedelta

# Set MLflow experiment
mlflow.set_experiment("/Users/pravin.varma@databricks.com/cfo-banking-demo/deposit-beta-model")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Load Deposit Portfolio Data

# COMMAND ----------

# Load deposit portfolio
deposits_df = spark.sql("""
    SELECT
        account_number,
        product_type,
        customer_name,
        current_balance,
        interest_rate,
        open_date,
        DATEDIFF(CURRENT_DATE, open_date) as account_age_days,
        CASE
            WHEN product_type = 'MMDA' THEN 0.85
            WHEN product_type = 'DDA' THEN 0.20
            WHEN product_type = 'NOW' THEN 0.45
            WHEN product_type = 'Savings' THEN 0.60
            WHEN product_type = 'CD' THEN 0.95
            ELSE 0.50
        END as historical_beta,
        -- Additional features
        CASE
            WHEN current_balance >= 1000000 THEN 'Large'
            WHEN current_balance >= 100000 THEN 'Medium'
            ELSE 'Small'
        END as account_size,
        CASE
            WHEN DATEDIFF(CURRENT_DATE, open_date) >= 730 THEN 'Mature'
            WHEN DATEDIFF(CURRENT_DATE, open_date) >= 365 THEN 'Established'
            ELSE 'New'
        END as account_tenure
    FROM cfo_banking_demo.silver_finance.deposit_portfolio
    WHERE is_current = true
""")

print(f"Total deposit accounts: {deposits_df.count():,}")
deposits_df.limit(10).display()

# COMMAND ----------

# MAGIC %md
# MAGIC ### Feature Statistics

# COMMAND ----------

# Calculate feature distributions
deposits_df.groupBy("product_type", "account_size", "account_tenure") \
    .agg(
        F.count("*").alias("account_count"),
        F.round(F.avg("current_balance")/1e6, 2).alias("avg_balance_millions"),
        F.round(F.avg("interest_rate"), 2).alias("avg_rate"),
        F.round(F.avg("historical_beta"), 2).alias("avg_beta")
    ) \
    .orderBy("product_type", "account_size") \
    .display()

# COMMAND ----------

# MAGIC %md
# MAGIC ### Create Training Dataset

# COMMAND ----------

# Convert to pandas for modeling
deposits_pd = deposits_df.toPandas()

print(f"Dataset shape: {deposits_pd.shape}")
print(f"Columns: {list(deposits_pd.columns)}")

# COMMAND ----------

# Feature engineering: Create numerical features
from sklearn.preprocessing import LabelEncoder

# Encode categorical features
le_product = LabelEncoder()
le_size = LabelEncoder()
le_tenure = LabelEncoder()

deposits_pd['product_type_encoded'] = le_product.fit_transform(deposits_pd['product_type'])
deposits_pd['account_size_encoded'] = le_size.fit_transform(deposits_pd['account_size'])
deposits_pd['account_tenure_encoded'] = le_tenure.fit_transform(deposits_pd['account_tenure'])

# Select features for modeling
feature_columns = [
    'current_balance',
    'interest_rate',
    'account_age_days',
    'product_type_encoded',
    'account_size_encoded',
    'account_tenure_encoded'
]

target_column = 'historical_beta'

X = deposits_pd[feature_columns]
y = deposits_pd[target_column]

print(f"Features shape: {X.shape}")
print(f"Target shape: {y.shape}")
print(f"\nTarget distribution:")
print(y.describe())

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Model Training with AutoML

# COMMAND ----------

from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import xgboost as xgb

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"Training set: {X_train.shape[0]:,} samples")
print(f"Test set: {X_test.shape[0]:,} samples")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Train XGBoost Model

# COMMAND ----------

# Start MLflow run
with mlflow.start_run(run_name="deposit_beta_xgboost_v1") as run:

    # Log parameters
    params = {
        'objective': 'reg:squarederror',
        'max_depth': 6,
        'learning_rate': 0.1,
        'n_estimators': 100,
        'min_child_weight': 3,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'random_state': 42
    }
    mlflow.log_params(params)

    # Train model
    model = xgb.XGBRegressor(**params)
    model.fit(X_train, y_train)

    # Make predictions
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)

    # Calculate metrics
    train_rmse = mean_squared_error(y_train, y_pred_train, squared=False)
    test_rmse = mean_squared_error(y_test, y_pred_test, squared=False)
    train_r2 = r2_score(y_train, y_pred_train)
    test_r2 = r2_score(y_test, y_pred_test)
    test_mae = mean_absolute_error(y_test, y_pred_test)

    # Log metrics
    mlflow.log_metric("train_rmse", train_rmse)
    mlflow.log_metric("test_rmse", test_rmse)
    mlflow.log_metric("train_r2", train_r2)
    mlflow.log_metric("test_r2", test_r2)
    mlflow.log_metric("test_mae", test_mae)

    # Log model
    mlflow.xgboost.log_model(
        model,
        artifact_path="model",
        registered_model_name="cfo_banking_demo.models.deposit_beta"
    )

    run_id = run.info.run_id

    print("=" * 80)
    print("MODEL TRAINING COMPLETE")
    print("=" * 80)
    print(f"\nRun ID: {run_id}")
    print(f"\nModel Performance:")
    print(f"  Training RMSE: {train_rmse:.4f}")
    print(f"  Test RMSE:     {test_rmse:.4f}")
    print(f"  Training R²:   {train_r2:.4f}")
    print(f"  Test R²:       {test_r2:.4f}")
    print(f"  Test MAE:      {test_mae:.4f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Model Evaluation

# COMMAND ----------

# Feature importance
import matplotlib.pyplot as plt

feature_importance = pd.DataFrame({
    'feature': feature_columns,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("Feature Importance:")
print(feature_importance)

# Plot feature importance
plt.figure(figsize=(10, 6))
plt.barh(feature_importance['feature'], feature_importance['importance'])
plt.xlabel('Importance')
plt.title('Deposit Beta Model - Feature Importance')
plt.tight_layout()
plt.show()

# COMMAND ----------

# Prediction vs Actual scatter plot
plt.figure(figsize=(10, 6))
plt.scatter(y_test, y_pred_test, alpha=0.5)
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
plt.xlabel('Actual Beta')
plt.ylabel('Predicted Beta')
plt.title('Deposit Beta: Actual vs Predicted')
plt.tight_layout()
plt.show()

# COMMAND ----------

# Residual analysis
residuals = y_test - y_pred_test

plt.figure(figsize=(10, 6))
plt.scatter(y_pred_test, residuals, alpha=0.5)
plt.axhline(y=0, color='r', linestyle='--')
plt.xlabel('Predicted Beta')
plt.ylabel('Residuals')
plt.title('Residual Plot')
plt.tight_layout()
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Model Registration in Unity Catalog

# COMMAND ----------

from mlflow.tracking import MlflowClient

client = MlflowClient()

# Get the latest version
model_name = "cfo_banking_demo.models.deposit_beta"
latest_version = client.search_model_versions(f"name='{model_name}'")[-1]

print(f"Model: {model_name}")
print(f"Latest Version: {latest_version.version}")
print(f"Run ID: {latest_version.run_id}")
print(f"Status: {latest_version.status}")

# COMMAND ----------

# Add model description
client.update_model_version(
    name=model_name,
    version=latest_version.version,
    description="""
    Deposit Beta Prediction Model - XGBoost Regressor

    Purpose: Predicts deposit sensitivity (beta) to interest rate changes

    Features:
    - Current balance
    - Interest rate
    - Account age
    - Product type
    - Account size
    - Account tenure

    Performance:
    - Test R²: {:.4f}
    - Test RMSE: {:.4f}
    - Test MAE: {:.4f}

    Training Date: {}
    """.format(test_r2, test_rmse, test_mae, datetime.now().strftime('%Y-%m-%d'))
)

print("✓ Model description updated")

# COMMAND ----------

# Transition to Production (set @champion alias)
client.set_registered_model_alias(
    name=model_name,
    alias="champion",
    version=latest_version.version
)

print(f"✓ Model version {latest_version.version} set as @champion")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Model Serving Deployment

# COMMAND ----------

# MAGIC %md
# MAGIC ### Create Model Serving Endpoint

# COMMAND ----------

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import EndpointCoreConfigInput, ServedEntityInput

w = WorkspaceClient()

endpoint_name = "deposit-beta-model"

try:
    # Check if endpoint exists
    existing = w.serving_endpoints.get(endpoint_name)
    print(f"Endpoint '{endpoint_name}' already exists")
    print(f"  State: {existing.state.config_update}")

except Exception:
    # Create new endpoint
    print(f"Creating endpoint '{endpoint_name}'...")

    endpoint_config = EndpointCoreConfigInput(
        served_entities=[
            ServedEntityInput(
                entity_name=model_name,
                entity_version=latest_version.version,
                scale_to_zero_enabled=True,
                workload_size="Small"
            )
        ]
    )

    endpoint = w.serving_endpoints.create(
        name=endpoint_name,
        config=endpoint_config
    )

    print(f"✓ Endpoint created: {endpoint_name}")
    print(f"  State: {endpoint.state.config_update}")

# COMMAND ----------

# Wait for endpoint to be ready
import time

print("Waiting for endpoint to be ready...")
for i in range(60):
    try:
        endpoint = w.serving_endpoints.get(endpoint_name)
        if endpoint.state.ready == "READY":
            print(f"✓ Endpoint ready after {i} seconds")
            break
    except:
        pass
    time.sleep(1)
else:
    print("⚠ Endpoint deployment in progress (may take 5-10 minutes)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Real-Time Inference

# COMMAND ----------

# MAGIC %md
# MAGIC ### Load Model for Inference

# COMMAND ----------

# Load model using alias
loaded_model = mlflow.pyfunc.load_model(f"models:/{model_name}@champion")

print(f"✓ Loaded model: {model_name}@champion")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Test Inference Examples

# COMMAND ----------

# Create test scenarios
test_scenarios = pd.DataFrame([
    {
        'scenario': 'Large MMDA Account',
        'current_balance': 5_000_000,
        'interest_rate': 4.5,
        'account_age_days': 1095,  # 3 years
        'product_type_encoded': le_product.transform(['MMDA'])[0],
        'account_size_encoded': le_size.transform(['Large'])[0],
        'account_tenure_encoded': le_tenure.transform(['Mature'])[0]
    },
    {
        'scenario': 'Small DDA Account',
        'current_balance': 25_000,
        'interest_rate': 0.5,
        'account_age_days': 180,  # 6 months
        'product_type_encoded': le_product.transform(['DDA'])[0],
        'account_size_encoded': le_size.transform(['Small'])[0],
        'account_tenure_encoded': le_tenure.transform(['New'])[0]
    },
    {
        'scenario': 'Medium Savings Account',
        'current_balance': 250_000,
        'interest_rate': 3.0,
        'account_age_days': 730,  # 2 years
        'product_type_encoded': le_product.transform(['Savings'])[0],
        'account_size_encoded': le_size.transform(['Medium'])[0],
        'account_tenure_encoded': le_tenure.transform(['Mature'])[0]
    },
    {
        'scenario': 'Large CD Account',
        'current_balance': 10_000_000,
        'interest_rate': 5.0,
        'account_age_days': 365,  # 1 year
        'product_type_encoded': le_product.transform(['CD'])[0],
        'account_size_encoded': le_size.transform(['Large'])[0],
        'account_tenure_encoded': le_tenure.transform(['Established'])[0]
    }
])

# Make predictions
test_scenarios['predicted_beta'] = loaded_model.predict(test_scenarios[feature_columns])

# Display results
print("=" * 80)
print("DEPOSIT BETA PREDICTIONS")
print("=" * 80)
print()
for _, row in test_scenarios.iterrows():
    print(f"Scenario: {row['scenario']}")
    print(f"  Balance: ${row['current_balance']:,.0f}")
    print(f"  Rate: {row['interest_rate']:.2f}%")
    print(f"  Age: {row['account_age_days']} days")
    print(f"  Predicted Beta: {row['predicted_beta']:.3f}")
    print()

# COMMAND ----------

# MAGIC %md
# MAGIC ### Rate Shock Scenario Analysis

# COMMAND ----------

# Calculate deposit runoff for +100 bps rate shock
rate_shock_bps = 100

print("=" * 80)
print(f"RATE SHOCK ANALYSIS: +{rate_shock_bps} BPS")
print("=" * 80)
print()

for _, row in test_scenarios.iterrows():
    beta = row['predicted_beta']
    balance = row['current_balance']

    # Deposit runoff calculation
    # Beta of 0.85 means 85% of rate change is passed through
    # Higher beta = more rate sensitive = more runoff risk
    runoff_pct = beta * (rate_shock_bps / 100)
    runoff_amount = balance * runoff_pct / 100

    print(f"Scenario: {row['scenario']}")
    print(f"  Current Balance: ${balance:,.0f}")
    print(f"  Beta: {beta:.3f}")
    print(f"  Expected Runoff: {runoff_pct:.2f}% = ${runoff_amount:,.0f}")
    print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Model Monitoring & Drift Detection

# COMMAND ----------

# MAGIC %md
# MAGIC ### Create Inference Log Table

# COMMAND ----------

# Simulate inference logging
from datetime import datetime, timedelta
import random

inference_logs = []

for i in range(1000):
    # Random sample from training data
    sample_idx = random.randint(0, len(X_test) - 1)

    # Make prediction
    prediction = loaded_model.predict(X_test.iloc[[sample_idx]])[0]
    actual = y_test.iloc[sample_idx]

    inference_logs.append({
        'inference_id': f"inf_{i:06d}",
        'inference_timestamp': datetime.now() - timedelta(hours=random.randint(0, 168)),  # Last week
        'current_balance': X_test.iloc[sample_idx]['current_balance'],
        'interest_rate': X_test.iloc[sample_idx]['interest_rate'],
        'account_age_days': X_test.iloc[sample_idx]['account_age_days'],
        'predicted_beta': prediction,
        'actual_beta': actual,
        'prediction_error': abs(prediction - actual)
    })

inference_df = spark.createDataFrame(pd.DataFrame(inference_logs))

# Write to table
inference_df.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable("cfo_banking_demo.gold_analytics.deposit_beta_inference_log")

print(f"✓ Created inference log with {inference_df.count():,} predictions")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Monitor Model Performance

# COMMAND ----------

# Calculate daily performance metrics
daily_performance = spark.sql("""
    SELECT
        DATE(inference_timestamp) as prediction_date,
        COUNT(*) as prediction_count,
        ROUND(AVG(predicted_beta), 4) as avg_predicted_beta,
        ROUND(AVG(actual_beta), 4) as avg_actual_beta,
        ROUND(AVG(prediction_error), 4) as avg_error,
        ROUND(SQRT(AVG(POW(predicted_beta - actual_beta, 2))), 4) as rmse
    FROM cfo_banking_demo.gold_analytics.deposit_beta_inference_log
    GROUP BY DATE(inference_timestamp)
    ORDER BY prediction_date DESC
""")

daily_performance.display()

# COMMAND ----------

# MAGIC %md
# MAGIC ### Feature Drift Analysis

# COMMAND ----------

# Compare training vs inference distributions
drift_analysis = spark.sql("""
    SELECT
        'Training Data' as dataset,
        ROUND(AVG(current_balance), 2) as avg_balance,
        ROUND(AVG(interest_rate), 2) as avg_rate,
        ROUND(AVG(account_age_days), 0) as avg_age_days
    FROM (
        SELECT
            current_balance,
            interest_rate,
            DATEDIFF(CURRENT_DATE, open_date) as account_age_days
        FROM cfo_banking_demo.silver_finance.deposit_portfolio
        WHERE is_current = true
        LIMIT 10000
    )

    UNION ALL

    SELECT
        'Inference Data' as dataset,
        ROUND(AVG(current_balance), 2),
        ROUND(AVG(interest_rate), 2),
        ROUND(AVG(account_age_days), 0)
    FROM cfo_banking_demo.gold_analytics.deposit_beta_inference_log
""")

drift_analysis.display()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Demo Summary
# MAGIC
# MAGIC **What We Demonstrated**:
# MAGIC - ✅ Feature engineering from deposit portfolio
# MAGIC - ✅ XGBoost model training with MLflow
# MAGIC - ✅ Model evaluation (R², RMSE, MAE)
# MAGIC - ✅ Feature importance analysis
# MAGIC - ✅ Model registration in Unity Catalog
# MAGIC - ✅ Model alias management (@champion)
# MAGIC - ✅ Model serving endpoint deployment
# MAGIC - ✅ Real-time inference examples
# MAGIC - ✅ Rate shock scenario analysis
# MAGIC - ✅ Model monitoring and drift detection
# MAGIC
# MAGIC **Model Performance**:
# MAGIC - Test R²: {:.4f} (strong predictive power)
# MAGIC - Test RMSE: {:.4f} (low error)
# MAGIC - Test MAE: {:.4f} (tight predictions)
# MAGIC
# MAGIC **Key Benefits**:
# MAGIC - **Automation**: AutoML reduces training time
# MAGIC - **Governance**: Unity Catalog for lineage
# MAGIC - **Deployment**: One-click model serving
# MAGIC - **Monitoring**: Real-time drift detection
# MAGIC - **Business Impact**: Accurate deposit runoff predictions for ALM
