#!/usr/bin/env python3
"""
WS1-02: Securities Portfolio Generator (SQL Warehouse version)
Generates realistic securities portfolio data for US regional bank Treasury department

Uses Databricks SQL Warehouse for execution
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import random
from datetime import datetime, timedelta
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

# Yield curve
YIELD_CURVE = {
    0.25: 4.8, 1.0: 4.5, 2.0: 4.2, 5.0: 4.0, 10.0: 4.1, 30.0: 4.3
}

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

def generate_cusip(security_type, index):
    """Generate realistic CUSIP"""
    prefix_map = {
        'UST': '912828',
        'Corporate': random.choice(['037833', '459200', '594918', '747525']),
        'Municipal': random.choice(['646137', '880628', '922908']),
        'Agency': random.choice(['313396', '3134G3', '3130A0']),
        'MBS': random.choice(['31359M', '31371X'])
    }
    prefix = prefix_map.get(security_type, '000000')
    suffix = f"{index:04d}"[:4]
    check_digit = random.randint(0, 9)
    return f"{prefix}{suffix}{check_digit}"

def interpolate_yield(years_to_maturity):
    """Interpolate yield from yield curve"""
    if years_to_maturity <= 0.25:
        return YIELD_CURVE[0.25]
    elif years_to_maturity >= 30:
        return YIELD_CURVE[30.0]
    points = sorted(YIELD_CURVE.keys())
    for i in range(len(points) - 1):
        if points[i] <= years_to_maturity <= points[i+1]:
            y1, y2 = YIELD_CURVE[points[i]], YIELD_CURVE[points[i+1]]
            x1, x2 = points[i], points[i+1]
            return y1 + (y2 - y1) * (years_to_maturity - x1) / (x2 - x1)
    return YIELD_CURVE[10.0]

def calculate_market_value(par_value, coupon_rate, ytm, years_to_maturity):
    """Calculate bond market value"""
    if years_to_maturity == 0:
        return par_value
    if ytm > coupon_rate:
        discount_factor = (ytm - coupon_rate) * years_to_maturity * 0.07
        return par_value * (1 - min(discount_factor, 0.25))
    else:
        premium_factor = (coupon_rate - ytm) * years_to_maturity * 0.07
        return par_value * (1 + min(premium_factor, 0.15))

def calculate_duration(years_to_maturity, coupon_rate):
    """Calculate duration"""
    if coupon_rate == 0:
        return years_to_maturity
    return years_to_maturity * 0.85

def generate_securities_data():
    """Generate all securities and return as list of dicts"""
    securities = []

    log_message("Generating US Treasuries (500)...")
    # Bills (50)
    for i in range(50):
        days = random.randint(30, 365)
        years = days / 365.0
        par = random.choice([5_000_000, 10_000_000, 25_000_000])
        ytm = interpolate_yield(years)
        mkt = par * (1 - ytm/100 * years)
        securities.append({
            'security_id': f'UST-BILL-{i:04d}',
            'cusip': generate_cusip('UST', i),
            'security_type': 'UST',
            'security_subtype': 'Bill',
            'issuer_name': 'US Treasury',
            'issue_date': (CURRENT_DATE - timedelta(days=random.randint(1, 180))).isoformat(),
            'maturity_date': (CURRENT_DATE + timedelta(days=days)).isoformat(),
            'par_value': par,
            'coupon_rate': 0.0,
            'yield_to_maturity': ytm,
            'market_value': mkt,
            'duration': years,
            'credit_rating': 'AAA',
            'security_classification': random.choice(['HTM', 'AFS']),
            'currency': 'USD'
        })

    # Notes (300)
    for i in range(300):
        years = random.uniform(1.0, 10.0)
        par = random.choice([5_000_000, 10_000_000, 25_000_000])
        ytm = interpolate_yield(years)
        coupon = ytm + random.uniform(-0.5, 0.5)
        mkt = calculate_market_value(par, coupon, ytm, years)
        dur = calculate_duration(years, coupon)
        securities.append({
            'security_id': f'UST-NOTE-{i:04d}',
            'cusip': generate_cusip('UST', i+50),
            'security_type': 'UST',
            'security_subtype': 'Note',
            'issuer_name': 'US Treasury',
            'issue_date': (CURRENT_DATE - timedelta(days=random.randint(30, 365))).isoformat(),
            'maturity_date': (CURRENT_DATE + timedelta(days=int(years*365))).isoformat(),
            'par_value': par,
            'coupon_rate': coupon,
            'yield_to_maturity': ytm,
            'market_value': mkt,
            'duration': dur,
            'credit_rating': 'AAA',
            'security_classification': random.choice(['HTM', 'HTM', 'AFS']),
            'currency': 'USD'
        })

    # Bonds (150)
    for i in range(150):
        years = random.uniform(10.0, 30.0)
        par = random.choice([10_000_000, 25_000_000, 50_000_000])
        ytm = interpolate_yield(years)
        coupon = ytm + random.uniform(-0.3, 0.3)
        mkt = calculate_market_value(par, coupon, ytm, years)
        dur = calculate_duration(years, coupon)
        securities.append({
            'security_id': f'UST-BOND-{i:04d}',
            'cusip': generate_cusip('UST', i+350),
            'security_type': 'UST',
            'security_subtype': 'Bond',
            'issuer_name': 'US Treasury',
            'issue_date': (CURRENT_DATE - timedelta(days=random.randint(180, 1825))).isoformat(),
            'maturity_date': (CURRENT_DATE + timedelta(days=int(years*365))).isoformat(),
            'par_value': par,
            'coupon_rate': coupon,
            'yield_to_maturity': ytm,
            'market_value': mkt,
            'duration': dur,
            'credit_rating': 'AAA',
            'security_classification': random.choice(['HTM', 'AFS']),
            'currency': 'USD'
        })

    log_message("Generating Corporate bonds (200)...")
    issuers = [
        ('Apple Inc', 'AA+'), ('Microsoft Corp', 'AAA'), ('JPMorgan Chase', 'A+'),
        ('Bank of America', 'A'), ('Wells Fargo', 'A-'), ('Goldman Sachs', 'BBB+')
    ]
    for i in range(200):
        issuer, _ = random.choice(issuers)
        rating = random.choice(['AAA', 'AA+', 'AA', 'A+', 'A', 'BBB+', 'BBB']) if i < 180 else random.choice(['BB+', 'BB', 'B+'])
        years = random.uniform(2.0, 15.0)
        par = random.choice([1_000_000, 5_000_000, 10_000_000])
        spread = {'AAA': 0.5, 'AA+': 0.6, 'A+': 1.0, 'A': 1.1, 'BBB+': 1.6, 'BBB': 1.9, 'BB+': 3.5, 'BB': 4.0, 'B+': 5.5}.get(rating, 1.5)
        ytm = interpolate_yield(years) + spread
        coupon = ytm + random.uniform(-0.5, 0.5)
        mkt = calculate_market_value(par, coupon, ytm, years)
        dur = calculate_duration(years, coupon)
        securities.append({
            'security_id': f'CORP-{i:04d}',
            'cusip': generate_cusip('Corporate', i),
            'security_type': 'Corporate',
            'security_subtype': 'Senior Unsecured',
            'issuer_name': issuer,
            'issue_date': (CURRENT_DATE - timedelta(days=random.randint(90, 730))).isoformat(),
            'maturity_date': (CURRENT_DATE + timedelta(days=int(years*365))).isoformat(),
            'par_value': par,
            'coupon_rate': coupon,
            'yield_to_maturity': ytm,
            'market_value': mkt,
            'duration': dur,
            'credit_rating': rating,
            'security_classification': random.choice(['HTM', 'AFS', 'Trading']),
            'currency': 'USD'
        })

    log_message("Generating Municipal bonds (150)...")
    muni_issuers = ['State of California', 'State of New York', 'City of Los Angeles', 'City of Chicago']
    for i in range(150):
        issuer = random.choice(muni_issuers)
        rating = random.choice(['AAA', 'AA+', 'AA', 'A+', 'A', 'BBB+'])
        years = random.uniform(3.0, 20.0)
        par = random.choice([1_000_000, 5_000_000, 10_000_000])
        ytm = interpolate_yield(years) * 0.70 + random.uniform(-0.2, 0.3)
        coupon = ytm + random.uniform(-0.3, 0.3)
        mkt = calculate_market_value(par, coupon, ytm, years)
        dur = calculate_duration(years, coupon)
        securities.append({
            'security_id': f'MUNI-{i:04d}',
            'cusip': generate_cusip('Municipal', i),
            'security_type': 'Municipal',
            'security_subtype': 'General Obligation',
            'issuer_name': issuer,
            'issue_date': (CURRENT_DATE - timedelta(days=random.randint(180, 1095))).isoformat(),
            'maturity_date': (CURRENT_DATE + timedelta(days=int(years*365))).isoformat(),
            'par_value': par,
            'coupon_rate': coupon,
            'yield_to_maturity': ytm,
            'market_value': mkt,
            'duration': dur,
            'credit_rating': rating,
            'security_classification': random.choice(['HTM', 'AFS']),
            'currency': 'USD'
        })

    log_message("Generating Agency securities (100)...")
    agencies = [('Fannie Mae', 'AA+'), ('Freddie Mac', 'AA+'), ('Federal Home Loan Bank', 'AA+')]
    for i in range(100):
        issuer, rating = random.choice(agencies)
        years = random.uniform(1.0, 10.0)
        par = random.choice([5_000_000, 10_000_000, 25_000_000])
        ytm = interpolate_yield(years) + random.uniform(0.2, 0.4)
        coupon = ytm + random.uniform(-0.3, 0.3)
        mkt = calculate_market_value(par, coupon, ytm, years)
        dur = calculate_duration(years, coupon)
        securities.append({
            'security_id': f'AGENCY-{i:04d}',
            'cusip': generate_cusip('Agency', i),
            'security_type': 'Agency',
            'security_subtype': 'Debenture',
            'issuer_name': issuer,
            'issue_date': (CURRENT_DATE - timedelta(days=random.randint(60, 730))).isoformat(),
            'maturity_date': (CURRENT_DATE + timedelta(days=int(years*365))).isoformat(),
            'par_value': par,
            'coupon_rate': coupon,
            'yield_to_maturity': ytm,
            'market_value': mkt,
            'duration': dur,
            'credit_rating': rating,
            'security_classification': random.choice(['HTM', 'AFS']),
            'currency': 'USD'
        })

    log_message("Generating MBS (50)...")
    for i in range(50):
        issuer = random.choice(['Fannie Mae', 'Freddie Mac', 'Ginnie Mae'])
        years = random.uniform(5.0, 30.0)
        par = random.choice([5_000_000, 10_000_000, 25_000_000])
        ytm = interpolate_yield(years) + random.uniform(0.6, 1.2)
        coupon = ytm + random.uniform(-0.5, 0.2)
        mkt = calculate_market_value(par, coupon, ytm, years)
        dur = calculate_duration(years, coupon) * 0.6
        securities.append({
            'security_id': f'MBS-{i:04d}',
            'cusip': generate_cusip('MBS', i),
            'security_type': 'MBS',
            'security_subtype': 'Pass-Through',
            'issuer_name': issuer,
            'issue_date': (CURRENT_DATE - timedelta(days=random.randint(365, 3650))).isoformat(),
            'maturity_date': (CURRENT_DATE + timedelta(days=int(years*365))).isoformat(),
            'par_value': par,
            'coupon_rate': coupon,
            'yield_to_maturity': ytm,
            'market_value': mkt,
            'duration': dur,
            'credit_rating': 'AAA' if issuer == 'Ginnie Mae' else 'AA+',
            'security_classification': random.choice(['HTM', 'AFS']),
            'currency': 'USD'
        })

    log_message(f"✓ Total securities generated: {len(securities)}")
    return securities

def main():
    """Main execution"""
    log_message("=" * 80)
    log_message("WS1-02: Securities Portfolio Generator")
    log_message("=" * 80)

    w = WorkspaceClient()
    log_message(f"✓ Connected to Databricks")

    # Generate securities
    securities = generate_securities_data()

    # Create bronze table
    log_message("\nCreating bronze layer table...")
    bronze_table = "cfo_banking_demo.bronze_core_banking.securities_portfolio"

    create_table_sql = f"""
    CREATE OR REPLACE TABLE {bronze_table} (
        security_id STRING NOT NULL,
        cusip STRING NOT NULL,
        isin STRING,
        security_type STRING NOT NULL,
        security_subtype STRING,
        issuer_name STRING NOT NULL,
        issue_date DATE,
        maturity_date DATE NOT NULL,
        par_value DOUBLE NOT NULL,
        coupon_rate DOUBLE NOT NULL,
        yield_to_maturity DOUBLE NOT NULL,
        market_value DOUBLE NOT NULL,
        duration DOUBLE NOT NULL,
        credit_rating STRING NOT NULL,
        security_classification STRING NOT NULL,
        currency STRING NOT NULL,
        book_value DOUBLE,
        unrealized_gain_loss DOUBLE,
        oci_adjustment DOUBLE,
        effective_date DATE NOT NULL,
        is_current BOOLEAN NOT NULL
    )
    """

    execute_sql(w, create_table_sql)
    log_message(f"✓ Created table {bronze_table}")

    # Insert securities in batches of 100
    log_message("\nInserting securities data...")
    batch_size = 100
    for batch_start in range(0, len(securities), batch_size):
        batch = securities[batch_start:batch_start + batch_size]
        values_list = []
        for sec in batch:
            isin = f"US{sec['cusip']}"
            book_value = sec['par_value'] if sec['security_classification'] == 'HTM' else sec['market_value']
            unrealized_gl = sec['market_value'] - book_value
            oci = unrealized_gl if sec['security_classification'] == 'AFS' else 0.0

            values_list.append(f"""(
                '{sec['security_id']}', '{sec['cusip']}', '{isin}',
                '{sec['security_type']}', '{sec['security_subtype']}', '{sec['issuer_name']}',
                '{sec['issue_date']}', '{sec['maturity_date']}',
                {sec['par_value']}, {sec['coupon_rate']}, {sec['yield_to_maturity']},
                {sec['market_value']}, {sec['duration']},
                '{sec['credit_rating']}', '{sec['security_classification']}', '{sec['currency']}',
                {book_value}, {unrealized_gl}, {oci},
                '{CURRENT_DATE}', true
            )""")

        insert_sql = f"""
        INSERT INTO {bronze_table} VALUES
        {', '.join(values_list)}
        """

        execute_sql(w, insert_sql)
        log_message(f"✓ Inserted batch {batch_start//batch_size + 1}/{(len(securities)-1)//batch_size + 1}")

    # Create silver layer
    log_message("\nCreating silver layer table...")
    silver_table = "cfo_banking_demo.silver_treasury.securities_portfolio"

    create_silver_sql = f"""
    CREATE OR REPLACE TABLE {silver_table} AS
    SELECT
        *,
        DATEDIFF(maturity_date, effective_date) AS days_to_maturity,
        DATEDIFF(maturity_date, effective_date) / 365.0 AS years_to_maturity,
        market_value / SUM(market_value) OVER () * 100 AS portfolio_weight,
        unrealized_gain_loss AS mtm_pnl
    FROM {bronze_table}
    """

    execute_sql(w, create_silver_sql)
    log_message(f"✓ Created {silver_table}")

    # Validations
    log_message("\nRunning validations...")

    count_sql = f"SELECT COUNT(*) as cnt FROM {bronze_table}"
    result = execute_sql(w, count_sql)
    count = int(result.result.data_array[0][0]) if result.result and result.result.data_array else 0
    assert count == 1000, f"Expected 1000, got {count}"
    log_message(f"✓ Record count: {count}")

    # Summary statistics
    log_message("\nGenerating summary statistics...")

    summary_sql = f"""
    SELECT
        security_type,
        COUNT(*) as count,
        SUM(par_value) as total_par,
        SUM(market_value) as total_market_value,
        AVG(yield_to_maturity) as avg_ytm,
        AVG(duration) as avg_duration
    FROM {silver_table}
    GROUP BY security_type
    ORDER BY total_market_value DESC
    """

    result = execute_sql(w, summary_sql)
    log_message("\nBy Security Type:")
    if result.result and result.result.data_array:
        for row in result.result.data_array:
            sec_type = row[0]
            count = int(row[1])
            mkt_value = float(row[3])
            log_message(f"  {sec_type}: {count} securities, ${mkt_value:,.0f} market value")

    log_message("\n" + "=" * 80)
    log_message("✅ WS1-02 Complete!")
    log_message("=" * 80)
    log_message(f"\nBronze table: {bronze_table}")
    log_message(f"Silver table: {silver_table}")
    log_message("\n✅ Ready for WS1-03")

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
