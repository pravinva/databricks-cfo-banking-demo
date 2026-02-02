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
        SELECT COUNT(*) as total_accounts,
               SUM(current_balance) as total_balance,
               AVG(predicted_beta) as avg_beta,
               SUM(CASE WHEN stated_rate < market_rate THEN 1 ELSE 0 END) as at_risk_accounts,
               SUM(CASE WHEN stated_rate < market_rate THEN current_balance ELSE 0 END) as at_risk_balance,
               SUM(CASE WHEN relationship_category = 'Strategic' THEN current_balance ELSE 0 END) / SUM(current_balance) * 100 as strategic_pct,
               SUM(CASE WHEN relationship_category = 'Tactical' THEN current_balance ELSE 0 END) / SUM(current_balance) * 100 as tactical_pct,
               SUM(CASE WHEN relationship_category = 'Expendable' THEN current_balance ELSE 0 END) / SUM(current_balance) * 100 as expendable_pct
        FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
    """),
    ("deposit-beta-distribution", """
        SELECT product_type,
               COUNT(*) as account_count,
               SUM(current_balance) as total_balance,
               AVG(predicted_beta) as avg_beta,
               relationship_category
        FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
        GROUP BY product_type, relationship_category
        ORDER BY total_balance DESC
        LIMIT 20
    """),
    ("component-decay-metrics", """
        SELECT relationship_category,
               closure_rate,
               abgr,
               compound_factor,
               year_1_retention,
               year_2_retention,
               year_3_retention
        FROM cfo_banking_demo.ml_models.component_decay_metrics
        ORDER BY relationship_category
    """),
    ("cohort-survival", """
        SELECT relationship_category,
               months_since_opening,
               avg_survival_rate as survival_rate
        FROM cfo_banking_demo.ml_models.cohort_survival_rates
        WHERE months_since_opening <= 36
        ORDER BY relationship_category, months_since_opening
    """),
    ("runoff-forecasts", """
        SELECT relationship_category,
               year,
               beginning_balance,
               projected_balance,
               runoff_amount,
               cumulative_runoff_pct
        FROM cfo_banking_demo.ml_models.deposit_runoff_forecasts
        ORDER BY relationship_category, year
    """),
    ("dynamic-beta-parameters", """
        SELECT relationship_category,
               beta_min,
               beta_max,
               k_steepness as k,
               R0_inflection as R0
        FROM cfo_banking_demo.ml_models.dynamic_beta_parameters
        ORDER BY relationship_category
    """)
]

print("Testing API endpoint queries:\n")
for name, query in endpoints:
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        print(f"✓ {name}: {len(rows)} rows")
    except Exception as e:
        print(f"✗ {name}: ERROR - {str(e)[:80]}")

cursor.close()
connection.close()
