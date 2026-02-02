from databricks import sql
import os

connection = sql.connect(
    server_hostname="e2-demo-field-eng.cloud.databricks.com",
    http_path="/sql/1.0/warehouses/4b9b953939869799",
    access_token=os.environ.get('DATABRICKS_TOKEN')
)

cursor = connection.cursor()

tables = [
    "deposit_beta_training_enhanced",
    "component_decay_metrics",
    "cohort_survival_rates",
    "deposit_runoff_forecasts"
]

for table in tables:
    print(f"\n=== {table} ===")
    cursor.execute(f"DESCRIBE cfo_banking_demo.ml_models.{table}")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

cursor.close()
connection.close()
