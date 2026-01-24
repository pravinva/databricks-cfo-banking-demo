#!/usr/bin/env python3
"""
WS3-02: Liquidity Coverage Ratio (LCR) Calculator
Calculate regulatory LCR: LCR = HQLA / Net Cash Outflows (must be > 100%)
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

def create_regulatory_schema(w):
    """Create gold regulatory schema"""
    log_message("Creating gold_regulatory schema...")
    execute_sql(w, "CREATE SCHEMA IF NOT EXISTS cfo_banking_demo.gold_regulatory")
    log_message("  ✓ Created gold_regulatory schema")

def calculate_hqla(w):
    """Calculate High Quality Liquid Assets"""

    log_message("Calculating HQLA (High Quality Liquid Assets)...")

    # Classify securities by HQLA level
    create_hqla_sql = """
    CREATE OR REPLACE TABLE cfo_banking_demo.gold_regulatory.hqla_inventory AS
    SELECT
        security_id,
        security_type,
        market_value,
        credit_rating,
        CASE
            WHEN security_type = 'UST' THEN 'Level_1'
            WHEN security_type = 'Agency' THEN 'Level_2A'
            WHEN security_type = 'Corporate' AND credit_rating IN ('AAA', 'AA+', 'AA', 'AA-') THEN 'Level_2A'
            WHEN security_type = 'Corporate' AND credit_rating IN ('A+', 'A', 'A-', 'BBB+', 'BBB', 'BBB-') THEN 'Level_2B'
            WHEN security_type = 'MBS' THEN 'Level_2A'
            ELSE 'Non_HQLA'
        END as hqla_level,
        CASE
            WHEN security_type = 'UST' THEN 0.0
            WHEN security_type = 'Agency' THEN 0.15
            WHEN security_type = 'MBS' THEN 0.15
            WHEN security_type = 'Corporate' AND credit_rating IN ('AAA', 'AA+', 'AA', 'AA-') THEN 0.15
            WHEN security_type = 'Corporate' THEN 0.50
            ELSE 1.0
        END as haircut,
        CASE
            WHEN security_type = 'UST' THEN market_value * 1.0
            WHEN security_type = 'Agency' THEN market_value * 0.85
            WHEN security_type = 'MBS' THEN market_value * 0.85
            WHEN security_type = 'Corporate' AND credit_rating IN ('AAA', 'AA+', 'AA', 'AA-') THEN market_value * 0.85
            WHEN security_type = 'Corporate' THEN market_value * 0.50
            ELSE 0.0
        END as hqla_value
    FROM cfo_banking_demo.silver_treasury.securities_portfolio
    WHERE is_current = true
    """

    execute_sql(w, create_hqla_sql)

    # Get HQLA totals
    result = execute_sql(w, """
        SELECT
            hqla_level,
            COUNT(*) as security_count,
            SUM(market_value) as market_value,
            SUM(hqla_value) as hqla_value
        FROM cfo_banking_demo.gold_regulatory.hqla_inventory
        GROUP BY hqla_level
        ORDER BY hqla_level
    """)

    hqla_totals = {}
    if result.result and result.result.data_array:
        log_message("  HQLA Breakdown:")
        for row in result.result.data_array:
            level = row[0]
            count = int(row[1])
            market_val = float(row[2])
            hqla_val = float(row[3])
            hqla_totals[level] = hqla_val
            log_message(f"    {level}: {count} securities, MV=${market_val:,.0f}, HQLA=${hqla_val:,.0f}")

    # Get cash position
    result = execute_sql(w, """
        SELECT SUM(balance) as cash_hqla
        FROM cfo_banking_demo.silver_finance.balance_sheet
        WHERE report_date = CURRENT_DATE()
        AND line_item IN ('Cash_Vault', 'Fed_Reserve_Account')
    """)

    cash_hqla = float(result.result.data_array[0][0]) if result.result and result.result.data_array and result.result.data_array[0][0] else 0

    hqla_level_1 = cash_hqla + hqla_totals.get('Level_1', 0)
    hqla_level_2a = hqla_totals.get('Level_2A', 0)
    hqla_level_2b = hqla_totals.get('Level_2B', 0)
    total_hqla = hqla_level_1 + hqla_level_2a + hqla_level_2b

    log_message(f"  Cash & Reserves: ${cash_hqla:,.0f}")
    log_message(f"  ✓ Total HQLA: ${total_hqla:,.0f}")

    return {
        'cash_hqla': cash_hqla,
        'hqla_level_1': hqla_level_1,
        'hqla_level_2a': hqla_level_2a,
        'hqla_level_2b': hqla_level_2b,
        'total_hqla': total_hqla
    }

def calculate_cash_outflows(w):
    """Calculate 30-day stressed cash outflows from deposits"""

    log_message("Calculating 30-day stressed cash outflows...")

    # Apply runoff rates to deposits
    create_outflows_sql = """
    CREATE OR REPLACE TABLE cfo_banking_demo.gold_regulatory.cash_outflows_30day AS
    SELECT
        account_id,
        product_type,
        product_name,
        current_balance,
        CASE
            WHEN product_type = 'DDA' THEN 0.03
            WHEN product_type = 'Savings' THEN 0.05
            WHEN product_type = 'NOW' THEN 0.05
            WHEN product_type = 'MMDA' THEN 0.10
            WHEN product_type = 'CD' AND product_name LIKE '%Brokered%' THEN 1.0
            WHEN product_type = 'CD' THEN 0.0
            ELSE 0.05
        END as runoff_rate,
        current_balance * CASE
            WHEN product_type = 'DDA' THEN 0.03
            WHEN product_type = 'Savings' THEN 0.05
            WHEN product_type = 'NOW' THEN 0.05
            WHEN product_type = 'MMDA' THEN 0.10
            WHEN product_type = 'CD' AND product_name LIKE '%Brokered%' THEN 1.0
            WHEN product_type = 'CD' THEN 0.0
            ELSE 0.05
        END as stressed_outflow
    FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
    WHERE account_status = 'Active'
    """

    execute_sql(w, create_outflows_sql)

    # Get outflow totals by product
    result = execute_sql(w, """
        SELECT
            product_type,
            SUM(current_balance) as total_balance,
            AVG(runoff_rate) as avg_runoff_rate,
            SUM(stressed_outflow) as total_outflow
        FROM cfo_banking_demo.gold_regulatory.cash_outflows_30day
        GROUP BY product_type
        ORDER BY total_outflow DESC
    """)

    total_outflows = 0
    if result.result and result.result.data_array:
        log_message("  Outflows by Product:")
        for row in result.result.data_array:
            product = row[0]
            balance = float(row[1])
            runoff = float(row[2])
            outflow = float(row[3])
            total_outflows += outflow
            log_message(f"    {product}: ${balance:,.0f} × {runoff*100:.1f}% = ${outflow:,.0f}")

    log_message(f"  ✓ Total Cash Outflows: ${total_outflows:,.0f}")

    return total_outflows

def calculate_cash_inflows(w):
    """Calculate 30-day cash inflows (capped at 75% of outflows)"""

    log_message("Calculating 30-day cash inflows...")

    # Identify loans maturing in next 30 days
    create_inflows_sql = """
    CREATE OR REPLACE TABLE cfo_banking_demo.gold_regulatory.cash_inflows_30day AS
    SELECT
        loan_id,
        product_type,
        current_balance,
        maturity_date,
        DATEDIFF(maturity_date, CURRENT_DATE()) as days_to_maturity,
        CASE
            WHEN product_type IN ('Commercial_RE', 'C&I') THEN 0.50
            WHEN product_type IN ('Residential_Mortgage', 'HELOC', 'Consumer_Auto', 'Consumer_Other') THEN 1.0
            ELSE 1.0
        END as inflow_rate,
        current_balance * CASE
            WHEN product_type IN ('Commercial_RE', 'C&I') THEN 0.50
            WHEN product_type IN ('Residential_Mortgage', 'HELOC', 'Consumer_Auto', 'Consumer_Other') THEN 1.0
            ELSE 1.0
        END as expected_inflow
    FROM cfo_banking_demo.silver_finance.loan_portfolio
    WHERE payment_status = 'Current'
    AND DATEDIFF(maturity_date, CURRENT_DATE()) BETWEEN 1 AND 30
    """

    execute_sql(w, create_inflows_sql)

    # Get total inflows
    result = execute_sql(w, """
        SELECT
            COUNT(*) as loan_count,
            SUM(expected_inflow) as total_inflows
        FROM cfo_banking_demo.gold_regulatory.cash_inflows_30day
    """)

    total_inflows_uncapped = 0
    loan_count = 0
    if result.result and result.result.data_array:
        loan_count = int(result.result.data_array[0][0]) if result.result.data_array[0][0] else 0
        total_inflows_uncapped = float(result.result.data_array[0][1]) if result.result.data_array[0][1] else 0

    log_message(f"  Loans maturing in 30 days: {loan_count}")
    log_message(f"  Uncapped inflows: ${total_inflows_uncapped:,.0f}")

    return total_inflows_uncapped

def calculate_lcr(w, hqla_data, total_outflows, total_inflows_uncapped):
    """Calculate LCR ratio"""

    log_message("Calculating LCR ratio...")

    # Cap inflows at 75% of outflows
    cap_limit = total_outflows * 0.75
    total_inflows_capped = min(total_inflows_uncapped, cap_limit)

    # Calculate net outflows (with 25% floor)
    net_outflows = max(
        total_outflows - total_inflows_capped,
        total_outflows * 0.25
    )

    # Calculate LCR ratio
    lcr_ratio = (hqla_data['total_hqla'] / net_outflows) * 100

    log_message(f"  Inflows capped at 75%: ${total_inflows_capped:,.0f}")
    log_message(f"  Net Outflows: ${net_outflows:,.0f}")
    log_message(f"  ✓ LCR Ratio: {lcr_ratio:.2f}%")

    return {
        'total_inflows_uncapped': total_inflows_uncapped,
        'total_inflows_capped': total_inflows_capped,
        'net_outflows': net_outflows,
        'lcr_ratio': lcr_ratio
    }

def save_lcr_record(w, hqla_data, total_outflows, lcr_data):
    """Save LCR calculation record"""

    log_message("Saving LCR calculation record...")

    # Create LCR daily table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS cfo_banking_demo.gold_regulatory.lcr_daily (
        calculation_date DATE,
        calculation_timestamp TIMESTAMP,
        total_hqla DECIMAL(18,2),
        hqla_level_1 DECIMAL(18,2),
        hqla_level_2a DECIMAL(18,2),
        hqla_level_2b DECIMAL(18,2),
        total_outflows DECIMAL(18,2),
        total_inflows_uncapped DECIMAL(18,2),
        total_inflows_capped DECIMAL(18,2),
        net_outflows DECIMAL(18,2),
        lcr_ratio DECIMAL(8,2),
        lcr_status STRING
    )
    """

    execute_sql(w, create_table_sql)

    # Insert record
    lcr_status = 'Pass' if lcr_data['lcr_ratio'] >= 100 else 'Fail'

    insert_sql = f"""
    INSERT INTO cfo_banking_demo.gold_regulatory.lcr_daily VALUES (
        '{CURRENT_DATE}',
        CURRENT_TIMESTAMP(),
        {hqla_data['total_hqla']},
        {hqla_data['hqla_level_1']},
        {hqla_data['hqla_level_2a']},
        {hqla_data['hqla_level_2b']},
        {total_outflows},
        {lcr_data['total_inflows_uncapped']},
        {lcr_data['total_inflows_capped']},
        {lcr_data['net_outflows']},
        {lcr_data['lcr_ratio']},
        '{lcr_status}'
    )
    """

    execute_sql(w, insert_sql)
    log_message("  ✓ LCR record saved")

def display_lcr_summary(hqla_data, total_outflows, lcr_data):
    """Display LCR calculation summary"""

    log_message("\n" + "=" * 80)
    log_message(f"LCR CALCULATION (as of {CURRENT_DATE})")
    log_message("=" * 80)

    log_message(f"\nHigh Quality Liquid Assets (HQLA):")
    log_message("-" * 80)
    log_message(f"  Level 1 (100%): ${hqla_data['hqla_level_1']:,.0f} ({hqla_data['hqla_level_1']/hqla_data['total_hqla']*100:.1f}%)")
    log_message(f"  Level 2A (85%): ${hqla_data['hqla_level_2a']:,.0f} ({hqla_data['hqla_level_2a']/hqla_data['total_hqla']*100:.1f}%)")
    log_message(f"  Level 2B (50%): ${hqla_data['hqla_level_2b']:,.0f} ({hqla_data['hqla_level_2b']/hqla_data['total_hqla']*100:.1f}%)")
    log_message(f"  Total HQLA:     ${hqla_data['total_hqla']:,.0f}")

    log_message(f"\nCash Flows (30-day stressed scenario):")
    log_message("-" * 80)
    log_message(f"  Gross Outflows:        ${total_outflows:,.0f}")
    log_message(f"  Less: Capped Inflows:  ${lcr_data['total_inflows_capped']:,.0f}")
    log_message(f"  Net Outflows:          ${lcr_data['net_outflows']:,.0f}")

    log_message(f"\nLCR Calculation:")
    log_message("-" * 80)
    log_message(f"  LCR = HQLA / Net Outflows")
    log_message(f"  LCR = ${hqla_data['total_hqla']:,.0f} / ${lcr_data['net_outflows']:,.0f}")
    log_message(f"  LCR = {lcr_data['lcr_ratio']:.2f}%")

    log_message(f"\nRegulatory Assessment:")
    log_message("-" * 80)
    log_message(f"  Required Minimum: 100.00%")
    log_message(f"  Actual LCR:       {lcr_data['lcr_ratio']:.2f}%")

    if lcr_data['lcr_ratio'] >= 100:
        buffer = lcr_data['lcr_ratio'] - 100
        log_message(f"  Status:           ✓ COMPLIANT")
        log_message(f"  Buffer:           +{buffer:.2f}%")
    else:
        shortfall = 100 - lcr_data['lcr_ratio']
        log_message(f"  Status:           ✗ NON-COMPLIANT")
        log_message(f"  Shortfall:        -{shortfall:.2f}%")

def run_stress_scenarios(w):
    """Run stress test scenarios"""

    log_message("\n" + "=" * 80)
    log_message("LCR STRESS TEST SCENARIOS")
    log_message("=" * 80)

    # Get latest LCR
    result = execute_sql(w, """
        SELECT
            total_hqla,
            total_outflows,
            total_inflows_capped
        FROM cfo_banking_demo.gold_regulatory.lcr_daily
        ORDER BY calculation_timestamp DESC
        LIMIT 1
    """)

    if result.result and result.result.data_array:
        row = result.result.data_array[0]
        hqla = float(row[0])
        outflows = float(row[1])
        inflows = float(row[2])

        scenarios = [
            ("Base Case", 1.0),
            ("Moderate Stress (1.5x runoff)", 1.5),
            ("Severe Stress (2.0x runoff)", 2.0),
            ("Extreme Stress (3.0x runoff)", 3.0)
        ]

        log_message("")
        for scenario_name, multiplier in scenarios:
            stressed_outflows = outflows * multiplier
            stressed_net = max(stressed_outflows - inflows, stressed_outflows * 0.25)
            stressed_lcr = (hqla / stressed_net) * 100
            status = "✓ Pass" if stressed_lcr >= 100 else "✗ Fail"

            log_message(f"{scenario_name}:")
            log_message(f"  Stressed Outflows: ${stressed_outflows:,.0f}")
            log_message(f"  Net Outflows:      ${stressed_net:,.0f}")
            log_message(f"  LCR Ratio:         {stressed_lcr:.2f}% {status}")
            log_message("")

def main():
    """Main execution function"""
    try:
        log_message("=" * 80)
        log_message("WS3-02: Liquidity Coverage Ratio (LCR) Calculator")
        log_message("=" * 80)

        # Initialize Databricks workspace client
        w = WorkspaceClient()
        log_message("✓ Connected to Databricks")
        log_message(f"✓ Using SQL Warehouse: {WAREHOUSE_ID}")

        # Create schema
        log_message("\n" + "-" * 80)
        create_regulatory_schema(w)

        # Calculate HQLA
        log_message("\n" + "-" * 80)
        hqla_data = calculate_hqla(w)

        # Calculate cash outflows
        log_message("\n" + "-" * 80)
        total_outflows = calculate_cash_outflows(w)

        # Calculate cash inflows
        log_message("\n" + "-" * 80)
        total_inflows_uncapped = calculate_cash_inflows(w)

        # Calculate LCR
        log_message("\n" + "-" * 80)
        lcr_data = calculate_lcr(w, hqla_data, total_outflows, total_inflows_uncapped)

        # Save LCR record
        log_message("\n" + "-" * 80)
        save_lcr_record(w, hqla_data, total_outflows, lcr_data)

        # Display summary
        display_lcr_summary(hqla_data, total_outflows, lcr_data)

        # Run stress scenarios
        run_stress_scenarios(w)

        log_message("\n" + "=" * 80)
        log_message("✅ WS3-02 Complete: LCR Calculator Successful")
        log_message("=" * 80)
        log_message("\nTables created:")
        log_message("  - cfo_banking_demo.gold_regulatory.hqla_inventory")
        log_message("  - cfo_banking_demo.gold_regulatory.cash_outflows_30day")
        log_message("  - cfo_banking_demo.gold_regulatory.cash_inflows_30day")
        log_message("  - cfo_banking_demo.gold_regulatory.lcr_daily")
        log_message("\nReady for WS4: Agent Framework Integration")

        return 0

    except Exception as e:
        log_message(f"\n\n❌ Error: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
