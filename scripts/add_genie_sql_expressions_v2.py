#!/usr/bin/env python3
"""
Add SQL Expressions to Existing Genie Space Configuration

This script:
1. Fetches current Genie space configuration
2. Adds SQL expressions (measures, dimensions, filters) to sql_snippets
3. Updates the space via PATCH API

Based on actual Genie Space API structure from:
databricks api patch /api/2.0/genie/spaces/{space_id}
"""

import json
import subprocess
import uuid
from typing import Dict, List

# Genie Space Configuration
SPACE_ID = "01f101adda151c09835a99254d4c308c"
SPACE_NAME = "Treasury Modeling - Deposits & Fee Income"


def generate_uuid() -> str:
    """Generate 32-character hex ID (UUID without hyphens)"""
    return uuid.uuid4().hex


def get_current_space_config() -> Dict:
    """Fetch current Genie space configuration"""
    cmd = [
        "databricks", "api", "get",
        f"/api/2.0/genie/spaces/{SPACE_ID}",
        "--output", "json"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    space_data = json.loads(result.stdout)

    # Parse serialized_space JSON string
    serialized_space_str = space_data.get("serialized_space", "{}")
    serialized_space = json.loads(serialized_space_str)

    return serialized_space


def create_sql_snippets() -> Dict:
    """
    Create SQL snippets structure for Genie Space

    Returns dict with three categories: filters, expressions, measures
    """
    snippets = {
        "filters": [],
        "expressions": [],  # Databricks uses "expressions" not "dimensions"
        "measures": []
    }

    # ===================================================================
    # MEASURES (Aggregations)
    # ===================================================================

    snippets["measures"].extend([
        {
            "id": generate_uuid(),
            "alias": "total_account_count",
            "display_name": "Total Account Count",
            "sql": "COUNT(*)",
            "comments": "Total number of deposit accounts. Use for portfolio size analysis.",
            "synonyms": ["account count", "number of accounts", "total accounts"]
        },
        {
            "id": generate_uuid(),
            "alias": "total_balance_millions",
            "display_name": "Total Balance (Millions)",
            "sql": "SUM(balance_millions)",
            "comments": "Total deposit balance in millions. Use with deposit_beta_training_enhanced table.",
            "synonyms": ["total balance", "sum of balances", "total deposits"]
        },
        {
            "id": generate_uuid(),
            "alias": "average_deposit_beta",
            "display_name": "Average Deposit Beta",
            "sql": "ROUND(AVG(target_beta), 3)",
            "comments": "Average deposit beta coefficient (0-1 scale). Higher beta = more rate sensitive. Strategic ~0.35, Tactical ~0.55, Expendable ~0.75.",
            "synonyms": ["avg beta", "mean beta", "portfolio beta", "average rate sensitivity"]
        },
        {
            "id": generate_uuid(),
            "alias": "average_interest_rate",
            "display_name": "Average Interest Rate",
            "sql": "ROUND(AVG(stated_rate), 3)",
            "comments": "Average stated interest rate on deposit accounts. Expressed as decimal (0.025 = 2.5%).",
            "synonyms": ["avg rate", "mean rate", "average stated rate"]
        },
        {
            "id": generate_uuid(),
            "alias": "at_risk_account_count",
            "display_name": "At-Risk Account Count",
            "sql": "SUM(CASE WHEN below_competitor_rate = 1 THEN 1 ELSE 0 END)",
            "comments": "Number of accounts priced below market competitive rate (flight risk accounts requiring retention action).",
            "synonyms": ["at risk count", "flight risk accounts", "below market accounts"]
        },
        {
            "id": generate_uuid(),
            "alias": "at_risk_percentage",
            "display_name": "At-Risk Percentage",
            "sql": "ROUND(SUM(CASE WHEN below_competitor_rate = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)",
            "comments": "Percentage of accounts at risk (priced below market). Test result: 87.0% of portfolio.",
            "synonyms": ["at risk pct", "flight risk percentage", "at risk %"]
        },
        {
            "id": generate_uuid(),
            "alias": "critical_risk_count",
            "display_name": "Critical Risk Count",
            "sql": "SUM(CASE WHEN rate_gap < -0.02 THEN 1 ELSE 0 END)",
            "comments": "Number of accounts with rate gap < -2% (critical flight risk requiring immediate action).",
            "synonyms": ["critical accounts", "severely at risk"]
        },
        {
            "id": generate_uuid(),
            "alias": "balance_in_billions",
            "display_name": "Balance in Billions",
            "sql": "SUM(current_balance) / 1000000000",
            "comments": "Total balance in billions. Use for aggregated portfolio reporting.",
            "synonyms": ["balance billions", "balance in B"]
        },
        {
            "id": generate_uuid(),
            "alias": "runoff_percentage",
            "display_name": "Runoff Percentage",
            "sql": "ROUND((projected_balance_billions - current_balance_billions) / current_balance_billions * 100, 1)",
            "comments": "Projected deposit runoff percentage over forecast period. Use with deposit_runoff_forecasts table.",
            "synonyms": ["runoff pct", "balance decline %", "attrition rate"]
        },
        {
            "id": generate_uuid(),
            "alias": "efficiency_ratio",
            "display_name": "Efficiency Ratio",
            "sql": "ROUND(non_interest_expense / (net_interest_income + non_interest_income) * 100, 1)",
            "comments": "Operating efficiency ratio. Formula: Non-Interest Expense / (NII + Non-Interest Income) × 100%. <50% = highly efficient, 50-60% = good, >70% = inefficient. Use with ppnr_forecasts table.",
            "synonyms": ["efficiency ratio", "expense ratio", "operating efficiency"]
        },
        {
            "id": generate_uuid(),
            "alias": "lcr_ratio",
            "display_name": "LCR Ratio",
            "sql": "ROUND(total_hqla / net_outflows * 100, 1)",
            "comments": "Liquidity Coverage Ratio per Basel III. Formula: HQLA / Net Cash Outflows × 100%. Must be ≥100% to comply. Use with lcr_daily table.",
            "synonyms": ["liquidity coverage ratio", "LCR", "Basel III liquidity"]
        }
    ])

    # ===================================================================
    # EXPRESSIONS (Derived Columns / Dimensions)
    # ===================================================================

    snippets["expressions"].extend([
        {
            "id": generate_uuid(),
            "alias": "risk_level_category",
            "display_name": "Risk Level Category",
            "sql": """CASE
                WHEN rate_gap < -0.02 THEN 'Critical'
                WHEN rate_gap < -0.01 THEN 'High Risk'
                WHEN rate_gap < 0 THEN 'Moderate Risk'
                ELSE 'Low Risk'
            END""",
            "comments": "Categorize accounts by rate gap risk level. Critical = rate gap < -2%, High Risk = -2% to -1%, Moderate = -1% to 0%, Low = 0%+.",
            "synonyms": ["risk category", "risk tier", "risk level"]
        },
        {
            "id": generate_uuid(),
            "alias": "balance_tier",
            "display_name": "Balance Tier",
            "sql": """CASE
                WHEN balance_millions < 0.1 THEN 'Small (<$100K)'
                WHEN balance_millions < 1 THEN 'Medium ($100K-$1M)'
                WHEN balance_millions < 10 THEN 'Large ($1M-$10M)'
                ELSE 'Very Large (>$10M)'
            END""",
            "comments": "Categorize accounts by balance size. Small = <$100K, Medium = $100K-$1M, Large = $1M-$10M, Very Large = >$10M.",
            "synonyms": ["balance category", "account size", "balance bucket"]
        },
        {
            "id": generate_uuid(),
            "alias": "beta_sensitivity_category",
            "display_name": "Beta Sensitivity Category",
            "sql": """CASE
                WHEN target_beta < 0.3 THEN 'Low Sensitivity (Sticky)'
                WHEN target_beta < 0.6 THEN 'Medium Sensitivity'
                ELSE 'High Sensitivity (Elastic)'
            END""",
            "comments": "Categorize accounts by beta sensitivity. Low (<0.3) = sticky deposits, Medium (0.3-0.6) = moderate sensitivity, High (>0.6) = rate chasers.",
            "synonyms": ["beta category", "rate sensitivity tier", "stickiness level"]
        },
        {
            "id": generate_uuid(),
            "alias": "capital_adequacy_status",
            "display_name": "Capital Adequacy Status",
            "sql": """CASE
                WHEN eve_cet1_ratio >= 0.105 THEN 'Well Capitalized'
                WHEN eve_cet1_ratio >= 0.07 THEN 'Adequately Capitalized'
                ELSE 'Undercapitalized'
            END""",
            "comments": "Categorize bank capital status per regulatory thresholds. Well Capitalized = CET1 ≥10.5%, Adequately Capitalized = 7-10.5%, Undercapitalized = <7%.",
            "synonyms": ["capital status", "CET1 category", "capital tier"]
        },
        {
            "id": generate_uuid(),
            "alias": "lcr_compliance_status",
            "display_name": "LCR Compliance Status",
            "sql": """CASE
                WHEN lcr_ratio >= 120 THEN 'Strong'
                WHEN lcr_ratio >= 100 THEN 'Compliant'
                ELSE 'Below Minimum'
            END""",
            "comments": "Categorize LCR compliance. Strong = ≥120%, Compliant = 100-120%, Below Minimum = <100% (regulatory violation).",
            "synonyms": ["LCR status", "liquidity status", "LCR compliance"]
        },
        {
            "id": generate_uuid(),
            "alias": "balance_millions",
            "display_name": "Balance in Millions",
            "sql": "current_balance / 1000000",
            "comments": "Convert account balance to millions. Use on deposit_accounts table with current_balance column.",
            "synonyms": ["balance millions", "balance in MM"]
        }
    ])

    # ===================================================================
    # FILTERS (WHERE Clause Conditions)
    # ===================================================================

    snippets["filters"].extend([
        {
            "id": generate_uuid(),
            "display_name": "Latest Data Only",
            "sql": "effective_date = (SELECT MAX(effective_date) FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced)",
            "comments": "Filter to most recent data snapshot. Use when querying deposit_beta_training_enhanced to avoid duplicates across time periods.",
            "synonyms": ["most recent", "current data", "latest snapshot"]
        },
        {
            "id": generate_uuid(),
            "display_name": "Active Accounts Only",
            "sql": "is_current = TRUE AND account_status = 'Active'",
            "comments": "Filter to active deposit accounts (excludes closed and dormant accounts).",
            "synonyms": ["active only", "open accounts", "current accounts"]
        },
        {
            "id": generate_uuid(),
            "display_name": "Strategic Customers",
            "sql": "relationship_category = 'Strategic'",
            "comments": "Filter to Strategic relationship category (core banking relationships with low beta ~0.2-0.4).",
            "synonyms": ["strategic only", "strategic segment"]
        },
        {
            "id": generate_uuid(),
            "display_name": "At-Risk Accounts",
            "sql": "below_competitor_rate = 1",
            "comments": "Filter to accounts priced below market competitive rate (flight risk requiring retention action).",
            "synonyms": ["at risk only", "flight risk", "below market"]
        },
        {
            "id": generate_uuid(),
            "display_name": "High Balance Accounts",
            "sql": "current_balance > 10000000",
            "comments": "Filter to accounts with balance over $10M (very large accounts requiring priority management).",
            "synonyms": ["high balance", "large accounts", ">$10M"]
        },
        {
            "id": generate_uuid(),
            "display_name": "Below Market Rate",
            "sql": "rate_gap < 0",
            "comments": "Filter to accounts where stated rate is below market fed funds rate (negative rate gap).",
            "synonyms": ["below market", "negative rate gap", "underpriced"]
        }
    ])

    # Sort all by ID (API requirement)
    for category in ["filters", "expressions", "measures"]:
        snippets[category].sort(key=lambda x: x["id"])

    return snippets


def update_space_with_sql_snippets():
    """Main execution: fetch config, add SQL snippets, update space"""

    print("=" * 70)
    print("Add SQL Expressions to Genie Space")
    print("=" * 70)
    print(f"\nSpace: {SPACE_NAME}")
    print(f"Space ID: {SPACE_ID}")

    # Fetch current configuration
    print("\n📥 Fetching current Genie space configuration...")
    current_config = get_current_space_config()
    print(f"   ✅ Current version: {current_config.get('version')}")
    print(f"   ✅ Tables: {len(current_config.get('data_sources', {}).get('tables', []))}")

    # Generate SQL snippets
    print("\n📊 Generating SQL expressions...")
    sql_snippets = create_sql_snippets()
    print(f"   ✅ Measures: {len(sql_snippets['measures'])}")
    print(f"   ✅ Expressions (Dimensions): {len(sql_snippets['expressions'])}")
    print(f"   ✅ Filters: {len(sql_snippets['filters'])}")

    # Add SQL snippets to config (preserve existing)
    current_config["sql_snippets"] = sql_snippets

    # Save updated config
    output_file = "/tmp/genie_space_updated.json"
    with open(output_file, "w") as f:
        json.dump(current_config, f, indent=2)
    print(f"\n   ✅ Saved updated config to {output_file}")

    # Prepare API payload
    payload = {
        "serialized_space": json.dumps(current_config)
    }

    payload_file = "/tmp/genie_update_payload.json"
    with open(payload_file, "w") as f:
        json.dump(payload, f, indent=2)

    # Execute PATCH request
    print("\n🚀 Updating Genie Space via API...")
    try:
        cmd = [
            "databricks", "api", "patch",
            f"/api/2.0/genie/spaces/{SPACE_ID}",
            "--json", f"@{payload_file}"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        print("\n✅ SUCCESS - SQL expressions added to Genie Space!")
        print("\n" + "=" * 70)
        print("NEXT STEPS")
        print("=" * 70)
        print("\n1. Open Genie Space in Databricks UI")
        print("2. Verify SQL expressions in Knowledge Store")
        print("3. Test natural language queries:")
        print("   - 'What is the average deposit beta?'")
        print("   - 'Show me at-risk accounts by risk level category'")
        print("   - 'What is the LCR ratio status?'")
        print("   - 'Show me balance tiers for Strategic customers'")

    except subprocess.CalledProcessError as e:
        print(f"\n❌ FAILED to update Genie Space")
        print(f"\nError: {e.stderr}")
        print(f"\nTroubleshooting:")
        print(f"1. Review payload: {payload_file}")
        print(f"2. Review config: {output_file}")
        print(f"3. Check API permissions")


if __name__ == "__main__":
    update_space_with_sql_snippets()
