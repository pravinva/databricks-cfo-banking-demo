#!/usr/bin/env python3
"""
WS1-04b: Complete CD Account Generation
Insert remaining 35,000 CD accounts (20K already inserted, need 35K more)
Uses smaller batch sizes to avoid timeout
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import random
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time

# Set random seed for reproducibility (offset from main script)
random.seed(43)  # Different seed to avoid duplicates
np.random.seed(43)

def log_message(message, level="INFO"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

# Constants
CURRENT_DATE = datetime(2026, 1, 24).date()
WAREHOUSE_ID = "4b9b953939869799"

# Deposit rate ranges
RATE_MAP = {
    2020: {'CD': (0.5, 2.0)},
    2021: {'CD': (0.5, 2.0)},
    2022: {'CD': (2.0, 3.5)},
    2023: {'CD': (3.5, 5.0)},
    2024: {'CD': (4.0, 5.5)},
    2025: {'CD': (3.5, 5.0)},
}

def execute_sql(w, sql_statement, warehouse_id=WAREHOUSE_ID):
    """Execute SQL statement with extended timeout"""
    statement = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql_statement,
        wait_timeout="50s"
    )

    # Wait for completion
    max_wait_time = 900  # 15 minutes max
    elapsed = 0
    while statement.status.state in [StatementState.PENDING, StatementState.RUNNING] and elapsed < max_wait_time:
        time.sleep(5)
        elapsed += 5
        statement = w.statement_execution.get_statement(statement.statement_id)

    if statement.status.state == StatementState.FAILED:
        error_msg = statement.status.error.message if statement.status.error else "Unknown error"
        raise Exception(f"SQL execution failed: {error_msg}")

    return statement

def get_deposit_rate(year, term_months):
    """Get realistic rate based on year and term"""
    min_rate, max_rate = RATE_MAP.get(year, {}).get('CD', (3.0, 5.0))

    # CDs: rates vary by term
    if term_months <= 6:
        max_rate = max_rate - 0.5
    elif term_months >= 24:
        max_rate = max_rate + 0.2

    return round(random.uniform(min_rate, max_rate), 4)

def assign_beta():
    """Assign deposit beta for CDs"""
    return round(random.uniform(0.90, 1.00), 4)

def generate_account_id(index):
    """Generate unique account ID"""
    return f"ACCT-CD-{index:08d}"

def generate_remaining_cds(start_index, count):
    """Generate remaining CD accounts"""
    accounts = []

    log_message(f"Generating {count:,} CD accounts starting at index {start_index:,}...")

    for i in range(count):
        if (i + 1) % 5000 == 0:
            log_message(f"  Generated {i+1:,}/{count:,} CD accounts...")

        # Pick term
        term_months = random.choice([3, 6, 12, 12, 12, 12, 24, 24, 60])  # Weighted toward 12-month

        open_year = random.choices([2020, 2021, 2022, 2023, 2024, 2025],
                                   weights=[5, 10, 20, 30, 25, 10])[0]
        open_date = datetime(open_year, random.randint(1, 12), random.randint(1, 28)).date()

        maturity_date = open_date + relativedelta(months=term_months)

        # Check if matured and renewed
        is_matured = maturity_date < CURRENT_DATE
        if is_matured and random.random() < 0.70:
            days_since_maturity = (CURRENT_DATE - maturity_date).days
            renewal_count = days_since_maturity // (term_months * 30)
            maturity_date = maturity_date + relativedelta(months=term_months * (renewal_count + 1))

        balance = int(np.random.lognormal(11.3, 0.9))  # Mean ~$80K
        balance = max(1000, min(5000000, balance))

        # Status
        if maturity_date < CURRENT_DATE:
            status = 'Matured'
        else:
            status = random.choices(['Active', 'Closed'], weights=[98, 2])[0]

        accounts.append({
            'account_id': generate_account_id(start_index + i),
            'account_number': f'CD-{start_index + i:010d}',
            'customer_id': f'CUST-{random.randint(10000, 999999)}',
            'customer_name': f'Customer CD {start_index + i}',
            'customer_type': 'Retail',
            'customer_segment': random.choices(['Mass_Market', 'Mass_Affluent', 'Private_Banking'],
                                              weights=[50, 35, 15])[0],
            'product_type': 'CD',
            'product_name': f'Retail_CD_{term_months}M',
            'account_open_date': open_date,
            'maturity_date': maturity_date,
            'current_balance': float(balance),
            'average_balance_30d': float(balance),
            'average_balance_90d': float(balance),
            'minimum_balance': float(balance),
            'maximum_balance': float(balance),
            'stated_rate': get_deposit_rate(open_year, term_months),
            'beta': assign_beta(),
            'decay_rate': 0.0,
            'interest_accrued': float(balance * get_deposit_rate(open_year, term_months) / 100 / 12),
            'ytd_interest_paid': 0.0,
            'transaction_count_30d': 0,
            'last_transaction_date': open_date,
            'account_status': status,
            'fdic_insured': True,
            'relationship_balance': float(balance * random.uniform(1.5, 4.0)),
            'has_online_banking': random.random() < 0.70,
            'has_mobile_banking': random.random() < 0.55,
            'autopay_enrolled': False,
            'overdraft_protection': False,
            'monthly_fee': 0.0,
            'fee_waivers': 'None',
            'geography': random.choices(['CA', 'TX', 'FL', 'NY', 'PA', 'IL', 'OH', 'GA', 'NC', 'MI'],
                                       weights=[15, 12, 10, 8, 5, 5, 5, 5, 5, 30])[0],
            'branch_id': f'BR-{random.randint(1, 50):03d}',
            'officer_id': None,
            'effective_date': CURRENT_DATE,
            'is_current': True
        })

    return accounts

def insert_accounts_small_batch(w, accounts, table_name):
    """Insert accounts in smaller batches to avoid timeout"""
    batch_size = 500  # Reduced from 1000
    total = len(accounts)

    log_message(f"Inserting {total:,} accounts in batches of {batch_size}...")

    for batch_idx in range(0, total, batch_size):
        batch = accounts[batch_idx:batch_idx + batch_size]

        # Format values for SQL INSERT
        values_list = []
        for acc in batch:
            maturity_date = f"'{acc['maturity_date']}'" if acc['maturity_date'] else "NULL"
            officer_id = f"'{acc['officer_id']}'" if acc['officer_id'] else "NULL"

            values = f"""(
                '{acc['account_id']}', '{acc['account_number']}', '{acc['customer_id']}',
                '{acc['customer_name']}', '{acc['customer_type']}', '{acc['customer_segment']}',
                '{acc['product_type']}', '{acc['product_name']}', '{acc['account_open_date']}',
                {maturity_date}, {acc['current_balance']}, {acc['average_balance_30d']},
                {acc['average_balance_90d']}, {acc['minimum_balance']}, {acc['maximum_balance']},
                {acc['stated_rate']}, {acc['beta']}, {acc['decay_rate']}, {acc['interest_accrued']},
                {acc['ytd_interest_paid']}, {acc['transaction_count_30d']}, '{acc['last_transaction_date']}',
                '{acc['account_status']}', {acc['fdic_insured']}, {acc['relationship_balance']},
                {acc['has_online_banking']}, {acc['has_mobile_banking']}, {acc['autopay_enrolled']},
                {acc['overdraft_protection']}, {acc['monthly_fee']}, '{acc['fee_waivers']}',
                '{acc['geography']}', '{acc['branch_id']}', {officer_id}, '{acc['effective_date']}',
                {acc['is_current']}
            )"""
            values_list.append(values)

        insert_sql = f"""
        INSERT INTO {table_name} VALUES
        {', '.join(values_list)}
        """

        try:
            execute_sql(w, insert_sql)

            if (batch_idx + batch_size) % 2500 == 0 or (batch_idx + batch_size) >= total:
                log_message(f"  Inserted {min(batch_idx + batch_size, total):,}/{total:,}")
        except Exception as e:
            log_message(f"  Error inserting batch at {batch_idx}: {str(e)}", "ERROR")
            raise

def main():
    """Main execution function"""
    try:
        log_message("=" * 80)
        log_message("WS1-04b: Complete CD Account Generation")
        log_message("=" * 80)

        # Initialize Databricks workspace client
        w = WorkspaceClient()
        log_message("✓ Connected to Databricks")
        log_message(f"✓ Using SQL Warehouse: {WAREHOUSE_ID}")

        # Check current count
        result = execute_sql(w, "SELECT COUNT(*) FROM cfo_banking_demo.bronze_core_banking.deposit_accounts WHERE product_type = 'CD'")
        current_cd_count = int(result.result.data_array[0][0]) if result.result and result.result.data_array else 0
        log_message(f"Current CD accounts in database: {current_cd_count:,}")

        # Calculate what we need
        target_count = 55000
        needed_count = target_count - current_cd_count

        if needed_count <= 0:
            log_message(f"✓ Already have {current_cd_count:,} CD accounts (target: {target_count:,})")
            return 0

        log_message(f"Need to generate {needed_count:,} more CD accounts")

        # Generate remaining CDs
        start_index = 347000 + current_cd_count
        remaining_cds = generate_remaining_cds(start_index, needed_count)

        # Insert in smaller batches
        insert_accounts_small_batch(w, remaining_cds, "cfo_banking_demo.bronze_core_banking.deposit_accounts")

        # Verify final count
        result = execute_sql(w, "SELECT COUNT(*) FROM cfo_banking_demo.bronze_core_banking.deposit_accounts WHERE product_type = 'CD'")
        final_cd_count = int(result.result.data_array[0][0]) if result.result and result.result.data_array else 0

        log_message(f"\n✓ Final CD account count: {final_cd_count:,}")

        log_message("\n" + "=" * 80)
        log_message("✅ WS1-04b Complete: Remaining CD Accounts Generated")
        log_message("=" * 80)

        return 0

    except Exception as e:
        log_message(f"\n\nError: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
