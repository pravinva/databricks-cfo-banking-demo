from databricks import sql
import os

connection = sql.connect(
    server_hostname="e2-demo-field-eng.cloud.databricks.com",
    http_path="/sql/1.0/warehouses/4b9b953939869799",
    access_token=os.environ.get('DATABRICKS_TOKEN')
)

cursor = connection.cursor()

# Check stress_test_results schema and data
print("=== stress_test_results ===")
cursor.execute("DESCRIBE cfo_banking_demo.ml_models.stress_test_results")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

print("\n=== Sample Data ===")
cursor.execute("SELECT * FROM cfo_banking_demo.ml_models.stress_test_results LIMIT 5")
columns = [desc[0] for desc in cursor.description]
print(f"Columns: {', '.join(columns)}")
for row in cursor.fetchall():
    print(f"  {row}")

# Check dynamic_beta_parameters
print("\n=== dynamic_beta_parameters ===")
cursor.execute("DESCRIBE cfo_banking_demo.ml_models.dynamic_beta_parameters")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

print("\n=== Sample Data ===")
cursor.execute("SELECT * FROM cfo_banking_demo.ml_models.dynamic_beta_parameters")
columns = [desc[0] for desc in cursor.description]
print(f"Columns: {', '.join(columns)}")
for row in cursor.fetchall():
    print(f"  {row}")

cursor.close()
connection.close()
