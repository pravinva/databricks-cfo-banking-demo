#!/usr/bin/env python3
"""
Script to verify schemas for all Genie Space tables and generate SQL COMMENT statements.

This script:
1. Queries Databricks Unity Catalog for actual table schemas
2. Compares with Genie Space configuration documentation
3. Generates SQL COMMENT statements for tables and columns
4. Outputs results to a file for review and execution
"""

import subprocess
import json
import sys
from typing import Dict, List, Any

# List of all 12 tables in the Genie Space configuration
TABLES = [
    # Phase 1: Deposit Beta Modeling
    "cfo_banking_demo.ml_models.deposit_beta_training_enhanced",
    "cfo_banking_demo.bronze_core_banking.deposit_accounts",

    # Phase 2: Vintage Analysis
    "cfo_banking_demo.ml_models.component_decay_metrics",
    "cfo_banking_demo.ml_models.cohort_survival_rates",
    "cfo_banking_demo.ml_models.deposit_runoff_forecasts",

    # Phase 3: CCAR Stress Testing
    "cfo_banking_demo.ml_models.dynamic_beta_parameters",
    "cfo_banking_demo.ml_models.stress_test_results",
    "cfo_banking_demo.gold_regulatory.lcr_daily",
    "cfo_banking_demo.gold_regulatory.hqla_inventory",

    # PPNR Forecasting
    "cfo_banking_demo.ml_models.ppnr_forecasts",
    "cfo_banking_demo.ml_models.non_interest_income_training_data",
    "cfo_banking_demo.ml_models.non_interest_expense_training_data",
]

# Table-level comments based on Genie Space documentation
TABLE_COMMENTS = {
    "cfo_banking_demo.ml_models.deposit_beta_training_enhanced":
        "Phase 1 Deposit Beta Model - Training dataset with 41 features for XGBoost model achieving 7.2% MAPE accuracy. "
        "Contains rate sensitivity analysis, relationship categorization (Strategic/Tactical/Expendable), and at-risk account identification. "
        "Use for: deposit pricing strategy, rate shock analysis, customer retention, and flight risk assessment.",

    "cfo_banking_demo.bronze_core_banking.deposit_accounts":
        "Bronze layer deposit account master data from core banking system. "
        "Contains current balances, rates, product types, and customer relationships. "
        "Updated daily via CDC. Use for: deposit portfolio analysis, customer segmentation, and balance trend monitoring.",

    "cfo_banking_demo.ml_models.component_decay_metrics":
        "Phase 2 Vintage Analysis - Component-level decay metrics tracking deposit runoff patterns by cohort and product. "
        "Shows month-over-month decay rates, cumulative survival, and half-life calculations. "
        "Use for: liquidity forecasting, deposit stability analysis, and funding cost projections.",

    "cfo_banking_demo.ml_models.cohort_survival_rates":
        "Phase 2 Vintage Analysis - Cohort-based survival rates tracking deposit retention over 36+ months. "
        "Essential for deposit runoff forecasting and liquidity stress testing. "
        "Use for: LCR forecasting, deposit mix optimization, and retention strategy.",

    "cfo_banking_demo.ml_models.deposit_runoff_forecasts":
        "Phase 2 Vintage Analysis - Forward-looking deposit runoff forecasts by cohort and product. "
        "12-month rolling forecasts with confidence intervals. "
        "Use for: cash flow forecasting, liquidity planning, and ALCO reporting.",

    "cfo_banking_demo.ml_models.dynamic_beta_parameters":
        "Phase 3 CCAR Stress Testing - Dynamic deposit beta coefficients under different stress scenarios. "
        "Models non-linear rate sensitivity across Baseline, Adverse, and Severely Adverse scenarios. "
        "Use for: stress testing, CCAR submissions, regulatory capital planning.",

    "cfo_banking_demo.ml_models.stress_test_results":
        "Phase 3 CCAR Stress Testing - Comprehensive deposit balance projections under regulatory stress scenarios. "
        "9-quarter forward projections aligned with Federal Reserve CCAR requirements. "
        "Use for: CCAR/DFAST submissions, capital planning, and regulatory reporting.",

    "cfo_banking_demo.gold_regulatory.lcr_daily":
        "Regulatory LCR (Liquidity Coverage Ratio) calculations per Basel III / 12 CFR Part 249. "
        "Daily HQLA and net cash outflow calculations with regulatory weights. "
        "Use for: daily LCR monitoring, regulatory reporting (FR 2052a), and liquidity risk management.",

    "cfo_banking_demo.gold_regulatory.hqla_inventory":
        "High-Quality Liquid Assets (HQLA) inventory per Basel III classification (Level 1, 2A, 2B). "
        "Daily fair value and haircut adjustments. "
        "Use for: LCR calculations, liquidity buffer management, and ALCO reporting.",

    "cfo_banking_demo.ml_models.ppnr_forecasts":
        "PPNR (Pre-Provision Net Revenue) forecasts by stress scenario. "
        "9-quarter projections of Net Interest Income, Non-Interest Income, Non-Interest Expense, and PPNR. "
        "Includes efficiency ratio calculations. "
        "Use for: CCAR submissions, earnings forecasting, and fee income analysis.",

    "cfo_banking_demo.ml_models.non_interest_income_training_data":
        "Non-interest income training data for PPNR forecasting models. "
        "Historical fee income by source (deposit fees, overdraft, wire transfer, etc.) with deposit relationship drivers. "
        "Use for: fee income modeling, revenue forecasting, and deposit relationship value analysis.",

    "cfo_banking_demo.ml_models.non_interest_expense_training_data":
        "Non-interest expense training data for PPNR forecasting models. "
        "Historical expense data by category (compensation, technology, occupancy, etc.) with efficiency metrics. "
        "Use for: expense forecasting, efficiency ratio analysis, and cost optimization."
}

def get_table_schema(table_name: str) -> Dict[str, Any]:
    """Query Databricks CLI to get table schema."""
    try:
        print(f"Querying schema for {table_name}...", file=sys.stderr)
        result = subprocess.run(
            ["databricks", "tables", "get", table_name, "--output", "json"],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error querying {table_name}: {e.stderr}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON for {table_name}: {e}", file=sys.stderr)
        return None

def generate_table_comment_sql(table_name: str, comment: str) -> str:
    """Generate SQL COMMENT statement for a table."""
    # Escape single quotes in comment
    escaped_comment = comment.replace("'", "''")
    return f"COMMENT ON TABLE {table_name} IS '{escaped_comment}';"

def generate_column_comment_sql(table_name: str, column_name: str, comment: str) -> str:
    """Generate SQL COMMENT statement for a column."""
    # Escape single quotes in comment
    escaped_comment = comment.replace("'", "''")
    return f"COMMENT ON COLUMN {table_name}.{column_name} IS '{escaped_comment}';"

def infer_column_comment(column_name: str, data_type: str) -> str:
    """Infer a basic comment for a column based on its name and type."""

    # Common column patterns
    if column_name == "account_id":
        return "Unique deposit account identifier"
    elif column_name == "customer_id":
        return "Unique customer identifier"
    elif column_name == "effective_date" or column_name == "as_of_date":
        return "Date of this data snapshot"
    elif column_name == "created_at" or column_name == "created_date":
        return "Record creation timestamp"
    elif column_name == "updated_at" or column_name == "updated_date":
        return "Record last update timestamp"
    elif "balance" in column_name.lower():
        return f"Account balance ({data_type})"
    elif "rate" in column_name.lower():
        return f"Interest rate or rate metric ({data_type})"
    elif "beta" in column_name.lower():
        return f"Deposit beta coefficient ({data_type})"
    elif "date" in column_name.lower():
        return f"Date field ({data_type})"
    elif "amount" in column_name.lower():
        return f"Dollar amount ({data_type})"
    elif "flag" in column_name.lower() or column_name.endswith("_flag"):
        return f"Boolean flag indicator ({data_type})"
    elif "count" in column_name.lower():
        return f"Count metric ({data_type})"
    elif "pct" in column_name.lower() or "percentage" in column_name.lower():
        return f"Percentage metric ({data_type})"
    elif "ratio" in column_name.lower():
        return f"Ratio metric ({data_type})"
    elif column_name.startswith("is_"):
        return f"Boolean indicator ({data_type})"
    else:
        return f"{column_name.replace('_', ' ').title()} ({data_type})"

def main():
    """Main execution function."""

    output_file = "/tmp/genie_table_comments.sql"
    summary_file = "/tmp/genie_schema_summary.txt"

    with open(output_file, 'w') as sql_file, open(summary_file, 'w') as summary_file_obj:

        sql_file.write("-- Generated SQL COMMENT statements for Genie Space tables\n")
        sql_file.write("-- Review these statements before executing in Databricks\n\n")

        summary_file_obj.write("=" * 80 + "\n")
        summary_file_obj.write("GENIE SPACE TABLE SCHEMA SUMMARY\n")
        summary_file_obj.write("=" * 80 + "\n\n")

        for table_name in TABLES:
            print(f"\nProcessing {table_name}...")

            schema_info = get_table_schema(table_name)

            if not schema_info:
                print(f"  ❌ Could not retrieve schema for {table_name}")
                summary_file_obj.write(f"\n❌ {table_name}\n")
                summary_file_obj.write("  Error: Could not retrieve schema\n")
                continue

            # Extract columns
            columns = schema_info.get('columns', [])
            num_columns = len(columns)

            print(f"  ✓ Found {num_columns} columns")

            # Write summary
            summary_file_obj.write(f"\n{'=' * 80}\n")
            summary_file_obj.write(f"{table_name}\n")
            summary_file_obj.write(f"{'=' * 80}\n")
            summary_file_obj.write(f"Columns: {num_columns}\n\n")

            for col in columns:
                col_name = col.get('name')
                col_type = col.get('type_name', col.get('type_text', 'UNKNOWN'))
                summary_file_obj.write(f"  - {col_name} ({col_type})\n")

            # Generate SQL comments
            sql_file.write(f"\n-- {table_name}\n")
            sql_file.write(f"-- Columns: {num_columns}\n\n")

            # Table-level comment
            if table_name in TABLE_COMMENTS:
                table_comment = TABLE_COMMENTS[table_name]
                sql_file.write(generate_table_comment_sql(table_name, table_comment) + "\n\n")

            # Column-level comments
            for col in columns:
                col_name = col.get('name')
                col_type = col.get('type_name', col.get('type_text', 'UNKNOWN'))
                col_comment = infer_column_comment(col_name, col_type)
                sql_file.write(generate_column_comment_sql(table_name, col_name, col_comment) + "\n")

            sql_file.write("\n")

    print(f"\n✅ SQL statements written to: {output_file}")
    print(f"✅ Schema summary written to: {summary_file}")
    print(f"\nNext steps:")
    print(f"1. Review {output_file}")
    print(f"2. Execute SQL in Databricks SQL Editor")
    print(f"3. Verify comments in Unity Catalog")

if __name__ == "__main__":
    main()
