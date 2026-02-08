#!/usr/bin/env python3
"""
Test all sample Genie Space queries to verify they work correctly.
"""

import subprocess
import json
import sys
from typing import Dict, List, Tuple

# Sample queries to test
QUERIES = {
    "Query #2 - Portfolio Beta Summary": """
        SELECT
            product_type,
            relationship_category,
            COUNT(*) AS account_count,
            ROUND(AVG(balance_millions), 2) AS avg_balance_millions,
            ROUND(AVG(target_beta), 3) AS avg_beta
        FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
        WHERE effective_date = (SELECT MAX(effective_date) FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced)
        GROUP BY product_type, relationship_category
        ORDER BY relationship_category, avg_beta
        LIMIT 5
    """,

    "Query #4 - Cohort Survival Rates": """
        SELECT
            relationship_category,
            months_since_open,
            account_survival_rate,
            balance_survival_rate
        FROM cfo_banking_demo.ml_models.cohort_survival_rates
        WHERE months_since_open IN (12, 24, 36)
        ORDER BY relationship_category, months_since_open
        LIMIT 10
    """,

    "Query #6 - 3-Year Runoff Forecast": """
        SELECT
            relationship_category,
            SUM(CASE WHEN months_ahead = 12 THEN projected_balance_billions ELSE 0 END) AS balance_12m,
            SUM(CASE WHEN months_ahead = 24 THEN projected_balance_billions ELSE 0 END) AS balance_24m,
            SUM(CASE WHEN months_ahead = 36 THEN projected_balance_billions ELSE 0 END) AS balance_36m,
            SUM(current_balance_billions) AS current_balance
        FROM cfo_banking_demo.ml_models.deposit_runoff_forecasts
        GROUP BY relationship_category
        LIMIT 5
    """,

    "Query #7 - Stress Test Summary": """
        SELECT
            scenario_name,
            rate_shock_bps,
            delta_nii_millions,
            eve_cet1_ratio,
            sot_status
        FROM cfo_banking_demo.ml_models.stress_test_results
        ORDER BY rate_shock_bps
        LIMIT 5
    """,

    "Query #8 - Dynamic Beta Parameters": """
        SELECT
            relationship_category,
            beta_min,
            beta_max,
            k_steepness,
            R0_inflection
        FROM cfo_banking_demo.ml_models.dynamic_beta_parameters
        LIMIT 5
    """,

    "Query #9 - LCR Daily Status": """
        SELECT
            calculation_date,
            lcr_ratio,
            total_hqla,
            net_outflows,
            lcr_status
        FROM cfo_banking_demo.gold_regulatory.lcr_daily
        ORDER BY calculation_date DESC
        LIMIT 5
    """,

    "Query #11 - PPNR Forecast": """
        SELECT
            month,
            net_interest_income,
            non_interest_income,
            non_interest_expense,
            ppnr
        FROM cfo_banking_demo.ml_models.ppnr_forecasts
        ORDER BY month DESC
        LIMIT 5
    """,

    "Query #13 - Non-Interest Income Trend": """
        SELECT
            month,
            target_fee_income,
            active_deposit_accounts,
            total_transactions_millions,
            digital_transaction_pct
        FROM cfo_banking_demo.ml_models.non_interest_income_training_data
        ORDER BY month DESC
        LIMIT 5
    """,

    "Query #14 - Efficiency Ratio Analysis": """
        SELECT
            month,
            target_operating_expense,
            active_accounts,
            total_assets_billions,
            digital_adoption_rate
        FROM cfo_banking_demo.ml_models.non_interest_expense_training_data
        ORDER BY month DESC
        LIMIT 5
    """,
}

def execute_query(query: str) -> Tuple[bool, str, List[Dict]]:
    """Execute query via Databricks CLI and return results."""
    try:
        # Clean up query
        query_clean = " ".join(query.split())

        result = subprocess.run(
            ['databricks', 'experimental', 'apps-mcp', 'tools', 'query', query_clean],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            # Try to parse JSON output
            try:
                # Extract JSON array from output
                output = result.stdout.strip()
                if output:
                    # Find JSON array in output
                    start = output.find('[')
                    end = output.rfind(']') + 1
                    if start >= 0 and end > start:
                        json_str = output[start:end]
                        data = json.loads(json_str)
                        return (True, "Success", data)
                return (False, "No data returned", [])
            except json.JSONDecodeError as e:
                return (False, f"JSON parse error: {e}", [])
        else:
            return (False, result.stderr[:200], [])

    except subprocess.TimeoutExpired:
        return (False, "Query timeout (60s)", [])
    except Exception as e:
        return (False, str(e)[:200], [])

def main():
    print("=" * 100)
    print("GENIE SPACE SAMPLE QUERY VALIDATION")
    print("=" * 100)
    print()

    passed = 0
    failed = 0

    for query_name, query_sql in QUERIES.items():
        print(f"Testing: {query_name}")
        print("-" * 100)

        success, message, data = execute_query(query_sql)

        if success:
            print(f"✅ PASSED")
            print(f"   Rows returned: {len(data)}")
            if data:
                print(f"   Sample row: {json.dumps(data[0], indent=6)}")
            passed += 1
        else:
            print(f"❌ FAILED: {message}")
            failed += 1

        print()

    print("=" * 100)
    print(f"SUMMARY: {passed} passed, {failed} failed out of {len(QUERIES)} queries")
    print("=" * 100)

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
