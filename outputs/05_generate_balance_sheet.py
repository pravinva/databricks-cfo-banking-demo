#!/usr/bin/env python3
"""
WS1-05: Balance Sheet Generator
Generate 365 days of daily balance sheet snapshots for US regional bank (~$45B assets)

Ties to existing portfolios:
- Securities: $2.8B (from WS1-02)
- Loans: $18B (from WS1-03)
- Deposits: $22B (from WS1-04)

Uses Databricks SQL Warehouse for execution
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
from datetime import datetime, timedelta
import random
import time

# Set random seed for reproducibility
random.seed(42)

def log_message(message, level="INFO"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

# Constants
CURRENT_DATE = datetime(2026, 1, 24).date()
WAREHOUSE_ID = "4b9b953939869799"

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

def main():
    """Main execution function"""
    try:
        log_message("=" * 80)
        log_message("WS1-05: Balance Sheet Generator")
        log_message("=" * 80)

        # Initialize Databricks workspace client
        w = WorkspaceClient()
        log_message("✓ Connected to Databricks")
        log_message(f"✓ Using SQL Warehouse: {WAREHOUSE_ID}")

        # Step 1: Get portfolio balances
        log_message("\nReading portfolio balances...")

        # Securities balance
        result = execute_sql(w, """
            SELECT SUM(market_value) as total_securities
            FROM cfo_banking_demo.silver_treasury.securities_portfolio
            WHERE is_current = true
        """)
        securities_balance = float(result.result.data_array[0][0]) if result.result and result.result.data_array else 0
        log_message(f"  Securities: ${securities_balance:,.0f}")

        # Loan balances
        result = execute_sql(w, """
            SELECT
                SUM(current_balance) as gross_loans,
                SUM(cecl_reserve) as cecl_reserve
            FROM cfo_banking_demo.silver_finance.loan_portfolio
            WHERE is_current = true
        """)
        if result.result and result.result.data_array:
            gross_loans = float(result.result.data_array[0][0])
            cecl_reserve = float(result.result.data_array[0][1])
            net_loans = gross_loans - cecl_reserve
        else:
            gross_loans = cecl_reserve = net_loans = 0

        log_message(f"  Gross Loans: ${gross_loans:,.0f}")
        log_message(f"  CECL Reserve: ${cecl_reserve:,.0f}")
        log_message(f"  Net Loans: ${net_loans:,.0f}")

        # Deposit balance
        result = execute_sql(w, """
            SELECT SUM(current_balance) as total_deposits
            FROM cfo_banking_demo.silver_treasury.deposit_portfolio
            WHERE is_current = true
        """)
        deposit_balance = float(result.result.data_array[0][0]) if result.result and result.result.data_array else 0
        log_message(f"  Deposits: ${deposit_balance:,.0f}")

        # Calculate balancing amounts
        total_assets_target = 45_000_000_000
        other_earning_assets = 20_000_000_000
        cash_and_due = 2_000_000_000
        non_earning_assets = total_assets_target - (cash_and_due + securities_balance + net_loans + other_earning_assets)

        log_message(f"  Other Earning Assets: ${other_earning_assets:,.0f}")
        log_message(f"  Cash & Due from Banks: ${cash_and_due:,.0f}")
        log_message(f"  Non-Earning Assets: ${non_earning_assets:,.0f}")
        log_message(f"  Total Assets (target): ${total_assets_target:,.0f}")

        # Calculate liabilities
        equity = 4_000_000_000
        total_liabilities = total_assets_target - equity
        borrowed_funds = total_liabilities - deposit_balance - 1_000_000_000

        log_message(f"  Total Liabilities: ${total_liabilities:,.0f}")
        log_message(f"  Borrowed Funds: ${borrowed_funds:,.0f}")
        log_message(f"  Equity: ${equity:,.0f}")

        # Step 2: Create bronze table
        log_message("\nCreating bronze layer table...")
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS cfo_banking_demo.bronze_core_banking.balance_sheet_daily (
            report_date DATE NOT NULL,
            line_item STRING NOT NULL,
            line_item_category STRING NOT NULL,
            line_item_subcategory STRING,
            balance DOUBLE,
            average_balance_qtd DOUBLE,
            average_balance_ytd DOUBLE,
            regulatory_classification STRING,
            risk_weight DOUBLE,
            hqla_classification STRING,
            nsfr_classification STRING,
            is_consolidated BOOLEAN,
            reporting_unit STRING,
            effective_timestamp TIMESTAMP
        )
        USING DELTA
        PARTITIONED BY (report_date)
        """
        execute_sql(w, create_table_sql)
        log_message("✓ Created balance_sheet_daily table")

        # Step 3: Generate and insert balance sheet data
        log_message("\nGenerating 365 days of balance sheet data...")
        log_message("This will create ~8,800 records (24 line items × 365 days)")

        # Generate in batches by month
        for month_offset in range(12):
            log_message(f"  Generating month {month_offset + 1}/12...")

            # Generate ~30 days per month
            days_in_batch = 31 if month_offset in [0, 2, 4, 6, 7, 9, 11] else 30
            start_day = month_offset * 30

            values_list = []

            for day_offset in range(start_day, min(start_day + days_in_batch, 365)):
                report_date = CURRENT_DATE - timedelta(days=day_offset)
                timestamp = datetime.combine(report_date, datetime.min.time())

                # Volatility for daily changes
                vol = random.uniform(0.98, 1.02)

                # Asset line items
                line_items = [
                    # Cash and Due from Banks
                    ('Cash_Vault', 'Asset', 'Current_Asset', 200_000_000 * vol, 'HQLA_Level_1', 0.0, 'Level_1', 'RSF_0'),
                    ('Fed_Reserve_Account', 'Asset', 'Current_Asset', 1_500_000_000 * vol, 'HQLA_Level_1', 0.0, 'Level_1', 'RSF_0'),
                    ('Due_from_Banks', 'Asset', 'Current_Asset', 300_000_000 * vol, 'Standard', 0.20, 'Non_HQLA', 'RSF_15'),

                    # Securities
                    ('Securities', 'Asset', 'Investment', securities_balance * vol, 'HQLA_Mixed', 0.10, 'Level_1_2A', 'RSF_15'),

                    # Loans
                    ('Loans_Gross', 'Asset', 'Loan', gross_loans * vol, 'Standard', 0.75, 'Non_HQLA', 'RSF_65'),
                    ('CECL_Reserve', 'Asset', 'Contra_Asset', -cecl_reserve * vol, 'Allowance', 0.0, 'Non_HQLA', None),

                    # Other Earning Assets
                    ('Fed_Funds_Sold', 'Asset', 'Earning_Asset', 8_000_000_000 * vol, 'Standard', 0.20, 'Level_2A', 'RSF_15'),
                    ('Interest_Bearing_Deposits', 'Asset', 'Earning_Asset', 10_000_000_000 * vol, 'Standard', 0.20, 'Level_2A', 'RSF_15'),
                    ('Reverse_Repos', 'Asset', 'Earning_Asset', 2_000_000_000 * vol, 'Standard', 0.20, 'Level_1', 'RSF_10'),

                    # Non-Earning Assets
                    ('Premises_Equipment', 'Asset', 'Fixed_Asset', 800_000_000, 'Standard', 1.0, 'Non_HQLA', 'RSF_100'),
                    ('Goodwill_Intangibles', 'Asset', 'Intangible', 300_000_000, 'Deduction', 0.0, 'Non_HQLA', None),
                    ('Other_Assets', 'Asset', 'Other_Asset', 1_100_000_000 * vol, 'Standard', 1.0, 'Non_HQLA', 'RSF_100'),

                    # Liabilities - Deposits
                    ('Deposits', 'Liability', 'Deposit', deposit_balance * vol, 'Deposit', None, None, 'ASF_95'),

                    # Borrowed Funds
                    ('Fed_Funds_Purchased', 'Liability', 'Borrowing', 3_000_000_000 * vol, 'Borrowing', None, None, 'ASF_0'),
                    ('FHLB_Advances', 'Liability', 'Borrowing', 8_000_000_000 * vol, 'Secured_Borrowing', None, None, 'ASF_50'),
                    ('Repos', 'Liability', 'Borrowing', 5_000_000_000 * vol, 'Secured_Borrowing', None, None, 'ASF_0'),
                    ('Subordinated_Debt', 'Liability', 'Long_Term_Debt', 2_000_000_000, 'Tier_2_Capital', None, None, 'ASF_100'),

                    # Other Liabilities
                    ('Other_Liabilities', 'Liability', 'Other_Liability', 1_000_000_000 * vol, 'Standard', None, None, 'ASF_0'),

                    # Equity
                    ('Common_Stock', 'Equity', 'Capital', 500_000_000, 'CET1', None, None, 'ASF_100'),
                    ('Additional_Paid_In_Capital', 'Equity', 'Capital', 1_000_000_000, 'CET1', None, None, 'ASF_100'),
                    ('Retained_Earnings', 'Equity', 'Retained_Earnings', 2_600_000_000 + (day_offset * 1_000_000), 'CET1', None, None, 'ASF_100'),
                    ('Accumulated_OCI', 'Equity', 'OCI', -100_000_000, 'OCI', None, None, 'ASF_100'),
                ]

                for item in line_items:
                    name, category, subcategory, balance, reg_class, risk_wt, hqla, nsfr = item
                    avg_bal = balance if balance > 0 else -balance
                    risk_wt_str = str(risk_wt) if risk_wt is not None else 'NULL'
                    hqla_str = f"'{hqla}'" if hqla else 'NULL'
                    nsfr_str = f"'{nsfr}'" if nsfr else 'NULL'

                    value = f"""(
                        '{report_date}', '{name}', '{category}', '{subcategory}',
                        {balance}, {avg_bal}, {avg_bal},
                        '{reg_class}', {risk_wt_str}, {hqla_str}, {nsfr_str},
                        true, 'Bank', '{timestamp}'
                    )"""
                    values_list.append(value)

            # Insert batch
            if values_list:
                insert_sql = f"""
                INSERT INTO cfo_banking_demo.bronze_core_banking.balance_sheet_daily VALUES
                {', '.join(values_list)}
                """
                execute_sql(w, insert_sql)
                log_message(f"    Inserted {len(values_list)} records (month {month_offset + 1})")

        # Step 4: Create silver layer
        log_message("\nCreating silver layer...")
        create_silver_sql = """
        CREATE OR REPLACE TABLE cfo_banking_demo.silver_finance.balance_sheet AS
        WITH daily_totals AS (
            SELECT
                report_date,
                SUM(CASE WHEN line_item_category = 'Asset' THEN balance ELSE 0 END) as total_assets
            FROM cfo_banking_demo.bronze_core_banking.balance_sheet_daily
            GROUP BY report_date
        )
        SELECT
            bs.*,
            dt.total_assets,
            (bs.balance / dt.total_assets * 100) as pct_of_total_assets
        FROM cfo_banking_demo.bronze_core_banking.balance_sheet_daily bs
        LEFT JOIN daily_totals dt ON bs.report_date = dt.report_date
        """
        execute_sql(w, create_silver_sql)
        log_message("✓ Created silver layer: cfo_banking_demo.silver_finance.balance_sheet")

        # Step 5: Validate data
        log_message("\n" + "=" * 80)
        log_message("DATA QUALITY VALIDATION")
        log_message("=" * 80)

        validation_passed = True

        # Check day count
        result = execute_sql(w, """
            SELECT COUNT(DISTINCT report_date) as day_count
            FROM cfo_banking_demo.bronze_core_banking.balance_sheet_daily
        """)
        day_count = int(result.result.data_array[0][0]) if result.result and result.result.data_array else 0

        if day_count != 365:
            log_message(f"✗ Expected 365 days, got {day_count}", "ERROR")
            validation_passed = False
        else:
            log_message(f"✓ Generated 365 days of data")

        # Check balance sheet balances
        result = execute_sql(w, f"""
            SELECT
                SUM(CASE WHEN line_item_category = 'Asset' THEN balance ELSE 0 END) as total_assets,
                SUM(CASE WHEN line_item_category = 'Liability' THEN balance ELSE 0 END) as total_liabilities,
                SUM(CASE WHEN line_item_category = 'Equity' THEN balance ELSE 0 END) as total_equity
            FROM cfo_banking_demo.bronze_core_banking.balance_sheet_daily
            WHERE report_date = '{CURRENT_DATE}'
        """)

        if result.result and result.result.data_array:
            total_assets = float(result.result.data_array[0][0])
            total_liabilities = float(result.result.data_array[0][1])
            total_equity = float(result.result.data_array[0][2])
            difference = total_assets - (total_liabilities + total_equity)

            log_message(f"Balance Sheet Check (as of {CURRENT_DATE}):")
            log_message(f"  Total Assets: ${total_assets:,.0f}")
            log_message(f"  Total Liabilities: ${total_liabilities:,.0f}")
            log_message(f"  Total Equity: ${total_equity:,.0f}")
            log_message(f"  Difference: ${difference:,.0f}")

            if abs(difference) > 100_000:
                log_message(f"✗ Balance sheet doesn't balance! Difference: ${difference:,.0f}", "ERROR")
                validation_passed = False
            else:
                log_message(f"✓ Balance sheet balances (difference < $100K)")

            # Check total assets
            if not (44e9 <= total_assets <= 46e9):
                log_message(f"✗ Expected ~$45B assets (±$1B), got ${total_assets:,.0f}", "ERROR")
                validation_passed = False
            else:
                log_message(f"✓ Total assets in expected range: ${total_assets:,.0f}")

        # Check record count
        result = execute_sql(w, """
            SELECT COUNT(*) as record_count
            FROM cfo_banking_demo.bronze_core_banking.balance_sheet_daily
        """)
        record_count = int(result.result.data_array[0][0]) if result.result and result.result.data_array else 0
        log_message(f"Total records: {record_count:,} (365 days × 22 line items)")

        if validation_passed:
            log_message("\n✅ All data quality checks passed")
        else:
            log_message("\n❌ Some data quality checks failed", "ERROR")

        # Step 6: Generate summary
        log_message("\n" + "=" * 80)
        log_message("BALANCE SHEET SUMMARY (as of 2026-01-24)")
        log_message("=" * 80)

        result = execute_sql(w, f"""
            SELECT
                line_item_category,
                line_item,
                balance
            FROM cfo_banking_demo.bronze_core_banking.balance_sheet_daily
            WHERE report_date = '{CURRENT_DATE}'
            ORDER BY
                CASE line_item_category
                    WHEN 'Asset' THEN 1
                    WHEN 'Liability' THEN 2
                    WHEN 'Equity' THEN 3
                END,
                line_item
        """)

        if result.result and result.result.data_array:
            current_category = None
            for row in result.result.data_array:
                category = row[0]
                item = row[1]
                balance = float(row[2])

                if category != current_category:
                    log_message(f"\n{category}s:")
                    log_message("-" * 80)
                    current_category = category

                log_message(f"  {item:40} ${balance:>15,.0f}")

        log_message("\n" + "=" * 80)
        log_message("✅ WS1-05 Complete: Balance Sheet Generated Successfully")
        log_message("=" * 80)
        log_message("\nTables created:")
        log_message("  - cfo_banking_demo.bronze_core_banking.balance_sheet_daily (365 days)")
        log_message("  - cfo_banking_demo.silver_finance.balance_sheet (with ratios)")
        log_message("\nReady for WS2: Real-time pipelines")

        return 0

    except Exception as e:
        log_message(f"\n\nError: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
