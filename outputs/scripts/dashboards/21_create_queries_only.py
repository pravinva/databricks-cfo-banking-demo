"""
Create SQL queries for Bank CFO Command Center
These can be used in Lakeview dashboards
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from databricks.sdk import WorkspaceClient

def create_query(w, warehouse_id, name, sql_text):
    """Create a single query"""
    print(f"\nCreating: {name}")

    try:
        response = w.api_client.do(
            'POST',
            '/api/2.0/preview/sql/queries',
            body={
                'data_source_id': warehouse_id,
                'name': name,
                'query': sql_text
            }
        )
        query_id = response['id']
        print(f"  ✓ Query ID: {query_id}")
        return query_id
    except Exception as e:
        print(f"  ✗ Error: {str(e)[:200]}")
        return None


def main():
    print("="*80)
    print("Creating Bank CFO Command Center Queries")
    print("="*80)

    w = WorkspaceClient()

    warehouses = list(w.warehouses.list())
    if not warehouses:
        print("\n✗ No SQL warehouses found")
        return 1

    warehouse_id = warehouses[0].id
    print(f"\n✓ Using warehouse: {warehouse_id}")

    queries = []

    # Query 1: KPI Scorecard
    queries.append(create_query(w, warehouse_id, "CFO - KPI Scorecard", """
SELECT
    'Total Assets' as metric,
    CONCAT('$', ROUND(SUM(current_balance)/1e9, 1), 'B') as value,
    '+1.8%' as change
FROM cfo_banking_demo.silver_finance.loan_portfolio
WHERE is_current = true

UNION ALL

SELECT 'Total Deposits', CONCAT('$', ROUND(SUM(current_balance)/1e9, 1), 'B'), '-0.5%'
FROM cfo_banking_demo.silver_finance.deposit_portfolio
WHERE is_current = true

UNION ALL

SELECT 'NIM', CONCAT(ROUND(AVG(net_interest_margin) * 100, 2), '%'), '+3 bps'
FROM cfo_banking_demo.gold_finance.profitability_metrics

UNION ALL

SELECT 'LCR', CONCAT(ROUND(AVG(lcr_ratio) * 100, 1), '%'), 'Compliant'
FROM cfo_banking_demo.gold_finance.liquidity_coverage_ratio
"""))

    # Query 2: Yield Curve
    queries.append(create_query(w, warehouse_id, "CFO - Yield Curve", """
SELECT
    tenor_years as maturity_years,
    ROUND(yield_rate * 100, 2) as yield_pct
FROM cfo_banking_demo.bronze_market.treasury_yields
WHERE observation_date = (SELECT MAX(observation_date) FROM cfo_banking_demo.bronze_market.treasury_yields)
ORDER BY tenor_years
"""))

    # Query 3: Portfolio Breakdown
    queries.append(create_query(w, warehouse_id, "CFO - Portfolio Breakdown", """
SELECT
    security_type,
    ROUND(SUM(market_value)/1e9, 2) as value_billions,
    ROUND(AVG(ytm) * 100, 2) as avg_yield_pct,
    ROUND(AVG(effective_duration), 1) as duration_years
FROM cfo_banking_demo.silver_finance.securities
WHERE is_current = true
GROUP BY security_type
ORDER BY value_billions DESC
"""))

    # Query 4: Deposit Beta
    queries.append(create_query(w, warehouse_id, "CFO - Deposit Beta", """
SELECT
    product_type,
    ROUND(SUM(current_balance)/1e9, 1) as balance_billions,
    ROUND(AVG(interest_rate) * 100, 2) as rate_pct,
    CASE product_type
        WHEN 'MMDA' THEN 0.85
        WHEN 'DDA' THEN 0.20
        WHEN 'NOW' THEN 0.45
        WHEN 'Savings' THEN 0.60
        ELSE 0.50
    END as beta
FROM cfo_banking_demo.silver_finance.deposit_portfolio
WHERE is_current = true
GROUP BY product_type
ORDER BY balance_billions DESC
"""))

    # Query 5: Capital Adequacy
    queries.append(create_query(w, warehouse_id, "CFO - Capital Adequacy", """
SELECT
    'CET1' as capital_type,
    ROUND((SUM(common_stock + retained_earnings - goodwill - intangibles)/1e9) / 25.0 * 100, 1) as actual_pct,
    7.0 as minimum_pct,
    8.5 as target_pct
FROM cfo_banking_demo.gold_finance.capital_structure

UNION ALL

SELECT 'Tier 1', ROUND((SUM(tier1_capital)/1e9) / 25.0 * 100, 1), 8.5, 10.0
FROM cfo_banking_demo.gold_finance.capital_structure

UNION ALL

SELECT 'Total Capital', ROUND((SUM(tier1_capital + tier2_capital)/1e9) / 25.0 * 100, 1), 10.5, 13.0
FROM cfo_banking_demo.gold_finance.capital_structure
"""))

    # Query 6: Liquidity Waterfall
    queries.append(create_query(w, warehouse_id, "CFO - Liquidity Waterfall", """
SELECT
    'HQLA Level 1' as component,
    ROUND(SUM(market_value)/1e9, 2) as value_billions,
    'source' as type
FROM cfo_banking_demo.silver_finance.securities
WHERE security_type IN ('UST', 'Agency MBS') AND is_current = true

UNION ALL

SELECT 'Retail Runoff', ROUND(SUM(current_balance * 0.03)/1e9, 2), 'outflow'
FROM cfo_banking_demo.silver_finance.deposit_portfolio
WHERE product_type IN ('MMDA', 'Savings') AND is_current = true

UNION ALL

SELECT 'Wholesale Runoff', ROUND(SUM(current_balance * 0.25)/1e9, 2), 'outflow'
FROM cfo_banking_demo.silver_finance.deposit_portfolio
WHERE product_type IN ('DDA', 'NOW') AND is_current = true
"""))

    # Query 7: Recent Loans
    queries.append(create_query(w, warehouse_id, "CFO - Recent Loan Activity", """
SELECT
    product_type,
    borrower_name,
    origination_date,
    ROUND(current_balance/1e6, 2) as amount_millions,
    ROUND(interest_rate, 2) as rate_pct
FROM cfo_banking_demo.silver_finance.loan_portfolio
WHERE origination_date >= CURRENT_DATE - INTERVAL 30 DAYS
ORDER BY origination_date DESC
LIMIT 50
"""))

    # Query 8: NIM Components
    queries.append(create_query(w, warehouse_id, "CFO - NIM Components", """
SELECT
    'Loan Interest' as component,
    ROUND(SUM(current_balance * interest_rate / 100.0 / 12.0)/1e6, 1) as monthly_millions,
    'income' as type
FROM cfo_banking_demo.silver_finance.loan_portfolio
WHERE is_current = true

UNION ALL

SELECT 'Deposit Interest', -ROUND(SUM(current_balance * interest_rate / 100.0 / 12.0)/1e6, 1), 'expense'
FROM cfo_banking_demo.silver_finance.deposit_portfolio
WHERE is_current = true

UNION ALL

SELECT 'Fees', ROUND(SUM(fee_revenue)/1e6, 1), 'income'
FROM cfo_banking_demo.gold_finance.profitability_metrics

UNION ALL

SELECT 'Operating Costs', -ROUND(SUM(operating_expenses)/1e6, 1), 'expense'
FROM cfo_banking_demo.gold_finance.profitability_metrics
"""))

    created_count = sum(1 for q in queries if q is not None)

    print("\n" + "="*80)
    print(f"✅ Created {created_count}/8 queries successfully!")
    print("="*80)

    print("\n📊 Next steps:")
    print("1. Open Databricks SQL → Queries")
    print("2. Find the queries starting with 'CFO -'")
    print("3. Create a new Lakeview dashboard")
    print("4. Add visualizations from these queries")
    print("5. Apply the design system colors:")
    print("   - Navy: #1B3139")
    print("   - Cyan: #00A8E1")
    print("   - Lava: #FF3621")

    return 0


if __name__ == "__main__":
    sys.exit(main())
