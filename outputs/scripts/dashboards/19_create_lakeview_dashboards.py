"""
Create Lakeview Dashboards programmatically using Databricks SDK
Bank CFO Command Center - Executive Analytics
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from databricks.sdk import WorkspaceClient
from databricks.sdk.service import sql
import json

def create_queries(w, warehouse_id):
    """Create all dashboard queries and return their IDs"""

    queries = {}

    # Query 1: KPI Scorecard
    print("\n1. Creating KPI Scorecard query...")
    query_sql = """
    SELECT
        'Total Assets' as metric_name,
        SUM(current_balance)/1e9 as current_value_billions,
        'Loans + Securities' as composition
    FROM cfo_banking_demo.silver_finance.loan_portfolio
    WHERE is_current = true

    UNION ALL

    SELECT
        'Total Deposits',
        SUM(current_balance)/1e9,
        'All Deposit Products'
    FROM cfo_banking_demo.silver_finance.deposit_portfolio
    WHERE is_current = true

    UNION ALL

    SELECT
        'Net Interest Margin',
        AVG(net_interest_margin) * 100,
        'Monthly Average'
    FROM cfo_banking_demo.gold_finance.profitability_metrics

    UNION ALL

    SELECT
        'LCR',
        AVG(lcr_ratio) * 100,
        'Basel III Compliance'
    FROM cfo_banking_demo.gold_finance.liquidity_coverage_ratio
    """

    query = w.queries.create(
        query=sql.CreateQueryRequestQuery(
        query=sql.CreateQueryRequestQuery(
            display_name="CFO Dashboard - KPI Scorecard",
            query_text=query_sql,
            warehouse_id=warehouse_id,
            description="Executive KPI metrics with 30-day trends"
        )
        )
    )
    queries['kpi'] = query.id
    print(f"   ✓ Created query: {query.id}")

    # Query 2: Liquidity Waterfall
    print("\n2. Creating Liquidity Waterfall query...")
    query_sql = """
    SELECT
        'Level 1 HQLA' as component,
        'source' as flow_type,
        SUM(market_value)/1e9 as value_billions,
        1 as sort_order
    FROM cfo_banking_demo.silver_finance.securities
    WHERE security_type IN ('UST', 'Agency MBS')
        AND is_current = true

    UNION ALL

    SELECT
        'Retail Deposit Runoff',
        'outflow',
        SUM(current_balance * 0.03)/1e9,
        2
    FROM cfo_banking_demo.silver_finance.deposit_portfolio
    WHERE product_type IN ('MMDA', 'Savings')
        AND is_current = true

    UNION ALL

    SELECT
        'Wholesale Funding Runoff',
        'outflow',
        SUM(current_balance * 0.25)/1e9,
        3
    FROM cfo_banking_demo.silver_finance.deposit_portfolio
    WHERE product_type IN ('DDA', 'NOW')
        AND is_current = true

    ORDER BY sort_order
    """

    query = w.queries.create(
        query=sql.CreateQueryRequestQuery(
        query=sql.CreateQueryRequestQuery(
            display_name="CFO Dashboard - Liquidity Waterfall",
            query_text=query_sql,
            warehouse_id=warehouse_id,
            description="LCR component breakdown"
        )
        )
    )
    queries['liquidity'] = query.id
    print(f"   ✓ Created query: {query.id}")

    # Query 3: Yield Curve
    print("\n3. Creating Yield Curve query...")
    query_sql = """
    SELECT
        tenor_years,
        yield_rate * 100 as yield_pct,
        observation_date
    FROM cfo_banking_demo.bronze_market.treasury_yields
    WHERE observation_date = (SELECT MAX(observation_date) FROM cfo_banking_demo.bronze_market.treasury_yields)
        AND tenor_years IN (0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30)
    ORDER BY tenor_years
    """

    query = w.queries.create(
        query=sql.CreateQueryRequestQuery(
        display_name="CFO Dashboard - Yield Curve",
        query_text=query_sql,
        warehouse_id=warehouse_id,
        description="Current Treasury yield curve"
        )
    )
    queries['yield_curve'] = query.id
    print(f"   ✓ Created query: {query.id}")

    # Query 4: Portfolio Risk
    print("\n4. Creating Portfolio Risk query...")
    query_sql = """
    SELECT
        security_type,
        COUNT(*) as position_count,
        SUM(market_value)/1e9 as market_value_billions,
        AVG(ytm) * 100 as avg_yield_pct,
        AVG(effective_duration) as avg_duration_years
    FROM cfo_banking_demo.silver_finance.securities
    WHERE is_current = true
    GROUP BY security_type
    ORDER BY market_value_billions DESC
    """

    query = w.queries.create(
        query=sql.CreateQueryRequestQuery(
        display_name="CFO Dashboard - Portfolio Risk",
        query_text=query_sql,
        warehouse_id=warehouse_id,
        description="Asset allocation by security type"
        )
    )
    queries['portfolio'] = query.id
    print(f"   ✓ Created query: {query.id}")

    # Query 5: Deposit Beta
    print("\n5. Creating Deposit Beta query...")
    query_sql = """
    SELECT
        product_type,
        COUNT(*) as account_count,
        SUM(current_balance)/1e9 as balance_billions,
        AVG(interest_rate) * 100 as current_rate_pct,
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

    query = w.queries.create(
        query=sql.CreateQueryRequestQuery(
        display_name="CFO Dashboard - Deposit Beta",
        query_text=query_sql,
        warehouse_id=warehouse_id,
        description="Rate shock sensitivity by product type"
        )
    )
    queries['deposit_beta'] = query.id
    print(f"   ✓ Created query: {query.id}")

    # Query 6: Recent Activity
    print("\n6. Creating Recent Activity query...")
    query_sql = """
    SELECT
        'Loan Origination' as activity_type,
        loan_id as entity_id,
        borrower_name as entity_name,
        product_type,
        origination_date as activity_date,
        current_balance/1e6 as amount_millions,
        'New loan originated' as activity_description
    FROM cfo_banking_demo.silver_finance.loan_portfolio
    WHERE origination_date >= CURRENT_DATE - INTERVAL 30 DAYS
    ORDER BY origination_date DESC
    LIMIT 50
    """

    query = w.queries.create(
        query=sql.CreateQueryRequestQuery(
        display_name="CFO Dashboard - Recent Activity",
        query_text=query_sql,
        warehouse_id=warehouse_id,
        description="Last 30 days of banking operations"
        )
    )
    queries['activity'] = query.id
    print(f"   ✓ Created query: {query.id}")

    # Query 7: Capital Adequacy
    print("\n7. Creating Capital Adequacy query...")
    query_sql = """
    WITH capital_components AS (
        SELECT
            'Common Equity Tier 1 (CET1)' as capital_type,
            SUM(common_stock + retained_earnings - goodwill - intangibles)/1e9 as capital_billions,
            7.0 as regulatory_minimum_pct,
            8.5 as well_capitalized_pct,
            10.5 as target_pct,
            1 as sort_order
        FROM cfo_banking_demo.gold_finance.capital_structure
        WHERE calculation_date = CURRENT_DATE

        UNION ALL

        SELECT
            'Tier 1 Capital',
            SUM(tier1_capital)/1e9,
            8.5,
            10.0,
            12.0,
            2
        FROM cfo_banking_demo.gold_finance.capital_structure
        WHERE calculation_date = CURRENT_DATE

        UNION ALL

        SELECT
            'Total Capital',
            SUM(tier1_capital + tier2_capital)/1e9,
            10.5,
            13.0,
            16.0,
            3
        FROM cfo_banking_demo.gold_finance.capital_structure
        WHERE calculation_date = CURRENT_DATE
    ),
    rwa AS (
        SELECT 25.0 as rwa_billions
    )
    SELECT
        cc.capital_type,
        cc.capital_billions,
        (cc.capital_billions / rwa.rwa_billions) * 100 as actual_ratio_pct,
        cc.regulatory_minimum_pct,
        cc.well_capitalized_pct,
        cc.target_pct
    FROM capital_components cc
    CROSS JOIN rwa
    ORDER BY cc.sort_order
    """

    query = w.queries.create(
        query=sql.CreateQueryRequestQuery(
        display_name="CFO Dashboard - Capital Adequacy",
        query_text=query_sql,
        warehouse_id=warehouse_id,
        description="Basel III capital ratios"
        )
    )
    queries['capital'] = query.id
    print(f"   ✓ Created query: {query.id}")

    # Query 8: NIM Waterfall
    print("\n8. Creating NIM Waterfall query...")
    query_sql = """
    SELECT
        'Loan Interest Income' as component,
        'income' as flow_type,
        SUM(current_balance * interest_rate / 100.0 / 12.0)/1e6 as monthly_amount_millions,
        1 as sort_order
    FROM cfo_banking_demo.silver_finance.loan_portfolio
    WHERE is_current = true

    UNION ALL

    SELECT
        'Deposit Interest Expense',
        'expense',
        -SUM(current_balance * interest_rate / 100.0 / 12.0)/1e6,
        2
    FROM cfo_banking_demo.silver_finance.deposit_portfolio
    WHERE is_current = true

    UNION ALL

    SELECT
        'Fee Income',
        'income',
        SUM(fee_revenue)/1e6,
        3
    FROM cfo_banking_demo.gold_finance.profitability_metrics

    UNION ALL

    SELECT
        'Operating Expenses',
        'expense',
        -SUM(operating_expenses)/1e6,
        4
    FROM cfo_banking_demo.gold_finance.profitability_metrics

    ORDER BY sort_order
    """

    query = w.queries.create(
        query=sql.CreateQueryRequestQuery(
        display_name="CFO Dashboard - NIM Waterfall",
        query_text=query_sql,
        warehouse_id=warehouse_id,
        description="Net interest margin component breakdown"
        )
    )
    queries['nim'] = query.id
    print(f"   ✓ Created query: {query.id}")

    return queries


def create_dashboard(w, warehouse_id, query_ids):
    """Create the Lakeview dashboard with visualizations"""

    print("\n" + "="*80)
    print("Creating Bank CFO Command Center Dashboard...")
    print("="*80)

    # Create dashboard
    dashboard = w.lakeview.create(
        display_name="Bank CFO Command Center",
        warehouse_id=warehouse_id,
        serialized_dashboard=json.dumps({
            "pages": [
                {
                    "name": "Executive Overview",
                    "displayName": "Executive Overview",
                    "layout": []
                }
            ]
        })
    )

    print(f"\n✓ Created dashboard: {dashboard.dashboard_id}")
    print(f"   Display Name: {dashboard.display_name}")
    print(f"   Path: {dashboard.path}")

    return dashboard


def main():
    """Main execution"""
    print("="*80)
    print("WS5: Creating Lakeview Dashboards")
    print("Bank CFO Command Center - Executive Analytics")
    print("="*80)

    # Initialize Databricks client
    w = WorkspaceClient()

    # Get SQL warehouse ID
    warehouses = list(w.warehouses.list())
    if not warehouses:
        print("\n✗ No SQL warehouses found. Please create one first.")
        return 1

    warehouse_id = warehouses[0].id
    print(f"\n✓ Using SQL Warehouse: {warehouse_id}")
    print(f"   Name: {warehouses[0].name}")

    # Create queries
    print("\n" + "="*80)
    print("Creating Dashboard Queries")
    print("="*80)

    query_ids = create_queries(w, warehouse_id)

    # Create dashboard
    dashboard = create_dashboard(w, warehouse_id, query_ids)

    # Summary
    print("\n" + "="*80)
    print("✅ Dashboard Creation Complete!")
    print("="*80)
    print(f"\nDashboard ID: {dashboard.dashboard_id}")
    print(f"Dashboard Path: {dashboard.path}")
    print(f"\nQueries created: {len(query_ids)}")
    for name, qid in query_ids.items():
        print(f"  - {name}: {qid}")

    print("\n📊 Next Steps:")
    print("  1. Open Databricks SQL → Dashboards")
    print(f"  2. Find 'Bank CFO Command Center' dashboard")
    print("  3. Add visualizations using the created queries")
    print("  4. Apply design system colors (navy/cyan/lava)")
    print("  5. Arrange in 12-column grid layout")

    print("\n✨ Reference files:")
    print("  - SQL Queries: outputs/17_dashboard_queries.sql")
    print("  - Chart Configs: outputs/17_plotly_chart_configs.py")
    print("  - Design System: outputs/17_design_system.py")
    print("  - User Guide: outputs/17_LAKEVIEW_DASHBOARD_GUIDE.md")

    return 0


if __name__ == "__main__":
    sys.exit(main())
