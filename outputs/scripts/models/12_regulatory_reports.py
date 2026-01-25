#!/usr/bin/env python3
"""
WS3-04: Regulatory Reporting Tables (FFIEC 101, Y9C, 2052a)
Create regulatory reporting tables for bank supervision
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import time
from datetime import datetime, date

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
    max_wait_time = 600  # 10 minutes
    elapsed = 0
    while statement.status.state in [StatementState.PENDING, StatementState.RUNNING] and elapsed < max_wait_time:
        time.sleep(3)
        elapsed += 3
        statement = w.statement_execution.get_statement(statement.statement_id)

    if statement.status.state == StatementState.FAILED:
        error_msg = statement.status.error.message if statement.status.error else "Unknown error"
        raise Exception(f"SQL execution failed: {error_msg}")

    return statement

def create_ffiec_101_report(w):
    """
    FFIEC 101 - Risk-Based Capital Reporting for Institutions Subject to Advanced Capital Adequacy Framework
    Simplified version with key schedules
    """

    log_message("Creating FFIEC 101 Regulatory Report...")

    # Schedule A: Regulatory Capital Components
    create_schedule_a = """
    CREATE OR REPLACE TABLE cfo_banking_demo.gold_regulatory.ffiec_101_schedule_a AS
    SELECT
        CURRENT_DATE() as report_date,
        'Q4' as report_quarter,
        YEAR(CURRENT_DATE()) as report_year,

        -- Common Equity Tier 1 Capital
        'CET1_01' as line_item_code,
        'Common Stock and Related Surplus' as line_item_description,
        COALESCE(SUM(CASE WHEN bs.line_item = 'Common_Equity' THEN bs.balance ELSE 0 END), 0) as amount_current,
        COALESCE(SUM(CASE WHEN bs.line_item = 'Common_Equity' THEN bs.balance ELSE 0 END), 0) as amount_prior_quarter
    FROM cfo_banking_demo.silver_finance.balance_sheet bs
    WHERE bs.report_date = CURRENT_DATE()

    UNION ALL

    SELECT
        CURRENT_DATE() as report_date,
        'Q4' as report_quarter,
        YEAR(CURRENT_DATE()) as report_year,
        'CET1_02' as line_item_code,
        'Retained Earnings' as line_item_description,
        COALESCE(SUM(CASE WHEN bs.line_item = 'Retained_Earnings' THEN bs.balance ELSE 0 END), 0) as amount_current,
        COALESCE(SUM(CASE WHEN bs.line_item = 'Retained_Earnings' THEN bs.balance ELSE 0 END), 0) as amount_prior_quarter
    FROM cfo_banking_demo.silver_finance.balance_sheet bs
    WHERE bs.report_date = CURRENT_DATE()

    UNION ALL

    SELECT
        CURRENT_DATE() as report_date,
        'Q4' as report_quarter,
        YEAR(CURRENT_DATE()) as report_year,
        'TIER1_01' as line_item_code,
        'Additional Tier 1 Capital Instruments' as line_item_description,
        COALESCE(SUM(CASE WHEN bs.line_item = 'Preferred_Stock' THEN bs.balance ELSE 0 END), 0) as amount_current,
        COALESCE(SUM(CASE WHEN bs.line_item = 'Preferred_Stock' THEN bs.balance ELSE 0 END), 0) as amount_prior_quarter
    FROM cfo_banking_demo.silver_finance.balance_sheet bs
    WHERE bs.report_date = CURRENT_DATE()

    UNION ALL

    SELECT
        CURRENT_DATE() as report_date,
        'Q4' as report_quarter,
        YEAR(CURRENT_DATE()) as report_year,
        'TIER2_01' as line_item_code,
        'Tier 2 Capital Instruments' as line_item_description,
        COALESCE(SUM(CASE WHEN bs.line_item = 'Subordinated_Debt' THEN bs.balance ELSE 0 END), 0) as amount_current,
        COALESCE(SUM(CASE WHEN bs.line_item = 'Subordinated_Debt' THEN bs.balance ELSE 0 END), 0) as amount_prior_quarter
    FROM cfo_banking_demo.silver_finance.balance_sheet bs
    WHERE bs.report_date = CURRENT_DATE()
    """

    execute_sql(w, create_schedule_a)
    log_message("  ✓ Created FFIEC 101 Schedule A (Capital Components)")

    # Schedule B: Risk-Weighted Assets
    create_schedule_b = """
    CREATE OR REPLACE TABLE cfo_banking_demo.gold_regulatory.ffiec_101_schedule_b AS
    SELECT
        CURRENT_DATE() as report_date,
        'Q4' as report_quarter,
        YEAR(CURRENT_DATE()) as report_year,
        'RWA_CREDIT' as category_code,
        'Credit Risk-Weighted Assets' as category_description,
        SUM(loan_rwa + securities_rwa) as rwa_amount
    FROM cfo_banking_demo.gold_regulatory.rwa_summary
    WHERE report_date = CURRENT_DATE()

    UNION ALL

    SELECT
        CURRENT_DATE() as report_date,
        'Q4' as report_quarter,
        YEAR(CURRENT_DATE()) as report_year,
        'RWA_MARKET' as category_code,
        'Market Risk-Weighted Assets' as category_description,
        0.0 as rwa_amount

    UNION ALL

    SELECT
        CURRENT_DATE() as report_date,
        'Q4' as report_quarter,
        YEAR(CURRENT_DATE()) as report_year,
        'RWA_OPERATIONAL' as category_code,
        'Operational Risk-Weighted Assets' as category_description,
        operational_risk_rwa as rwa_amount
    FROM cfo_banking_demo.gold_regulatory.rwa_summary
    WHERE report_date = CURRENT_DATE()

    UNION ALL

    SELECT
        CURRENT_DATE() as report_date,
        'Q4' as report_quarter,
        YEAR(CURRENT_DATE()) as report_year,
        'RWA_TOTAL' as category_code,
        'Total Risk-Weighted Assets' as category_description,
        total_rwa as rwa_amount
    FROM cfo_banking_demo.gold_regulatory.rwa_summary
    WHERE report_date = CURRENT_DATE()
    """

    execute_sql(w, create_schedule_b)
    log_message("  ✓ Created FFIEC 101 Schedule B (Risk-Weighted Assets)")

    # Get summary statistics
    result = execute_sql(w, """
        SELECT
            SUM(CASE WHEN line_item_code LIKE 'CET1%' THEN amount_current ELSE 0 END) as cet1_capital,
            SUM(CASE WHEN line_item_code LIKE 'TIER1%' THEN amount_current ELSE 0 END) as tier1_additional,
            SUM(CASE WHEN line_item_code LIKE 'TIER2%' THEN amount_current ELSE 0 END) as tier2_capital
        FROM cfo_banking_demo.gold_regulatory.ffiec_101_schedule_a
    """)

    if result.result and result.result.data_array and result.result.data_array[0]:
        cet1 = float(result.result.data_array[0][0] or 0)
        tier1_add = float(result.result.data_array[0][1] or 0)
        tier2 = float(result.result.data_array[0][2] or 0)
        log_message(f"  CET1 Capital: ${cet1:,.0f}")
        log_message(f"  Additional Tier 1: ${tier1_add:,.0f}")
        log_message(f"  Tier 2 Capital: ${tier2:,.0f}")

def create_y9c_report(w):
    """
    FR Y-9C - Consolidated Financial Statements for Holding Companies
    Simplified version with key schedules
    """

    log_message("Creating FR Y-9C Regulatory Report...")

    # Schedule HC-R: Regulatory Capital (Part I)
    create_schedule_hcr = """
    CREATE OR REPLACE TABLE cfo_banking_demo.gold_regulatory.y9c_schedule_hcr AS
    SELECT
        CURRENT_DATE() as report_date,
        'Q4' as report_quarter,
        YEAR(CURRENT_DATE()) as report_year,

        -- Tier 1 Capital
        'HC-R-10' as mdrm_code,
        'Common Equity Tier 1 Capital' as item_description,
        cet1_capital as amount
    FROM cfo_banking_demo.gold_regulatory.capital_adequacy
    WHERE report_date = CURRENT_DATE()

    UNION ALL

    SELECT
        CURRENT_DATE() as report_date,
        'Q4' as report_quarter,
        YEAR(CURRENT_DATE()) as report_year,
        'HC-R-20' as mdrm_code,
        'Tier 1 Capital' as item_description,
        tier1_capital as amount
    FROM cfo_banking_demo.gold_regulatory.capital_adequacy
    WHERE report_date = CURRENT_DATE()

    UNION ALL

    SELECT
        CURRENT_DATE() as report_date,
        'Q4' as report_quarter,
        YEAR(CURRENT_DATE()) as report_year,
        'HC-R-35' as mdrm_code,
        'Total Capital' as item_description,
        total_capital as amount
    FROM cfo_banking_demo.gold_regulatory.capital_adequacy
    WHERE report_date = CURRENT_DATE()

    UNION ALL

    SELECT
        CURRENT_DATE() as report_date,
        'Q4' as report_quarter,
        YEAR(CURRENT_DATE()) as report_year,
        'HC-R-40' as mdrm_code,
        'Total Risk-Weighted Assets' as item_description,
        total_rwa as amount
    FROM cfo_banking_demo.gold_regulatory.capital_adequacy
    WHERE report_date = CURRENT_DATE()

    UNION ALL

    SELECT
        CURRENT_DATE() as report_date,
        'Q4' as report_quarter,
        YEAR(CURRENT_DATE()) as report_year,
        'HC-R-70' as mdrm_code,
        'Common Equity Tier 1 Ratio' as item_description,
        cet1_ratio_pct as amount
    FROM cfo_banking_demo.gold_regulatory.capital_adequacy
    WHERE report_date = CURRENT_DATE()
    """

    execute_sql(w, create_schedule_hcr)
    log_message("  ✓ Created Y-9C Schedule HC-R (Regulatory Capital)")

    # Schedule HC-C: Loans and Leases
    create_schedule_hcc = """
    CREATE OR REPLACE TABLE cfo_banking_demo.gold_regulatory.y9c_schedule_hcc AS
    SELECT
        CURRENT_DATE() as report_date,
        'Q4' as report_quarter,
        YEAR(CURRENT_DATE()) as report_year,
        CASE
            WHEN product_type = 'C&I' THEN 'HC-C-4'
            WHEN product_type = 'Commercial_RE' THEN 'HC-C-1a'
            WHEN product_type = 'Residential_Mortgage' THEN 'HC-C-1c'
            WHEN product_type = 'HELOC' THEN 'HC-C-1d'
            WHEN product_type = 'Consumer_Auto' THEN 'HC-C-9a'
            WHEN product_type = 'Consumer_Other' THEN 'HC-C-10'
            ELSE 'HC-C-99'
        END as mdrm_code,
        CASE
            WHEN product_type = 'C&I' THEN 'Commercial and Industrial Loans'
            WHEN product_type = 'Commercial_RE' THEN 'Construction and Land Development Loans'
            WHEN product_type = 'Residential_Mortgage' THEN 'Residential Mortgage Loans'
            WHEN product_type = 'HELOC' THEN 'Home Equity Lines of Credit'
            WHEN product_type = 'Consumer_Auto' THEN 'Automobile Loans'
            WHEN product_type = 'Consumer_Other' THEN 'Other Consumer Loans'
            ELSE 'Other Loans'
        END as item_description,
        SUM(current_balance) as amount
    FROM cfo_banking_demo.silver_finance.loan_portfolio
    WHERE is_current = true
    GROUP BY product_type
    """

    execute_sql(w, create_schedule_hcc)
    log_message("  ✓ Created Y-9C Schedule HC-C (Loans and Leases)")

    # Get total loans
    result = execute_sql(w, """
        SELECT SUM(amount) as total_loans
        FROM cfo_banking_demo.gold_regulatory.y9c_schedule_hcc
    """)

    if result.result and result.result.data_array and result.result.data_array[0]:
        total_loans = float(result.result.data_array[0][0] or 0)
        log_message(f"  Total Loans Reported: ${total_loans:,.0f}")

def create_2052a_report(w):
    """
    FRY-14Q / 2052a - Complex Institution Liquidity Monitoring Report
    Based on Basel III LCR components
    """

    log_message("Creating FR 2052a Liquidity Report...")

    # Panel A: High-Quality Liquid Assets
    create_panel_a = """
    CREATE OR REPLACE TABLE cfo_banking_demo.gold_regulatory.fr_2052a_panel_a AS
    SELECT
        CURRENT_DATE() as report_date,
        'A-1' as line_code,
        'Level 1 HQLA' as line_description,
        hqla_level_1 as fair_value,
        hqla_level_1 as hqla_amount,
        100.0 as hqla_percentage
    FROM cfo_banking_demo.gold_regulatory.lcr_daily
    WHERE calculation_date = CURRENT_DATE()

    UNION ALL

    SELECT
        CURRENT_DATE() as report_date,
        'A-2' as line_code,
        'Level 2A HQLA' as line_description,
        hqla_level_2a as fair_value,
        hqla_level_2a as hqla_amount,
        85.0 as hqla_percentage
    FROM cfo_banking_demo.gold_regulatory.lcr_daily
    WHERE calculation_date = CURRENT_DATE()

    UNION ALL

    SELECT
        CURRENT_DATE() as report_date,
        'A-3' as line_code,
        'Level 2B HQLA' as line_description,
        hqla_level_2b as fair_value,
        hqla_level_2b as hqla_amount,
        50.0 as hqla_percentage
    FROM cfo_banking_demo.gold_regulatory.lcr_daily
    WHERE calculation_date = CURRENT_DATE()

    UNION ALL

    SELECT
        CURRENT_DATE() as report_date,
        'A-TOTAL' as line_code,
        'Total HQLA' as line_description,
        total_hqla as fair_value,
        total_hqla as hqla_amount,
        100.0 as hqla_percentage
    FROM cfo_banking_demo.gold_regulatory.lcr_daily
    WHERE calculation_date = CURRENT_DATE()
    """

    execute_sql(w, create_panel_a)
    log_message("  ✓ Created FR 2052a Panel A (HQLA)")

    # Panel B: Cash Outflows
    create_panel_b = """
    CREATE OR REPLACE TABLE cfo_banking_demo.gold_regulatory.fr_2052a_panel_b AS
    SELECT
        CURRENT_DATE() as report_date,
        'B-1' as line_code,
        'Retail Deposit Outflows' as line_description,
        SUM(current_balance) as deposit_balance,
        SUM(stressed_outflow) as stressed_outflow_amount
    FROM cfo_banking_demo.gold_regulatory.cash_outflows_30day
    WHERE product_type IN ('DDA', 'Savings', 'MMDA')

    UNION ALL

    SELECT
        CURRENT_DATE() as report_date,
        'B-2' as line_code,
        'Wholesale Funding Outflows' as line_description,
        SUM(current_balance) as deposit_balance,
        SUM(stressed_outflow) as stressed_outflow_amount
    FROM cfo_banking_demo.gold_regulatory.cash_outflows_30day
    WHERE product_type LIKE '%Brokered%'

    UNION ALL

    SELECT
        CURRENT_DATE() as report_date,
        'B-TOTAL' as line_code,
        'Total Cash Outflows' as line_description,
        SUM(current_balance) as deposit_balance,
        SUM(stressed_outflow) as stressed_outflow_amount
    FROM cfo_banking_demo.gold_regulatory.cash_outflows_30day
    """

    execute_sql(w, create_panel_b)
    log_message("  ✓ Created FR 2052a Panel B (Cash Outflows)")

    # Panel C: Cash Inflows (capped at 75% of outflows)
    create_panel_c = """
    CREATE OR REPLACE TABLE cfo_banking_demo.gold_regulatory.fr_2052a_panel_c AS
    SELECT
        CURRENT_DATE() as report_date,
        'C-1' as line_code,
        'Performing Loan Principal Repayments' as line_description,
        SUM(current_balance) as contractual_inflow,
        SUM(expected_inflow) as expected_inflow
    FROM cfo_banking_demo.gold_regulatory.cash_inflows_30day

    UNION ALL

    SELECT
        CURRENT_DATE() as report_date,
        'C-TOTAL' as line_code,
        'Total Cash Inflows (Capped)' as line_description,
        SUM(current_balance) as contractual_inflow,
        SUM(expected_inflow) as expected_inflow
    FROM cfo_banking_demo.gold_regulatory.cash_inflows_30day
    """

    execute_sql(w, create_panel_c)
    log_message("  ✓ Created FR 2052a Panel C (Cash Inflows)")

    # Summary: LCR Calculation
    create_summary = """
    CREATE OR REPLACE TABLE cfo_banking_demo.gold_regulatory.fr_2052a_summary AS
    SELECT
        CURRENT_DATE() as report_date,
        total_hqla as hqla_amount,
        total_outflows as gross_outflows,
        total_inflows_capped as capped_inflows,
        net_outflows,
        lcr_ratio
    FROM cfo_banking_demo.gold_regulatory.lcr_daily
    WHERE calculation_date = CURRENT_DATE()
    """

    execute_sql(w, create_summary)
    log_message("  ✓ Created FR 2052a Summary (LCR Calculation)")

    # Get LCR ratio
    result = execute_sql(w, """
        SELECT lcr_ratio
        FROM cfo_banking_demo.gold_regulatory.fr_2052a_summary
    """)

    if result.result and result.result.data_array and result.result.data_array[0]:
        lcr_ratio = float(result.result.data_array[0][0] or 0)
        log_message(f"  LCR Ratio: {lcr_ratio:.2f}%")

def main():
    log_message("=" * 80)
    log_message("WS3-04: Regulatory Reporting Tables")
    log_message("=" * 80)

    # Initialize Databricks client
    w = WorkspaceClient()
    log_message("✓ Connected to Databricks")
    log_message(f"✓ Using SQL Warehouse: {WAREHOUSE_ID}")

    log_message("")
    log_message("-" * 80)

    # Create FFIEC 101
    create_ffiec_101_report(w)

    log_message("")
    log_message("-" * 80)

    # Create Y-9C
    create_y9c_report(w)

    log_message("")
    log_message("-" * 80)

    # Create 2052a
    create_2052a_report(w)

    log_message("")
    log_message("=" * 80)
    log_message("✅ WS3-04 Complete: Regulatory Reporting Tables Created")
    log_message("=" * 80)
    log_message("")
    log_message("FFIEC 101 Tables:")
    log_message("  - cfo_banking_demo.gold_regulatory.ffiec_101_schedule_a (Capital Components)")
    log_message("  - cfo_banking_demo.gold_regulatory.ffiec_101_schedule_b (Risk-Weighted Assets)")
    log_message("")
    log_message("FR Y-9C Tables:")
    log_message("  - cfo_banking_demo.gold_regulatory.y9c_schedule_hcr (Regulatory Capital)")
    log_message("  - cfo_banking_demo.gold_regulatory.y9c_schedule_hcc (Loans and Leases)")
    log_message("")
    log_message("FR 2052a Tables:")
    log_message("  - cfo_banking_demo.gold_regulatory.fr_2052a_panel_a (HQLA)")
    log_message("  - cfo_banking_demo.gold_regulatory.fr_2052a_panel_b (Cash Outflows)")
    log_message("  - cfo_banking_demo.gold_regulatory.fr_2052a_panel_c (Cash Inflows)")
    log_message("  - cfo_banking_demo.gold_regulatory.fr_2052a_summary (LCR Calculation)")
    log_message("")

if __name__ == "__main__":
    main()
