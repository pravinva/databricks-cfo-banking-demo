# Databricks notebook source
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
