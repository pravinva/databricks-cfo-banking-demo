#!/usr/bin/env python3
"""
Add SQL Expressions to Genie Space: Treasury Modeling - Deposits & Fee Income

This script adds pre-defined SQL expressions (measures, dimensions, filters)
to the Genie Space to improve query generation accuracy.

Based on Databricks Genie API documentation:
- https://docs.databricks.com/aws/en/genie/conversation-api
- https://docs.databricks.com/aws/en/genie/best-practices

SQL expressions are defined in docs/genie-space/VERIFIED_QUERIES.md
"""

import json
import subprocess
import uuid
from typing import Dict, List, Any


# Genie Space Configuration
SPACE_ID = "01f101adda151c09835a99254d4c308c"
SPACE_NAME = "Treasury Modeling - Deposits & Fee Income"
WAREHOUSE_ID = "4b9b953939869799"


def generate_uuid() -> str:
    """Generate 32-character hex ID (UUID without hyphens)"""
    return uuid.uuid4().hex


def create_measure(name: str, sql: str, description: str, synonyms: List[str] = None) -> Dict:
    """
    Create a measure SQL snippet

    Args:
        name: Display name (e.g., "Average Deposit Beta")
        sql: SQL expression (e.g., "ROUND(AVG(target_beta), 3)")
        description: Business description
        synonyms: Alternative names for natural language matching

    Returns:
        SQL snippet dictionary
    """
    return {
        "id": generate_uuid(),
        "name": name,
        "type": "measure",
        "sql": sql,
        "description": description,
        "synonyms": synonyms or []
    }


def create_dimension(name: str, sql: str, description: str, synonyms: List[str] = None) -> Dict:
    """
    Create a dimension SQL snippet

    Args:
        name: Display name (e.g., "Risk Level Category")
        sql: SQL CASE statement or column reference
        description: Business description
        synonyms: Alternative names

    Returns:
        SQL snippet dictionary
    """
    return {
        "id": generate_uuid(),
        "name": name,
        "type": "dimension",
        "sql": sql,
        "description": description,
        "synonyms": synonyms or []
    }


def create_filter(name: str, sql: str, description: str, synonyms: List[str] = None) -> Dict:
    """
    Create a filter SQL snippet

    Args:
        name: Display name (e.g., "Latest Data Only")
        sql: WHERE clause condition
        description: Usage description
        synonyms: Alternative names

    Returns:
        SQL snippet dictionary
    """
    return {
        "id": generate_uuid(),
        "name": name,
        "type": "filter",
        "sql": sql,
        "description": description,
        "synonyms": synonyms or []
    }


def get_sql_expressions() -> List[Dict]:
    """
    Define all SQL expressions for the Treasury Modeling Genie Space

    These expressions are derived from VERIFIED_QUERIES.md and have been
    tested against actual data (January 2026).

    Returns:
        List of SQL snippet dictionaries
    """
    expressions = []

    # =====================================================================
    # MEASURES (Aggregations & Metrics)
    # =====================================================================

    # Basic Aggregations - ✅ VERIFIED
    expressions.append(create_measure(
        name="Total Account Count",
        sql="COUNT(*)",
        description="Total number of deposit accounts. Use for portfolio size analysis.",
        synonyms=["account count", "number of accounts", "total accounts"]
    ))

    expressions.append(create_measure(
        name="Total Balance (Millions)",
        sql="SUM(balance_millions)",
        description="Total deposit balance in millions. Use with deposit_beta_training_enhanced table.",
        synonyms=["total balance", "sum of balances", "total deposits"]
    ))

    expressions.append(create_measure(
        name="Average Deposit Beta",
        sql="ROUND(AVG(target_beta), 3)",
        description="Average deposit beta coefficient (0-1 scale). Higher beta = more rate sensitive. Strategic ~0.35, Tactical ~0.55, Expendable ~0.75.",
        synonyms=["avg beta", "mean beta", "portfolio beta", "average rate sensitivity"]
    ))

    expressions.append(create_measure(
        name="Average Interest Rate",
        sql="ROUND(AVG(stated_rate), 3)",
        description="Average stated interest rate on deposit accounts. Expressed as decimal (0.025 = 2.5%).",
        synonyms=["avg rate", "mean rate", "average stated rate"]
    ))

    # Conditional Aggregations - ✅ VERIFIED
    expressions.append(create_measure(
        name="At-Risk Account Count",
        sql="SUM(CASE WHEN below_competitor_rate = 1 THEN 1 ELSE 0 END)",
        description="Number of accounts priced below market competitive rate (flight risk accounts requiring retention action).",
        synonyms=["at risk count", "flight risk accounts", "below market accounts"]
    ))

    expressions.append(create_measure(
        name="At-Risk Percentage",
        sql="ROUND(SUM(CASE WHEN below_competitor_rate = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)",
        description="Percentage of accounts at risk (priced below market). Test result: 87.0% of portfolio.",
        synonyms=["at risk pct", "flight risk percentage", "at risk %"]
    ))

    expressions.append(create_measure(
        name="Critical Risk Count",
        sql="SUM(CASE WHEN rate_gap < -0.02 THEN 1 ELSE 0 END)",
        description="Number of accounts with rate gap < -2% (critical flight risk requiring immediate action).",
        synonyms=["critical accounts", "severely at risk"]
    ))

    # Financial Calculations
    expressions.append(create_measure(
        name="Balance in Millions",
        sql="current_balance / 1000000",
        description="Convert account balance to millions. Use on deposit_accounts table with current_balance column.",
        synonyms=["balance millions", "balance in MM"]
    ))

    expressions.append(create_measure(
        name="Balance in Billions",
        sql="SUM(current_balance) / 1000000000",
        description="Total balance in billions. Use for aggregated portfolio reporting.",
        synonyms=["balance billions", "balance in B"]
    ))

    expressions.append(create_measure(
        name="Runoff Percentage",
        sql="ROUND((projected_balance_billions - current_balance_billions) / current_balance_billions * 100, 1)",
        description="Projected deposit runoff percentage over forecast period. Use with deposit_runoff_forecasts table.",
        synonyms=["runoff pct", "balance decline %", "attrition rate"]
    ))

    expressions.append(create_measure(
        name="Closure Rate Percentage",
        sql="ROUND((1 - account_survival_rate) * 100, 1)",
        description="Account closure rate percentage. Use with cohort_survival_rates table. Strategic ~15%, Tactical ~40%, Expendable ~60% at 36 months.",
        synonyms=["closure rate", "attrition rate", "account loss rate"]
    ))

    # Treasury/ALM Formulas - ✅ VERIFIED
    expressions.append(create_measure(
        name="Dynamic Beta at Market Rate",
        sql="beta_min + (beta_max - beta_min) / (1 + EXP(-k_steepness * (market_rate - R0_inflection)))",
        description="Calculate deposit beta at specific market rate using sigmoid function. Use with dynamic_beta_parameters table. Formula: β(Rm) = β_min + (β_max - β_min) / [1 + exp(-k*(Rm-R0))].",
        synonyms=["sigmoid beta", "rate-dependent beta", "dynamic beta response"]
    ))

    expressions.append(create_measure(
        name="Efficiency Ratio",
        sql="ROUND(non_interest_expense / (net_interest_income + non_interest_income) * 100, 1)",
        description="Operating efficiency ratio. Formula: Non-Interest Expense / (NII + Non-Interest Income) × 100%. <50% = highly efficient, 50-60% = good, >70% = inefficient. Use with ppnr_forecasts table.",
        synonyms=["efficiency ratio", "expense ratio", "operating efficiency"]
    ))

    expressions.append(create_measure(
        name="LCR Ratio",
        sql="ROUND(total_hqla / net_outflows * 100, 1)",
        description="Liquidity Coverage Ratio per Basel III. Formula: HQLA / Net Cash Outflows × 100%. Must be ≥100% to comply. Use with lcr_daily table.",
        synonyms=["liquidity coverage ratio", "LCR", "Basel III liquidity"]
    ))

    # =====================================================================
    # DIMENSIONS (Grouping/Categorization)
    # =====================================================================

    # Derived Dimensions (CASE Statements) - ✅ VERIFIED
    expressions.append(create_dimension(
        name="Risk Level Category",
        sql="""CASE
            WHEN rate_gap < -0.02 THEN 'Critical'
            WHEN rate_gap < -0.01 THEN 'High Risk'
            WHEN rate_gap < 0 THEN 'Moderate Risk'
            ELSE 'Low Risk'
        END""",
        description="Categorize accounts by rate gap risk level. Critical = rate gap < -2%, High Risk = -2% to -1%, Moderate = -1% to 0%, Low = 0%+.",
        synonyms=["risk category", "risk tier", "risk level"]
    ))

    expressions.append(create_dimension(
        name="Balance Tier",
        sql="""CASE
            WHEN balance_millions < 0.1 THEN 'Small (<$100K)'
            WHEN balance_millions < 1 THEN 'Medium ($100K-$1M)'
            WHEN balance_millions < 10 THEN 'Large ($1M-$10M)'
            ELSE 'Very Large (>$10M)'
        END""",
        description="Categorize accounts by balance size. Small = <$100K, Medium = $100K-$1M, Large = $1M-$10M, Very Large = >$10M.",
        synonyms=["balance category", "account size", "balance bucket"]
    ))

    expressions.append(create_dimension(
        name="Beta Sensitivity Category",
        sql="""CASE
            WHEN target_beta < 0.3 THEN 'Low Sensitivity (Sticky)'
            WHEN target_beta < 0.6 THEN 'Medium Sensitivity'
            ELSE 'High Sensitivity (Elastic)'
        END""",
        description="Categorize accounts by beta sensitivity. Low (<0.3) = sticky deposits, Medium (0.3-0.6) = moderate sensitivity, High (>0.6) = rate chasers.",
        synonyms=["beta category", "rate sensitivity tier", "stickiness level"]
    ))

    expressions.append(create_dimension(
        name="Capital Adequacy Status",
        sql="""CASE
            WHEN eve_cet1_ratio >= 0.105 THEN 'Well Capitalized'
            WHEN eve_cet1_ratio >= 0.07 THEN 'Adequately Capitalized'
            ELSE 'Undercapitalized'
        END""",
        description="Categorize bank capital status per regulatory thresholds. Well Capitalized = CET1 ≥10.5%, Adequately Capitalized = 7-10.5%, Undercapitalized = <7%.",
        synonyms=["capital status", "CET1 category", "capital tier"]
    ))

    expressions.append(create_dimension(
        name="LCR Compliance Status",
        sql="""CASE
            WHEN lcr_ratio >= 120 THEN 'Strong'
            WHEN lcr_ratio >= 100 THEN 'Compliant'
            ELSE 'Below Minimum'
        END""",
        description="Categorize LCR compliance. Strong = ≥120%, Compliant = 100-120%, Below Minimum = <100% (regulatory violation).",
        synonyms=["LCR status", "liquidity status", "LCR compliance"]
    ))

    # =====================================================================
    # FILTERS (WHERE Clause Patterns)
    # =====================================================================

    expressions.append(create_filter(
        name="Latest Data Only",
        sql="effective_date = (SELECT MAX(effective_date) FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced)",
        description="Filter to most recent data snapshot. Use when querying deposit_beta_training_enhanced to avoid duplicates across time periods.",
        synonyms=["most recent", "current data", "latest snapshot"]
    ))

    expressions.append(create_filter(
        name="Active Accounts Only",
        sql="is_current = TRUE AND account_status = 'Active'",
        description="Filter to active deposit accounts (excludes closed and dormant accounts).",
        synonyms=["active only", "open accounts", "current accounts"]
    ))

    expressions.append(create_filter(
        name="Strategic Customers",
        sql="relationship_category = 'Strategic'",
        description="Filter to Strategic relationship category (core banking relationships with low beta ~0.2-0.4).",
        synonyms=["strategic only", "strategic segment"]
    ))

    expressions.append(create_filter(
        name="At-Risk Accounts",
        sql="below_competitor_rate = 1",
        description="Filter to accounts priced below market competitive rate (flight risk requiring retention action).",
        synonyms=["at risk only", "flight risk", "below market"]
    ))

    expressions.append(create_filter(
        name="High Balance Accounts",
        sql="current_balance > 10000000",
        description="Filter to accounts with balance over $10M (very large accounts requiring priority management).",
        synonyms=["high balance", "large accounts", ">$10M"]
    ))

    expressions.append(create_filter(
        name="Below Market Rate",
        sql="rate_gap < 0",
        description="Filter to accounts where stated rate is below market fed funds rate (negative rate gap).",
        synonyms=["below market", "negative rate gap", "underpriced"]
    ))

    return expressions


def create_serialized_space(expressions: List[Dict]) -> Dict:
    """
    Create the serialized_space JSON structure for Genie API

    Args:
        expressions: List of SQL snippet dictionaries

    Returns:
        Complete serialized_space configuration
    """
    # Sort expressions alphabetically by ID (API requirement)
    expressions_sorted = sorted(expressions, key=lambda x: x["id"])

    serialized_space = {
        "version": 2,
        "config": {
            "sample_questions": []
        },
        "data_sources": [
            # Tables are already added to the space, we're just adding SQL expressions
            # The API should preserve existing tables when we update
        ],
        "sql_snippets": {
            "measures": [e for e in expressions_sorted if e["type"] == "measure"],
            "dimensions": [e for e in expressions_sorted if e["type"] == "dimension"],
            "filters": [e for e in expressions_sorted if e["type"] == "filter"]
        },
        "instructions": {
            "text_instructions": """
# CFO Deposit & Stress Modeling - Genie Instructions

You are a specialized AI assistant for CFO and Treasury operations at a banking institution.

## SQL Expressions Available

You have access to pre-defined SQL expressions (measures, dimensions, filters) that represent
common business concepts. Use these expressions whenever possible instead of writing raw SQL.

**Measures** - Aggregations and calculations (e.g., "Average Deposit Beta", "At-Risk Percentage")
**Dimensions** - Categorization and grouping (e.g., "Risk Level Category", "Balance Tier")
**Filters** - Common WHERE clause conditions (e.g., "Latest Data Only", "Strategic Customers")

When users ask questions, map their natural language to the appropriate SQL expressions.

## Important Notes

1. **Always use "Latest Data Only" filter** when querying deposit_beta_training_enhanced unless user specifies a time period
2. **Relationship categories are case-sensitive**: Strategic, Tactical, Expendable
3. **Product types**: MMDA, DDA, NOW, Savings, CD
4. **CCAR scenarios**: Baseline, Adverse, Severely Adverse (exact spelling required)
5. **Balances**: Specify if in millions, billions, or dollars
6. **Rates**: Express as decimals (0.025 = 2.5%)

## Query Guidelines

- Group by relationship_category, product_type, or scenario when comparing segments
- Use SUM() for balances, AVG() for betas and rates, COUNT() for accounts
- Always provide regulatory context (e.g., "CET1 must be ≥7% to pass stress test")
- Highlight risk indicators and suggest actions when appropriate

See full instructions in Genie Space configuration for detailed guidance.
"""
        }
    }

    return serialized_space


def update_genie_space(space_id: str, serialized_space: Dict) -> bool:
    """
    Update Genie Space with SQL expressions using Databricks API

    Args:
        space_id: Genie space ID (32-character hex)
        serialized_space: Complete serialized_space configuration

    Returns:
        True if successful, False otherwise
    """
    # Convert serialized_space to JSON string (API requirement)
    serialized_space_json = json.dumps(serialized_space)

    # Prepare API request payload
    payload = {
        "serialized_space": serialized_space_json
    }

    # Write payload to temp file for databricks cli
    payload_file = "/tmp/genie_space_update.json"
    with open(payload_file, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"\n📝 Updating Genie Space: {SPACE_NAME}")
    print(f"   Space ID: {space_id}")
    print(f"   Measures: {len([e for e in serialized_space['sql_snippets']['measures']])}")
    print(f"   Dimensions: {len([e for e in serialized_space['sql_snippets']['dimensions']])}")
    print(f"   Filters: {len([e for e in serialized_space['sql_snippets']['filters']])}")

    # Execute API call using databricks cli
    try:
        cmd = [
            "databricks", "api", "patch",
            f"/api/2.0/genie/spaces/{space_id}",
            "--json", f"@{payload_file}"
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        print(f"\n✅ Successfully updated Genie Space!")
        print(f"\nResponse: {result.stdout}")

        return True

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Failed to update Genie Space")
        print(f"Error: {e.stderr}")
        return False


def main():
    """Main execution function"""
    print("=" * 70)
    print("Add SQL Expressions to Genie Space")
    print("=" * 70)
    print(f"\nSpace: {SPACE_NAME}")
    print(f"Space ID: {SPACE_ID}")
    print(f"Warehouse ID: {WAREHOUSE_ID}")

    # Generate SQL expressions
    print("\n📊 Generating SQL expressions from VERIFIED_QUERIES.md...")
    expressions = get_sql_expressions()

    measures = [e for e in expressions if e["type"] == "measure"]
    dimensions = [e for e in expressions if e["type"] == "dimension"]
    filters = [e for e in expressions if e["type"] == "filter"]

    print(f"\n   ✅ Generated {len(measures)} measures")
    print(f"   ✅ Generated {len(dimensions)} dimensions")
    print(f"   ✅ Generated {len(filters)} filters")
    print(f"   ✅ Total: {len(expressions)} SQL expressions")

    # Create serialized_space structure
    print("\n🔧 Creating serialized_space JSON structure...")
    serialized_space = create_serialized_space(expressions)

    # Save to file for reference
    output_file = "/tmp/genie_sql_expressions.json"
    with open(output_file, "w") as f:
        json.dump(serialized_space, f, indent=2)
    print(f"   ✅ Saved to {output_file}")

    # Update Genie Space via API
    print("\n🚀 Updating Genie Space via Databricks API...")
    success = update_genie_space(SPACE_ID, serialized_space)

    if success:
        print("\n" + "=" * 70)
        print("✅ COMPLETE - SQL expressions added to Genie Space!")
        print("=" * 70)
        print("\nNext Steps:")
        print("1. Open Genie Space in Databricks UI")
        print("2. Verify SQL expressions appear in the Knowledge Store")
        print("3. Test queries like:")
        print("   - 'What is the average deposit beta?'")
        print("   - 'Show me at-risk accounts by risk level category'")
        print("   - 'What is the LCR ratio status?'")
    else:
        print("\n" + "=" * 70)
        print("❌ FAILED - Could not update Genie Space")
        print("=" * 70)
        print("\nTroubleshooting:")
        print("1. Check Databricks CLI authentication")
        print("2. Verify space_id is correct")
        print("3. Ensure you have edit permissions on the Genie Space")
        print(f"4. Review API payload in {output_file}")


if __name__ == "__main__":
    main()
