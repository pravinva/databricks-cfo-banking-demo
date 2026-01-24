#!/usr/bin/env python3
"""
WS2-02: Real-Time Loan Origination Pipeline
Generate loan originations, create GL entries, update loan subledger
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import random
import time
from datetime import datetime, timedelta, date

def log_message(message, level="INFO"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

# Constants
WAREHOUSE_ID = "4b9b953939869799"
CURRENT_DATE = date.today()

def execute_sql(w, sql_statement, warehouse_id=WAREHOUSE_ID):
    """Execute SQL statement with extended timeout"""
    statement = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql_statement,
        wait_timeout="50s"
    )

    # Wait for completion
    max_wait_time = 300  # 5 minutes max
    elapsed = 0
    while statement.status.state in [StatementState.PENDING, StatementState.RUNNING] and elapsed < max_wait_time:
        time.sleep(3)
        elapsed += 3
        statement = w.statement_execution.get_statement(statement.statement_id)

    if statement.status.state == StatementState.FAILED:
        error_msg = statement.status.error.message if statement.status.error else "Unknown error"
        raise Exception(f"SQL execution failed: {error_msg}")

    return statement

def generate_loan_origination_messages(count=50):
    """Generate loan origination messages"""

    product_types = ['C&I', 'Commercial_RE', 'Residential_Mortgage', 'Consumer_Auto']

    # Loan amount based on product
    amount_ranges = {
        'C&I': (500_000, 5_000_000),
        'Commercial_RE': (1_000_000, 10_000_000),
        'Residential_Mortgage': (200_000, 1_500_000),
        'Consumer_Auto': (15_000, 75_000)
    }

    messages = []

    log_message(f"Generating {count} loan origination messages...")

    for i in range(count):
        product = random.choice(product_types)
        min_amt, max_amt = amount_ranges[product]
        amount = random.randint(min_amt, max_amt)

        # Term months based on product
        if product == 'C&I':
            term_months = random.choice([12, 24, 36, 60])
        elif product == 'Commercial_RE':
            term_months = random.choice([60, 120, 180, 240])
        elif product == 'Residential_Mortgage':
            term_months = random.choice([180, 240, 360])
        else:  # Consumer_Auto
            term_months = random.choice([36, 48, 60, 72])

        maturity_date = CURRENT_DATE + timedelta(days=term_months * 30)

        message = {
            'message_id': f'LO-{datetime.now().strftime("%Y%m%d-%H%M%S")}-{i:04d}',
            'timestamp': datetime.now(),
            'loan_id': f'LOAN-NEW-{900000 + i}',
            'borrower_id': f'CUST-{random.randint(10000, 99999)}',
            'borrower_name': f'Borrower {i+1}',
            'product_type': product,
            'loan_amount': float(amount),
            'interest_rate': round(random.uniform(6.5, 9.0), 4),
            'term_months': term_months,
            'origination_date': CURRENT_DATE,
            'maturity_date': maturity_date,
            'disbursement_account': f'DDA-{random.randint(100000, 999999)}',
            'collateral_type': 'Real_Estate' if product in ['Commercial_RE', 'Residential_Mortgage'] else 'Equipment',
            'collateral_value': float(amount * random.uniform(1.2, 2.0)),
            'officer_id': f'LO-{random.randint(1, 50):03d}',
            'branch_id': f'BR-{random.randint(1, 20):03d}',
            'credit_score': random.randint(650, 800) if product in ['Residential_Mortgage', 'Consumer_Auto'] else None,
            'status': 'approved'
        }

        messages.append(message)

    log_message(f"  ✓ Generated {count} loan origination messages")
    return messages

def create_bronze_table(w):
    """Create bronze table for loan origination events"""

    log_message("Creating bronze loan origination table...")

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS cfo_banking_demo.bronze_core_banking.loan_origination_events (
        message_id STRING,
        timestamp TIMESTAMP,
        loan_id STRING,
        borrower_id STRING,
        borrower_name STRING,
        product_type STRING,
        loan_amount DECIMAL(18,2),
        interest_rate DECIMAL(8,4),
        term_months INT,
        origination_date DATE,
        maturity_date DATE,
        disbursement_account STRING,
        collateral_type STRING,
        collateral_value DECIMAL(18,2),
        officer_id STRING,
        branch_id STRING,
        credit_score INT,
        status STRING,
        ingestion_timestamp TIMESTAMP
    )
    """

    execute_sql(w, create_table_sql)
    log_message("  ✓ Created loan_origination_events table")

def insert_loan_messages(w, messages):
    """Insert loan origination messages into bronze table"""

    log_message(f"Inserting {len(messages)} loan origination messages...")

    # Batch insert
    batch_size = 25
    for i in range(0, len(messages), batch_size):
        batch = messages[i:i+batch_size]

        values_list = []
        for msg in batch:
            credit_score = msg['credit_score'] if msg['credit_score'] else 'NULL'

            values = f"""(
                '{msg['message_id']}', '{msg['timestamp']}', '{msg['loan_id']}',
                '{msg['borrower_id']}', '{msg['borrower_name']}', '{msg['product_type']}',
                {msg['loan_amount']}, {msg['interest_rate']}, {msg['term_months']},
                '{msg['origination_date']}', '{msg['maturity_date']}', '{msg['disbursement_account']}',
                '{msg['collateral_type']}', {msg['collateral_value']}, '{msg['officer_id']}',
                '{msg['branch_id']}', {credit_score}, '{msg['status']}', CURRENT_TIMESTAMP()
            )"""
            values_list.append(values)

        insert_sql = f"""
        INSERT INTO cfo_banking_demo.bronze_core_banking.loan_origination_events
        VALUES {', '.join(values_list)}
        """

        execute_sql(w, insert_sql)

    log_message(f"  ✓ Inserted {len(messages)} loan origination messages")

def create_gl_tables(w):
    """Create GL entry tables"""

    log_message("Creating GL entry tables...")

    # GL entry headers
    create_headers_sql = """
    CREATE TABLE IF NOT EXISTS cfo_banking_demo.silver_finance.gl_entries_from_loans (
        entry_id STRING,
        entry_date DATE,
        entry_timestamp TIMESTAMP,
        posting_date DATE,
        accounting_period STRING,
        entry_type STRING,
        source_system STRING,
        source_transaction_id STRING,
        batch_id STRING,
        entry_status STRING,
        description STRING,
        total_debits DECIMAL(18,2),
        total_credits DECIMAL(18,2),
        created_by STRING,
        approved_by STRING,
        is_balanced BOOLEAN,
        is_reversed BOOLEAN,
        reversed_by_entry_id STRING,
        effective_timestamp TIMESTAMP
    )
    """
    execute_sql(w, create_headers_sql)
    log_message("  ✓ Created gl_entries_from_loans table")

    # GL entry lines
    create_lines_sql = """
    CREATE TABLE IF NOT EXISTS cfo_banking_demo.silver_finance.gl_entry_lines_from_loans (
        line_id STRING,
        entry_id STRING,
        line_number INT,
        account_number STRING,
        debit_amount DECIMAL(18,2),
        credit_amount DECIMAL(18,2),
        line_description STRING,
        cost_center STRING,
        department STRING,
        product_code STRING,
        customer_id STRING,
        reference_number STRING,
        effective_timestamp TIMESTAMP
    )
    """
    execute_sql(w, create_lines_sql)
    log_message("  ✓ Created gl_entry_lines_from_loans table")

def generate_gl_entries(w):
    """Generate GL entries from loan origination messages"""

    log_message("Generating GL entry headers...")

    # Insert GL headers
    insert_headers_sql = """
    INSERT INTO cfo_banking_demo.silver_finance.gl_entries_from_loans
    SELECT
        CONCAT('GLE-', DATE_FORMAT(timestamp, 'yyyyMMdd-HHmmss'), '-', loan_id) as entry_id,
        origination_date as entry_date,
        timestamp as entry_timestamp,
        origination_date as posting_date,
        DATE_FORMAT(origination_date, 'yyyy-MM') as accounting_period,
        'Regular' as entry_type,
        'Loan_Origination' as source_system,
        message_id as source_transaction_id,
        NULL as batch_id,
        'Posted' as entry_status,
        CONCAT('Loan origination - ', loan_id, ' - ', product_type) as description,
        loan_amount as total_debits,
        loan_amount as total_credits,
        'system' as created_by,
        'system' as approved_by,
        true as is_balanced,
        false as is_reversed,
        NULL as reversed_by_entry_id,
        CURRENT_TIMESTAMP() as effective_timestamp
    FROM cfo_banking_demo.bronze_core_banking.loan_origination_events
    WHERE status = 'approved'
    """

    execute_sql(w, insert_headers_sql)
    log_message("  ✓ Generated GL entry headers")

    log_message("Generating GL entry lines (debits and credits)...")

    # Insert debit lines (Loans account)
    insert_debits_sql = """
    INSERT INTO cfo_banking_demo.silver_finance.gl_entry_lines_from_loans
    SELECT
        CONCAT(message_id, '-DEBIT') as line_id,
        CONCAT('GLE-', DATE_FORMAT(timestamp, 'yyyyMMdd-HHmmss'), '-', loan_id) as entry_id,
        1 as line_number,
        CASE
            WHEN product_type = 'C&I' THEN '1210-000'
            WHEN product_type = 'Commercial_RE' THEN '1200-000'
            WHEN product_type = 'Residential_Mortgage' THEN '1220-000'
            ELSE '1230-000'
        END as account_number,
        loan_amount as debit_amount,
        0 as credit_amount,
        CONCAT('Loan disbursement - ', loan_id) as line_description,
        branch_id as cost_center,
        'Lending' as department,
        product_type as product_code,
        borrower_id as customer_id,
        loan_id as reference_number,
        CURRENT_TIMESTAMP() as effective_timestamp
    FROM cfo_banking_demo.bronze_core_banking.loan_origination_events
    WHERE status = 'approved'
    """

    execute_sql(w, insert_debits_sql)
    log_message("  ✓ Generated debit lines (loan accounts)")

    # Insert credit lines (DDA Deposits account)
    insert_credits_sql = """
    INSERT INTO cfo_banking_demo.silver_finance.gl_entry_lines_from_loans
    SELECT
        CONCAT(message_id, '-CREDIT') as line_id,
        CONCAT('GLE-', DATE_FORMAT(timestamp, 'yyyyMMdd-HHmmss'), '-', loan_id) as entry_id,
        2 as line_number,
        '2010-000' as account_number,
        0 as debit_amount,
        loan_amount as credit_amount,
        CONCAT('Customer funding - ', disbursement_account) as line_description,
        branch_id as cost_center,
        'Lending' as department,
        product_type as product_code,
        borrower_id as customer_id,
        disbursement_account as reference_number,
        CURRENT_TIMESTAMP() as effective_timestamp
    FROM cfo_banking_demo.bronze_core_banking.loan_origination_events
    WHERE status = 'approved'
    """

    execute_sql(w, insert_credits_sql)
    log_message("  ✓ Generated credit lines (DDA deposits)")

def create_loan_subledger(w):
    """Create loan subledger entries"""

    log_message("Creating loan subledger table...")

    # Create schema if needed
    execute_sql(w, "CREATE SCHEMA IF NOT EXISTS cfo_banking_demo.silver_loans")

    create_subledger_sql = """
    CREATE TABLE IF NOT EXISTS cfo_banking_demo.silver_loans.loan_subledger_transactions (
        transaction_id STRING,
        transaction_timestamp TIMESTAMP,
        posting_date DATE,
        loan_id STRING,
        transaction_type STRING,
        principal_amount DECIMAL(18,2),
        interest_amount DECIMAL(18,2),
        fee_amount DECIMAL(18,2),
        balance_before DECIMAL(18,2),
        balance_after DECIMAL(18,2),
        gl_entry_id STRING,
        payment_method STRING,
        description STRING,
        effective_timestamp TIMESTAMP
    )
    """

    execute_sql(w, create_subledger_sql)
    log_message("  ✓ Created loan_subledger_transactions table")

    log_message("Generating loan subledger entries...")

    # Insert subledger entries
    insert_subledger_sql = """
    INSERT INTO cfo_banking_demo.silver_loans.loan_subledger_transactions
    SELECT
        CONCAT('LST-', message_id) as transaction_id,
        timestamp as transaction_timestamp,
        origination_date as posting_date,
        loan_id,
        'Origination' as transaction_type,
        loan_amount as principal_amount,
        0 as interest_amount,
        0 as fee_amount,
        0 as balance_before,
        loan_amount as balance_after,
        CONCAT('GLE-', DATE_FORMAT(timestamp, 'yyyyMMdd-HHmmss'), '-', loan_id) as gl_entry_id,
        'Wire' as payment_method,
        CONCAT('Loan originated - ', product_type) as description,
        CURRENT_TIMESTAMP() as effective_timestamp
    FROM cfo_banking_demo.bronze_core_banking.loan_origination_events
    WHERE status = 'approved'
    """

    execute_sql(w, insert_subledger_sql)
    log_message("  ✓ Generated loan subledger entries")

def create_intraday_liquidity_summary(w):
    """Create intraday liquidity summary"""

    log_message("Creating intraday liquidity summary...")

    # Create schema if needed
    execute_sql(w, "CREATE SCHEMA IF NOT EXISTS cfo_banking_demo.gold_dashboards")

    create_summary_sql = """
    CREATE OR REPLACE TABLE cfo_banking_demo.gold_dashboards.intraday_liquidity_summary AS
    SELECT
        CURRENT_DATE() as position_date,
        'Loan_Originations' as activity_type,
        COUNT(*) as transaction_count,
        SUM(loan_amount) as gross_amount,
        -SUM(loan_amount) as cash_impact,
        MAX(timestamp) as last_update
    FROM cfo_banking_demo.bronze_core_banking.loan_origination_events
    WHERE DATE(origination_date) = CURRENT_DATE()
    GROUP BY position_date, activity_type
    """

    execute_sql(w, create_summary_sql)
    log_message("  ✓ Created intraday liquidity summary")

def validate_gl_entries(w):
    """Validate GL entries are balanced"""

    log_message("\n" + "=" * 80)
    log_message("GL ENTRY VALIDATION")
    log_message("=" * 80)

    # Count GL entries
    result = execute_sql(w, """
        SELECT COUNT(*) as count
        FROM cfo_banking_demo.silver_finance.gl_entries_from_loans
    """)
    gl_count = int(result.result.data_array[0][0]) if result.result and result.result.data_array else 0
    log_message(f"GL entries created: {gl_count}")

    # Check balance
    result = execute_sql(w, """
        SELECT
            COUNT(*) as total_entries,
            SUM(CASE WHEN is_balanced = true THEN 1 ELSE 0 END) as balanced_entries,
            SUM(total_debits) as total_debits,
            SUM(total_credits) as total_credits,
            SUM(total_debits - total_credits) as difference
        FROM cfo_banking_demo.silver_finance.gl_entries_from_loans
    """)

    if result.result and result.result.data_array:
        row = result.result.data_array[0]
        total = int(row[0])
        balanced = int(row[1])
        debits = float(row[2])
        credits = float(row[3])
        diff = float(row[4])

        log_message(f"  Total entries: {total}")
        log_message(f"  Balanced entries: {balanced}/{total}")
        log_message(f"  Total debits: ${debits:,.2f}")
        log_message(f"  Total credits: ${credits:,.2f}")
        log_message(f"  Difference: ${diff:,.2f}")

        if diff == 0:
            log_message("  ✓ All GL entries are balanced!")
        else:
            log_message(f"  ⚠️  GL entries have ${diff:,.2f} difference", "WARNING")

    # Count GL lines
    result = execute_sql(w, """
        SELECT COUNT(*) as count
        FROM cfo_banking_demo.silver_finance.gl_entry_lines_from_loans
    """)
    lines_count = int(result.result.data_array[0][0]) if result.result and result.result.data_array else 0
    log_message(f"GL entry lines created: {lines_count}")

    # Count subledger entries
    result = execute_sql(w, """
        SELECT COUNT(*) as count
        FROM cfo_banking_demo.silver_loans.loan_subledger_transactions
    """)
    subledger_count = int(result.result.data_array[0][0]) if result.result and result.result.data_array else 0
    log_message(f"Loan subledger entries: {subledger_count}")

def display_liquidity_summary(w):
    """Display intraday liquidity summary"""

    log_message("\n" + "=" * 80)
    log_message("INTRADAY LIQUIDITY SUMMARY")
    log_message("=" * 80)

    result = execute_sql(w, """
        SELECT
            position_date,
            activity_type,
            transaction_count,
            gross_amount,
            cash_impact,
            last_update
        FROM cfo_banking_demo.gold_dashboards.intraday_liquidity_summary
    """)

    if result.result and result.result.data_array:
        row = result.result.data_array[0]
        log_message(f"Position Date: {row[0]}")
        log_message(f"Activity Type: {row[1]}")
        log_message(f"Transaction Count: {row[2]}")
        log_message(f"Gross Amount: ${float(row[3]):,.2f}")
        log_message(f"Cash Impact: ${float(row[4]):,.2f}")
        log_message(f"Last Update: {row[5]}")

def main():
    """Main execution function"""
    try:
        log_message("=" * 80)
        log_message("WS2-02: Real-Time Loan Origination Pipeline")
        log_message("=" * 80)

        # Initialize Databricks workspace client
        w = WorkspaceClient()
        log_message("✓ Connected to Databricks")
        log_message(f"✓ Using SQL Warehouse: {WAREHOUSE_ID}")

        # Generate loan origination messages
        log_message("\n" + "-" * 80)
        messages = generate_loan_origination_messages(count=50)

        # Create and populate bronze layer
        log_message("\n" + "-" * 80)
        create_bronze_table(w)
        insert_loan_messages(w, messages)

        # Create and populate silver layer (GL entries)
        log_message("\n" + "-" * 80)
        create_gl_tables(w)
        generate_gl_entries(w)

        # Create loan subledger
        log_message("\n" + "-" * 80)
        create_loan_subledger(w)

        # Create intraday liquidity summary (gold layer)
        log_message("\n" + "-" * 80)
        create_intraday_liquidity_summary(w)

        # Validate GL entries
        validate_gl_entries(w)

        # Display liquidity summary
        display_liquidity_summary(w)

        log_message("\n" + "=" * 80)
        log_message("✅ WS2-02 Complete: Loan Origination Pipeline Successful")
        log_message("=" * 80)
        log_message("\nTables created:")
        log_message("  - cfo_banking_demo.bronze_core_banking.loan_origination_events")
        log_message("  - cfo_banking_demo.silver_finance.gl_entries_from_loans")
        log_message("  - cfo_banking_demo.silver_finance.gl_entry_lines_from_loans")
        log_message("  - cfo_banking_demo.silver_loans.loan_subledger_transactions")
        log_message("  - cfo_banking_demo.gold_dashboards.intraday_liquidity_summary")
        log_message("\nReady for WS3: Advanced Analytics Workflows")

        return 0

    except Exception as e:
        log_message(f"\n\n❌ Error: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
