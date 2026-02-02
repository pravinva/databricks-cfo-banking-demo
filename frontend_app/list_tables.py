from databricks import sql
import os

connection = sql.connect(
    server_hostname="e2-demo-field-eng.cloud.databricks.com",
    http_path="/sql/1.0/warehouses/4b9b953939869799",
    access_token=os.environ.get('DATABRICKS_TOKEN')
)

cursor = connection.cursor()
cursor.execute("SHOW TABLES IN cfo_banking_demo.ml_models")
tables = cursor.fetchall()

print("Tables in cfo_banking_demo.ml_models:")
for table in tables:
    print(f"  - {table[1]}")

cursor.close()
connection.close()
