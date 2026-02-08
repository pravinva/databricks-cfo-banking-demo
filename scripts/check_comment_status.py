#!/usr/bin/env python3
"""
Check which tables have comments applied.
"""

import subprocess
import json

TABLES = [
    "cfo_banking_demo.ml_models.deposit_beta_training_enhanced",
    "cfo_banking_demo.bronze_core_banking.deposit_accounts",
    "cfo_banking_demo.ml_models.component_decay_metrics",
    "cfo_banking_demo.ml_models.cohort_survival_rates",
    "cfo_banking_demo.ml_models.deposit_runoff_forecasts",
    "cfo_banking_demo.ml_models.dynamic_beta_parameters",
    "cfo_banking_demo.ml_models.stress_test_results",
    "cfo_banking_demo.gold_regulatory.lcr_daily",
    "cfo_banking_demo.ml_models.ppnr_forecasts",
    "cfo_banking_demo.ml_models.non_interest_income_training_data",
    "cfo_banking_demo.ml_models.non_interest_expense_training_data",
]

def check_table(table_name):
    """Check if table has comment."""
    try:
        result = subprocess.run(
            ['databricks', 'tables', 'get', table_name, '--output', 'json'],
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            table_comment = data.get('comment', '')
            columns = data.get('columns', [])

            # Count columns with comments
            cols_with_comments = sum(1 for col in columns if col.get('comment'))
            total_cols = len(columns)

            return {
                'has_table_comment': bool(table_comment),
                'table_comment': table_comment[:80] + '...' if len(table_comment) > 80 else table_comment,
                'cols_with_comments': cols_with_comments,
                'total_cols': total_cols
            }
        else:
            return None

    except Exception as e:
        return None

def main():
    print("=" * 100)
    print("GENIE SPACE TABLE COMMENT STATUS")
    print("=" * 100)
    print()

    for i, table in enumerate(TABLES, 1):
        short_name = table.replace('cfo_banking_demo.', '')
        print(f"[{i}/12] {short_name}")

        status = check_table(table)

        if status:
            if status['has_table_comment']:
                print(f"  ✓ Table comment: {status['table_comment']}")
            else:
                print(f"  ✗ No table comment")

            if status['cols_with_comments'] > 0:
                pct = (status['cols_with_comments'] / status['total_cols']) * 100
                print(f"  ✓ Column comments: {status['cols_with_comments']}/{status['total_cols']} ({pct:.0f}%)")
            else:
                print(f"  ✗ No column comments (0/{status['total_cols']})")
        else:
            print(f"  ✗ Error checking table")

        print()

if __name__ == "__main__":
    main()
