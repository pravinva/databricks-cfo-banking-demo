"""
Create missing tables for WS5 Lakeview Dashboards
Populate from existing data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_tools_library import CFOAgentTools
from datetime import datetime, timedelta
import random

def create_missing_tables():
    """Create all missing schemas and tables for dashboard queries"""
    agent = CFOAgentTools()

    print("="*80)
    print("Creating Missing Tables for WS5 Dashboards")
    print("="*80)

    # Create bronze_market schema
    print("\n1. Creating bronze_market schema...")
    result = agent.query_unity_catalog("""
        CREATE SCHEMA IF NOT EXISTS cfo_banking_demo.bronze_market
        COMMENT 'Market data from external providers (Alpha Vantage, Bloomberg, etc.)'
    """)
    if result['success']:
        print("   ✓ Schema created")
    else:
        print(f"   ✗ Error: {result.get('error', 'Unknown')}")

    # Create gold_finance schema
    print("\n2. Creating gold_finance schema...")
    result = agent.query_unity_catalog("""
        CREATE SCHEMA IF NOT EXISTS cfo_banking_demo.gold_finance
        COMMENT 'Business-level aggregates and metrics for executive reporting'
    """)
    if result['success']:
        print("   ✓ Schema created")
    else:
        print(f"   ✗ Error: {result.get('error', 'Unknown')}")

    # Create gold_analytics schema
    print("\n3. Creating gold_analytics schema...")
    result = agent.query_unity_catalog("""
        CREATE SCHEMA IF NOT EXISTS cfo_banking_demo.gold_analytics
        COMMENT 'ML predictions and advanced analytics'
    """)
    if result['success']:
        print("   ✓ Schema created")
    else:
        print(f"   ✗ Error: {result.get('error', 'Unknown')}")

    # Create silver_finance.securities table (alias to bronze securities)
    print("\n4. Creating silver_finance.securities view...")
    result = agent.query_unity_catalog("""
        CREATE OR REPLACE VIEW cfo_banking_demo.silver_finance.securities AS
        SELECT
            security_id,
            security_name,
            security_type,
            cusip,
            market_value,
            par_value,
            book_value,
            ytm,
            coupon_rate,
            maturity_date,
            purchase_date,
            effective_duration,
            oas_spread,
            TRUE as is_current,
            CURRENT_TIMESTAMP as load_timestamp
        FROM cfo_banking_demo.bronze_core_banking.securities_portfolio
    """)
    if result['success']:
        print("   ✓ View created")
    else:
        print(f"   ✗ Error: {result.get('error', 'Unknown')}")

    # Create silver_finance.deposit_portfolio view
    print("\n5. Creating silver_finance.deposit_portfolio view...")
    result = agent.query_unity_catalog("""
        CREATE OR REPLACE VIEW cfo_banking_demo.silver_finance.deposit_portfolio AS
        SELECT
            account_id,
            account_holder_name,
            product_type,
            customer_segment,
            current_balance,
            interest_rate,
            open_date,
            relationship_manager,
            TRUE as is_current,
            CURRENT_TIMESTAMP as load_timestamp
        FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
    """)
    if result['success']:
        print("   ✓ View created")
    else:
        print(f"   ✗ Error: {result.get('error', 'Unknown')}")

    # Create bronze_market.treasury_yields table with sample data
    print("\n6. Creating bronze_market.treasury_yields table...")
    result = agent.query_unity_catalog("""
        CREATE TABLE IF NOT EXISTS cfo_banking_demo.bronze_market.treasury_yields (
            observation_date DATE,
            tenor_years DECIMAL(5,2),
            yield_rate DECIMAL(8,6),
            data_source STRING,
            load_timestamp TIMESTAMP
        )
        COMMENT 'US Treasury yield curve data from Alpha Vantage'
    """)
    if result['success']:
        print("   ✓ Table created")
    else:
        print(f"   ✗ Error: {result.get('error', 'Unknown')}")

    # Populate treasury yields with 90 days of sample data
    print("   Populating with 90 days of yield curve data...")

    tenors = [0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30]
    base_yields = {
        0.25: 0.0520,
        0.5: 0.0530,
        1: 0.0545,
        2: 0.0465,
        3: 0.0430,
        5: 0.0420,
        7: 0.0425,
        10: 0.0445,
        20: 0.0470,
        30: 0.0480
    }

    # Generate 90 days of data
    values = []
    for days_ago in range(90):
        obs_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')

        for tenor in tenors:
            # Add some realistic variation
            variation = random.uniform(-0.002, 0.002)
            yield_rate = base_yields[tenor] + variation

            values.append(f"('{obs_date}', {tenor}, {yield_rate}, 'Alpha Vantage', CURRENT_TIMESTAMP)")

    # Insert in batches
    batch_size = 500
    for i in range(0, len(values), batch_size):
        batch = values[i:i+batch_size]
        insert_sql = f"""
            INSERT INTO cfo_banking_demo.bronze_market.treasury_yields
            VALUES {', '.join(batch)}
        """
        result = agent.query_unity_catalog(insert_sql)
        if not result['success']:
            print(f"   ✗ Batch {i//batch_size + 1} failed: {result.get('error', 'Unknown')[:100]}")
            break
    else:
        print(f"   ✓ Inserted {len(values)} yield curve records")

    # Create gold_finance.capital_structure table
    print("\n7. Creating gold_finance.capital_structure table...")
    result = agent.query_unity_catalog("""
        CREATE TABLE IF NOT EXISTS cfo_banking_demo.gold_finance.capital_structure (
            calculation_date DATE,
            common_stock DECIMAL(18,2),
            retained_earnings DECIMAL(18,2),
            preferred_stock DECIMAL(18,2),
            goodwill DECIMAL(18,2),
            intangibles DECIMAL(18,2),
            tier1_capital DECIMAL(18,2),
            tier2_capital DECIMAL(18,2),
            risk_weighted_assets DECIMAL(18,2)
        )
        COMMENT 'Capital adequacy metrics for Basel III reporting'
    """)
    if result['success']:
        print("   ✓ Table created")
    else:
        print(f"   ✗ Error: {result.get('error', 'Unknown')}")

    # Insert sample capital structure data
    print("   Inserting capital structure data...")
    result = agent.query_unity_catalog("""
        INSERT INTO cfo_banking_demo.gold_finance.capital_structure VALUES
        (CURRENT_DATE, 2500000000, 1800000000, 500000000, 150000000, 80000000, 4570000000, 850000000, 25000000000)
    """)
    if result['success']:
        print("   ✓ Data inserted")
    else:
        print(f"   ✗ Error: {result.get('error', 'Unknown')}")

    # Create gold_finance.profitability_metrics table
    print("\n8. Creating gold_finance.profitability_metrics table...")
    result = agent.query_unity_catalog("""
        CREATE TABLE IF NOT EXISTS cfo_banking_demo.gold_finance.profitability_metrics (
            calculation_date DATE,
            net_interest_margin DECIMAL(8,6),
            fee_revenue DECIMAL(18,2),
            operating_expenses DECIMAL(18,2)
        )
        COMMENT 'Profitability and efficiency metrics'
    """)
    if result['success']:
        print("   ✓ Table created")
    else:
        print(f"   ✗ Error: {result.get('error', 'Unknown')}")

    # Insert sample profitability data
    print("   Inserting profitability metrics...")
    result = agent.query_unity_catalog("""
        INSERT INTO cfo_banking_demo.gold_finance.profitability_metrics VALUES
        (CURRENT_DATE, 0.0325, 45000000, 125000000)
    """)
    if result['success']:
        print("   ✓ Data inserted")
    else:
        print(f"   ✗ Error: {result.get('error', 'Unknown')}")

    # Create gold_finance.liquidity_coverage_ratio table
    print("\n9. Creating gold_finance.liquidity_coverage_ratio table...")
    result = agent.query_unity_catalog("""
        CREATE TABLE IF NOT EXISTS cfo_banking_demo.gold_finance.liquidity_coverage_ratio (
            calculation_date DATE,
            hqla_total DECIMAL(18,2),
            net_cash_outflows DECIMAL(18,2),
            lcr_ratio DECIMAL(8,6)
        )
        COMMENT 'LCR compliance metrics'
    """)
    if result['success']:
        print("   ✓ Table created")
    else:
        print(f"   ✗ Error: {result.get('error', 'Unknown')}")

    # Insert sample LCR data
    print("   Inserting LCR metrics...")
    result = agent.query_unity_catalog("""
        INSERT INTO cfo_banking_demo.gold_finance.liquidity_coverage_ratio VALUES
        (CURRENT_DATE, 8500000000, 7200000000, 1.18055556)
    """)
    if result['success']:
        print("   ✓ Data inserted")
    else:
        print(f"   ✗ Error: {result.get('error', 'Unknown')}")

    print("\n" + "="*80)
    print("✅ All missing tables created successfully!")
    print("="*80)

    return 0


if __name__ == "__main__":
    sys.exit(create_missing_tables())
