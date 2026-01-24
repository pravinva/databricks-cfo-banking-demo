"""
============================================================================
WS5: Dashboard Query Validation Script
Test all 8 SQL queries against Unity Catalog
============================================================================
Created: 2026-01-25
Purpose: Validate SQL syntax and data availability for Lakeview dashboards
============================================================================
"""

import sys
import os

# Add outputs directory to path
outputs_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, outputs_dir)

from agent_tools_library import CFOAgentTools
import json
from datetime import datetime

def test_query(agent_tools, query_name, query_sql):
    """
    Test a single SQL query against Unity Catalog

    Args:
        agent_tools: CFOAgentTools instance
        query_name: Human-readable name
        query_sql: SQL query string

    Returns:
        dict with test results
    """
    print(f"\n{'='*80}")
    print(f"Testing: {query_name}")
    print(f"{'='*80}")

    try:
        # Execute query
        result = agent_tools.query_unity_catalog(query_sql)

        if result.get("success"):
            data = result.get("data", [])
            row_count = len(data)

            print(f"✅ SUCCESS")
            print(f"   Rows returned: {row_count}")

            if row_count > 0:
                print(f"   Sample (first row): {data[0]}")

            return {
                "query_name": query_name,
                "status": "success",
                "row_count": row_count,
                "execution_time": result.get("execution_time_ms", 0),
                "sample_data": data[:3] if row_count > 0 else []
            }
        else:
            error_msg = result.get("error", "Unknown error")
            print(f"❌ FAILED")
            print(f"   Error: {error_msg}")

            return {
                "query_name": query_name,
                "status": "failed",
                "error": error_msg
            }

    except Exception as e:
        print(f"❌ EXCEPTION")
        print(f"   Error: {str(e)}")

        return {
            "query_name": query_name,
            "status": "exception",
            "error": str(e)
        }


def main():
    """Run all dashboard query tests"""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║  WS5: Dashboard Query Validation                                           ║
║  Testing 8 sophisticated SQL queries for Lakeview dashboards              ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)

    # Initialize agent tools
    agent_tools = CFOAgentTools()

    # Test queries (simplified versions for validation)
    test_queries = {
        "1. KPI Scorecard - Current Metrics": """
            SELECT
                'Total Assets' as metric_name,
                SUM(current_balance)/1e9 as current_value_billions,
                'Loans + Securities' as composition
            FROM cfo_banking_demo.silver_finance.loan_portfolio
            WHERE is_current = true
        """,

        "2. Liquidity Waterfall - HQLA Level 1": """
            SELECT
                'Level 1 HQLA' as component,
                'source' as flow_type,
                SUM(market_value)/1e9 as value_billions
            FROM cfo_banking_demo.silver_finance.securities
            WHERE security_type IN ('UST', 'Agency MBS')
                AND is_current = true
        """,

        "3. Yield Curve - Latest Snapshot": """
            SELECT
                tenor_years,
                yield_rate * 100 as yield_pct,
                observation_date
            FROM cfo_banking_demo.bronze_market.treasury_yields
            WHERE observation_date = (SELECT MAX(observation_date) FROM cfo_banking_demo.bronze_market.treasury_yields)
                AND tenor_years IN (0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30)
            ORDER BY tenor_years
        """,

        "4. Portfolio Risk Metrics": """
            SELECT
                security_type,
                COUNT(*) as position_count,
                SUM(market_value)/1e9 as market_value_billions,
                AVG(ytm) * 100 as avg_yield_pct,
                AVG(effective_duration) as avg_duration_years
            FROM cfo_banking_demo.silver_finance.securities
            WHERE is_current = true
            GROUP BY security_type
        """,

        "5. Deposit Beta - Product Summary": """
            SELECT
                product_type,
                COUNT(*) as account_count,
                SUM(current_balance)/1e9 as balance_billions,
                AVG(interest_rate) * 100 as current_rate_pct
            FROM cfo_banking_demo.silver_finance.deposit_portfolio
            WHERE is_current = true
            GROUP BY product_type
        """,

        "6. Recent Activity - Loans": """
            SELECT
                'Loan Origination' as activity_type,
                loan_id as entity_id,
                borrower_name as entity_name,
                product_type,
                origination_date as activity_date,
                current_balance/1e6 as amount_millions
            FROM cfo_banking_demo.silver_finance.loan_portfolio
            WHERE origination_date >= CURRENT_DATE - INTERVAL 7 DAYS
            ORDER BY origination_date DESC
            LIMIT 10
        """,

        "7. Capital Adequacy - CET1": """
            SELECT
                'Common Equity Tier 1 (CET1)' as capital_type,
                SUM(common_stock + retained_earnings - goodwill - intangibles)/1e9 as capital_billions,
                7.0 as regulatory_minimum_pct,
                8.5 as well_capitalized_pct
            FROM cfo_banking_demo.gold_finance.capital_structure
            WHERE calculation_date = CURRENT_DATE
        """,

        "8. NIM Components - Loan Interest": """
            SELECT
                'Loan Interest Income' as component,
                'income' as flow_type,
                SUM(current_balance * interest_rate / 100.0 / 12.0)/1e6 as monthly_amount_millions
            FROM cfo_banking_demo.silver_finance.loan_portfolio
            WHERE is_current = true
        """
    }

    # Run tests
    results = []
    for query_name, query_sql in test_queries.items():
        result = test_query(agent_tools, query_name, query_sql)
        results.append(result)

    # Summary report
    print(f"\n\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}\n")

    success_count = sum(1 for r in results if r["status"] == "success")
    failed_count = sum(1 for r in results if r["status"] != "success")

    print(f"Total Queries Tested: {len(results)}")
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {failed_count}")

    print("\n\nDETAILED RESULTS:\n")
    for result in results:
        status_icon = "✅" if result["status"] == "success" else "❌"
        print(f"{status_icon} {result['query_name']}")

        if result["status"] == "success":
            print(f"   Rows: {result['row_count']}, Time: {result.get('execution_time', 0)}ms")
        else:
            print(f"   Error: {result.get('error', 'Unknown')[:100]}")

    # Save results to file
    output_file = "logs/ws5_query_validation.json"
    os.makedirs("logs", exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump({
            "test_date": datetime.now().isoformat(),
            "total_queries": len(results),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results
        }, f, indent=2)

    print(f"\n\n📄 Detailed results saved to: {output_file}")

    # Overall status
    if failed_count == 0:
        print("\n🎉 ALL QUERIES PASSED - Ready for Lakeview dashboard creation!")
        return 0
    else:
        print(f"\n⚠️  {failed_count} QUERIES FAILED - Please review errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
