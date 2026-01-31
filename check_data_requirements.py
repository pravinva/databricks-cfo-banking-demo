#!/usr/bin/env python3
"""
Check data requirements for deposit beta modeling notebooks.
Answers: Do we need to add data? Create new tables? Use AlphaVantage API?
"""

import os
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import sql

# Initialize Databricks client
w = WorkspaceClient()
warehouse_id = "8baced1ff014912d"  # Shared endpoint

def execute_query(query: str, description: str):
    """Execute SQL query and return results."""
    print(f"\n{'='*80}")
    print(f"🔍 {description}")
    print(f"{'='*80}")

    try:
        response = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=query,
            catalog="cfo_banking_demo",
            wait_timeout="50s"
        )

        if response.status.state == sql.StatementState.SUCCEEDED:
            if response.result and response.result.data_array:
                # Print column headers
                if response.manifest and response.manifest.schema and response.manifest.schema.columns:
                    headers = [col.name for col in response.manifest.schema.columns]
                    print("\n" + " | ".join(headers))
                    print("-" * 80)

                # Print rows
                for row in response.result.data_array:
                    print(" | ".join(str(val) if val is not None else "NULL" for val in row))

                return response.result.data_array
            else:
                print("✓ Query executed successfully (no results)")
                return []
        else:
            print(f"❌ Query failed: {response.status.error}")
            return None

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

# ============================================================================
# CHECK 1: Existing Tables
# ============================================================================
print("\n" + "="*80)
print("📊 PART 1: EXISTING TABLES INVENTORY")
print("="*80)

execute_query(
    "SHOW TABLES IN cfo_banking_demo.bronze_core_banking",
    "Tables in bronze_core_banking"
)

execute_query(
    "SHOW TABLES IN cfo_banking_demo.silver_treasury",
    "Tables in silver_treasury"
)

execute_query(
    "SHOW TABLES IN cfo_banking_demo.silver_finance",
    "Tables in silver_finance"
)

execute_query(
    "SHOW TABLES IN cfo_banking_demo.gold_finance",
    "Tables in gold_finance"
)

# ============================================================================
# CHECK 2: Yield Curves Data Quality
# ============================================================================
print("\n" + "="*80)
print("📈 PART 2: YIELD CURVES DATA QUALITY")
print("="*80)

execute_query(
    """
    SELECT
        MIN(date) as earliest_date,
        MAX(date) as latest_date,
        COUNT(*) as total_rows,
        COUNT(DISTINCT date) as unique_dates
    FROM cfo_banking_demo.silver_treasury.yield_curves
    """,
    "Yield curves date range and completeness"
)

execute_query(
    "DESCRIBE cfo_banking_demo.silver_treasury.yield_curves",
    "Yield curves table schema"
)

execute_query(
    """
    SELECT
        date,
        fed_funds_rate,
        treasury_3m,
        treasury_2y,
        treasury_10y
    FROM cfo_banking_demo.silver_treasury.yield_curves
    ORDER BY date DESC
    LIMIT 10
    """,
    "Recent yield curves data (last 10 rows)"
)

# ============================================================================
# CHECK 3: Deposit Accounts Data
# ============================================================================
print("\n" + "="*80)
print("💰 PART 3: DEPOSIT ACCOUNTS DATA")
print("="*80)

execute_query(
    """
    SELECT
        MIN(effective_date) as earliest_date,
        MAX(effective_date) as latest_date,
        COUNT(DISTINCT account_id) as unique_accounts,
        COUNT(*) as total_rows
    FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
    WHERE is_current = true
    """,
    "Deposit accounts date range"
)

execute_query(
    """
    SELECT
        product_type,
        COUNT(*) as account_count,
        AVG(current_balance) as avg_balance,
        AVG(beta) as avg_beta
    FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
    WHERE is_current = true
    GROUP BY product_type
    ORDER BY account_count DESC
    """,
    "Deposit accounts by product type"
)

# Check for relationship features
execute_query(
    """
    SELECT
        COUNT(DISTINCT customer_id) as total_customers,
        COUNT(DISTINCT CASE WHEN product_count > 1 THEN customer_id END) as multi_product_customers,
        COUNT(DISTINCT CASE WHEN has_checking = true THEN customer_id END) as checking_customers,
        COUNT(DISTINCT CASE WHEN has_savings = true THEN customer_id END) as savings_customers
    FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
    WHERE is_current = true
    """,
    "Customer relationship data"
)

# ============================================================================
# CHECK 4: General Ledger Data (recently backfilled)
# ============================================================================
print("\n" + "="*80)
print("📒 PART 4: GENERAL LEDGER DATA")
print("="*80)

execute_query(
    """
    SELECT
        MIN(transaction_date) as earliest_date,
        MAX(transaction_date) as latest_date,
        COUNT(*) as total_transactions,
        COUNT(DISTINCT account_number) as unique_accounts,
        SUM(CASE WHEN debit_amount > 0 THEN debit_amount ELSE 0 END) as total_debits,
        SUM(CASE WHEN credit_amount > 0 THEN credit_amount ELSE 0 END) as total_credits
    FROM cfo_banking_demo.silver_finance.general_ledger
    """,
    "General ledger summary"
)

# ============================================================================
# SUMMARY & RECOMMENDATIONS
# ============================================================================
print("\n" + "="*80)
print("📋 PART 5: DATA REQUIREMENTS ANALYSIS")
print("="*80)

print("""
Based on the analysis above, here are the data requirements:

EXISTING TABLES (✓ Already Available):
- bronze_core_banking.deposit_accounts ✓
- bronze_core_banking.loan_portfolio ✓
- silver_treasury.yield_curves ✓
- bronze_core_banking.chart_of_accounts ✓
- silver_finance.general_ledger ✓ (backfilled with 9,216 rows)
- gold_finance.profitability_metrics ✓

NEW TABLES (Created by Notebooks):
Phase 1:
- cfo_banking_demo.ml_models.deposit_beta_training_enhanced
- cfo_banking_demo.ml_models.deposit_beta_predictions_phase1

Phase 2:
- cfo_banking_demo.ml_models.deposit_cohort_analysis
- cfo_banking_demo.ml_models.cohort_survival_rates
- cfo_banking_demo.ml_models.component_decay_metrics
- cfo_banking_demo.ml_models.deposit_beta_training_phase2
- cfo_banking_demo.ml_models.deposit_runoff_forecasts

Phase 3:
- cfo_banking_demo.ml_models.dynamic_beta_parameters
- cfo_banking_demo.ml_models.stress_test_results
- cfo_banking_demo.ml_models.taylor_sensitivity_analysis
- cfo_banking_demo.ml_models.gap_analysis_results

DATA GAPS TO ADDRESS:
""")

# Check if we need competitive rate data
result = execute_query(
    """
    SELECT COUNT(*) as has_competitor_rate
    FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
    WHERE is_current = true
    AND competitor_avg_rate IS NOT NULL
    LIMIT 1
    """,
    "Check if competitor_avg_rate exists"
)

print("\n" + "="*80)
print("🔍 DATA GAP ANALYSIS COMPLETE")
print("="*80)
