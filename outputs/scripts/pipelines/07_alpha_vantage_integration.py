#!/usr/bin/env python3
"""
WS2-01: Alpha Vantage Market Data Integration
Fetch Treasury yields and FX rates from Alpha Vantage API
Store in Unity Catalog bronze → silver → gold layers
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import requests
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

def fetch_treasury_yields(api_key):
    """Fetch US Treasury yield curve from Alpha Vantage"""

    maturities = ['3month', '2year', '5year', '10year', '30year']
    all_data = []

    log_message("Fetching Treasury yields from Alpha Vantage...")

    for maturity in maturities:
        url = f"https://www.alphavantage.co/query?function=TREASURY_YIELD&interval=daily&maturity={maturity}&apikey={api_key}"

        try:
            response = requests.get(url, timeout=30)
            data = response.json()

            if 'data' in data:
                records = data['data'][:30]  # Last 30 days
                for record in records:
                    # Skip records with "." (empty values)
                    if record['value'] != '.':
                        try:
                            all_data.append({
                                'date': record['date'],
                                'maturity': maturity,
                                'value': float(record['value'])
                            })
                        except ValueError:
                            # Skip invalid numeric values
                            continue
                log_message(f"  ✓ Fetched {maturity}: {len([r for r in records if r['value'] != '.'])} records")
            elif 'Note' in data:
                log_message(f"  ⚠️  API limit warning for {maturity}: {data['Note']}", "WARNING")
            else:
                log_message(f"  ⚠️  Unexpected response for {maturity}: {data}", "WARNING")

            # Rate limit: Free tier allows 25 calls/day, 5 calls/minute
            time.sleep(12)  # 12 seconds between calls = max 5/minute

        except Exception as e:
            log_message(f"  ❌ Error fetching {maturity}: {e}", "ERROR")

    return all_data

def fetch_fx_rates(api_key):
    """Fetch FX rates from Alpha Vantage"""

    pairs = [
        ('EUR', 'USD'),
        ('GBP', 'USD'),
        ('JPY', 'USD'),
        ('AUD', 'USD'),
        ('CAD', 'USD')
    ]

    fx_data = []

    log_message("Fetching FX rates from Alpha Vantage...")

    for from_curr, to_curr in pairs:
        url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={from_curr}&to_currency={to_curr}&apikey={api_key}"

        try:
            response = requests.get(url, timeout=30)
            data = response.json()

            if 'Realtime Currency Exchange Rate' in data:
                rate_data = data['Realtime Currency Exchange Rate']
                fx_data.append({
                    'date': str(CURRENT_DATE),
                    'from_currency': from_curr,
                    'to_currency': to_curr,
                    'exchange_rate': float(rate_data['5. Exchange Rate']),
                    'last_refreshed': rate_data['6. Last Refreshed'],
                    'bid_price': float(rate_data['8. Bid Price']),
                    'ask_price': float(rate_data['9. Ask Price'])
                })
                log_message(f"  ✓ Fetched {from_curr}/{to_curr}: {rate_data['5. Exchange Rate']}")
            elif 'Note' in data:
                log_message(f"  ⚠️  API limit for {from_curr}/{to_curr}: {data['Note']}", "WARNING")
            else:
                log_message(f"  ⚠️  Unexpected response for {from_curr}/{to_curr}", "WARNING")

            # Rate limit
            time.sleep(12)

        except Exception as e:
            log_message(f"  ❌ Error fetching {from_curr}/{to_curr}: {e}", "ERROR")

    return fx_data

def create_bronze_tables(w):
    """Create bronze layer tables"""

    log_message("Creating bronze market data schema...")
    execute_sql(w, "CREATE SCHEMA IF NOT EXISTS cfo_banking_demo.bronze_market_data")

    # Treasury yields bronze table
    create_treasury_bronze = """
    CREATE TABLE IF NOT EXISTS cfo_banking_demo.bronze_market_data.treasury_yields_raw (
        date DATE,
        maturity STRING,
        value DOUBLE,
        ingestion_timestamp TIMESTAMP
    )
    """
    execute_sql(w, create_treasury_bronze)
    log_message("  ✓ Created treasury_yields_raw table")

    # FX rates bronze table
    create_fx_bronze = """
    CREATE TABLE IF NOT EXISTS cfo_banking_demo.bronze_market_data.fx_rates_raw (
        date DATE,
        from_currency STRING,
        to_currency STRING,
        exchange_rate DOUBLE,
        last_refreshed STRING,
        bid_price DOUBLE,
        ask_price DOUBLE,
        ingestion_timestamp TIMESTAMP
    )
    """
    execute_sql(w, create_fx_bronze)
    log_message("  ✓ Created fx_rates_raw table")

def insert_treasury_data(w, treasury_data):
    """Insert treasury yield data into bronze table"""

    if not treasury_data:
        log_message("No treasury data to insert", "WARNING")
        return

    log_message(f"Inserting {len(treasury_data)} treasury yield records...")

    # Batch insert
    batch_size = 100
    for i in range(0, len(treasury_data), batch_size):
        batch = treasury_data[i:i+batch_size]

        values_list = []
        for record in batch:
            values = f"('{record['date']}', '{record['maturity']}', {record['value']}, CURRENT_TIMESTAMP())"
            values_list.append(values)

        insert_sql = f"""
        INSERT INTO cfo_banking_demo.bronze_market_data.treasury_yields_raw
        VALUES {', '.join(values_list)}
        """

        execute_sql(w, insert_sql)

    log_message(f"  ✓ Inserted {len(treasury_data)} treasury yield records")

def insert_fx_data(w, fx_data):
    """Insert FX rate data into bronze table"""

    if not fx_data:
        log_message("No FX data to insert", "WARNING")
        return

    log_message(f"Inserting {len(fx_data)} FX rate records...")

    values_list = []
    for record in fx_data:
        values = f"""(
            '{record['date']}', '{record['from_currency']}', '{record['to_currency']}',
            {record['exchange_rate']}, '{record['last_refreshed']}',
            {record['bid_price']}, {record['ask_price']}, CURRENT_TIMESTAMP()
        )"""
        values_list.append(values)

    insert_sql = f"""
    INSERT INTO cfo_banking_demo.bronze_market_data.fx_rates_raw
    VALUES {', '.join(values_list)}
    """

    execute_sql(w, insert_sql)
    log_message(f"  ✓ Inserted {len(fx_data)} FX rate records")

def create_silver_tables(w):
    """Create and populate silver layer tables"""

    log_message("Creating silver layer tables...")

    # Pivot yield curve to wide format
    create_yield_curves = """
    CREATE OR REPLACE TABLE cfo_banking_demo.silver_treasury.yield_curves AS
    SELECT
        date,
        MAX(CASE WHEN maturity = '3month' THEN value END) as rate_3m,
        MAX(CASE WHEN maturity = '2year' THEN value END) as rate_2y,
        MAX(CASE WHEN maturity = '5year' THEN value END) as rate_5y,
        MAX(CASE WHEN maturity = '10year' THEN value END) as rate_10y,
        MAX(CASE WHEN maturity = '30year' THEN value END) as rate_30y,
        CURRENT_TIMESTAMP() as ingestion_timestamp
    FROM cfo_banking_demo.bronze_market_data.treasury_yields_raw
    GROUP BY date
    ORDER BY date DESC
    """
    execute_sql(w, create_yield_curves)
    log_message("  ✓ Created yield_curves table (pivoted)")

    # FX rates silver with currency pair
    create_fx_silver = """
    CREATE OR REPLACE TABLE cfo_banking_demo.silver_treasury.fx_rates AS
    SELECT
        date,
        CONCAT(from_currency, '/', to_currency) as currency_pair,
        from_currency,
        to_currency,
        exchange_rate,
        bid_price,
        ask_price,
        (ask_price - bid_price) as spread,
        last_refreshed,
        ingestion_timestamp
    FROM cfo_banking_demo.bronze_market_data.fx_rates_raw
    ORDER BY date DESC, currency_pair
    """
    execute_sql(w, create_fx_silver)
    log_message("  ✓ Created fx_rates table (formatted)")

def create_gold_tables(w):
    """Create gold layer for latest market data"""

    log_message("Creating gold analytics schema...")
    execute_sql(w, "CREATE SCHEMA IF NOT EXISTS cfo_banking_demo.gold_analytics")

    # Latest yield curve
    create_market_data_latest = """
    CREATE OR REPLACE TABLE cfo_banking_demo.gold_analytics.market_data_latest AS
    SELECT
        'treasury_yield' as data_type,
        date,
        rate_3m,
        rate_2y,
        rate_5y,
        rate_10y,
        rate_30y,
        ingestion_timestamp
    FROM cfo_banking_demo.silver_treasury.yield_curves
    WHERE date = (SELECT MAX(date) FROM cfo_banking_demo.silver_treasury.yield_curves)
    """
    execute_sql(w, create_market_data_latest)
    log_message("  ✓ Created market_data_latest table")

def display_latest_data(w):
    """Display latest market data"""

    log_message("\n" + "=" * 80)
    log_message("LATEST MARKET DATA")
    log_message("=" * 80)

    # Latest yield curve
    result = execute_sql(w, """
        SELECT date, rate_3m, rate_2y, rate_5y, rate_10y, rate_30y
        FROM cfo_banking_demo.gold_analytics.market_data_latest
    """)

    if result.result and result.result.data_array:
        row = result.result.data_array[0]
        log_message(f"\nTreasury Yields (as of {row[0]}):")
        log_message("-" * 80)
        # Convert string values to float for formatting
        r3m = float(row[1]) if row[1] is not None else None
        r2y = float(row[2]) if row[2] is not None else None
        r5y = float(row[3]) if row[3] is not None else None
        r10y = float(row[4]) if row[4] is not None else None
        r30y = float(row[5]) if row[5] is not None else None

        log_message(f"  3-Month:  {r3m:.2f}%" if r3m else "  3-Month:  N/A")
        log_message(f"  2-Year:   {r2y:.2f}%" if r2y else "  2-Year:   N/A")
        log_message(f"  5-Year:   {r5y:.2f}%" if r5y else "  5-Year:   N/A")
        log_message(f"  10-Year:  {r10y:.2f}%" if r10y else "  10-Year:  N/A")
        log_message(f"  30-Year:  {r30y:.2f}%" if r30y else "  30-Year:  N/A")

    # Latest FX rates
    result = execute_sql(w, """
        SELECT currency_pair, exchange_rate, spread, last_refreshed
        FROM cfo_banking_demo.silver_treasury.fx_rates
        WHERE date = CURRENT_DATE()
        ORDER BY currency_pair
    """)

    log_message(f"\nFX Rates (as of {CURRENT_DATE}):")
    log_message("-" * 80)
    if result.result and result.result.data_array:
        for row in result.result.data_array:
            rate = float(row[1]) if row[1] is not None else None
            spread = float(row[2]) if row[2] is not None else None
            if rate and spread:
                log_message(f"  {row[0]}: {rate:.4f} (spread: {spread:.4f}) - {row[3]}")
            else:
                log_message(f"  {row[0]}: N/A")

def validate_data(w):
    """Validate data quality"""

    log_message("\n" + "=" * 80)
    log_message("DATA QUALITY VALIDATION")
    log_message("=" * 80)

    # Count treasury records
    result = execute_sql(w, """
        SELECT COUNT(*) FROM cfo_banking_demo.bronze_market_data.treasury_yields_raw
    """)
    treasury_count = int(result.result.data_array[0][0]) if result.result and result.result.data_array else 0

    # Count unique dates
    result = execute_sql(w, """
        SELECT COUNT(DISTINCT date) FROM cfo_banking_demo.bronze_market_data.treasury_yields_raw
    """)
    treasury_dates = int(result.result.data_array[0][0]) if result.result and result.result.data_array else 0

    # Count FX records
    result = execute_sql(w, """
        SELECT COUNT(*) FROM cfo_banking_demo.bronze_market_data.fx_rates_raw
    """)
    fx_count = int(result.result.data_array[0][0]) if result.result and result.result.data_array else 0

    log_message(f"Treasury yield records: {treasury_count} ({treasury_dates} unique dates)")

    if treasury_dates >= 20:
        log_message("  ✓ Sufficient treasury data (20+ days)")
    else:
        log_message(f"  ⚠️  Limited treasury data ({treasury_dates} days)", "WARNING")

    log_message(f"FX rate records: {fx_count}")

    if fx_count >= 5:
        log_message("  ✓ All 5 FX pairs fetched")
    else:
        log_message(f"  ⚠️  Missing FX pairs ({fx_count}/5)", "WARNING")

def main():
    """Main execution function"""
    try:
        log_message("=" * 80)
        log_message("WS2-01: Alpha Vantage Market Data Integration")
        log_message("=" * 80)

        # Initialize Databricks workspace client
        w = WorkspaceClient()
        log_message("✓ Connected to Databricks")
        log_message(f"✓ Using SQL Warehouse: {WAREHOUSE_ID}")

        # Get API key from secrets
        log_message("\nRetrieving Alpha Vantage API key from Databricks secrets...")
        try:
            api_key = w.secrets.get_secret(scope="cfo_demo", key="alpha_vantage_api_key").value
            log_message("✓ API key retrieved successfully")
        except Exception as e:
            log_message(f"\n❌ Failed to retrieve API key: {e}", "ERROR")
            log_message("\nPlease set the API key using:", "ERROR")
            log_message("  databricks secrets put-secret cfo_demo alpha_vantage_api_key", "ERROR")
            return 1

        # Fetch data from Alpha Vantage
        log_message("\n" + "-" * 80)
        treasury_data = fetch_treasury_yields(api_key)

        log_message("")
        fx_data = fetch_fx_rates(api_key)

        if not treasury_data and not fx_data:
            log_message("\n❌ No data fetched from Alpha Vantage", "ERROR")
            log_message("This may be due to API rate limits. Try again in a few minutes.", "WARNING")
            return 1

        # Create and populate bronze layer
        log_message("\n" + "-" * 80)
        create_bronze_tables(w)

        if treasury_data:
            insert_treasury_data(w, treasury_data)

        if fx_data:
            insert_fx_data(w, fx_data)

        # Create silver layer
        log_message("\n" + "-" * 80)
        create_silver_tables(w)

        # Create gold layer
        log_message("\n" + "-" * 80)
        create_gold_tables(w)

        # Display latest data
        display_latest_data(w)

        # Validate
        validate_data(w)

        log_message("\n" + "=" * 80)
        log_message("✅ WS2-01 Complete: Market Data Integration Successful")
        log_message("=" * 80)
        log_message("\nTables created:")
        log_message("  - cfo_banking_demo.bronze_market_data.treasury_yields_raw")
        log_message("  - cfo_banking_demo.bronze_market_data.fx_rates_raw")
        log_message("  - cfo_banking_demo.silver_treasury.yield_curves")
        log_message("  - cfo_banking_demo.silver_treasury.fx_rates")
        log_message("  - cfo_banking_demo.gold_analytics.market_data_latest")
        log_message("\nReady for WS2-02: Loan Origination Pipeline")

        return 0

    except Exception as e:
        log_message(f"\n\n❌ Error: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
