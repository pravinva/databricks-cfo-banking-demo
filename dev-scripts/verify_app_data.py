#!/usr/bin/env python3
"""
Verify all data required by the CFO Banking Demo app is accessible.
"""
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
WAREHOUSE_ID = "4b9b953939869799"

print("=" * 100)
print("CFO BANKING DEMO - DATA VERIFICATION")
print("=" * 100)

checks = []

# 1. Check loan_portfolio
print("\n1. LOAN PORTFOLIO")
print("-" * 100)
loan_query = """
SELECT
    product_type,
    COUNT(*) as loan_count,
    SUM(current_balance) / 1e9 as balance_billions,
    AVG(interest_rate) * 100 as avg_rate_pct
FROM cfo_banking_demo.bronze_core_banking.loan_portfolio
WHERE is_current = TRUE
GROUP BY product_type
ORDER BY balance_billions DESC
"""

result = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=loan_query,
    wait_timeout="30s"
)

if result.result and result.result.data_array and len(result.result.data_array) > 0:
    print(f"{'Product Type':<25} {'Loans':<15} {'Balance (B)':<15} {'Avg Rate':<15}")
    print("-" * 70)
    for row in result.result.data_array:
        ptype = row[0]
        count = int(row[1])
        balance = float(row[2])
        rate = float(row[3])
        print(f"{ptype:<25} {count:<15,} ${balance:<14.2f} {rate:<14.2f}%")
    checks.append(("Loan Portfolio", "✓ PASS", f"{len(result.result.data_array)} product types"))
else:
    print("⚠️  NO LOAN DATA FOUND")
    checks.append(("Loan Portfolio", "✗ FAIL", "No data"))

# 2. Check deposit_accounts
print("\n\n2. DEPOSIT ACCOUNTS")
print("-" * 100)
deposit_query = """
SELECT
    product_type,
    COUNT(*) as account_count,
    SUM(current_balance) / 1e9 as balance_billions,
    AVG(stated_rate) * 100 as avg_rate_pct
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
WHERE account_status = 'Active'
GROUP BY product_type
ORDER BY balance_billions DESC
"""

result = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=deposit_query,
    wait_timeout="30s"
)

if result.result and result.result.data_array and len(result.result.data_array) > 0:
    print(f"{'Product Type':<25} {'Accounts':<15} {'Balance (B)':<15} {'Avg Rate':<15}")
    print("-" * 70)
    for row in result.result.data_array:
        ptype = row[0]
        count = int(row[1])
        balance = float(row[2])
        rate = float(row[3])
        print(f"{ptype:<25} {count:<15,} ${balance:<14.2f} {rate:<14.2f}%")
    checks.append(("Deposit Accounts", "✓ PASS", f"{len(result.result.data_array)} product types"))
else:
    print("⚠️  NO DEPOSIT DATA FOUND")
    checks.append(("Deposit Accounts", "✗ FAIL", "No data"))

# 3. Check general_ledger
print("\n\n3. GENERAL LEDGER (Revenue & Expenses)")
print("-" * 100)
gl_query = """
SELECT
    CASE
        WHEN account_num LIKE '41%' THEN 'Revenue'
        WHEN account_num LIKE '6%' THEN 'Expense'
        ELSE 'Other'
    END as account_category,
    COUNT(*) as txn_count,
    SUM(credit_amount) / 1e6 as total_credit_millions,
    SUM(debit_amount) / 1e6 as total_debit_millions,
    MIN(transaction_date) as earliest_date,
    MAX(transaction_date) as latest_date
FROM cfo_banking_demo.silver_finance.general_ledger
GROUP BY CASE
    WHEN account_num LIKE '41%' THEN 'Revenue'
    WHEN account_num LIKE '6%' THEN 'Expense'
    ELSE 'Other'
END
ORDER BY account_category
"""

result = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=gl_query,
    wait_timeout="30s"
)

if result.result and result.result.data_array and len(result.result.data_array) > 0:
    print(f"{'Category':<15} {'Txns':<10} {'Credit (M)':<15} {'Debit (M)':<15} {'Date Range':<30}")
    print("-" * 85)
    for row in result.result.data_array:
        category = row[0]
        count = int(row[1])
        credit = float(row[2]) if row[2] else 0
        debit = float(row[3]) if row[3] else 0
        date_range = f"{row[4]} to {row[5]}"
        print(f"{category:<15} {count:<10,} ${credit:<14,.1f} ${debit:<14,.1f} {date_range:<30}")
    checks.append(("General Ledger", "✓ PASS", f"{sum([int(r[1]) for r in result.result.data_array])} transactions"))
else:
    print("⚠️  NO GL DATA FOUND")
    checks.append(("General Ledger", "✗ FAIL", "No data"))

# 4. Check securities_portfolio
print("\n\n4. SECURITIES PORTFOLIO")
print("-" * 100)
securities_query = """
SELECT
    security_type,
    COUNT(*) as security_count,
    SUM(market_value) / 1e9 as market_value_billions
FROM cfo_banking_demo.silver_treasury.securities_portfolio
WHERE is_current = TRUE
GROUP BY security_type
ORDER BY market_value_billions DESC
"""

result = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=securities_query,
    wait_timeout="30s"
)

if result.result and result.result.data_array and len(result.result.data_array) > 0:
    print(f"{'Security Type':<25} {'Count':<15} {'Market Value (B)':<20}")
    print("-" * 60)
    for row in result.result.data_array:
        stype = row[0]
        count = int(row[1])
        value = float(row[2])
        print(f"{stype:<25} {count:<15,} ${value:<19.2f}")
    checks.append(("Securities Portfolio", "✓ PASS", f"{len(result.result.data_array)} security types"))
else:
    print("⚠️  NO SECURITIES DATA FOUND")
    checks.append(("Securities Portfolio", "✗ FAIL", "No data"))

# Summary
print("\n\n" + "=" * 100)
print("VERIFICATION SUMMARY")
print("=" * 100)
print(f"{'Component':<30} {'Status':<15} {'Details':<50}")
print("-" * 100)
for component, status, details in checks:
    print(f"{component:<30} {status:<15} {details:<50}")

all_passed = all([check[1] == "✓ PASS" for check in checks])
if all_passed:
    print("\n✓ ALL CHECKS PASSED - App should work correctly")
else:
    print("\n⚠️  SOME CHECKS FAILED - App may have display issues")

print("=" * 100)
