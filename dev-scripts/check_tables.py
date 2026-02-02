from databricks import sql
import os

connection = sql.connect(
    server_hostname="e2-demo-field-eng.cloud.databricks.com",
    http_path="/sql/1.0/warehouses/4b9b953939869799",
    access_token=os.environ.get('DATABRICKS_TOKEN')
)

cursor = connection.cursor()

tables = [
    "cfo_banking_demo.ml_models.deposit_beta_training_enhanced",
    "cfo_banking_demo.ml_models.component_decay_metrics",
    "cfo_banking_demo.ml_models.stress_test_results",
    "cfo_banking_demo.ml_models.dynamic_beta_parameters",
    "cfo_banking_demo.ml_models.stress_test_scenario_summary",
    "cfo_banking_demo.ml_models.cohort_survival_analysis",
    "cfo_banking_demo.ml_models.runoff_forecast_3yr"
]

for table in tables:
    try:
        cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
        result = cursor.fetchone()
        print(f"✓ {table.split('.')[-1]}: {result[0]} rows")
    except Exception as e:
        print(f"✗ {table.split('.')[-1]}: ERROR - {str(e)[:100]}")

cursor.close()
connection.close()
