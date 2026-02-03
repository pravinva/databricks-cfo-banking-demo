#!/usr/bin/env python3
"""
Complete GL backfill with realistic P&L for a $44B bank.
Generates 24 months of data with proper account structure.
"""
from databricks.sdk import WorkspaceClient
from datetime import datetime, timedelta
import random

w = WorkspaceClient()
WAREHOUSE_ID = "4b9b953939869799"

print("=" * 100)
print("COMPLETE GL BACKFILL - REALISTIC BANK P&L")
print("=" * 100)

# Step 1: Truncate existing table
print("\n1. Truncating general_ledger table...")
truncate_sql = "TRUNCATE TABLE cfo_banking_demo.silver_finance.general_ledger"
try:
    w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        statement=truncate_sql,
        wait_timeout="30s"
    )
    print("   ✓ Table truncated")
except Exception as e:
    print(f"   ✗ Truncate failed: {str(e)}")
    exit(1)

# Step 2: Define complete chart of accounts
# Based on $18B loans, $27B deposits, $13B securities = $44B total assets
accounts = [
    # INTEREST INCOME (40xx) - Total ~$140M/month
    ('4010', 'Interest Income - Loans', 'interest_income', 85000000),           # $18B @ 5.5% = $82.5M/month
    ('4020', 'Interest Income - Securities', 'interest_income', 40000000),      # $13B @ 3.5% = $37.9M/month
    ('4030', 'Interest Income - Fed Funds Sold', 'interest_income', 15000000),  # $5B @ 3.0% = $12.5M/month

    # NON-INTEREST INCOME (41xx) - Total ~$50M/month
    ('4100', 'Service Charges on Deposits', 'fee_income', 12000000),            # 340K accounts @ $35/mo
    ('4110', 'Card Interchange Fees', 'fee_income', 18000000),                  # Card volume
    ('4120', 'Loan Origination Fees', 'fee_income', 8000000),                   # New loan fees
    ('4130', 'Wealth Management Fees', 'fee_income', 10000000),                 # AUM fees
    ('4140', 'Other Fee Income', 'fee_income', 2000000),                        # Misc fees

    # INTEREST EXPENSE (50xx) - Total ~$20M/month
    ('5010', 'Interest Expense - Deposits', 'interest_expense', 12000000),      # $27B @ 0.5% = $11.2M/month
    ('5020', 'Interest Expense - Borrowings', 'interest_expense', 8000000),     # $3B @ 3.0% = $7.5M/month

    # NON-INTEREST EXPENSE (6xxx) - Total ~$125M/month
    ('6100', 'Salaries and Benefits', 'operating_expense', 60000000),           # ~1,500 employees @ $40K/mo
    ('6200', 'Occupancy and Equipment', 'operating_expense', 15000000),         # Rent, utilities, depreciation
    ('6300', 'Technology and Communications', 'operating_expense', 20000000),   # IT, software, telecom
    ('6400', 'Marketing and Business Development', 'operating_expense', 10000000), # Advertising, promotions
    ('6500', 'Professional Fees', 'operating_expense', 8000000),                # Legal, audit, consulting
    ('6600', 'FDIC Insurance', 'operating_expense', 5000000),                   # Deposit insurance
    ('6900', 'Other Operating Expenses', 'operating_expense', 7000000),         # Misc expenses
]

# Step 3: Generate 24 months of data
print("\n2. Generating 24 months of realistic GL data...")
rows = []
base_date = datetime.now().date()

for month_offset in range(24):
    transaction_date = base_date - timedelta(days=30 * month_offset)
    month_num = transaction_date.month

    # Seasonality factors (Q4 higher, Q1 lower)
    if month_num in [11, 12]:
        seasonality = 1.15  # Q4 boost
    elif month_num in [1, 2]:
        seasonality = 0.92  # Q1 slowdown
    else:
        seasonality = 1.0

    # Trend (slight growth over time)
    trend = 1.0 + (0.02 * month_offset / 12)  # 2% annual growth

    for account_num, account_name, account_type, base_amount in accounts:
        # Apply seasonality and trend
        amount = base_amount * seasonality * trend

        # Add random variance (±5%)
        variance = 1.0 + random.uniform(-0.05, 0.05)
        amount = amount * variance

        # Determine debit/credit based on account type
        if account_type in ['interest_income', 'fee_income']:
            credit_amt = amount
            debit_amt = 0.0
        else:  # interest_expense, operating_expense
            credit_amt = 0.0
            debit_amt = amount

        txn_id = f"GL-{transaction_date.strftime('%Y%m')}-{account_num}-{len(rows):04d}"

        rows.append({
            'transaction_id': txn_id,
            'transaction_date': transaction_date.strftime('%Y-%m-%d'),
            'account_num': account_num,
            'account_name': account_name,
            'debit_amount': debit_amt,
            'credit_amount': credit_amt,
            'balance': credit_amt - debit_amt,  # Credit increases equity, debit decreases
            'description': f'Monthly {account_type.replace("_", " ")} for {transaction_date.strftime("%B %Y")}',
            'created_by': 'system',
            'created_timestamp': datetime.now().isoformat()
        })

print(f"   Generated {len(rows)} rows (24 months × {len(accounts)} accounts)")

# Step 4: Insert in batches
print("\n3. Inserting data in batches...")
batch_size = 50
total_batches = (len(rows) + batch_size - 1) // batch_size

for i in range(0, len(rows), batch_size):
    batch = rows[i:i + batch_size]
    batch_num = i // batch_size + 1

    values_list = []
    for row in batch:
        values = f"('{row['transaction_id']}', '{row['transaction_date']}', '{row['account_num']}', " \
                f"'{row['account_name']}', {row['debit_amount']}, {row['credit_amount']}, " \
                f"{row['balance']}, '{row['description']}', '{row['created_by']}', " \
                f"CURRENT_TIMESTAMP())"
        values_list.append(values)

    insert_sql = f"""
    INSERT INTO cfo_banking_demo.silver_finance.general_ledger
    (transaction_id, transaction_date, account_num, account_name, debit_amount,
     credit_amount, balance, description, created_by, created_timestamp)
    VALUES {','.join(values_list)}
    """

    try:
        result = w.statement_execution.execute_statement(
            warehouse_id=WAREHOUSE_ID,
            statement=insert_sql,
            wait_timeout="30s"
        )
        print(f"   ✓ Batch {batch_num}/{total_batches} ({len(batch)} rows)")
    except Exception as e:
        print(f"   ✗ Batch {batch_num} failed: {str(e)[:100]}")

# Step 5: Verify P&L structure
print("\n4. Verifying P&L structure...")
verify_sql = """
SELECT
    CASE
        WHEN account_num LIKE '40%' THEN 'Interest Income'
        WHEN account_num LIKE '41%' THEN 'Non-Interest Income'
        WHEN account_num LIKE '50%' THEN 'Interest Expense'
        WHEN account_num LIKE '6%' THEN 'Operating Expense'
        ELSE 'Other'
    END as category,
    COUNT(*) as txn_count,
    SUM(credit_amount) / 1e6 as total_credit_millions,
    SUM(debit_amount) / 1e6 as total_debit_millions,
    (SUM(credit_amount) - SUM(debit_amount)) / 1e6 as net_millions
FROM cfo_banking_demo.silver_finance.general_ledger
GROUP BY CASE
    WHEN account_num LIKE '40%' THEN 'Interest Income'
    WHEN account_num LIKE '41%' THEN 'Non-Interest Income'
    WHEN account_num LIKE '50%' THEN 'Interest Expense'
    WHEN account_num LIKE '6%' THEN 'Operating Expense'
    ELSE 'Other'
END
ORDER BY category
"""

result = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=verify_sql,
    wait_timeout="30s"
)

print(f"\n{'Category':<25} {'Txns':<10} {'Credit (M)':<15} {'Debit (M)':<15} {'Net (M)':<15}")
print("-" * 80)
if result.result and result.result.data_array:
    for row in result.result.data_array:
        category = row[0]
        count = int(row[1])
        credit = float(row[2]) if row[2] else 0
        debit = float(row[3]) if row[3] else 0
        net = float(row[4]) if row[4] else 0
        print(f"{category:<25} {count:<10,} ${credit:<14,.1f} ${debit:<14,.1f} ${net:<14,.1f}")

# Calculate expected PPNR
print("\n5. Expected monthly P&L:")
print("-" * 80)
interest_income = 140.0  # $140M
interest_expense = 20.0  # $20M
nii = interest_income - interest_expense  # $120M
non_interest_income = 50.0  # $50M
operating_expense = 125.0  # $125M
ppnr = nii + non_interest_income - operating_expense  # $45M

print(f"Interest Income:        ${interest_income:>8.1f}M")
print(f"Interest Expense:       ${interest_expense:>8.1f}M")
print(f"Net Interest Income:    ${nii:>8.1f}M")
print(f"Non-Interest Income:    ${non_interest_income:>8.1f}M")
print(f"Operating Expense:      ${operating_expense:>8.1f}M")
print(f"PPNR:                   ${ppnr:>8.1f}M")

print("\n" + "=" * 100)
print("GL BACKFILL COMPLETE")
print("=" * 100)
print("\nNext steps:")
print("  1. Drop PPNR training tables: python3 dev-scripts/fix_ppnr_schema.py")
print("  2. Re-run Train_PPNR_Models.py notebook")
print("  3. Verify PPNR is ~$45M/month with realistic variance")
