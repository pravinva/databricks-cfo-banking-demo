from databricks import sql
import os

connection = sql.connect(
    server_hostname="e2-demo-field-eng.cloud.databricks.com",
    http_path="/sql/1.0/warehouses/4b9b953939869799",
    access_token=os.environ.get('DATABRICKS_TOKEN')
)

cursor = connection.cursor()

endpoints = [
    ("deposit-beta-metrics", """
        SELECT
            COUNT(*) as total_accounts,
            SUM(balance_millions * 1000000) as total_balance,
            AVG(target_beta) as avg_beta
        FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
        WHERE effective_date = (SELECT MAX(effective_date) FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced)
    """),
    ("component-decay-metrics", """
        SELECT
            relationship_category,
            AVG(lambda_closure_rate) as closure_rate,
            AVG(g_abgr) as abgr
        FROM cfo_banking_demo.ml_models.component_decay_metrics
        GROUP BY relationship_category
    """),
    ("cohort-survival", """
        SELECT
            relationship_category,
            months_since_open,
            AVG(account_survival_rate) as survival_rate
        FROM cfo_banking_demo.ml_models.cohort_survival_rates
        WHERE months_since_open <= 36
        GROUP BY relationship_category, months_since_open
        ORDER BY relationship_category, months_since_open
    """),
    ("runoff-forecasts", """
        SELECT
            relationship_category,
            CAST(months_ahead / 12 AS INT) as year,
            projected_balance_billions
        FROM cfo_banking_demo.ml_models.deposit_runoff_forecasts
        WHERE months_ahead IN (12, 24, 36)
    """)
]

print("Testing updated API queries:\n")
for name, query in endpoints:
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        print(f"✓ {name}: {len(rows)} rows")
        if len(rows) > 0 and len(rows) <= 3:
            print(f"  Sample: {rows[0]}")
    except Exception as e:
        print(f"✗ {name}: ERROR - {str(e)[:100]}")

cursor.close()
connection.close()
