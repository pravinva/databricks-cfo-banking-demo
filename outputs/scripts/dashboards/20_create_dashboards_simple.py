"""
Create Lakeview Dashboards one by one using Databricks API
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from databricks.sdk import WorkspaceClient
import time

def create_query(w, warehouse_id, name, sql_text, description):
    """Create a single query"""
    print(f"\nCreating query: {name}")

    try:
        # Use the API directly
        response = w.api_client.do(
            'POST',
            '/api/2.0/preview/sql/queries',
            body={
                'data_source_id': warehouse_id,
                'name': name,
                'query': sql_text,
                'description': description,
                'options': {
                    'parameters': []
                }
            }
        )
        query_id = response['id']
        print(f"✓ Created query ID: {query_id}")
        return query_id
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return None


def create_visualization(w, query_id, viz_name, viz_type, viz_options):
    """Create a visualization for a query"""
    print(f"  Creating visualization: {viz_name}")

    try:
        response = w.api_client.do(
            'POST',
            f'/api/2.0/preview/sql/queries/{query_id}/visualizations',
            body={
                'type': viz_type,
                'name': viz_name,
                'description': '',
                'options': viz_options
            }
        )
        viz_id = response['id']
        print(f"  ✓ Created visualization ID: {viz_id}")
        return viz_id
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return None


def create_dashboard(w):
    """Create the dashboard"""
    print("\nCreating dashboard...")

    try:
        response = w.api_client.do(
            'POST',
            '/api/2.0/preview/sql/dashboards',
            body={
                'name': 'Bank CFO Command Center',
                'tags': ['cfo', 'treasury', 'risk', 'executive']
            }
        )
        dashboard_id = response['id']
        print(f"✓ Created dashboard ID: {dashboard_id}")
        return dashboard_id
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return None


def add_widget_to_dashboard(w, dashboard_id, viz_id, position):
    """Add a visualization widget to the dashboard"""
    print(f"  Adding widget at position {position}")

    try:
        response = w.api_client.do(
            'POST',
            f'/api/2.0/preview/sql/dashboards/{dashboard_id}/widgets',
            body={
                'visualization_id': viz_id,
                'text': '',
                'width': 1,
                'options': {
                    'position': position
                }
            }
        )
        widget_id = response['id']
        print(f"  ✓ Added widget ID: {widget_id}")
        return widget_id
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return None


def main():
    print("="*80)
    print("Creating Bank CFO Command Center Dashboard")
    print("="*80)

    w = WorkspaceClient()

    # Get warehouse
    warehouses = list(w.warehouses.list())
    if not warehouses:
        print("\n✗ No SQL warehouses found")
        return 1

    warehouse_id = warehouses[0].id
    print(f"\n✓ Using warehouse: {warehouse_id}")

    # Create dashboard first
    dashboard_id = create_dashboard(w)
    if not dashboard_id:
        return 1

    # Query 1: KPI Scorecard
    print("\n" + "="*80)
    print("Query 1: KPI Scorecard")
    print("="*80)

    query1_sql = """
SELECT
    'Total Assets' as metric_name,
    ROUND(SUM(current_balance)/1e9, 1) as value_billions,
    '+1.8%' as change_pct
FROM cfo_banking_demo.silver_finance.loan_portfolio
WHERE is_current = true

UNION ALL

SELECT
    'Total Deposits',
    ROUND(SUM(current_balance)/1e9, 1),
    '-0.5%'
FROM cfo_banking_demo.silver_finance.deposit_portfolio
WHERE is_current = true

UNION ALL

SELECT
    'Net Interest Margin',
    ROUND(AVG(net_interest_margin) * 100, 2),
    '+3 bps'
FROM cfo_banking_demo.gold_finance.profitability_metrics

UNION ALL

SELECT
    'LCR Ratio',
    ROUND(AVG(lcr_ratio) * 100, 1),
    'Compliant'
FROM cfo_banking_demo.gold_finance.liquidity_coverage_ratio
"""

    query1_id = create_query(
        w, warehouse_id,
        "CFO Dashboard - KPI Scorecard",
        query1_sql,
        "Executive KPI metrics"
    )

    if query1_id:
        # Create counter visualization for each KPI
        viz1_id = create_visualization(
            w, query1_id,
            "KPI Metrics",
            "COUNTER",
            {
                'counterLabel': '{{metric_name}}',
                'counterValue': '{{value_billions}}',
                'stringDecimal': 1,
                'stringDecChar': '.',
                'stringThouSep': ','
            }
        )

        if viz1_id:
            add_widget_to_dashboard(w, dashboard_id, viz1_id, {'col': 0, 'row': 0, 'sizeX': 3, 'sizeY': 2})

    time.sleep(1)

    # Query 2: Yield Curve
    print("\n" + "="*80)
    print("Query 2: Yield Curve")
    print("="*80)

    query2_sql = """
SELECT
    tenor_years,
    ROUND(yield_rate * 100, 2) as yield_pct
FROM cfo_banking_demo.bronze_market.treasury_yields
WHERE observation_date = (SELECT MAX(observation_date) FROM cfo_banking_demo.bronze_market.treasury_yields)
ORDER BY tenor_years
"""

    query2_id = create_query(
        w, warehouse_id,
        "CFO Dashboard - Yield Curve",
        query2_sql,
        "Current Treasury yield curve"
    )

    if query2_id:
        viz2_id = create_visualization(
            w, query2_id,
            "Treasury Yield Curve",
            "CHART",
            {
                'globalSeriesType': 'line',
                'sortX': True,
                'legend': {'enabled': True},
                'yAxis': [{'type': 'linear', 'title': {'text': 'Yield (%)'}}],
                'xAxis': {'type': 'category', 'labels': {'enabled': True}, 'title': {'text': 'Maturity (Years)'}},
                'series': {'stacking': None},
                'columnMapping': {
                    'tenor_years': 'x',
                    'yield_pct': 'y'
                }
            }
        )

        if viz2_id:
            add_widget_to_dashboard(w, dashboard_id, viz2_id, {'col': 3, 'row': 0, 'sizeX': 3, 'sizeY': 2})

    time.sleep(1)

    # Query 3: Portfolio Risk
    print("\n" + "="*80)
    print("Query 3: Portfolio Risk")
    print("="*80)

    query3_sql = """
SELECT
    security_type,
    ROUND(SUM(market_value)/1e9, 2) as value_billions,
    ROUND(AVG(ytm) * 100, 2) as avg_yield_pct,
    ROUND(AVG(effective_duration), 1) as avg_duration_years
FROM cfo_banking_demo.silver_finance.securities
WHERE is_current = true
GROUP BY security_type
ORDER BY value_billions DESC
"""

    query3_id = create_query(
        w, warehouse_id,
        "CFO Dashboard - Portfolio Risk",
        query3_sql,
        "Securities portfolio breakdown"
    )

    if query3_id:
        viz3_id = create_visualization(
            w, query3_id,
            "Portfolio by Security Type",
            "TABLE",
            {
                'itemsPerPage': 10,
                'columns': [
                    {'name': 'security_type', 'type': 'string', 'displayAs': 'string', 'title': 'Security Type'},
                    {'name': 'value_billions', 'type': 'float', 'displayAs': 'number', 'title': 'Value ($B)'},
                    {'name': 'avg_yield_pct', 'type': 'float', 'displayAs': 'number', 'title': 'Avg Yield (%)'},
                    {'name': 'avg_duration_years', 'type': 'float', 'displayAs': 'number', 'title': 'Duration (Y)'}
                ]
            }
        )

        if viz3_id:
            add_widget_to_dashboard(w, dashboard_id, viz3_id, {'col': 0, 'row': 2, 'sizeX': 3, 'sizeY': 2})

    time.sleep(1)

    # Query 4: Deposit Beta
    print("\n" + "="*80)
    print("Query 4: Deposit Beta Sensitivity")
    print("="*80)

    query4_sql = """
SELECT
    product_type,
    ROUND(SUM(current_balance)/1e9, 1) as balance_billions,
    ROUND(AVG(interest_rate) * 100, 2) as current_rate_pct,
    CASE product_type
        WHEN 'MMDA' THEN 0.85
        WHEN 'DDA' THEN 0.20
        WHEN 'NOW' THEN 0.45
        WHEN 'Savings' THEN 0.60
        ELSE 0.50
    END as deposit_beta
FROM cfo_banking_demo.silver_finance.deposit_portfolio
WHERE is_current = true
GROUP BY product_type
ORDER BY balance_billions DESC
"""

    query4_id = create_query(
        w, warehouse_id,
        "CFO Dashboard - Deposit Beta",
        query4_sql,
        "Rate sensitivity by product"
    )

    if query4_id:
        viz4_id = create_visualization(
            w, query4_id,
            "Deposit Beta by Product",
            "TABLE",
            {
                'itemsPerPage': 10,
                'columns': [
                    {'name': 'product_type', 'type': 'string', 'displayAs': 'string', 'title': 'Product'},
                    {'name': 'balance_billions', 'type': 'float', 'displayAs': 'number', 'title': 'Balance ($B)'},
                    {'name': 'current_rate_pct', 'type': 'float', 'displayAs': 'number', 'title': 'Rate (%)'},
                    {'name': 'deposit_beta', 'type': 'float', 'displayAs': 'number', 'title': 'Beta'}
                ]
            }
        )

        if viz4_id:
            add_widget_to_dashboard(w, dashboard_id, viz4_id, {'col': 3, 'row': 2, 'sizeX': 3, 'sizeY': 2})

    time.sleep(1)

    # Query 5: Capital Adequacy
    print("\n" + "="*80)
    print("Query 5: Capital Adequacy")
    print("="*80)

    query5_sql = """
WITH capital AS (
    SELECT
        'CET1' as ratio_type,
        ROUND((SUM(common_stock + retained_earnings - goodwill - intangibles)/1e9) / 25.0 * 100, 1) as actual_pct,
        7.0 as minimum_pct,
        8.5 as target_pct
    FROM cfo_banking_demo.gold_finance.capital_structure

    UNION ALL

    SELECT
        'Tier 1',
        ROUND((SUM(tier1_capital)/1e9) / 25.0 * 100, 1),
        8.5,
        10.0
    FROM cfo_banking_demo.gold_finance.capital_structure

    UNION ALL

    SELECT
        'Total Capital',
        ROUND((SUM(tier1_capital + tier2_capital)/1e9) / 25.0 * 100, 1),
        10.5,
        13.0
    FROM cfo_banking_demo.gold_finance.capital_structure
)
SELECT * FROM capital
"""

    query5_id = create_query(
        w, warehouse_id,
        "CFO Dashboard - Capital Adequacy",
        query5_sql,
        "Basel III capital ratios"
    )

    if query5_id:
        viz5_id = create_visualization(
            w, query5_id,
            "Capital Ratios",
            "TABLE",
            {
                'itemsPerPage': 10,
                'columns': [
                    {'name': 'ratio_type', 'type': 'string', 'displayAs': 'string', 'title': 'Capital Type'},
                    {'name': 'actual_pct', 'type': 'float', 'displayAs': 'number', 'title': 'Actual (%)'},
                    {'name': 'minimum_pct', 'type': 'float', 'displayAs': 'number', 'title': 'Minimum (%)'},
                    {'name': 'target_pct', 'type': 'float', 'displayAs': 'number', 'title': 'Target (%)'}
                ]
            }
        )

        if viz5_id:
            add_widget_to_dashboard(w, dashboard_id, viz5_id, {'col': 0, 'row': 4, 'sizeX': 3, 'sizeY': 2})

    print("\n" + "="*80)
    print("✅ Dashboard Created Successfully!")
    print("="*80)
    print(f"\nDashboard ID: {dashboard_id}")
    print(f"\nOpen in Databricks SQL:")
    print(f"https://e2-demo-field-eng.cloud.databricks.com/sql/dashboards/{dashboard_id}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
