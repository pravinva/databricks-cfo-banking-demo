#!/usr/bin/env python3
"""
WS1-06: GL and Subledger Schema Setup
Creates General Ledger and subledger table schemas for real-time accounting

Uses Databricks SQL Warehouse for execution
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
from datetime import datetime
import time

def log_message(message, level="INFO"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

# Constants
CURRENT_DATE = datetime(2026, 1, 24).date()
WAREHOUSE_ID = "4b9b953939869799"

def execute_sql(w, sql_statement, warehouse_id=WAREHOUSE_ID, wait=True):
    """Execute SQL statement"""
    statement = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql_statement,
        wait_timeout="50s"
    )

    if wait:
        # Wait for completion (poll beyond initial 50s if needed)
        max_wait_time = 600  # 10 minutes max
        elapsed = 0
        while statement.status.state in [StatementState.PENDING, StatementState.RUNNING] and elapsed < max_wait_time:
            time.sleep(3)
            elapsed += 3
            statement = w.statement_execution.get_statement(statement.statement_id)

        if statement.status.state == StatementState.FAILED:
            error_msg = statement.status.error.message if statement.status.error else "Unknown error"
            raise Exception(f"SQL execution failed: {error_msg}")

        if statement.status.state in [StatementState.PENDING, StatementState.RUNNING]:
            raise Exception(f"SQL execution timed out after {max_wait_time}s")

    return statement

def main():
    """Main execution"""
    log_message("=" * 80)
    log_message("WS1-06: GL and Subledger Schema Setup")
    log_message("=" * 80)

    w = WorkspaceClient()
    log_message(f"✓ Connected to Databricks")
    log_message(f"✓ Using SQL Warehouse: {WAREHOUSE_ID}")

    # ==========================================================================
    # 1. Create Chart of Accounts
    # ==========================================================================
    log_message("\n" + "=" * 80)
    log_message("STEP 1: Creating Chart of Accounts")
    log_message("=" * 80)

    create_coa_sql = f"""
    CREATE OR REPLACE TABLE cfo_banking_demo.bronze_core_banking.chart_of_accounts (
        account_number STRING NOT NULL,
        account_name STRING NOT NULL,
        account_type STRING NOT NULL,
        account_category STRING NOT NULL,
        normal_balance STRING NOT NULL,
        is_control_account BOOLEAN NOT NULL,
        subledger_type STRING,
        financial_statement STRING NOT NULL,
        regulatory_code STRING,
        is_active BOOLEAN NOT NULL,
        effective_date DATE NOT NULL
    )
    """

    execute_sql(w, create_coa_sql)
    log_message("✓ Created chart_of_accounts table")

    # Insert Chart of Accounts data
    log_message("Inserting Chart of Accounts data...")

    coa_data = [
        # ASSETS (1000-1999)
        ("1010-000", "Cash in Vault", "Asset", "Current_Asset", "Debit", False, None, "Balance_Sheet", "RCFD0081", True),
        ("1020-000", "Fed Reserve Account", "Asset", "Current_Asset", "Debit", False, None, "Balance_Sheet", "RCFD0090", True),
        ("1030-000", "Due from Banks", "Asset", "Current_Asset", "Debit", False, None, "Balance_Sheet", "RCFD0070", True),
        ("1100-000", "Securities - US Treasury", "Asset", "Investment", "Debit", False, None, "Balance_Sheet", "RCFD0211", True),
        ("1110-000", "Securities - Corporate", "Asset", "Investment", "Debit", False, None, "Balance_Sheet", "RCFD1707", True),
        ("1120-000", "Securities - Municipal", "Asset", "Investment", "Debit", False, None, "Balance_Sheet", "RCFD0213", True),
        ("1130-000", "Securities - Agency", "Asset", "Investment", "Debit", False, None, "Balance_Sheet", "RCFD1288", True),
        ("1140-000", "Securities - MBS", "Asset", "Investment", "Debit", False, None, "Balance_Sheet", "RCFD1709", True),
        ("1200-000", "Loans - Commercial RE", "Asset", "Loan", "Debit", True, "Loan", "Balance_Sheet", "RCFD2122", True),
        ("1210-000", "Loans - C&I", "Asset", "Loan", "Debit", True, "Loan", "Balance_Sheet", "RCFD1766", True),
        ("1220-000", "Loans - Residential Mortgage", "Asset", "Loan", "Debit", True, "Loan", "Balance_Sheet", "RCFD1797", True),
        ("1230-000", "Loans - Consumer", "Asset", "Loan", "Debit", True, "Loan", "Balance_Sheet", "RCFD2011", True),
        ("1240-000", "Loans - HELOC", "Asset", "Loan", "Debit", True, "Loan", "Balance_Sheet", "RCFD5367", True),
        ("1290-000", "Allowance for Credit Losses", "Asset", "Contra_Asset", "Credit", False, None, "Balance_Sheet", "RCFD3123", True),
        ("1300-000", "Premises & Equipment", "Asset", "Fixed_Asset", "Debit", False, None, "Balance_Sheet", "RCFD2145", True),
        ("1400-000", "Accrued Interest Receivable", "Asset", "Current_Asset", "Debit", False, None, "Balance_Sheet", "RCFD0430", True),
        ("1500-000", "Deferred Tax Assets", "Asset", "Other_Asset", "Debit", False, None, "Balance_Sheet", "RCFD2148", True),
        ("1600-000", "Goodwill", "Asset", "Intangible", "Debit", False, None, "Balance_Sheet", "RCFD3163", True),
        ("1700-000", "Other Assets", "Asset", "Other_Asset", "Debit", False, None, "Balance_Sheet", "RCFD2160", True),
        # LIABILITIES (2000-2999)
        ("2010-000", "DDA Deposits", "Liability", "Deposit", "Credit", True, "Deposit", "Balance_Sheet", "RCON2215", True),
        ("2020-000", "Savings Deposits", "Liability", "Deposit", "Credit", True, "Deposit", "Balance_Sheet", "RCON0352", True),
        ("2030-000", "MMDA Deposits", "Liability", "Deposit", "Credit", True, "Deposit", "Balance_Sheet", "RCONB551", True),
        ("2040-000", "Time Deposits", "Liability", "Deposit", "Credit", True, "Deposit", "Balance_Sheet", "RCON2604", True),
        ("2100-000", "Fed Funds Purchased", "Liability", "Borrowing", "Credit", False, None, "Balance_Sheet", "RCFD2800", True),
        ("2110-000", "FHLB Advances", "Liability", "Borrowing", "Credit", False, None, "Balance_Sheet", "RCFD2651", True),
        ("2120-000", "Repos", "Liability", "Borrowing", "Credit", False, None, "Balance_Sheet", "RCFD2800", True),
        ("2150-000", "Subordinated Debt", "Liability", "Long_Term_Debt", "Credit", False, None, "Balance_Sheet", "RCFD3200", True),
        ("2200-000", "Accrued Interest Payable", "Liability", "Current_Liability", "Credit", False, None, "Balance_Sheet", "RCFD2930", True),
        ("2300-000", "Other Liabilities", "Liability", "Other_Liability", "Credit", False, None, "Balance_Sheet", "RCFD2938", True),
        # EQUITY (3000-3999)
        ("3010-000", "Common Stock", "Equity", "Capital", "Credit", False, None, "Balance_Sheet", "RCFD3230", True),
        ("3020-000", "Additional Paid-In Capital", "Equity", "Capital", "Credit", False, None, "Balance_Sheet", "RCFD3839", True),
        ("3030-000", "Retained Earnings", "Equity", "Retained_Earnings", "Credit", False, None, "Balance_Sheet", "RCFD3632", True),
        ("3040-000", "Accumulated OCI", "Equity", "OCI", "Credit", False, None, "Balance_Sheet", "RCFDB530", True),
        # REVENUE (4000-4999)
        ("4010-000", "Interest Income - Loans", "Revenue", "Interest_Income", "Credit", False, None, "Income_Statement", "RIAD4010", True),
        ("4020-000", "Interest Income - Securities", "Revenue", "Interest_Income", "Credit", False, None, "Income_Statement", "RIAD4020", True),
        ("4030-000", "Interest Income - Other", "Revenue", "Interest_Income", "Credit", False, None, "Income_Statement", "RIAD4518", True),
        ("4100-000", "Fee Income - Service Charges", "Revenue", "Non_Interest_Income", "Credit", False, None, "Income_Statement", "RIAD4080", True),
        ("4110-000", "Fee Income - Card Interchange", "Revenue", "Non_Interest_Income", "Credit", False, None, "Income_Statement", "RIADB488", True),
        ("4120-000", "Fee Income - Mortgage Banking", "Revenue", "Non_Interest_Income", "Credit", False, None, "Income_Statement", "RIAD4091", True),
        ("4200-000", "Other Income", "Revenue", "Non_Interest_Income", "Credit", False, None, "Income_Statement", "RIAD4092", True),
        # EXPENSES (5000-5999)
        ("5010-000", "Interest Expense - Deposits", "Expense", "Interest_Expense", "Debit", False, None, "Income_Statement", "RIAD4170", True),
        ("5020-000", "Interest Expense - Borrowings", "Expense", "Interest_Expense", "Debit", False, None, "Income_Statement", "RIAD4200", True),
        ("5100-000", "Provision for Credit Losses", "Expense", "Provision", "Debit", False, None, "Income_Statement", "RIAD4230", True),
        ("5200-000", "Compensation Expense", "Expense", "Operating_Expense", "Debit", False, None, "Income_Statement", "RIAD4135", True),
        ("5300-000", "Occupancy Expense", "Expense", "Operating_Expense", "Debit", False, None, "Income_Statement", "RIAD4217", True),
        ("5400-000", "Technology Expense", "Expense", "Operating_Expense", "Debit", False, None, "Income_Statement", "RIAD4092", True),
        ("5500-000", "Professional Fees", "Expense", "Operating_Expense", "Debit", False, None, "Income_Statement", "RIAD4136", True),
        ("5600-000", "Marketing Expense", "Expense", "Operating_Expense", "Debit", False, None, "Income_Statement", "RIAD4141", True),
        ("5900-000", "Other Expense", "Expense", "Operating_Expense", "Debit", False, None, "Income_Statement", "RIAD4092", True),
    ]

    # Insert in batches
    batch_size = 25
    for batch_start in range(0, len(coa_data), batch_size):
        batch = coa_data[batch_start:batch_start + batch_size]
        values_list = []
        for row in batch:
            account_number, account_name, account_type, account_category, normal_balance, is_control, subledger, fin_stmt, reg_code, is_active = row
            subledger_val = f"'{subledger}'" if subledger else "NULL"
            reg_code_val = f"'{reg_code}'" if reg_code else "NULL"
            values_list.append(f"('{account_number}', '{account_name}', '{account_type}', '{account_category}', '{normal_balance}', {is_control}, {subledger_val}, '{fin_stmt}', {reg_code_val}, {is_active}, '{CURRENT_DATE}')")

        insert_sql = f"""
        INSERT INTO cfo_banking_demo.bronze_core_banking.chart_of_accounts VALUES
        {', '.join(values_list)}
        """
        execute_sql(w, insert_sql)

    log_message(f"✓ Inserted {len(coa_data)} accounts")

    # ==========================================================================
    # 2. Create GL Entries Table
    # ==========================================================================
    log_message("\n" + "=" * 80)
    log_message("STEP 2: Creating GL Entries Table")
    log_message("=" * 80)

    create_gl_entries_sql = """
    CREATE OR REPLACE TABLE cfo_banking_demo.silver_finance.gl_entries (
        entry_id STRING NOT NULL,
        entry_date DATE NOT NULL,
        entry_timestamp TIMESTAMP NOT NULL,
        posting_date DATE NOT NULL,
        accounting_period STRING NOT NULL,
        entry_type STRING NOT NULL,
        source_system STRING NOT NULL,
        source_transaction_id STRING,
        batch_id STRING,
        entry_status STRING NOT NULL,
        description STRING,
        total_debits DECIMAL(18, 2) NOT NULL,
        total_credits DECIMAL(18, 2) NOT NULL,
        created_by STRING,
        approved_by STRING,
        is_balanced BOOLEAN NOT NULL,
        is_reversed BOOLEAN NOT NULL,
        reversed_by_entry_id STRING,
        effective_timestamp TIMESTAMP NOT NULL
    )
    """

    execute_sql(w, create_gl_entries_sql)
    log_message("✓ Created gl_entries table (empty)")

    # ==========================================================================
    # 3. Create GL Entry Lines Table
    # ==========================================================================
    log_message("\n" + "=" * 80)
    log_message("STEP 3: Creating GL Entry Lines Table")
    log_message("=" * 80)

    create_gl_lines_sql = """
    CREATE OR REPLACE TABLE cfo_banking_demo.silver_finance.gl_entry_lines (
        line_id STRING NOT NULL,
        entry_id STRING NOT NULL,
        line_number INT NOT NULL,
        account_number STRING NOT NULL,
        debit_amount DECIMAL(18, 2) NOT NULL,
        credit_amount DECIMAL(18, 2) NOT NULL,
        line_description STRING,
        cost_center STRING,
        department STRING,
        product_code STRING,
        customer_id STRING,
        reference_number STRING,
        effective_timestamp TIMESTAMP NOT NULL
    )
    """

    execute_sql(w, create_gl_lines_sql)
    log_message("✓ Created gl_entry_lines table (empty)")

    # ==========================================================================
    # 4. Create Loan Subledger Table
    # ==========================================================================
    log_message("\n" + "=" * 80)
    log_message("STEP 4: Creating Loan Subledger Table")
    log_message("=" * 80)

    create_loan_subledger_sql = """
    CREATE OR REPLACE TABLE cfo_banking_demo.silver_finance.loan_subledger (
        transaction_id STRING NOT NULL,
        transaction_timestamp TIMESTAMP NOT NULL,
        posting_date DATE NOT NULL,
        loan_id STRING NOT NULL,
        transaction_type STRING NOT NULL,
        principal_amount DECIMAL(18, 2) NOT NULL,
        interest_amount DECIMAL(18, 2) NOT NULL,
        fee_amount DECIMAL(18, 2) NOT NULL,
        balance_before DECIMAL(18, 2) NOT NULL,
        balance_after DECIMAL(18, 2) NOT NULL,
        gl_entry_id STRING,
        payment_method STRING,
        description STRING,
        effective_timestamp TIMESTAMP NOT NULL
    )
    """

    execute_sql(w, create_loan_subledger_sql)
    log_message("✓ Created loan_subledger table (empty)")

    # ==========================================================================
    # 5. Create Deposit Subledger Table
    # ==========================================================================
    log_message("\n" + "=" * 80)
    log_message("STEP 5: Creating Deposit Subledger Table")
    log_message("=" * 80)

    create_deposit_subledger_sql = """
    CREATE OR REPLACE TABLE cfo_banking_demo.silver_finance.deposit_subledger (
        transaction_id STRING NOT NULL,
        transaction_timestamp TIMESTAMP NOT NULL,
        posting_date DATE NOT NULL,
        account_id STRING NOT NULL,
        transaction_type STRING NOT NULL,
        amount DECIMAL(18, 2) NOT NULL,
        balance_before DECIMAL(18, 2) NOT NULL,
        balance_after DECIMAL(18, 2) NOT NULL,
        gl_entry_id STRING,
        channel STRING,
        description STRING,
        effective_timestamp TIMESTAMP NOT NULL
    )
    """

    execute_sql(w, create_deposit_subledger_sql)
    log_message("✓ Created deposit_subledger table (empty)")

    # ==========================================================================
    # 6. Create Intraday Cash Position Table
    # ==========================================================================
    log_message("\n" + "=" * 80)
    log_message("STEP 6: Creating Intraday Cash Position Table")
    log_message("=" * 80)

    create_intraday_cash_sql = """
    CREATE OR REPLACE TABLE cfo_banking_demo.silver_treasury.intraday_cash_position (
        position_timestamp TIMESTAMP NOT NULL,
        position_date DATE NOT NULL,
        cash_source STRING NOT NULL,
        opening_balance DECIMAL(18, 2) NOT NULL,
        gross_inflows DECIMAL(18, 2) NOT NULL,
        gross_outflows DECIMAL(18, 2) NOT NULL,
        net_change DECIMAL(18, 2) NOT NULL,
        current_balance DECIMAL(18, 2) NOT NULL,
        projected_eod_balance DECIMAL(18, 2) NOT NULL,
        liquidity_buffer DECIMAL(18, 2) NOT NULL,
        is_snapshot BOOLEAN NOT NULL,
        effective_timestamp TIMESTAMP NOT NULL
    )
    """

    execute_sql(w, create_intraday_cash_sql)
    log_message("✓ Created intraday_cash_position table (empty)")

    # ==========================================================================
    # 7. Create Views
    # ==========================================================================
    log_message("\n" + "=" * 80)
    log_message("STEP 7: Creating Views")
    log_message("=" * 80)

    # Trial Balance View
    create_trial_balance_view_sql = """
    CREATE OR REPLACE VIEW cfo_banking_demo.silver_finance.vw_trial_balance AS
    SELECT
        coa.account_number,
        coa.account_name,
        coa.account_type,
        coa.normal_balance,
        COALESCE(SUM(gel.debit_amount), 0) as total_debits,
        COALESCE(SUM(gel.credit_amount), 0) as total_credits,
        CASE
            WHEN coa.normal_balance = 'Debit' THEN COALESCE(SUM(gel.debit_amount), 0) - COALESCE(SUM(gel.credit_amount), 0)
            ELSE COALESCE(SUM(gel.credit_amount), 0) - COALESCE(SUM(gel.debit_amount), 0)
        END as balance
    FROM cfo_banking_demo.bronze_core_banking.chart_of_accounts coa
    LEFT JOIN cfo_banking_demo.silver_finance.gl_entry_lines gel
        ON coa.account_number = gel.account_number
    WHERE coa.is_active = true
    GROUP BY coa.account_number, coa.account_name, coa.account_type, coa.normal_balance
    ORDER BY coa.account_number
    """

    execute_sql(w, create_trial_balance_view_sql)
    log_message("✓ Created vw_trial_balance view")

    # Loan Activity Summary View
    create_loan_activity_view_sql = """
    CREATE OR REPLACE VIEW cfo_banking_demo.silver_finance.vw_loan_activity_summary AS
    SELECT
        posting_date,
        transaction_type,
        COUNT(*) as transaction_count,
        SUM(principal_amount) as total_principal,
        SUM(interest_amount) as total_interest,
        SUM(fee_amount) as total_fees
    FROM cfo_banking_demo.silver_finance.loan_subledger
    GROUP BY posting_date, transaction_type
    ORDER BY posting_date DESC, transaction_type
    """

    execute_sql(w, create_loan_activity_view_sql)
    log_message("✓ Created vw_loan_activity_summary view")

    # Cash Position Current View
    create_cash_position_view_sql = """
    CREATE OR REPLACE VIEW cfo_banking_demo.silver_treasury.vw_cash_position_current AS
    SELECT *
    FROM cfo_banking_demo.silver_treasury.intraday_cash_position
    WHERE position_timestamp = (
        SELECT MAX(position_timestamp)
        FROM cfo_banking_demo.silver_treasury.intraday_cash_position
    )
    """

    execute_sql(w, create_cash_position_view_sql)
    log_message("✓ Created vw_cash_position_current view")

    # ==========================================================================
    # 8. Insert Sample Test Entry
    # ==========================================================================
    log_message("\n" + "=" * 80)
    log_message("STEP 8: Inserting Sample Test Entry")
    log_message("=" * 80)

    current_timestamp = datetime.now()

    # Insert sample GL entry
    insert_test_entry_sql = f"""
    INSERT INTO cfo_banking_demo.silver_finance.gl_entries VALUES (
        'TEST-001',
        '{CURRENT_DATE}',
        '{current_timestamp}',
        '{CURRENT_DATE}',
        '2026-01',
        'Regular',
        'Test',
        'TEST-TXN-001',
        'TEST-BATCH-001',
        'Posted',
        'Sample test entry',
        1000.00,
        1000.00,
        'system',
        'system',
        true,
        false,
        NULL,
        '{current_timestamp}'
    )
    """

    execute_sql(w, insert_test_entry_sql)
    log_message("✓ Inserted sample GL entry")

    # Insert sample entry lines
    insert_test_lines_sql = f"""
    INSERT INTO cfo_banking_demo.silver_finance.gl_entry_lines VALUES
    (
        'TEST-001-L1',
        'TEST-001',
        1,
        '1010-000',
        1000.00,
        0.00,
        'Test debit - Cash',
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        '{current_timestamp}'
    ),
    (
        'TEST-001-L2',
        'TEST-001',
        2,
        '3030-000',
        0.00,
        1000.00,
        'Test credit - Retained Earnings',
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        '{current_timestamp}'
    )
    """

    execute_sql(w, insert_test_lines_sql)
    log_message("✓ Inserted sample entry lines")

    # ==========================================================================
    # 9. Validation
    # ==========================================================================
    log_message("\n" + "=" * 80)
    log_message("STEP 9: Running Validations")
    log_message("=" * 80)

    # Check all tables
    tables_to_check = [
        ("cfo_banking_demo.bronze_core_banking.chart_of_accounts", 47),
        ("cfo_banking_demo.silver_finance.gl_entries", 1),
        ("cfo_banking_demo.silver_finance.gl_entry_lines", 2),
        ("cfo_banking_demo.silver_finance.loan_subledger", 0),
        ("cfo_banking_demo.silver_finance.deposit_subledger", 0),
        ("cfo_banking_demo.silver_treasury.intraday_cash_position", 0)
    ]

    for table_name, expected_count in tables_to_check:
        count_sql = f"SELECT COUNT(*) as cnt FROM {table_name}"
        result = execute_sql(w, count_sql)
        count = int(result.result.data_array[0][0]) if result.result and result.result.data_array else 0
        log_message(f"✓ {table_name}: {count} rows (expected {expected_count})")
        if count != expected_count:
            log_message(f"  ⚠️  Warning: Expected {expected_count} rows, got {count}", "WARN")

    # Test trial balance view
    trial_balance_sql = "SELECT COUNT(*) as cnt FROM cfo_banking_demo.silver_finance.vw_trial_balance"
    result = execute_sql(w, trial_balance_sql)
    tb_count = int(result.result.data_array[0][0]) if result.result and result.result.data_array else 0
    log_message(f"✓ Trial balance view: {tb_count} accounts")

    # Verify test entry is balanced
    verify_balance_sql = """
    SELECT
        entry_id,
        total_debits,
        total_credits,
        is_balanced,
        (total_debits - total_credits) as difference
    FROM cfo_banking_demo.silver_finance.gl_entries
    WHERE entry_id = 'TEST-001'
    """

    result = execute_sql(w, verify_balance_sql)
    if result.result and result.result.data_array:
        row = result.result.data_array[0]
        entry_id = row[0]
        debits = float(row[1])
        credits = float(row[2])
        is_balanced = row[3]
        difference = float(row[4])
        log_message(f"\nTest Entry Verification:")
        log_message(f"  Entry ID: {entry_id}")
        log_message(f"  Total Debits: ${debits:,.2f}")
        log_message(f"  Total Credits: ${credits:,.2f}")
        log_message(f"  Difference: ${difference:,.2f}")
        log_message(f"  Is Balanced: {is_balanced}")
        if is_balanced and difference == 0:
            log_message("  ✅ Test entry is balanced!")
        else:
            log_message("  ⚠️  Test entry not balanced!", "WARN")

    # ==========================================================================
    # Summary
    # ==========================================================================
    log_message("\n" + "=" * 80)
    log_message("✅ WS1-06 Complete!")
    log_message("=" * 80)

    log_message("\nChart of Accounts:")
    log_message("  Total Accounts: 47")

    # Get account type summary
    summary_sql = """
    SELECT
        account_type,
        COUNT(*) as count
    FROM cfo_banking_demo.bronze_core_banking.chart_of_accounts
    GROUP BY account_type
    ORDER BY account_type
    """
    result = execute_sql(w, summary_sql)
    if result.result and result.result.data_array:
        for row in result.result.data_array:
            acc_type = row[0]
            count = int(row[1])
            log_message(f"    {acc_type}: {count} accounts")

    log_message("\nTables Created:")
    log_message("  ✓ bronze_core_banking.chart_of_accounts")
    log_message("  ✓ silver_finance.gl_entries")
    log_message("  ✓ silver_finance.gl_entry_lines")
    log_message("  ✓ silver_finance.loan_subledger")
    log_message("  ✓ silver_finance.deposit_subledger")
    log_message("  ✓ silver_treasury.intraday_cash_position")

    log_message("\nViews Created:")
    log_message("  ✓ vw_trial_balance")
    log_message("  ✓ vw_loan_activity_summary")
    log_message("  ✓ vw_cash_position_current")

    log_message("\n✅ Ready for WS2 (real-time pipelines)")

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
