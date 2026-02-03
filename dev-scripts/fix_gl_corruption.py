#!/usr/bin/env python3
"""
Fix GL table corruption by truncating and repopulating with clean data.
"""
from databricks.sdk import WorkspaceClient
from datetime import datetime, timedelta
import random

w = WorkspaceClient()
WAREHOUSE_ID = "4b9b953939869799"

print("=" * 80)
print("FIXING GL TABLE CORRUPTION")
print("=" * 80)

# Step 1: Truncate the table
print("\n1. Truncating general_ledger table...")
truncate_sql = "TRUNCATE TABLE cfo_banking_demo.silver_finance.general_ledger"

try:
    result = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        statement=truncate_sql,
        wait_timeout="30s"
    )
    print("   ✓ Table truncated successfully")
except Exception as e:
    print(f"   ✗ Truncate failed: {str(e)}")
    exit(1)

# Step 2: Generate clean data
print("\n2. Generating 24 months × 10 accounts = 240 rows...")

accounts = [
    # Revenue accounts (4xxx)
    ('4100', 'Service Charges on Deposits', 'revenue', 3500000),
    ('4110', 'Card Interchange Fees', 'revenue', 5000000),
    ('4120', 'Loan Origination Fees', 'revenue', 2500000),
    ('4130', 'Wealth Management Fees', 'revenue', 4000000),
    # Expense accounts (6xxx)
    ('6100', 'Salaries and Employee Benefits', 'expense', 50000000),
    ('6200', 'Occupancy Costs', 'expense', 10000000),
    ('6300', 'Technology and Equipment', 'expense', 15000000),
    ('6400', 'Marketing and Advertising', 'expense', 8000000),
    ('6500', 'Professional Fees', 'expense', 5000000),
    ('6600', 'FDIC Insurance and Other', 'expense', 3000000),
]

rows = []
base_date = datetime.now().date()

for month_offset in range(24):
    transaction_date = base_date - timedelta(days=30 * month_offset)

    for account_num, account_name, acct_type, base_amount in accounts:
        # Add seasonality and randomness
        seasonality = 1 + 0.1 * random.uniform(-1, 1)
        amount = base_amount * seasonality

        if acct_type == 'revenue':
            credit_amt = amount
            debit_amt = 0.0
        else:  # expense
            credit_amt = 0.0
            debit_amt = amount

        txn_id = f"GL-{len(rows) + 1:06d}"

        rows.append({
            'transaction_id': txn_id,
            'transaction_date': transaction_date.strftime('%Y-%m-%d'),
            'account_num': account_num,
            'account_name': account_name,
            'debit_amount': debit_amt,
            'credit_amount': credit_amt,
            'balance': debit_amt + credit_amt,
            'description': f'Monthly {acct_type} for {transaction_date.strftime("%B %Y")}',
            'created_by': 'system',
            'created_timestamp': datetime.now().isoformat()
        })

print(f"   Generated {len(rows)} rows")

# Step 3: Insert in batches
print("\n3. Inserting clean data in batches...")
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

# Step 4: Verify clean data
print("\n4. Verifying clean data...")
verify_sql = """
SELECT
    account_num,
    COUNT(*) as row_count,
    AVG(credit_amount) as avg_credit,
    MIN(credit_amount) as min_credit,
    MAX(credit_amount) as max_credit,
    SUM(credit_amount) as total_credit,
    MIN(transaction_date) as earliest_date,
    MAX(transaction_date) as latest_date
FROM cfo_banking_demo.silver_finance.general_ledger
WHERE account_num LIKE '41%'
GROUP BY account_num
ORDER BY account_num
"""

result = w.statement_execution.execute_statement(
    warehouse_id=WAREHOUSE_ID,
    statement=verify_sql,
    wait_timeout="30s"
)

print("\nRevenue Accounts (41xx) in general_ledger:")
print("=" * 120)
print(f"{'Account':<15} {'Rows':<10} {'Avg Credit':<20} {'Min':<20} {'Max':<20} {'Total':<20} {'Date Range':<30}")
print("-" * 120)

if result.result and result.result.data_array:
    for row in result.result.data_array:
        account = row[0]
        count = int(row[1]) if row[1] else 0
        avg = float(row[2]) if row[2] else 0
        min_val = float(row[3]) if row[3] else 0
        max_val = float(row[4]) if row[4] else 0
        total = float(row[5]) if row[5] else 0
        date_range = f"{row[6]} to {row[7]}"

        # Check for corruption
        if avg > 1_000_000_000:  # More than 1 billion average is corrupt
            status = "⚠️  STILL CORRUPT"
        else:
            status = "✓ CLEAN"

        print(f"{account:<15} {count:<10} ${avg:<19,.0f} ${min_val:<19,.0f} ${max_val:<19,.0f} ${total:<19,.0f} {date_range:<30} {status}")

print("\n" + "=" * 80)
print("GL TABLE FIXED")
print("=" * 80)
print("\nNext: Re-run Train_PPNR_Models.py notebook")
