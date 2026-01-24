#!/usr/bin/env python3
"""
WS1-04: Deposit Portfolio Generator
Generate 402K deposit accounts + 36 months behavior history for CFO Banking Demo

Portfolio: ~$22B across 402,000 accounts
- DDA: $7.7B (180,000 accounts)
- NOW: $1.1B (22,000 accounts)
- Savings: $3.3B (110,000 accounts)
- MMDA: $4.4B (35,000 accounts)
- CDs: $5.5B (55,000 accounts)

Uses Databricks SQL Warehouse for execution
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import random
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time

# Set random seed for reproducibility
random.seed(42)
np.random.seed(42)

def log_message(message, level="INFO"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

# Constants
CURRENT_DATE = datetime(2026, 1, 24).date()
WAREHOUSE_ID = "4b9b953939869799"

# Deposit rate ranges by year and product
RATE_MAP = {
    2019: {'DDA': (0.0, 0.05), 'NOW': (0.1, 0.5), 'Savings': (0.3, 1.0), 'MMDA': (0.5, 1.5), 'CD': (0.5, 2.0)},
    2020: {'DDA': (0.0, 0.05), 'NOW': (0.1, 0.5), 'Savings': (0.3, 1.0), 'MMDA': (0.5, 1.5), 'CD': (0.5, 2.0)},
    2021: {'DDA': (0.0, 0.05), 'NOW': (0.1, 0.5), 'Savings': (0.3, 1.0), 'MMDA': (0.5, 1.5), 'CD': (0.5, 2.0)},
    2022: {'DDA': (0.0, 0.1), 'NOW': (0.3, 1.0), 'Savings': (0.8, 1.8), 'MMDA': (1.5, 2.5), 'CD': (2.0, 3.5)},
    2023: {'DDA': (0.0, 0.1), 'NOW': (0.5, 1.2), 'Savings': (1.2, 2.2), 'MMDA': (2.0, 3.5), 'CD': (3.5, 5.0)},
    2024: {'DDA': (0.0, 0.1), 'NOW': (0.5, 1.5), 'Savings': (1.5, 2.5), 'MMDA': (2.8, 4.0), 'CD': (4.0, 5.5)},
    2025: {'DDA': (0.0, 0.1), 'NOW': (0.5, 1.5), 'Savings': (1.0, 2.5), 'MMDA': (2.5, 4.0), 'CD': (3.5, 5.0)},
    2026: {'DDA': (0.0, 0.1), 'NOW': (0.5, 1.5), 'Savings': (1.0, 2.5), 'MMDA': (2.5, 4.0), 'CD': (3.5, 5.0)},
}

def execute_sql(w, sql_statement, warehouse_id=WAREHOUSE_ID):
    """Execute SQL statement"""
    statement = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql_statement,
        wait_timeout="50s"
    )

    # Wait for completion
    max_wait_time = 600
    elapsed = 0
    while statement.status.state in [StatementState.PENDING, StatementState.RUNNING] and elapsed < max_wait_time:
        time.sleep(3)
        elapsed += 3
        statement = w.statement_execution.get_statement(statement.statement_id)

    if statement.status.state == StatementState.FAILED:
        error_msg = statement.status.error.message if statement.status.error else "Unknown error"
        raise Exception(f"SQL execution failed: {error_msg}")

    return statement

def get_deposit_rate(product_type, year, term_months=None):
    """Get realistic rate based on product and year"""
    min_rate, max_rate = RATE_MAP.get(year, {}).get(product_type, (0.5, 2.0))

    # CDs: rates vary by term
    if product_type == 'CD' and term_months:
        if term_months <= 6:
            max_rate = max_rate - 0.5
        elif term_months >= 24:
            max_rate = max_rate + 0.2

    return round(random.uniform(min_rate, max_rate), 4)

def assign_beta(product_type):
    """Assign deposit beta based on product type"""
    beta_map = {
        'DDA': (0.05, 0.15),
        'NOW': (0.10, 0.25),
        'Savings': (0.30, 0.50),
        'MMDA': (0.50, 0.80),
        'CD': (0.90, 1.00)
    }
    min_beta, max_beta = beta_map.get(product_type, (0.30, 0.50))
    return round(random.uniform(min_beta, max_beta), 4)

def generate_account_id(product_type, index):
    """Generate unique account ID"""
    prefix_map = {
        'DDA': 'CHK',
        'NOW': 'NOW',
        'Savings': 'SAV',
        'MMDA': 'MMD',
        'CD': 'CD'
    }
    return f"ACCT-{prefix_map[product_type]}-{index:08d}"

def generate_dda_accounts(start_index):
    """Generate DDA accounts (180,000 total: 150K retail + 25K small business + 5K commercial)"""
    accounts = []

    log_message("    Generating 150,000 retail DDA accounts...")
    # Retail checking (150,000)
    for i in range(150000):
        if i > 0 and i % 20000 == 0:
            log_message(f"      Progress: {i:,}/150,000 retail DDA accounts...")

        open_year = random.choices([2019, 2020, 2021, 2022, 2023, 2024, 2025],
                                   weights=[10, 15, 20, 20, 20, 10, 5])[0]
        open_date = datetime(open_year, random.randint(1, 12), random.randint(1, 28)).date()

        # Balance - log normal distribution
        balance = int(np.random.lognormal(9.0, 1.2))  # Mean ~$12K
        balance = max(100, min(500000, balance))

        status = random.choices(['Active', 'Dormant', 'Closed'], weights=[85, 13, 2])[0]

        accounts.append({
            'account_id': generate_account_id('DDA', start_index + i),
            'account_number': f'CHK-{start_index + i:010d}',
            'customer_id': f'CUST-{random.randint(10000, 999999)}',
            'customer_name': f'Customer {start_index + i}',
            'customer_type': 'Retail',
            'customer_segment': random.choices(['Mass_Market', 'Mass_Affluent', 'Private_Banking'],
                                              weights=[70, 25, 5])[0],
            'product_type': 'DDA',
            'product_name': random.choice(['Checking', 'Premium_Checking', 'Student_Checking']),
            'account_open_date': open_date,
            'maturity_date': None,
            'current_balance': float(balance),
            'average_balance_30d': float(balance * random.uniform(0.8, 1.2)),
            'average_balance_90d': float(balance * random.uniform(0.7, 1.3)),
            'minimum_balance': float(balance * 0.1),
            'maximum_balance': float(balance * 2.0),
            'stated_rate': get_deposit_rate('DDA', open_year),
            'beta': assign_beta('DDA'),
            'decay_rate': round(random.uniform(0.02, 0.08), 4),
            'interest_accrued': 0.0,
            'ytd_interest_paid': 0.0,
            'transaction_count_30d': random.randint(5, 50),
            'last_transaction_date': CURRENT_DATE - timedelta(days=random.randint(1, 30)),
            'account_status': status,
            'fdic_insured': True,
            'relationship_balance': float(balance * random.uniform(1.0, 3.0)),
            'has_online_banking': random.random() < 0.75,
            'has_mobile_banking': random.random() < 0.60,
            'autopay_enrolled': random.random() < 0.40,
            'overdraft_protection': random.random() < 0.30,
            'monthly_fee': random.choice([0.0, 5.0, 10.0, 15.0]),
            'fee_waivers': random.choice(['None', 'Minimum_Balance', 'Direct_Deposit']),
            'geography': random.choices(['CA', 'TX', 'FL', 'NY', 'PA', 'IL', 'OH', 'GA', 'NC', 'MI'],
                                       weights=[15, 12, 10, 8, 5, 5, 5, 5, 5, 30])[0],
            'branch_id': f'BR-{random.randint(1, 50):03d}',
            'officer_id': None,
            'effective_date': CURRENT_DATE,
            'is_current': True
        })

    log_message("    Generating 25,000 small business DDA accounts...")
    # Small business checking (25,000)
    for i in range(25000):
        if i > 0 and i % 10000 == 0:
            log_message(f"      Progress: {i:,}/25,000 small business accounts...")

        open_year = random.choices([2019, 2020, 2021, 2022, 2023, 2024, 2025],
                                   weights=[10, 15, 20, 20, 20, 10, 5])[0]
        open_date = datetime(open_year, random.randint(1, 12), random.randint(1, 28)).date()

        balance = int(np.random.lognormal(11.9, 0.8))  # Mean ~$150K
        balance = max(5000, min(5000000, balance))

        status = random.choices(['Active', 'Dormant', 'Closed'], weights=[90, 8, 2])[0]

        accounts.append({
            'account_id': generate_account_id('DDA', start_index + 150000 + i),
            'account_number': f'CHK-{start_index + 150000 + i:010d}',
            'customer_id': f'BSNS-{random.randint(10000, 99999)}',
            'customer_name': f'Business {i} LLC',
            'customer_type': 'Small_Business',
            'customer_segment': 'Commercial',
            'product_type': 'DDA',
            'product_name': 'Business_Checking',
            'account_open_date': open_date,
            'maturity_date': None,
            'current_balance': float(balance),
            'average_balance_30d': float(balance * random.uniform(0.8, 1.2)),
            'average_balance_90d': float(balance * random.uniform(0.7, 1.3)),
            'minimum_balance': float(balance * 0.3),
            'maximum_balance': float(balance * 2.5),
            'stated_rate': get_deposit_rate('DDA', open_year),
            'beta': assign_beta('DDA'),
            'decay_rate': round(random.uniform(0.05, 0.15), 4),
            'interest_accrued': 0.0,
            'ytd_interest_paid': 0.0,
            'transaction_count_30d': random.randint(20, 200),
            'last_transaction_date': CURRENT_DATE - timedelta(days=random.randint(1, 10)),
            'account_status': status,
            'fdic_insured': True,
            'relationship_balance': float(balance * random.uniform(1.5, 4.0)),
            'has_online_banking': random.random() < 0.90,
            'has_mobile_banking': random.random() < 0.70,
            'autopay_enrolled': random.random() < 0.60,
            'overdraft_protection': True,
            'monthly_fee': random.choice([15.0, 25.0, 50.0]),
            'fee_waivers': random.choice(['Minimum_Balance', 'Transaction_Volume']),
            'geography': random.choices(['CA', 'TX', 'FL', 'NY', 'PA', 'IL', 'OH', 'GA', 'NC', 'MI'],
                                       weights=[15, 12, 10, 8, 5, 5, 5, 5, 5, 30])[0],
            'branch_id': f'BR-{random.randint(1, 50):03d}',
            'officer_id': f'RO-{random.randint(1, 30):03d}',
            'effective_date': CURRENT_DATE,
            'is_current': True
        })

    log_message("    Generating 5,000 commercial DDA accounts...")
    # Commercial checking (5,000)
    for i in range(5000):
        open_year = random.choices([2019, 2020, 2021, 2022, 2023, 2024, 2025],
                                   weights=[10, 15, 20, 20, 20, 10, 5])[0]
        open_date = datetime(open_year, random.randint(1, 12), random.randint(1, 28)).date()

        balance = int(np.random.lognormal(13.5, 0.6))  # Mean ~$750K
        balance = max(25000, min(25000000, balance))

        status = random.choices(['Active', 'Dormant', 'Closed'], weights=[95, 4, 1])[0]

        accounts.append({
            'account_id': generate_account_id('DDA', start_index + 175000 + i),
            'account_number': f'CHK-{start_index + 175000 + i:010d}',
            'customer_id': f'CORP-{random.randint(1000, 9999)}',
            'customer_name': f'Corporation {i} Inc',
            'customer_type': 'Commercial',
            'customer_segment': 'Large_Corporate',
            'product_type': 'DDA',
            'product_name': 'Commercial_Checking',
            'account_open_date': open_date,
            'maturity_date': None,
            'current_balance': float(balance),
            'average_balance_30d': float(balance * random.uniform(0.8, 1.2)),
            'average_balance_90d': float(balance * random.uniform(0.7, 1.3)),
            'minimum_balance': float(balance * 0.5),
            'maximum_balance': float(balance * 3.0),
            'stated_rate': get_deposit_rate('DDA', open_year),
            'beta': assign_beta('DDA'),
            'decay_rate': round(random.uniform(0.08, 0.20), 4),
            'interest_accrued': 0.0,
            'ytd_interest_paid': 0.0,
            'transaction_count_30d': random.randint(100, 1000),
            'last_transaction_date': CURRENT_DATE - timedelta(days=random.randint(1, 5)),
            'account_status': status,
            'fdic_insured': True,
            'relationship_balance': float(balance * random.uniform(2.0, 10.0)),
            'has_online_banking': True,
            'has_mobile_banking': random.random() < 0.80,
            'autopay_enrolled': random.random() < 0.80,
            'overdraft_protection': True,
            'monthly_fee': random.choice([50.0, 100.0, 200.0]),
            'fee_waivers': 'Minimum_Balance',
            'geography': random.choices(['CA', 'TX', 'FL', 'NY', 'PA', 'IL', 'OH', 'GA', 'NC', 'MI'],
                                       weights=[15, 12, 10, 8, 5, 5, 5, 5, 5, 30])[0],
            'branch_id': f'BR-{random.randint(1, 50):03d}',
            'officer_id': f'RO-{random.randint(1, 30):03d}',
            'effective_date': CURRENT_DATE,
            'is_current': True
        })

    return accounts

def generate_now_accounts(start_index):
    """Generate NOW accounts (22,000 total)"""
    accounts = []

    log_message("    Generating 22,000 NOW accounts...")
    for i in range(22000):
        if i > 0 and i % 10000 == 0:
            log_message(f"      Progress: {i:,}/22,000 NOW accounts...")

        open_year = random.choices([2019, 2020, 2021, 2022, 2023, 2024, 2025],
                                   weights=[10, 15, 20, 20, 20, 10, 5])[0]
        open_date = datetime(open_year, random.randint(1, 12), random.randint(1, 28)).date()

        balance = int(np.random.lognormal(10.8, 0.8))  # Mean ~$50K
        balance = max(1000, min(2000000, balance))

        status = random.choices(['Active', 'Dormant', 'Closed'], weights=[85, 13, 2])[0]

        accounts.append({
            'account_id': generate_account_id('NOW', start_index + i),
            'account_number': f'NOW-{start_index + i:010d}',
            'customer_id': f'CUST-{random.randint(10000, 999999)}',
            'customer_name': f'Customer NOW {i}',
            'customer_type': random.choice(['Retail', 'Small_Business']),
            'customer_segment': random.choices(['Mass_Affluent', 'Private_Banking', 'Commercial'],
                                              weights=[50, 30, 20])[0],
            'product_type': 'NOW',
            'product_name': 'Negotiable_Order_Withdrawal',
            'account_open_date': open_date,
            'maturity_date': None,
            'current_balance': float(balance),
            'average_balance_30d': float(balance * random.uniform(0.8, 1.2)),
            'average_balance_90d': float(balance * random.uniform(0.7, 1.3)),
            'minimum_balance': float(balance * 0.2),
            'maximum_balance': float(balance * 2.5),
            'stated_rate': get_deposit_rate('NOW', open_year),
            'beta': assign_beta('NOW'),
            'decay_rate': round(random.uniform(0.03, 0.10), 4),
            'interest_accrued': 0.0,
            'ytd_interest_paid': 0.0,
            'transaction_count_30d': random.randint(3, 30),
            'last_transaction_date': CURRENT_DATE - timedelta(days=random.randint(1, 30)),
            'account_status': status,
            'fdic_insured': True,
            'relationship_balance': float(balance * random.uniform(1.2, 3.5)),
            'has_online_banking': random.random() < 0.80,
            'has_mobile_banking': random.random() < 0.65,
            'autopay_enrolled': random.random() < 0.50,
            'overdraft_protection': random.random() < 0.40,
            'monthly_fee': random.choice([0.0, 10.0, 15.0]),
            'fee_waivers': random.choice(['None', 'Minimum_Balance']),
            'geography': random.choices(['CA', 'TX', 'FL', 'NY', 'PA', 'IL', 'OH', 'GA', 'NC', 'MI'],
                                       weights=[15, 12, 10, 8, 5, 5, 5, 5, 5, 30])[0],
            'branch_id': f'BR-{random.randint(1, 50):03d}',
            'officer_id': f'RO-{random.randint(1, 30):03d}' if random.random() < 0.3 else None,
            'effective_date': CURRENT_DATE,
            'is_current': True
        })

    return accounts

def generate_savings_accounts(start_index):
    """Generate Savings accounts (110,000 total: 100K retail + 10K specialty)"""
    accounts = []

    log_message("    Generating 100,000 retail savings accounts...")
    # Retail savings (100,000)
    for i in range(100000):
        if i > 0 and i % 20000 == 0:
            log_message(f"      Progress: {i:,}/100,000 retail savings accounts...")

        open_year = random.choices([2019, 2020, 2021, 2022, 2023, 2024, 2025],
                                   weights=[10, 15, 20, 20, 20, 10, 5])[0]
        open_date = datetime(open_year, random.randint(1, 12), random.randint(1, 28)).date()

        balance = int(np.random.lognormal(10.2, 1.0))  # Mean ~$28K
        balance = max(100, min(1000000, balance))

        status = random.choices(['Active', 'Dormant', 'Closed'], weights=[85, 13, 2])[0]

        accounts.append({
            'account_id': generate_account_id('Savings', start_index + i),
            'account_number': f'SAV-{start_index + i:010d}',
            'customer_id': f'CUST-{random.randint(10000, 999999)}',
            'customer_name': f'Customer SAV {i}',
            'customer_type': 'Retail',
            'customer_segment': random.choices(['Mass_Market', 'Mass_Affluent', 'Private_Banking'],
                                              weights=[60, 30, 10])[0],
            'product_type': 'Savings',
            'product_name': random.choice(['Regular_Savings', 'High_Yield_Savings']),
            'account_open_date': open_date,
            'maturity_date': None,
            'current_balance': float(balance),
            'average_balance_30d': float(balance * random.uniform(0.9, 1.1)),
            'average_balance_90d': float(balance * random.uniform(0.8, 1.2)),
            'minimum_balance': float(balance * 0.1),
            'maximum_balance': float(balance * 1.8),
            'stated_rate': get_deposit_rate('Savings', open_year),
            'beta': assign_beta('Savings'),
            'decay_rate': round(random.uniform(0.05, 0.15), 4),
            'interest_accrued': 0.0,
            'ytd_interest_paid': 0.0,
            'transaction_count_30d': random.randint(0, 10),
            'last_transaction_date': CURRENT_DATE - timedelta(days=random.randint(1, 60)),
            'account_status': status,
            'fdic_insured': True,
            'relationship_balance': float(balance * random.uniform(1.5, 4.0)),
            'has_online_banking': random.random() < 0.75,
            'has_mobile_banking': random.random() < 0.60,
            'autopay_enrolled': random.random() < 0.20,
            'overdraft_protection': False,
            'monthly_fee': random.choice([0.0, 5.0]),
            'fee_waivers': random.choice(['None', 'Minimum_Balance', 'Linked_Account']),
            'geography': random.choices(['CA', 'TX', 'FL', 'NY', 'PA', 'IL', 'OH', 'GA', 'NC', 'MI'],
                                       weights=[15, 12, 10, 8, 5, 5, 5, 5, 5, 30])[0],
            'branch_id': f'BR-{random.randint(1, 50):03d}',
            'officer_id': None,
            'effective_date': CURRENT_DATE,
            'is_current': True
        })

    log_message("    Generating 10,000 specialty savings accounts...")
    # Specialty savings (10,000)
    for i in range(10000):
        open_year = random.choices([2019, 2020, 2021, 2022, 2023, 2024, 2025],
                                   weights=[10, 15, 20, 20, 20, 10, 5])[0]
        open_date = datetime(open_year, random.randint(1, 12), random.randint(1, 28)).date()

        balance = int(np.random.lognormal(11.3, 0.6))  # Mean ~$80K
        balance = max(5000, min(5000000, balance))

        status = random.choices(['Active', 'Dormant', 'Closed'], weights=[90, 8, 2])[0]

        accounts.append({
            'account_id': generate_account_id('Savings', start_index + 100000 + i),
            'account_number': f'SAV-{start_index + 100000 + i:010d}',
            'customer_id': f'CUST-{random.randint(10000, 999999)}',
            'customer_name': f'Customer Specialty SAV {i}',
            'customer_type': 'Retail',
            'customer_segment': random.choices(['Mass_Affluent', 'Private_Banking'],
                                              weights=[60, 40])[0],
            'product_type': 'Savings',
            'product_name': random.choice(['Premium_Savings', 'Wealth_Builder_Savings']),
            'account_open_date': open_date,
            'maturity_date': None,
            'current_balance': float(balance),
            'average_balance_30d': float(balance * random.uniform(0.9, 1.1)),
            'average_balance_90d': float(balance * random.uniform(0.85, 1.15)),
            'minimum_balance': float(balance * 0.3),
            'maximum_balance': float(balance * 2.0),
            'stated_rate': get_deposit_rate('Savings', open_year),
            'beta': assign_beta('Savings'),
            'decay_rate': round(random.uniform(0.08, 0.18), 4),
            'interest_accrued': 0.0,
            'ytd_interest_paid': 0.0,
            'transaction_count_30d': random.randint(0, 5),
            'last_transaction_date': CURRENT_DATE - timedelta(days=random.randint(1, 90)),
            'account_status': status,
            'fdic_insured': True,
            'relationship_balance': float(balance * random.uniform(2.0, 6.0)),
            'has_online_banking': random.random() < 0.85,
            'has_mobile_banking': random.random() < 0.70,
            'autopay_enrolled': random.random() < 0.30,
            'overdraft_protection': False,
            'monthly_fee': 0.0,
            'fee_waivers': 'Minimum_Balance',
            'geography': random.choices(['CA', 'TX', 'FL', 'NY', 'PA', 'IL', 'OH', 'GA', 'NC', 'MI'],
                                       weights=[15, 12, 10, 8, 5, 5, 5, 5, 5, 30])[0],
            'branch_id': f'BR-{random.randint(1, 50):03d}',
            'officer_id': f'RO-{random.randint(1, 30):03d}',
            'effective_date': CURRENT_DATE,
            'is_current': True
        })

    return accounts

def generate_mmda_accounts(start_index):
    """Generate MMDA accounts (35,000 total: 25K retail + 10K commercial)"""
    accounts = []

    log_message("    Generating 25,000 retail MMDA accounts...")
    # Retail MMDA (25,000)
    for i in range(25000):
        if i > 0 and i % 10000 == 0:
            log_message(f"      Progress: {i:,}/25,000 retail MMDA accounts...")

        open_year = random.choices([2019, 2020, 2021, 2022, 2023, 2024, 2025],
                                   weights=[10, 15, 20, 20, 20, 10, 5])[0]
        open_date = datetime(open_year, random.randint(1, 12), random.randint(1, 28)).date()

        balance = int(np.random.lognormal(11.5, 0.7))  # Mean ~$100K
        balance = max(10000, min(10000000, balance))

        status = random.choices(['Active', 'Dormant', 'Closed'], weights=[88, 10, 2])[0]

        accounts.append({
            'account_id': generate_account_id('MMDA', start_index + i),
            'account_number': f'MMD-{start_index + i:010d}',
            'customer_id': f'CUST-{random.randint(10000, 999999)}',
            'customer_name': f'Customer MMDA {i}',
            'customer_type': 'Retail',
            'customer_segment': random.choices(['Mass_Affluent', 'Private_Banking'],
                                              weights=[70, 30])[0],
            'product_type': 'MMDA',
            'product_name': 'Money_Market_Deposit',
            'account_open_date': open_date,
            'maturity_date': None,
            'current_balance': float(balance),
            'average_balance_30d': float(balance * random.uniform(0.9, 1.1)),
            'average_balance_90d': float(balance * random.uniform(0.85, 1.15)),
            'minimum_balance': float(balance * 0.4),
            'maximum_balance': float(balance * 2.2),
            'stated_rate': get_deposit_rate('MMDA', open_year),
            'beta': assign_beta('MMDA'),
            'decay_rate': round(random.uniform(0.10, 0.25), 4),
            'interest_accrued': 0.0,
            'ytd_interest_paid': 0.0,
            'transaction_count_30d': random.randint(0, 15),
            'last_transaction_date': CURRENT_DATE - timedelta(days=random.randint(1, 45)),
            'account_status': status,
            'fdic_insured': True,
            'relationship_balance': float(balance * random.uniform(1.5, 5.0)),
            'has_online_banking': random.random() < 0.85,
            'has_mobile_banking': random.random() < 0.70,
            'autopay_enrolled': random.random() < 0.35,
            'overdraft_protection': random.random() < 0.20,
            'monthly_fee': random.choice([0.0, 10.0]),
            'fee_waivers': random.choice(['Minimum_Balance', 'Linked_Account']),
            'geography': random.choices(['CA', 'TX', 'FL', 'NY', 'PA', 'IL', 'OH', 'GA', 'NC', 'MI'],
                                       weights=[15, 12, 10, 8, 5, 5, 5, 5, 5, 30])[0],
            'branch_id': f'BR-{random.randint(1, 50):03d}',
            'officer_id': f'RO-{random.randint(1, 30):03d}' if random.random() < 0.4 else None,
            'effective_date': CURRENT_DATE,
            'is_current': True
        })

    log_message("    Generating 10,000 commercial MMDA accounts...")
    # Commercial MMDA (10,000)
    for i in range(10000):
        open_year = random.choices([2019, 2020, 2021, 2022, 2023, 2024, 2025],
                                   weights=[10, 15, 20, 20, 20, 10, 5])[0]
        open_date = datetime(open_year, random.randint(1, 12), random.randint(1, 28)).date()

        balance = int(np.random.lognormal(12.2, 0.6))  # Mean ~$190K
        balance = max(25000, min(25000000, balance))

        status = random.choices(['Active', 'Dormant', 'Closed'], weights=[92, 6, 2])[0]

        accounts.append({
            'account_id': generate_account_id('MMDA', start_index + 25000 + i),
            'account_number': f'MMD-{start_index + 25000 + i:010d}',
            'customer_id': f'BSNS-{random.randint(10000, 99999)}',
            'customer_name': f'Business MMDA {i} LLC',
            'customer_type': random.choice(['Small_Business', 'Commercial']),
            'customer_segment': 'Commercial',
            'product_type': 'MMDA',
            'product_name': 'Business_Money_Market',
            'account_open_date': open_date,
            'maturity_date': None,
            'current_balance': float(balance),
            'average_balance_30d': float(balance * random.uniform(0.85, 1.15)),
            'average_balance_90d': float(balance * random.uniform(0.75, 1.25)),
            'minimum_balance': float(balance * 0.5),
            'maximum_balance': float(balance * 3.0),
            'stated_rate': get_deposit_rate('MMDA', open_year),
            'beta': assign_beta('MMDA'),
            'decay_rate': round(random.uniform(0.15, 0.30), 4),
            'interest_accrued': 0.0,
            'ytd_interest_paid': 0.0,
            'transaction_count_30d': random.randint(5, 50),
            'last_transaction_date': CURRENT_DATE - timedelta(days=random.randint(1, 20)),
            'account_status': status,
            'fdic_insured': True,
            'relationship_balance': float(balance * random.uniform(2.0, 8.0)),
            'has_online_banking': random.random() < 0.95,
            'has_mobile_banking': random.random() < 0.75,
            'autopay_enrolled': random.random() < 0.60,
            'overdraft_protection': random.random() < 0.30,
            'monthly_fee': random.choice([10.0, 15.0, 25.0]),
            'fee_waivers': 'Minimum_Balance',
            'geography': random.choices(['CA', 'TX', 'FL', 'NY', 'PA', 'IL', 'OH', 'GA', 'NC', 'MI'],
                                       weights=[15, 12, 10, 8, 5, 5, 5, 5, 5, 30])[0],
            'branch_id': f'BR-{random.randint(1, 50):03d}',
            'officer_id': f'RO-{random.randint(1, 30):03d}',
            'effective_date': CURRENT_DATE,
            'is_current': True
        })

    return accounts

def generate_cd_accounts(start_index):
    """Generate CD accounts (55,000 total: 50K retail + 5K brokered)"""
    accounts = []

    # Retail CDs (50,000)
    term_distribution = [
        (3, 5000),   # 3-month: 5,000
        (6, 10000),  # 6-month: 10,000
        (12, 20000), # 12-month: 20,000
        (24, 10000), # 24-month: 10,000
        (60, 5000),  # 60-month: 5,000
    ]

    retail_idx = 0
    for term_months, count in term_distribution:
        log_message(f"    Generating {count:,} {term_months}-month retail CDs...")
        for i in range(count):
            open_year = random.choices([2020, 2021, 2022, 2023, 2024, 2025],
                                       weights=[5, 10, 20, 30, 25, 10])[0]
            open_date = datetime(open_year, random.randint(1, 12), random.randint(1, 28)).date()

            # Maturity date
            maturity_date = open_date + relativedelta(months=term_months)

            # Check if matured and renewed
            is_matured = maturity_date < CURRENT_DATE
            if is_matured and random.random() < 0.70:  # 70% renewal rate
                # Renewed - set new maturity
                days_since_maturity = (CURRENT_DATE - maturity_date).days
                renewal_count = days_since_maturity // (term_months * 30)
                maturity_date = maturity_date + relativedelta(months=term_months * (renewal_count + 1))

            balance = int(np.random.lognormal(11.3, 0.9))  # Mean ~$80K
            balance = max(1000, min(5000000, balance))

            # Status depends on maturity
            if maturity_date < CURRENT_DATE:
                status = 'Matured'
            else:
                status = random.choices(['Active', 'Closed'], weights=[98, 2])[0]

            accounts.append({
                'account_id': generate_account_id('CD', start_index + retail_idx),
                'account_number': f'CD-{start_index + retail_idx:010d}',
                'customer_id': f'CUST-{random.randint(10000, 999999)}',
                'customer_name': f'Customer CD {retail_idx}',
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
                'stated_rate': get_deposit_rate('CD', open_year, term_months),
                'beta': assign_beta('CD'),
                'decay_rate': 0.0,  # CDs don't decay
                'interest_accrued': float(balance * get_deposit_rate('CD', open_year, term_months) / 100 / 12),
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
            retail_idx += 1

    # Brokered CDs (5,000)
    log_message(f"    Generating 5,000 brokered CD accounts...")
    for i in range(5000):
        term_months = random.choice([12, 18, 24, 36])

        open_year = random.choices([2022, 2023, 2024, 2025],
                                   weights=[10, 30, 40, 20])[0]
        open_date = datetime(open_year, random.randint(1, 12), random.randint(1, 28)).date()

        maturity_date = open_date + relativedelta(months=term_months)

        balance = int(np.random.lognormal(12.6, 0.5))  # Mean ~$300K
        balance = max(100000, min(10000000, balance))

        if maturity_date < CURRENT_DATE:
            status = 'Matured'
        else:
            status = 'Active'

        accounts.append({
            'account_id': generate_account_id('CD', start_index + 50000 + i),
            'account_number': f'CD-{start_index + 50000 + i:010d}',
            'customer_id': f'BROKER-{random.randint(100, 999)}',
            'customer_name': f'Brokered CD {i}',
            'customer_type': 'Brokered',
            'customer_segment': 'Wholesale',
            'product_type': 'CD',
            'product_name': f'Brokered_CD_{term_months}M',
            'account_open_date': open_date,
            'maturity_date': maturity_date,
            'current_balance': float(balance),
            'average_balance_30d': float(balance),
            'average_balance_90d': float(balance),
            'minimum_balance': float(balance),
            'maximum_balance': float(balance),
            'stated_rate': get_deposit_rate('CD', open_year, term_months),
            'beta': 1.00,  # Brokered CDs have beta = 1.00
            'decay_rate': 0.0,
            'interest_accrued': float(balance * get_deposit_rate('CD', open_year, term_months) / 100 / 12),
            'ytd_interest_paid': 0.0,
            'transaction_count_30d': 0,
            'last_transaction_date': open_date,
            'account_status': status,
            'fdic_insured': True,
            'relationship_balance': float(balance),
            'has_online_banking': False,
            'has_mobile_banking': False,
            'autopay_enrolled': False,
            'overdraft_protection': False,
            'monthly_fee': 0.0,
            'fee_waivers': 'None',
            'geography': 'National',
            'branch_id': 'BR-HQ',
            'officer_id': f'TRO-{random.randint(1, 5):02d}',
            'effective_date': CURRENT_DATE,
            'is_current': True
        })

    return accounts

def insert_accounts_batch(w, accounts, table_name):
    """Insert accounts in batches"""
    batch_size = 1000
    total = len(accounts)

    log_message(f"    Inserting {total:,} accounts in batches of {batch_size}...")

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

        execute_sql(w, insert_sql)

        if (batch_idx + batch_size) % 5000 == 0 or (batch_idx + batch_size) >= total:
            log_message(f"      Inserted {min(batch_idx + batch_size, total):,}/{total:,}")

def main():
    """Main execution function"""
    try:
        log_message("=" * 80)
        log_message("WS1-04: Deposit Portfolio Generator")
        log_message("=" * 80)

        # Initialize Databricks workspace client
        w = WorkspaceClient()
        log_message("✓ Connected to Databricks")
        log_message(f"✓ Using SQL Warehouse: {WAREHOUSE_ID}")

        # Step 1: Create bronze table
        log_message("\nCreating bronze layer table...")
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS cfo_banking_demo.bronze_core_banking.deposit_accounts (
            account_id STRING NOT NULL,
            account_number STRING NOT NULL,
            customer_id STRING NOT NULL,
            customer_name STRING,
            customer_type STRING,
            customer_segment STRING,
            product_type STRING NOT NULL,
            product_name STRING,
            account_open_date DATE,
            maturity_date DATE,
            current_balance DOUBLE,
            average_balance_30d DOUBLE,
            average_balance_90d DOUBLE,
            minimum_balance DOUBLE,
            maximum_balance DOUBLE,
            stated_rate DOUBLE,
            beta DOUBLE,
            decay_rate DOUBLE,
            interest_accrued DOUBLE,
            ytd_interest_paid DOUBLE,
            transaction_count_30d INT,
            last_transaction_date DATE,
            account_status STRING,
            fdic_insured BOOLEAN,
            relationship_balance DOUBLE,
            has_online_banking BOOLEAN,
            has_mobile_banking BOOLEAN,
            autopay_enrolled BOOLEAN,
            overdraft_protection BOOLEAN,
            monthly_fee DOUBLE,
            fee_waivers STRING,
            geography STRING,
            branch_id STRING,
            officer_id STRING,
            effective_date DATE,
            is_current BOOLEAN
        )
        USING DELTA
        PARTITIONED BY (product_type)
        """
        execute_sql(w, create_table_sql)
        log_message("✓ Created deposit_accounts table")

        # Step 2: Generate and insert deposit accounts
        log_message("\nGenerating DDA accounts (180,000)...")
        dda_accounts = generate_dda_accounts(0)
        insert_accounts_batch(w, dda_accounts, "cfo_banking_demo.bronze_core_banking.deposit_accounts")
        log_message(f"✓ Generated and inserted {len(dda_accounts):,} DDA accounts")

        log_message("\nGenerating NOW accounts (22,000)...")
        now_accounts = generate_now_accounts(180000)
        insert_accounts_batch(w, now_accounts, "cfo_banking_demo.bronze_core_banking.deposit_accounts")
        log_message(f"✓ Generated and inserted {len(now_accounts):,} NOW accounts")

        log_message("\nGenerating Savings accounts (110,000)...")
        savings_accounts = generate_savings_accounts(202000)
        insert_accounts_batch(w, savings_accounts, "cfo_banking_demo.bronze_core_banking.deposit_accounts")
        log_message(f"✓ Generated and inserted {len(savings_accounts):,} Savings accounts")

        log_message("\nGenerating MMDA accounts (35,000)...")
        mmda_accounts = generate_mmda_accounts(312000)
        insert_accounts_batch(w, mmda_accounts, "cfo_banking_demo.bronze_core_banking.deposit_accounts")
        log_message(f"✓ Generated and inserted {len(mmda_accounts):,} MMDA accounts")

        log_message("\nGenerating CD accounts (55,000)...")
        cd_accounts = generate_cd_accounts(347000)
        insert_accounts_batch(w, cd_accounts, "cfo_banking_demo.bronze_core_banking.deposit_accounts")
        log_message(f"✓ Generated and inserted {len(cd_accounts):,} CD accounts")

        # Get total count
        result = execute_sql(w, "SELECT COUNT(*) FROM cfo_banking_demo.bronze_core_banking.deposit_accounts")
        total_count = int(result.result.data_array[0][0]) if result.result and result.result.data_array else 0
        log_message(f"\n✓ Total accounts in database: {total_count:,}")

        # Step 3: Create silver layer
        log_message("\nCreating silver layer...")
        create_silver_sql = """
        CREATE OR REPLACE TABLE cfo_banking_demo.silver_treasury.deposit_portfolio AS
        SELECT
            *,
            CASE
                WHEN current_balance < 50000 THEN 'Small'
                WHEN current_balance < 500000 THEN 'Medium'
                WHEN current_balance < 5000000 THEN 'Large'
                ELSE 'Very_Large'
            END as balance_tier,
            MONTHS_BETWEEN(effective_date, account_open_date) as customer_lifetime_months,
            transaction_count_30d / GREATEST(MONTHS_BETWEEN(effective_date, account_open_date), 1) as account_velocity,
            (CAST(has_online_banking AS INT) * 30 +
             CAST(has_mobile_banking AS INT) * 40 +
             CAST(autopay_enrolled AS INT) * 30) as digital_engagement_score
        FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
        """
        execute_sql(w, create_silver_sql)
        log_message("✓ Created silver layer: cfo_banking_demo.silver_treasury.deposit_portfolio")

        # Step 4: Generate summary statistics
        log_message("\nGenerating summary statistics...")
        summary_sql = """
        SELECT
            product_type,
            COUNT(*) as account_count,
            SUM(current_balance) as total_balance
        FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
        GROUP BY product_type
        ORDER BY product_type
        """
        result = execute_sql(w, summary_sql)

        log_message("\n" + "=" * 80)
        log_message("DEPOSIT PORTFOLIO SUMMARY (as of 2026-01-24)")
        log_message("=" * 80)

        total_balance = 0.0
        if result.result and result.result.data_array:
            for row in result.result.data_array:
                product_type = row[0]
                count = int(row[1])
                balance = float(row[2])
                total_balance += balance
                log_message(f"  {product_type:15} ${balance:>15,.0f}  {count:>7,} accounts")

        log_message(f"\n  {'TOTAL':15} ${total_balance:>15,.0f}  {total_count:>7,} accounts")

        # Step 5: Validate data
        log_message("\n" + "=" * 80)
        log_message("DATA QUALITY VALIDATION")
        log_message("=" * 80)

        validation_passed = True

        # Check account count
        if not (395000 <= total_count <= 410000):
            log_message(f"✗ Expected ~402K accounts (±5K), got {total_count:,}", "ERROR")
            validation_passed = False
        else:
            log_message(f"✓ Account count in expected range: {total_count:,}")

        # Check total balance
        if not (20e9 <= total_balance <= 24e9):
            log_message(f"✗ Expected ~$22B (±$2B), got ${total_balance:,.0f}", "ERROR")
            validation_passed = False
        else:
            log_message(f"✓ Total balance in expected range: ${total_balance:,.0f}")

        # Check unique account IDs
        result = execute_sql(w, "SELECT COUNT(DISTINCT account_id) FROM cfo_banking_demo.bronze_core_banking.deposit_accounts")
        unique_ids = int(result.result.data_array[0][0]) if result.result and result.result.data_array else 0
        if unique_ids != total_count:
            log_message(f"✗ Account IDs not unique: {unique_ids}/{total_count}", "ERROR")
            validation_passed = False
        else:
            log_message(f"✓ All account IDs unique ({unique_ids:,})")

        # Check beta values
        result = execute_sql(w, "SELECT COUNT(*) FROM cfo_banking_demo.bronze_core_banking.deposit_accounts WHERE beta < 0 OR beta > 1")
        invalid_beta = int(result.result.data_array[0][0]) if result.result and result.result.data_array else 0
        if invalid_beta > 0:
            log_message(f"✗ Found {invalid_beta} accounts with invalid beta", "ERROR")
            validation_passed = False
        else:
            log_message(f"✓ All beta values between 0 and 1")

        if validation_passed:
            log_message("\n✅ All data quality checks passed")
        else:
            log_message("\n❌ Some data quality checks failed", "ERROR")

        log_message("\n" + "=" * 80)
        log_message("✅ WS1-04 Complete: Deposit Portfolio Generated Successfully")
        log_message("=" * 80)
        log_message("\nNote: Behavior history generation (36 months, ~14.5M records)")
        log_message("      will be added in a separate step due to size")

        return 0

    except Exception as e:
        log_message(f"\n\nError: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
