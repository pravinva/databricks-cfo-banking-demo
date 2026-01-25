#!/usr/bin/env python3
"""
WS3-03: Risk Weighted Assets (RWA) Calculator
Calculate regulatory RWA using Basel III standardized approach
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

def create_rwa_loan_portfolio(w):
    """Calculate RWA for loan portfolio using standardized approach"""

    log_message("Calculating RWA for loan portfolio...")

    # Basel III standardized risk weights:
    # C&I (Corporate): 100% (unrated)
    # Commercial_RE: 100%
    # Residential_Mortgage: 35% (standardized approach)
    # HELOC: 75%
    # Consumer_Auto: 75%
    # Consumer_Other: 75%

    create_table_sql = """
    CREATE OR REPLACE TABLE cfo_banking_demo.gold_regulatory.rwa_loan_portfolio AS
    SELECT
        loan_id,
        product_type,
        current_balance as exposure_amount,
        CASE
            WHEN product_type = 'C&I' THEN 1.00
            WHEN product_type = 'Commercial_RE' THEN 1.00
            WHEN product_type = 'Residential_Mortgage' THEN 0.35
            WHEN product_type = 'HELOC' THEN 0.75
            WHEN product_type = 'Consumer_Auto' THEN 0.75
            WHEN product_type = 'Consumer_Other' THEN 0.75
            ELSE 1.00
        END as risk_weight,
        current_balance * CASE
            WHEN product_type = 'C&I' THEN 1.00
            WHEN product_type = 'Commercial_RE' THEN 1.00
            WHEN product_type = 'Residential_Mortgage' THEN 0.35
            WHEN product_type = 'HELOC' THEN 0.75
            WHEN product_type = 'Consumer_Auto' THEN 0.75
            WHEN product_type = 'Consumer_Other' THEN 0.75
            ELSE 1.00
        END as rwa_amount,
        CURRENT_DATE() as calculation_date
    FROM cfo_banking_demo.silver_finance.loan_portfolio
    WHERE is_current = true
    """

    execute_sql(w, create_table_sql)

    # Get summary by product
    result = execute_sql(w, """
        SELECT
            product_type,
            COUNT(*) as loan_count,
            SUM(exposure_amount) as total_exposure,
            AVG(risk_weight) * 100 as risk_weight_pct,
            SUM(rwa_amount) as total_rwa
        FROM cfo_banking_demo.gold_regulatory.rwa_loan_portfolio
        GROUP BY product_type
        ORDER BY total_rwa DESC
    """)

    total_rwa_loans = 0
    total_exposure = 0
    if result.result and result.result.data_array:
        log_message("  RWA by Loan Product:")
        for row in result.result.data_array:
            product = row[0]
            count = int(row[1])
            exposure = float(row[2])
            rw_pct = float(row[3])
            rwa = float(row[4])
            total_rwa_loans += rwa
            total_exposure += exposure
            log_message(f"    {product:25s} {count:5d} loans, ${exposure:,.0f} @ {rw_pct:.0f}% = RWA ${rwa:,.0f}")

    log_message(f"  ✓ Total Loan RWA: ${total_rwa_loans:,.0f} (Exposure: ${total_exposure:,.0f})")

    return {
        'loan_rwa': total_rwa_loans,
        'loan_exposure': total_exposure
    }

def create_rwa_securities_portfolio(w):
    """Calculate RWA for securities portfolio"""

    log_message("Calculating RWA for securities portfolio...")

    # Risk weights based on security type:
    # US_Treasury: 0%
    # US_Agency: 20%
    # GSE_MBS: 20%
    # Municipal: 20%
    # Corporate: 20% (investment grade), 100% (unrated)
    # ABS: 100%

    create_table_sql = """
    CREATE OR REPLACE TABLE cfo_banking_demo.gold_regulatory.rwa_securities_portfolio AS
    SELECT
        security_id,
        security_type,
        security_name,
        market_value as exposure_amount,
        CASE
            WHEN security_type = 'US_Treasury' THEN 0.00
            WHEN security_type = 'US_Agency' THEN 0.20
            WHEN security_type = 'GSE_MBS' THEN 0.20
            WHEN security_type = 'Municipal' THEN 0.20
            WHEN security_type = 'Corporate' THEN 0.20
            WHEN security_type = 'ABS' THEN 1.00
            ELSE 1.00
        END as risk_weight,
        market_value * CASE
            WHEN security_type = 'US_Treasury' THEN 0.00
            WHEN security_type = 'US_Agency' THEN 0.20
            WHEN security_type = 'GSE_MBS' THEN 0.20
            WHEN security_type = 'Municipal' THEN 0.20
            WHEN security_type = 'Corporate' THEN 0.20
            WHEN security_type = 'ABS' THEN 1.00
            ELSE 1.00
        END as rwa_amount,
        CURRENT_DATE() as calculation_date
    FROM cfo_banking_demo.silver_finance.securities
    WHERE is_current = true
    """

    execute_sql(w, create_table_sql)

    # Get summary by security type
    result = execute_sql(w, """
        SELECT
            security_type,
            COUNT(*) as security_count,
            SUM(exposure_amount) as total_exposure,
            AVG(risk_weight) * 100 as risk_weight_pct,
            SUM(rwa_amount) as total_rwa
        FROM cfo_banking_demo.gold_regulatory.rwa_securities_portfolio
        GROUP BY security_type
        ORDER BY total_rwa DESC
    """)

    total_rwa_securities = 0
    total_exposure = 0
    if result.result and result.result.data_array:
        log_message("  RWA by Security Type:")
        for row in result.result.data_array:
            sec_type = row[0]
            count = int(row[1])
            exposure = float(row[2])
            rw_pct = float(row[3])
            rwa = float(row[4])
            total_rwa_securities += rwa
            total_exposure += exposure
            log_message(f"    {sec_type:15s} {count:4d} securities, ${exposure:,.0f} @ {rw_pct:.0f}% = RWA ${rwa:,.0f}")

    log_message(f"  ✓ Total Securities RWA: ${total_rwa_securities:,.0f} (Exposure: ${total_exposure:,.0f})")

    return {
        'securities_rwa': total_rwa_securities,
        'securities_exposure': total_exposure
    }

def create_rwa_operational_risk(w):
    """Calculate operational risk RWA using Basic Indicator Approach (BIA)"""

    log_message("Calculating Operational Risk RWA (BIA)...")

    # Basic Indicator Approach: 15% of average gross income over 3 years
    # Simplified: Use current year net interest income + non-interest income

    # Get revenue from balance sheet
    result = execute_sql(w, """
        SELECT
            SUM(CASE WHEN line_item = 'Net_Interest_Income' THEN balance ELSE 0 END) as net_interest_income,
            SUM(CASE WHEN line_item LIKE '%Fee%' OR line_item = 'Investment_Gains' THEN balance ELSE 0 END) as non_interest_income
        FROM cfo_banking_demo.silver_finance.balance_sheet
        WHERE report_date = CURRENT_DATE()
    """)

    net_interest_income = 0
    non_interest_income = 0
    if result.result and result.result.data_array and result.result.data_array[0]:
        net_interest_income = float(result.result.data_array[0][0] or 0)
        non_interest_income = float(result.result.data_array[0][1] or 0)

    gross_income = net_interest_income + non_interest_income
    operational_rwa = gross_income * 0.15  # 15% BIA multiplier

    log_message(f"  Net Interest Income: ${net_interest_income:,.0f}")
    log_message(f"  Non-Interest Income: ${non_interest_income:,.0f}")
    log_message(f"  Gross Income: ${gross_income:,.0f}")
    log_message(f"  ✓ Operational RWA (15% × Gross Income): ${operational_rwa:,.0f}")

    return operational_rwa

def create_rwa_summary(w, loan_rwa, securities_rwa, operational_rwa):
    """Create summary RWA table"""

    log_message("Creating RWA summary table...")

    create_summary_sql = f"""
    CREATE OR REPLACE TABLE cfo_banking_demo.gold_regulatory.rwa_summary AS
    SELECT
        CURRENT_DATE() as report_date,
        {loan_rwa:.2f} as loan_rwa,
        {securities_rwa:.2f} as securities_rwa,
        0.0 as other_assets_rwa,
        {operational_rwa:.2f} as operational_risk_rwa,
        {loan_rwa + securities_rwa + operational_rwa:.2f} as total_rwa
    """

    execute_sql(w, create_summary_sql)
    log_message("  ✓ RWA summary table created")

    return loan_rwa + securities_rwa + operational_rwa

def calculate_capital_ratios(w, total_rwa):
    """Calculate capital adequacy ratios"""

    log_message("Calculating capital ratios...")

    # Get capital from balance sheet
    result = execute_sql(w, """
        SELECT
            SUM(CASE WHEN line_item = 'Common_Equity' THEN balance ELSE 0 END) as cet1_capital,
            SUM(CASE WHEN line_item IN ('Common_Equity', 'Preferred_Stock') THEN balance ELSE 0 END) as tier1_capital,
            SUM(CASE WHEN line_item IN ('Common_Equity', 'Preferred_Stock', 'Subordinated_Debt') THEN balance ELSE 0 END) as total_capital
        FROM cfo_banking_demo.silver_finance.balance_sheet
        WHERE report_date = CURRENT_DATE()
    """)

    cet1_capital = 0
    tier1_capital = 0
    total_capital = 0
    if result.result and result.result.data_array and result.result.data_array[0]:
        cet1_capital = float(result.result.data_array[0][0] or 0)
        tier1_capital = float(result.result.data_array[0][1] or 0)
        total_capital = float(result.result.data_array[0][2] or 0)

    cet1_ratio = (cet1_capital / total_rwa * 100) if total_rwa > 0 else 0
    tier1_ratio = (tier1_capital / total_rwa * 100) if total_rwa > 0 else 0
    total_capital_ratio = (total_capital / total_rwa * 100) if total_rwa > 0 else 0

    # Create capital ratios table
    create_ratios_sql = f"""
    CREATE OR REPLACE TABLE cfo_banking_demo.gold_regulatory.capital_adequacy AS
    SELECT
        CURRENT_DATE() as report_date,
        {cet1_capital:.2f} as cet1_capital,
        {tier1_capital:.2f} as tier1_capital,
        {total_capital:.2f} as total_capital,
        {total_rwa:.2f} as total_rwa,
        {cet1_ratio:.4f} as cet1_ratio_pct,
        {tier1_ratio:.4f} as tier1_ratio_pct,
        {total_capital_ratio:.4f} as total_capital_ratio_pct,
        CASE WHEN {cet1_ratio} >= 4.5 THEN 'Compliant' ELSE 'Non-Compliant' END as cet1_status,
        CASE WHEN {tier1_ratio} >= 6.0 THEN 'Compliant' ELSE 'Non-Compliant' END as tier1_status,
        CASE WHEN {total_capital_ratio} >= 8.0 THEN 'Compliant' ELSE 'Non-Compliant' END as total_capital_status
    """

    execute_sql(w, create_ratios_sql)

    return {
        'cet1_capital': cet1_capital,
        'tier1_capital': tier1_capital,
        'total_capital': total_capital,
        'cet1_ratio': cet1_ratio,
        'tier1_ratio': tier1_ratio,
        'total_capital_ratio': total_capital_ratio
    }

def main():
    log_message("=" * 80)
    log_message("WS3-03: Risk Weighted Assets (RWA) Calculator")
    log_message("=" * 80)

    # Initialize Databricks client
    w = WorkspaceClient()
    log_message("✓ Connected to Databricks")
    log_message(f"✓ Using SQL Warehouse: {WAREHOUSE_ID}")

    log_message("")
    log_message("-" * 80)

    # Calculate loan RWA
    loan_metrics = create_rwa_loan_portfolio(w)

    log_message("")
    log_message("-" * 80)

    # Calculate securities RWA
    securities_metrics = create_rwa_securities_portfolio(w)

    log_message("")
    log_message("-" * 80)

    # Calculate operational risk RWA
    operational_rwa = create_rwa_operational_risk(w)

    log_message("")
    log_message("-" * 80)

    # Create summary
    total_rwa = create_rwa_summary(w,
                                    loan_metrics['loan_rwa'],
                                    securities_metrics['securities_rwa'],
                                    operational_rwa)

    log_message("")
    log_message("-" * 80)

    # Calculate capital ratios
    capital_metrics = calculate_capital_ratios(w, total_rwa)

    # Print summary report
    log_message("")
    log_message("=" * 80)
    log_message(f"RISK WEIGHTED ASSETS CALCULATION (as of {CURRENT_DATE})")
    log_message("=" * 80)
    log_message("")
    log_message("Risk Weighted Assets Breakdown:")
    log_message("-" * 80)
    log_message(f"  Loan Portfolio RWA:        ${loan_metrics['loan_rwa']:>15,.0f} ({loan_metrics['loan_rwa']/total_rwa*100:>5.1f}%)")
    log_message(f"  Securities Portfolio RWA:  ${securities_metrics['securities_rwa']:>15,.0f} ({securities_metrics['securities_rwa']/total_rwa*100:>5.1f}%)")
    log_message(f"  Operational Risk RWA:      ${operational_rwa:>15,.0f} ({operational_rwa/total_rwa*100:>5.1f}%)")
    log_message(f"  Total RWA:                 ${total_rwa:>15,.0f}")
    log_message("")
    log_message("Capital Adequacy Ratios:")
    log_message("-" * 80)
    log_message(f"  CET1 Capital:    ${capital_metrics['cet1_capital']:>15,.0f}")
    log_message(f"  Tier 1 Capital:  ${capital_metrics['tier1_capital']:>15,.0f}")
    log_message(f"  Total Capital:   ${capital_metrics['total_capital']:>15,.0f}")
    log_message("")
    log_message("  CET1 Ratio:      {:.2f}%  (Min 4.5%) {}".format(
        capital_metrics['cet1_ratio'],
        "✓ Compliant" if capital_metrics['cet1_ratio'] >= 4.5 else "✗ Non-Compliant"
    ))
    log_message("  Tier 1 Ratio:    {:.2f}%  (Min 6.0%) {}".format(
        capital_metrics['tier1_ratio'],
        "✓ Compliant" if capital_metrics['tier1_ratio'] >= 6.0 else "✗ Non-Compliant"
    ))
    log_message("  Total CAR:       {:.2f}%  (Min 8.0%) {}".format(
        capital_metrics['total_capital_ratio'],
        "✓ Compliant" if capital_metrics['total_capital_ratio'] >= 8.0 else "✗ Non-Compliant"
    ))
    log_message("")
    log_message("=" * 80)
    log_message("✅ WS3-03 Complete: RWA Calculator Successful")
    log_message("=" * 80)
    log_message("")
    log_message("Tables created:")
    log_message("  - cfo_banking_demo.gold_regulatory.rwa_loan_portfolio")
    log_message("  - cfo_banking_demo.gold_regulatory.rwa_securities_portfolio")
    log_message("  - cfo_banking_demo.gold_regulatory.rwa_summary")
    log_message("  - cfo_banking_demo.gold_regulatory.capital_adequacy")
    log_message("")

if __name__ == "__main__":
    main()
