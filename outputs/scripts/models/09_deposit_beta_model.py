#!/usr/bin/env python3
"""
WS3-01: Deposit Beta Model (Simplified Statistical Approach)
Calculate deposit sensitivity to interest rate changes without full ML pipeline
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import time
from datetime import datetime

def log_message(message, level="INFO"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

# Constants
WAREHOUSE_ID = "4b9b953939869799"

def execute_sql(w, sql_statement, warehouse_id=WAREHOUSE_ID):
    """Execute SQL statement with extended timeout"""
    statement = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql_statement,
        wait_timeout="50s"
    )

    # Wait for completion
    max_wait_time = 600  # 10 minutes for complex queries
    elapsed = 0
    while statement.status.state in [StatementState.PENDING, StatementState.RUNNING] and elapsed < max_wait_time:
        time.sleep(3)
        elapsed += 3
        statement = w.statement_execution.get_statement(statement.statement_id)

    if statement.status.state == StatementState.FAILED:
        error_msg = statement.status.error.message if statement.status.error else "Unknown error"
        raise Exception(f"SQL execution failed: {error_msg}")

    return statement

def create_deposit_behavior_history(w):
    """Create synthetic deposit behavior history for beta modeling"""

    log_message("Creating deposit behavior history table...")

    # Note: In production, this would come from actual historical data
    # Here we'll create synthetic data based on the deposit portfolio

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS cfo_banking_demo.bronze_core_banking.deposit_behavior_history (
        account_id STRING,
        period_date DATE,
        beginning_balance DECIMAL(18,2),
        ending_balance DECIMAL(18,2),
        balance_change DECIMAL(18,2),
        balance_change_pct DECIMAL(8,4),
        fed_funds_rate DECIMAL(8,4),
        rate_change DECIMAL(8,4),
        product_type STRING,
        customer_segment STRING,
        has_online_banking BOOLEAN
    )
    """

    execute_sql(w, create_table_sql)
    log_message("  ✓ Created deposit_behavior_history table")

def generate_behavior_history(w):
    """Generate 12 months of synthetic behavior history"""

    log_message("Generating 12 months of deposit behavior history...")
    log_message("  (Simulating rate changes and balance responses)")

    # Insert synthetic behavior data
    # Simplified: Use current balances and simulate historical behavior
    insert_sql = """
    INSERT INTO cfo_banking_demo.bronze_core_banking.deposit_behavior_history
    SELECT
        account_id,
        ADD_MONTHS(CURRENT_DATE(), -seq.month_offset) as period_date,
        current_balance * (1 + (RAND() * 0.1 - 0.05)) as beginning_balance,
        current_balance * (1 + (RAND() * 0.1 - 0.05)) as ending_balance,
        current_balance * (RAND() * 0.1 - 0.05) as balance_change,
        (RAND() * 10 - 5) as balance_change_pct,
        CASE
            WHEN seq.month_offset >= 10 THEN 2.5 + (RAND() * 0.5)
            WHEN seq.month_offset >= 6 THEN 3.5 + (RAND() * 0.5)
            ELSE 4.5 + (RAND() * 0.5)
        END as fed_funds_rate,
        CASE
            WHEN seq.month_offset = 11 THEN 0.0
            WHEN seq.month_offset >= 10 THEN 0.25
            WHEN seq.month_offset >= 6 THEN 0.5
            ELSE 0.25
        END as rate_change,
        product_type,
        customer_segment,
        has_online_banking
    FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
    CROSS JOIN (
        SELECT 0 as month_offset UNION ALL
        SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL
        SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL
        SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9 UNION ALL
        SELECT 10 UNION ALL SELECT 11
    ) seq
    WHERE product_type IN ('DDA', 'NOW', 'Savings', 'MMDA')
    LIMIT 100000
    """

    execute_sql(w, insert_sql)

    # Get count
    result = execute_sql(w, """
        SELECT COUNT(*) FROM cfo_banking_demo.bronze_core_banking.deposit_behavior_history
    """)
    count = int(result.result.data_array[0][0]) if result.result and result.result.data_array else 0

    log_message(f"  ✓ Generated {count:,} behavior records")

def create_beta_features(w):
    """Create feature table for beta analysis"""

    log_message("Creating beta analysis features...")

    create_features_sql = """
    CREATE OR REPLACE TABLE cfo_banking_demo.gold_analytics.deposit_beta_features AS
    SELECT
        h.account_id,
        h.product_type,
        h.customer_segment,
        h.has_online_banking,
        h.period_date,
        h.beginning_balance,
        h.balance_change_pct,
        h.fed_funds_rate,
        h.rate_change,
        h.rate_change * 10000 as rate_change_bps,
        CASE WHEN h.rate_change > 0 THEN 1 ELSE 0 END as rate_increasing,
        a.beta as assigned_beta
    FROM cfo_banking_demo.bronze_core_banking.deposit_behavior_history h
    LEFT JOIN cfo_banking_demo.bronze_core_banking.deposit_accounts a
        ON h.account_id = a.account_id
    WHERE h.balance_change_pct IS NOT NULL
        AND h.rate_change IS NOT NULL
    """

    execute_sql(w, create_features_sql)

    # Get count
    result = execute_sql(w, """
        SELECT COUNT(*) FROM cfo_banking_demo.gold_analytics.deposit_beta_features
    """)
    count = int(result.result.data_array[0][0]) if result.result and result.result.data_array else 0

    log_message(f"  ✓ Created {count:,} feature records")

def calculate_beta_statistics(w):
    """Calculate statistical beta by product type"""

    log_message("Calculating deposit beta statistics by product type...")

    create_beta_stats_sql = """
    CREATE OR REPLACE TABLE cfo_banking_demo.gold_analytics.deposit_beta_statistics AS
    SELECT
        product_type,
        COUNT(*) as observation_count,
        AVG(balance_change_pct) as avg_balance_change_pct,
        STDDEV(balance_change_pct) as stddev_balance_change,
        AVG(CASE WHEN rate_increasing = 1 THEN balance_change_pct END) as avg_change_rates_up,
        AVG(CASE WHEN rate_increasing = 0 THEN balance_change_pct END) as avg_change_rates_down,
        -- Beta = sensitivity of balance change to rate change
        CORR(rate_change_bps, balance_change_pct) as correlation,
        -- Simple linear regression beta coefficient
        COVAR_POP(rate_change_bps, balance_change_pct) /
            NULLIF(VAR_POP(rate_change_bps), 0) as statistical_beta,
        AVG(assigned_beta) as avg_assigned_beta
    FROM cfo_banking_demo.gold_analytics.deposit_beta_features
    GROUP BY product_type
    ORDER BY product_type
    """

    execute_sql(w, create_beta_stats_sql)
    log_message("  ✓ Calculated beta statistics")

def calculate_segment_beta(w):
    """Calculate beta by customer segment"""

    log_message("Calculating beta by customer segment...")

    create_segment_beta_sql = """
    CREATE OR REPLACE TABLE cfo_banking_demo.gold_analytics.deposit_beta_by_segment AS
    SELECT
        customer_segment,
        product_type,
        COUNT(*) as observation_count,
        AVG(balance_change_pct) as avg_balance_change_pct,
        CORR(rate_change_bps, balance_change_pct) as correlation,
        COVAR_POP(rate_change_bps, balance_change_pct) /
            NULLIF(VAR_POP(rate_change_bps), 0) as statistical_beta,
        AVG(assigned_beta) as avg_assigned_beta
    FROM cfo_banking_demo.gold_analytics.deposit_beta_features
    GROUP BY customer_segment, product_type
    ORDER BY customer_segment, product_type
    """

    execute_sql(w, create_segment_beta_sql)
    log_message("  ✓ Calculated segment beta")

def create_beta_prediction_table(w):
    """Create table with predicted deposit runoff for rate scenarios"""

    log_message("Creating beta prediction scenarios...")

    create_predictions_sql = """
    CREATE OR REPLACE TABLE cfo_banking_demo.gold_analytics.deposit_runoff_predictions AS
    SELECT
        a.product_type,
        SUM(a.current_balance) as total_balance,
        AVG(a.beta) as avg_beta,
        -- Scenario 1: +25 bps rate increase
        SUM(a.current_balance * a.beta * 0.0025) as runoff_25bps,
        -- Scenario 2: +50 bps rate increase
        SUM(a.current_balance * a.beta * 0.0050) as runoff_50bps,
        -- Scenario 3: +100 bps rate increase
        SUM(a.current_balance * a.beta * 0.0100) as runoff_100bps,
        -- Scenario 4: +200 bps rate increase (stress test)
        SUM(a.current_balance * a.beta * 0.0200) as runoff_200bps,
        COUNT(*) as account_count
    FROM cfo_banking_demo.bronze_core_banking.deposit_accounts a
    WHERE a.product_type IN ('DDA', 'NOW', 'Savings', 'MMDA')
        AND a.account_status = 'Active'
    GROUP BY a.product_type
    ORDER BY total_balance DESC
    """

    execute_sql(w, create_predictions_sql)
    log_message("  ✓ Created runoff prediction scenarios")

def display_beta_statistics(w):
    """Display beta statistics"""

    log_message("\n" + "=" * 80)
    log_message("DEPOSIT BETA STATISTICS BY PRODUCT TYPE")
    log_message("=" * 80)

    result = execute_sql(w, """
        SELECT
            product_type,
            observation_count,
            avg_balance_change_pct,
            correlation,
            statistical_beta,
            avg_assigned_beta
        FROM cfo_banking_demo.gold_analytics.deposit_beta_statistics
        ORDER BY product_type
    """)

    if result.result and result.result.data_array:
        for row in result.result.data_array:
            product = row[0]
            obs_count = int(row[1])
            avg_change = float(row[2]) if row[2] else 0
            corr = float(row[3]) if row[3] else 0
            stat_beta = float(row[4]) if row[4] else 0
            assigned_beta = float(row[5]) if row[5] else 0

            log_message(f"\n{product}:")
            log_message(f"  Observations: {obs_count:,}")
            log_message(f"  Avg Balance Change: {avg_change:.2f}%")
            log_message(f"  Correlation: {corr:.4f}")
            log_message(f"  Statistical Beta: {stat_beta:.4f}")
            log_message(f"  Assigned Beta: {assigned_beta:.4f}")

def display_runoff_predictions(w):
    """Display runoff predictions for rate scenarios"""

    log_message("\n" + "=" * 80)
    log_message("DEPOSIT RUNOFF PREDICTIONS (RATE SHOCK SCENARIOS)")
    log_message("=" * 80)

    result = execute_sql(w, """
        SELECT
            product_type,
            total_balance,
            avg_beta,
            runoff_25bps,
            runoff_50bps,
            runoff_100bps,
            runoff_200bps,
            account_count
        FROM cfo_banking_demo.gold_analytics.deposit_runoff_predictions
        ORDER BY total_balance DESC
    """)

    if result.result and result.result.data_array:
        for row in result.result.data_array:
            product = row[0]
            total_bal = float(row[1])
            avg_beta = float(row[2])
            runoff_25 = float(row[3])
            runoff_50 = float(row[4])
            runoff_100 = float(row[5])
            runoff_200 = float(row[6])
            acct_count = int(row[7])

            log_message(f"\n{product}:")
            log_message(f"  Total Balance: ${total_bal:,.0f}")
            log_message(f"  Average Beta: {avg_beta:.4f}")
            log_message(f"  Account Count: {acct_count:,}")
            log_message(f"  Runoff Scenarios:")
            log_message(f"    +25 bps: ${runoff_25:,.0f} ({runoff_25/total_bal*100:.2f}%)")
            log_message(f"    +50 bps: ${runoff_50:,.0f} ({runoff_50/total_bal*100:.2f}%)")
            log_message(f"    +100 bps: ${runoff_100:,.0f} ({runoff_100/total_bal*100:.2f}%)")
            log_message(f"    +200 bps: ${runoff_200:,.0f} ({runoff_200/total_bal*100:.2f}%) [stress]")

    # Total runoff
    result = execute_sql(w, """
        SELECT
            SUM(total_balance) as total_deposits,
            SUM(runoff_25bps) as total_runoff_25,
            SUM(runoff_50bps) as total_runoff_50,
            SUM(runoff_100bps) as total_runoff_100,
            SUM(runoff_200bps) as total_runoff_200
        FROM cfo_banking_demo.gold_analytics.deposit_runoff_predictions
    """)

    if result.result and result.result.data_array:
        row = result.result.data_array[0]
        total_deposits = float(row[0])
        total_runoff_25 = float(row[1])
        total_runoff_50 = float(row[2])
        total_runoff_100 = float(row[3])
        total_runoff_200 = float(row[4])

        log_message(f"\nTOTAL PORTFOLIO:")
        log_message(f"  Total Deposits: ${total_deposits:,.0f}")
        log_message(f"  +25 bps runoff: ${total_runoff_25:,.0f} ({total_runoff_25/total_deposits*100:.2f}%)")
        log_message(f"  +50 bps runoff: ${total_runoff_50:,.0f} ({total_runoff_50/total_deposits*100:.2f}%)")
        log_message(f"  +100 bps runoff: ${total_runoff_100:,.0f} ({total_runoff_100/total_deposits*100:.2f}%)")
        log_message(f"  +200 bps runoff: ${total_runoff_200:,.0f} ({total_runoff_200/total_deposits*100:.2f}%)")

def main():
    """Main execution function"""
    try:
        log_message("=" * 80)
        log_message("WS3-01: Deposit Beta Model (Statistical Approach)")
        log_message("=" * 80)

        # Initialize Databricks workspace client
        w = WorkspaceClient()
        log_message("✓ Connected to Databricks")
        log_message(f"✓ Using SQL Warehouse: {WAREHOUSE_ID}")

        # Create behavior history
        log_message("\n" + "-" * 80)
        create_deposit_behavior_history(w)
        generate_behavior_history(w)

        # Create features
        log_message("\n" + "-" * 80)
        create_beta_features(w)

        # Calculate beta statistics
        log_message("\n" + "-" * 80)
        calculate_beta_statistics(w)
        calculate_segment_beta(w)

        # Create predictions
        log_message("\n" + "-" * 80)
        create_beta_prediction_table(w)

        # Display results
        display_beta_statistics(w)
        display_runoff_predictions(w)

        log_message("\n" + "=" * 80)
        log_message("✅ WS3-01 Complete: Deposit Beta Model Generated")
        log_message("=" * 80)
        log_message("\nTables created:")
        log_message("  - cfo_banking_demo.bronze_core_banking.deposit_behavior_history")
        log_message("  - cfo_banking_demo.gold_analytics.deposit_beta_features")
        log_message("  - cfo_banking_demo.gold_analytics.deposit_beta_statistics")
        log_message("  - cfo_banking_demo.gold_analytics.deposit_beta_by_segment")
        log_message("  - cfo_banking_demo.gold_analytics.deposit_runoff_predictions")
        log_message("\nReady for WS3-02: LCR Calculations")

        return 0

    except Exception as e:
        log_message(f"\n\n❌ Error: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
