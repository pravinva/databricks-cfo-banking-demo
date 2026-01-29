#!/usr/bin/env python3
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import time

w = WorkspaceClient()
warehouse_id = "4b9b953939869799"

def execute_sql(sql_query):
    """Execute SQL and return results"""
    statement = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql_query,
        wait_timeout="50s"
    )

    while statement.status.state in [StatementState.PENDING, StatementState.RUNNING]:
        time.sleep(2)
        statement = w.statement_execution.get_statement(statement.statement_id)

    if statement.result and statement.result.data_array:
        return statement.result.data_array
    return []

print("=" * 100)
print("CHECKING FOR GL TRANSACTION DATA")
print("=" * 100)

# Check if general_ledger table exists
print("\n1. Checking silver_finance.general_ledger...")
try:
    schema = execute_sql("DESCRIBE TABLE cfo_banking_demo.silver_finance.general_ledger")
    print("\n✓ Table exists! Columns:")
    for row in schema[:15]:  # Show first 15 columns
        print(f"   - {row[0]:30s} {row[1]}")

    # Get row count
    count_result = execute_sql("SELECT COUNT(*) as cnt FROM cfo_banking_demo.silver_finance.general_ledger")
    if count_result:
        print(f"\n   Row count: {count_result[0][0]:,}")

    # Get sample data
    print("\n   Sample transactions (first 3):")
    sample = execute_sql("SELECT * FROM cfo_banking_demo.silver_finance.general_ledger LIMIT 3")
    for i, row in enumerate(sample, 1):
        print(f"   Row {i}: {row[:6]}...")

    # Check account number patterns
    print("\n   Checking account number patterns (revenue/expense accounts):")
    patterns = execute_sql("""
        SELECT
            SUBSTRING(account_number, 1, 2) as account_prefix,
            COUNT(*) as transaction_count,
            SUM(debit_amount) as total_debits,
            SUM(credit_amount) as total_credits
        FROM cfo_banking_demo.silver_finance.general_ledger
        WHERE account_number IS NOT NULL
        GROUP BY SUBSTRING(account_number, 1, 2)
        ORDER BY account_prefix
        LIMIT 10
    """)

    if patterns:
        print("\n   Account Prefix | Transactions | Total Debits | Total Credits")
        print("   " + "-" * 70)
        for row in patterns:
            prefix, count, debits, credits = row
            print(f"   {prefix:14s} | {count:12,} | ${debits or 0:12,.0f} | ${credits or 0:12,.0f}")

except Exception as e:
    print(f"\n✗ Error accessing general_ledger: {e}")

print("\n" + "=" * 100)

# Check chart of accounts
print("\n2. Checking bronze_core_banking.chart_of_accounts...")
try:
    coa_schema = execute_sql("DESCRIBE TABLE cfo_banking_demo.bronze_core_banking.chart_of_accounts")
    print("\n✓ Table exists! Columns:")
    for row in coa_schema[:10]:
        print(f"   - {row[0]:30s} {row[1]}")

    # Get sample accounts
    print("\n   Sample accounts (revenue & expense):")
    sample_coa = execute_sql("""
        SELECT account_number, account_name, account_type, account_category
        FROM cfo_banking_demo.bronze_core_banking.chart_of_accounts
        WHERE account_type IN ('Revenue', 'Expense')
        LIMIT 10
    """)

    if sample_coa:
        print("\n   Account# | Name | Type | Category")
        print("   " + "-" * 80)
        for row in sample_coa:
            acc_num, acc_name, acc_type, acc_cat = row
            print(f"   {acc_num} | {acc_name[:30]:30s} | {acc_type:8s} | {acc_cat}")

    # Count revenue/expense accounts
    count_types = execute_sql("""
        SELECT account_type, COUNT(*) as account_count
        FROM cfo_banking_demo.bronze_core_banking.chart_of_accounts
        GROUP BY account_type
        ORDER BY account_type
    """)

    if count_types:
        print("\n   Account counts by type:")
        for row in count_types:
            acc_type, count = row
            print(f"   {acc_type:15s}: {count:3,} accounts")

except Exception as e:
    print(f"\n✗ Error accessing chart_of_accounts: {e}")

print("\n" + "=" * 100)

# Check profitability_metrics for comparison
print("\n3. Checking gold_finance.profitability_metrics...")
try:
    prof_data = execute_sql("""
        SELECT
            calculation_date,
            net_interest_margin,
            fee_revenue,
            operating_expenses
        FROM cfo_banking_demo.gold_finance.profitability_metrics
        LIMIT 5
    """)

    if prof_data:
        print("\n✓ Gold layer profitability metrics available:")
        print("\n   Date | NIM | Fee Revenue | Operating Expenses")
        print("   " + "-" * 70)
        for row in prof_data:
            date, nim, fee_rev, op_exp = row
            print(f"   {date} | {nim:.4f} | ${fee_rev:12,.0f} | ${op_exp:12,.0f}")

except Exception as e:
    print(f"\n✗ Error accessing profitability_metrics: {e}")

print("\n" + "=" * 100)
print("\nSUMMARY:")
print("-" * 100)
print("✓ = Data available and usable")
print("✗ = Data missing or insufficient")
print("=" * 100)
