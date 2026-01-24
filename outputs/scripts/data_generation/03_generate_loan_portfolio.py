#!/usr/bin/env python3
"""
WS1-03: Loan Portfolio Generator
Generates realistic loan portfolio data for US regional bank

Portfolio: ~$18B across 97,200 loans
- Commercial RE: $4.5B (1,500 loans)
- C&I: $5.4B (2,700 loans)
- Residential: $4.5B (15,000 loans)
- HELOC: $1.44B (12,000 loans)
- Consumer Auto: $1.44B (48,000 loans)
- Consumer Other: $720M (18,000 loans)

Uses Databricks SQL Warehouse for execution
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import random
import numpy as np
from datetime import datetime, timedelta
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

# Interest rate ranges by year and product
RATE_MAP = {
    2019: {'Commercial_RE': (3.5, 4.5), 'CNI': (3.5, 4.5), 'Residential_Mortgage': (3.0, 4.0), 'HELOC': (4.0, 5.0), 'Consumer_Auto': (3.5, 5.5), 'Consumer_Other': (6.0, 9.0)},
    2020: {'Commercial_RE': (3.0, 4.0), 'CNI': (3.0, 4.0), 'Residential_Mortgage': (2.5, 3.5), 'HELOC': (3.5, 4.5), 'Consumer_Auto': (3.0, 5.0), 'Consumer_Other': (5.0, 8.0)},
    2021: {'Commercial_RE': (3.0, 4.5), 'CNI': (3.5, 4.5), 'Residential_Mortgage': (2.5, 3.5), 'HELOC': (3.5, 5.0), 'Consumer_Auto': (3.0, 5.0), 'Consumer_Other': (5.0, 8.0)},
    2022: {'Commercial_RE': (5.0, 7.0), 'CNI': (5.5, 7.5), 'Residential_Mortgage': (4.0, 6.0), 'HELOC': (5.0, 7.0), 'Consumer_Auto': (5.0, 8.0), 'Consumer_Other': (7.0, 11.0)},
    2023: {'Commercial_RE': (6.0, 8.0), 'CNI': (6.5, 8.5), 'Residential_Mortgage': (5.0, 7.0), 'HELOC': (6.0, 8.0), 'Consumer_Auto': (6.0, 9.0), 'Consumer_Other': (8.0, 12.0)},
    2024: {'Commercial_RE': (7.0, 9.0), 'CNI': (7.5, 9.5), 'Residential_Mortgage': (6.0, 7.5), 'HELOC': (7.0, 9.0), 'Consumer_Auto': (7.0, 11.0), 'Consumer_Other': (9.0, 14.0)},
    2025: {'Commercial_RE': (6.5, 8.5), 'CNI': (7.0, 9.0), 'Residential_Mortgage': (6.0, 7.0), 'HELOC': (6.5, 8.5), 'Consumer_Auto': (6.5, 10.0), 'Consumer_Other': (8.5, 13.0)},
    2026: {'Commercial_RE': (6.5, 8.5), 'CNI': (7.0, 9.0), 'Residential_Mortgage': (6.5, 7.0), 'HELOC': (6.5, 8.5), 'Consumer_Auto': (6.5, 10.0), 'Consumer_Other': (8.5, 13.0)},
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

def get_interest_rate(product_type, year):
    """Get realistic rate based on product and year"""
    min_rate, max_rate = RATE_MAP.get(year, {}).get(product_type, (5.0, 7.0))
    return round(random.uniform(min_rate, max_rate), 4)

def calculate_cecl_params(credit_score, product_type, payment_status):
    """Calculate CECL parameters"""
    # PD (Probability of Default)
    status_pd_map = {
        'Current': 0.01,
        'Past_Due_30': 0.05,
        'Past_Due_60': 0.10,
        'Past_Due_90': 0.15,
        'Default': 0.25,
        'Charged_Off': 1.0
    }
    base_pd = status_pd_map.get(payment_status, 0.01)

    # Adjust for credit score
    if credit_score:
        score_adjustment = (750 - credit_score) / 1000
        pd = max(0.001, min(0.999, base_pd + score_adjustment))
    else:
        pd = base_pd

    # LGD (Loss Given Default) by product
    lgd_map = {
        'Commercial_RE': 0.10,
        'CNI': 0.30,
        'Residential_Mortgage': 0.15,
        'HELOC': 0.25,
        'Consumer_Auto': 0.40,
        'Consumer_Other': 0.70
    }
    lgd = lgd_map.get(product_type, 0.30)

    return pd, lgd

def generate_loan_batch(product_type, count, start_index, avg_amount, prefix, product_config):
    """Generate a batch of loans for a given product type"""
    loans = []

    for i in range(count):
        # Origination year distribution
        year = random.choices(
            [2019, 2020, 2021, 2022, 2023, 2024, 2025],
            weights=[5, 10, 15, 25, 25, 15, 5]
        )[0]
        orig_date = datetime(year, random.randint(1, 12), random.randint(1, 28)).date()

        # Loan amount (log-normal distribution)
        amount = int(np.random.lognormal(np.log(avg_amount), product_config['amount_stddev']))
        amount = max(product_config['min_amount'], min(product_config['max_amount'], amount))

        # Term
        term_months = random.choice(product_config['term_options'])
        maturity_date = orig_date + timedelta(days=term_months * 30)

        # Current balance (amortized)
        months_elapsed = (CURRENT_DATE.year - orig_date.year) * 12 + (CURRENT_DATE.month - orig_date.month)
        months_elapsed = max(0, months_elapsed)
        amort_pct = min(1.0, months_elapsed / term_months) if term_months > 0 else 0
        current_balance = amount * (1 - amort_pct * product_config['amort_factor'])

        # Interest rate
        rate = get_interest_rate(product_type, year)

        # Credit score (for consumer products)
        if product_config['has_credit_score']:
            credit_score = int(np.random.normal(720, 60))
            credit_score = max(500, min(850, credit_score))
        else:
            credit_score = None

        # Payment status
        status = random.choices(
            ['Current', 'Past_Due_30', 'Past_Due_60', 'Past_Due_90', 'Default', 'Charged_Off'],
            weights=[94, 3, 1.5, 1, 0.3, 0.2]
        )[0]

        dpd_map = {
            'Current': 0,
            'Past_Due_30': random.randint(30, 59),
            'Past_Due_60': random.randint(60, 89),
            'Past_Due_90': random.randint(90, 179),
            'Default': random.randint(180, 365),
            'Charged_Off': 0
        }
        days_past_due = dpd_map[status]

        # CECL
        pd, lgd = calculate_cecl_params(credit_score, product_type, status)
        ead = current_balance
        cecl_reserve = ead * pd * lgd

        # Geography
        state = random.choices(
            ['CA', 'TX', 'FL', 'NY', 'PA', 'IL', 'OH', 'GA', 'NC', 'MI'],
            weights=[15, 12, 10, 8, 6, 5, 5, 5, 4, 30]
        )[0]

        # Build loan record
        loan_index = start_index + i
        loan_id = f"LOAN-{prefix}-{loan_index:06d}"

        loan = (
            loan_id,
            f'ACC-{loan_index:010d}',
            f'BWID-{random.randint(10000, 99999)}',
            product_config['borrower_name'](i, loan_index),
            product_config['borrower_type'],
            product_type,
            product_config['loan_purpose'](i),
            orig_date.isoformat(),
            maturity_date.isoformat(),
            float(amount),
            float(current_balance),
            float(current_balance * 0.98),
            float(current_balance * 0.02),
            0.0,
            rate,
            product_config['rate_type'](),
            product_config['rate_index']() if product_config['has_rate_index'] else None,
            round(random.uniform(1.5, 3.5), 4) if product_config['has_rate_margin'] else None,
            'Monthly',
            float(current_balance * (rate/100/12)) if current_balance > 0 else 0,
            status,
            days_past_due,
            (CURRENT_DATE + timedelta(days=30)).isoformat(),
            (CURRENT_DATE - timedelta(days=random.randint(1, 30))).isoformat(),
            float(current_balance * (rate/100/12)) if current_balance > 0 else 0,
            max(0, term_months - months_elapsed),
            term_months,
            product_config['collateral_type'](i),
            float(amount * random.uniform(1.2, 2.0)) if product_config['has_collateral'] else None,
            round(current_balance / (amount * 1.5), 4) if amount > 0 else 0,
            credit_score,
            product_config['risk_rating'](),
            round(pd, 6),
            round(lgd, 6),
            float(ead),
            float(cecl_reserve),
            state,
            product_config['industry_code'],
            f'LO-{random.randint(1, 50):03d}',
            f'BR-{random.randint(1, 20):03d}',
            CURRENT_DATE.isoformat(),
            True
        )

        loans.append(loan)

    return loans

def main():
    """Main execution"""
    log_message("=" * 80)
    log_message("WS1-03: Loan Portfolio Generator")
    log_message("=" * 80)

    w = WorkspaceClient()
    log_message(f"✓ Connected to Databricks")
    log_message(f"✓ Using SQL Warehouse: {WAREHOUSE_ID}")

    # Product configurations
    products = [
        {
            'type': 'Commercial_RE',
            'count': 1500,
            'avg_amount': 3_000_000,
            'prefix': 'CRE',
            'config': {
                'min_amount': 500_000,
                'max_amount': 50_000_000,
                'amount_stddev': 0.6,
                'term_options': [60, 84, 120, 180, 240, 300],
                'amort_factor': 0.3,
                'has_credit_score': False,
                'borrower_type': 'Business',
                'borrower_name': lambda i, idx: f'Commercial Properties LLC {idx}',
                'loan_purpose': lambda i: random.choice(['Office', 'Retail', 'Multifamily', 'Industrial']),
                'rate_type': lambda: random.choice(['Fixed', 'Variable']),
                'has_rate_index': True,
                'rate_index': lambda: 'SOFR' if random.choice([True, False]) else None,
                'has_rate_margin': True,
                'collateral_type': lambda i: random.choice(['Office', 'Retail', 'Multifamily', 'Industrial']),
                'has_collateral': True,
                'risk_rating': lambda: random.choices(['Pass', 'Watch', 'Special_Mention', 'Substandard'], weights=[85, 10, 3, 2])[0],
                'industry_code': '531'
            }
        },
        {
            'type': 'CNI',
            'count': 2700,
            'avg_amount': 2_000_000,
            'prefix': 'CNI',
            'config': {
                'min_amount': 100_000,
                'max_amount': 25_000_000,
                'amount_stddev': 0.7,
                'term_options': [36, 60, 84, 120],
                'amort_factor': 0.4,
                'has_credit_score': False,
                'borrower_type': 'Business',
                'borrower_name': lambda i, idx: f'Business Corp {idx}',
                'loan_purpose': lambda i: random.choice(['Working_Capital', 'Equipment', 'Term_Loan', 'Acquisition']),
                'rate_type': lambda: random.choice(['Fixed', 'Variable']),
                'has_rate_index': True,
                'rate_index': lambda: 'SOFR' if random.choice([True, False]) else None,
                'has_rate_margin': True,
                'collateral_type': lambda i: random.choice(['Equipment', 'Inventory', 'Receivables', 'General']),
                'has_collateral': True,
                'risk_rating': lambda: random.choices(['Pass', 'Watch', 'Special_Mention', 'Substandard'], weights=[85, 10, 3, 2])[0],
                'industry_code': random.choice(['211', '236', '311', '423', '441', '722'])
            }
        },
        {
            'type': 'Residential_Mortgage',
            'count': 15000,
            'avg_amount': 300_000,
            'prefix': 'RES',
            'config': {
                'min_amount': 100_000,
                'max_amount': 2_000_000,
                'amount_stddev': 0.5,
                'term_options': [180, 240, 360],
                'amort_factor': 0.25,
                'has_credit_score': True,
                'borrower_type': 'Individual',
                'borrower_name': lambda i, idx: f'Homeowner {idx}',
                'loan_purpose': lambda i: random.choice(['Purchase', 'Refinance']),
                'rate_type': lambda: random.choices(['Fixed', 'ARM'], weights=[85, 15])[0],
                'has_rate_index': False,
                'rate_index': lambda: None,
                'has_rate_margin': False,
                'collateral_type': lambda i: 'Residential_Property',
                'has_collateral': True,
                'risk_rating': lambda: random.choices(['Pass', 'Watch'], weights=[96, 4])[0],
                'industry_code': None
            }
        },
        {
            'type': 'HELOC',
            'count': 12000,
            'avg_amount': 120_000,
            'prefix': 'HEL',
            'config': {
                'min_amount': 10_000,
                'max_amount': 500_000,
                'amount_stddev': 0.6,
                'term_options': [120, 180, 240],
                'amort_factor': 0.2,
                'has_credit_score': True,
                'borrower_type': 'Individual',
                'borrower_name': lambda i, idx: f'HELOC Borrower {idx}',
                'loan_purpose': lambda i: random.choice(['Home_Improvement', 'Debt_Consolidation', 'Education']),
                'rate_type': lambda: 'Variable',
                'has_rate_index': True,
                'rate_index': lambda: 'Prime',
                'has_rate_margin': True,
                'collateral_type': lambda i: 'Home_Equity',
                'has_collateral': True,
                'risk_rating': lambda: random.choices(['Pass', 'Watch'], weights=[94, 6])[0],
                'industry_code': None
            }
        },
        {
            'type': 'Consumer_Auto',
            'count': 48000,
            'avg_amount': 30_000,
            'prefix': 'AUTO',
            'config': {
                'min_amount': 5_000,
                'max_amount': 100_000,
                'amount_stddev': 0.5,
                'term_options': [36, 48, 60, 72, 84],
                'amort_factor': 0.6,
                'has_credit_score': True,
                'borrower_type': 'Individual',
                'borrower_name': lambda i, idx: f'Auto Buyer {idx}',
                'loan_purpose': lambda i: random.choice(['New_Vehicle', 'Used_Vehicle']),
                'rate_type': lambda: 'Fixed',
                'has_rate_index': False,
                'rate_index': lambda: None,
                'has_rate_margin': False,
                'collateral_type': lambda i: 'Vehicle',
                'has_collateral': True,
                'risk_rating': lambda: random.choices(['Pass', 'Watch'], weights=[92, 8])[0],
                'industry_code': None
            }
        },
        {
            'type': 'Consumer_Other',
            'count': 18000,
            'avg_amount': 40_000,
            'prefix': 'CONS',
            'config': {
                'min_amount': 1_000,
                'max_amount': 100_000,
                'amount_stddev': 0.7,
                'term_options': [12, 24, 36, 48, 60],
                'amort_factor': 0.7,
                'has_credit_score': True,
                'borrower_type': 'Individual',
                'borrower_name': lambda i, idx: f'Consumer {idx}',
                'loan_purpose': lambda i: random.choice(['Personal', 'Debt_Consolidation', 'Medical', 'Education']),
                'rate_type': lambda: 'Fixed',
                'has_rate_index': False,
                'rate_index': lambda: None,
                'has_rate_margin': False,
                'collateral_type': lambda i: None,
                'has_collateral': False,
                'risk_rating': lambda: random.choices(['Pass', 'Watch'], weights=[88, 12])[0],
                'industry_code': None
            }
        }
    ]

    # Create bronze table
    log_message("\nCreating bronze layer table...")

    create_table_sql = """
    CREATE OR REPLACE TABLE cfo_banking_demo.bronze_core_banking.loan_portfolio (
        loan_id STRING NOT NULL,
        account_number STRING NOT NULL,
        borrower_id STRING NOT NULL,
        borrower_name STRING NOT NULL,
        borrower_type STRING NOT NULL,
        product_type STRING NOT NULL,
        loan_purpose STRING,
        origination_date DATE NOT NULL,
        maturity_date DATE NOT NULL,
        original_amount DOUBLE NOT NULL,
        current_balance DOUBLE NOT NULL,
        principal_balance DOUBLE NOT NULL,
        interest_accrued DOUBLE NOT NULL,
        fees_accrued DOUBLE NOT NULL,
        interest_rate DOUBLE NOT NULL,
        rate_type STRING,
        rate_index STRING,
        rate_margin DOUBLE,
        payment_frequency STRING NOT NULL,
        monthly_payment DOUBLE NOT NULL,
        payment_status STRING NOT NULL,
        days_past_due INT NOT NULL,
        next_payment_date DATE NOT NULL,
        last_payment_date DATE,
        last_payment_amount DOUBLE,
        remaining_term_months INT NOT NULL,
        original_term_months INT NOT NULL,
        collateral_type STRING,
        collateral_value DOUBLE,
        ltv_ratio DOUBLE,
        credit_score INT,
        risk_rating STRING NOT NULL,
        pd DOUBLE NOT NULL,
        lgd DOUBLE NOT NULL,
        ead DOUBLE NOT NULL,
        cecl_reserve DOUBLE NOT NULL,
        geography STRING NOT NULL,
        industry_code STRING,
        officer_id STRING NOT NULL,
        branch_id STRING NOT NULL,
        effective_date DATE NOT NULL,
        is_current BOOLEAN NOT NULL
    )
    PARTITIONED BY (product_type)
    """

    execute_sql(w, create_table_sql)
    log_message("✓ Created loan_portfolio table")

    # Generate and insert loans by product type
    total_loans = 0
    start_index = 0

    for product in products:
        log_message(f"\nGenerating {product['type']} loans ({product['count']:,})...")

        loans = generate_loan_batch(
            product['type'],
            product['count'],
            start_index,
            product['avg_amount'],
            product['prefix'],
            product['config']
        )

        log_message(f"  Generated {len(loans):,} {product['type']} loans")

        # Insert in batches
        batch_size = 1000
        for batch_idx in range(0, len(loans), batch_size):
            batch = loans[batch_idx:batch_idx + batch_size]
            values_list = []

            for loan in batch:
                # Format values with proper NULL handling
                formatted_vals = []
                for val in loan:
                    if val is None:
                        formatted_vals.append('NULL')
                    elif isinstance(val, bool):
                        formatted_vals.append('true' if val else 'false')
                    elif isinstance(val, (int, float)):
                        formatted_vals.append(str(val))
                    else:
                        formatted_vals.append(f"'{str(val)}'")

                values_list.append(f"({', '.join(formatted_vals)})")

            insert_sql = f"""
            INSERT INTO cfo_banking_demo.bronze_core_banking.loan_portfolio VALUES
            {', '.join(values_list)}
            """

            execute_sql(w, insert_sql)

            if (batch_idx + batch_size) % 5000 == 0 or (batch_idx + batch_size) >= len(loans):
                log_message(f"    Inserted {min(batch_idx + batch_size, len(loans)):,}/{len(loans):,}")

        total_loans += len(loans)
        start_index += product['count']

    log_message(f"\n✓ Total loans inserted: {total_loans:,}")

    # Create silver layer
    log_message("\nCreating silver layer...")

    create_silver_sql = """
    CREATE OR REPLACE TABLE cfo_banking_demo.silver_finance.loan_portfolio AS
    SELECT
        *,
        current_balance / NULLIF(original_amount, 0) as utilization_rate,
        CAST(DATEDIFF(effective_date, origination_date) / 30 AS INT) as months_since_origination,
        CASE
            WHEN payment_status = 'Current' THEN 'Current'
            WHEN payment_status LIKE 'Past_Due%' THEN 'Delinquent'
            ELSE 'Default'
        END as delinquency_status
    FROM cfo_banking_demo.bronze_core_banking.loan_portfolio
    """

    execute_sql(w, create_silver_sql)
    log_message("✓ Created silver layer")

    # Validations and summary
    log_message("\n" + "=" * 80)
    log_message("Running Validations and Generating Summary")
    log_message("=" * 80)

    # Count by product
    count_sql = """
    SELECT
        product_type,
        COUNT(*) as loan_count,
        SUM(current_balance) as total_balance,
        AVG(interest_rate) as avg_rate,
        SUM(cecl_reserve) as total_reserve
    FROM cfo_banking_demo.silver_finance.loan_portfolio
    GROUP BY product_type
    ORDER BY total_balance DESC
    """

    result = execute_sql(w, count_sql)

    log_message("\nLoan Portfolio Summary:")
    log_message("-" * 80)

    grand_total_balance = 0
    grand_total_reserve = 0
    grand_total_count = 0

    if result.result and result.result.data_array:
        for row in result.result.data_array:
            prod_type = row[0]
            count = int(row[1])
            balance = float(row[2])
            avg_rate = float(row[3])
            reserve = float(row[4])

            grand_total_count += count
            grand_total_balance += balance
            grand_total_reserve += reserve

            pct = (balance / grand_total_balance * 100) if grand_total_balance > 0 else 0
            log_message(f"  {prod_type:20} {count:7,} loans  ${balance:14,.0f} ({pct:5.1f}%)  Avg Rate: {avg_rate:5.2f}%")

    log_message("-" * 80)
    log_message(f"  {'TOTAL':20} {grand_total_count:7,} loans  ${grand_total_balance:14,.0f} (100.0%)")
    log_message(f"\n  Total CECL Reserve: ${grand_total_reserve:,.0f} ({grand_total_reserve/grand_total_balance*100:.2f}%)")

    # Payment status distribution
    status_sql = """
    SELECT
        payment_status,
        COUNT(*) as count,
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage
    FROM cfo_banking_demo.silver_finance.loan_portfolio
    GROUP BY payment_status
    ORDER BY count DESC
    """

    result = execute_sql(w, status_sql)

    log_message("\nPayment Status Distribution:")
    log_message("-" * 80)

    if result.result and result.result.data_array:
        for row in result.result.data_array:
            status = row[0]
            count = int(row[1])
            pct = float(row[2])
            log_message(f"  {status:15} {count:7,} loans ({pct:5.2f}%)")

    log_message("\n" + "=" * 80)
    log_message("✅ WS1-03 Complete!")
    log_message("=" * 80)
    log_message(f"\nBronze table: cfo_banking_demo.bronze_core_banking.loan_portfolio")
    log_message(f"Silver table: cfo_banking_demo.silver_finance.loan_portfolio")
    log_message(f"\n✅ Ready for WS1-04")

    return 0

if __name__ == "__main__":
    import sys
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        log_message(f"\n\nError: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
