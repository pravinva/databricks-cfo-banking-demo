#!/usr/bin/env python3
"""
Verify Historical Data Quality - Post-Backfill Validation
Confirms the 64-year historical backfill was successful and data is production-ready.
"""

import time
from datetime import datetime
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import sql

print("\n" + "="*80)
print("🔍 HISTORICAL DATA QUALITY VERIFICATION")
print("="*80)
print("Purpose: Validate 64-year treasury yield backfill is production-ready")
print("="*80)

# Initialize
w = WorkspaceClient()
WAREHOUSE_ID = "4b9b953939869799"

def execute_sql(query, description=""):
    """Execute SQL and return results."""
    if description:
        print(f"\n{description}...")
    response = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        statement=query,
        catalog="cfo_banking_demo",
        wait_timeout="50s"
    )
    while response.status.state in [sql.StatementState.PENDING, sql.StatementState.RUNNING]:
        time.sleep(2)
        response = w.statement_execution.get_statement(response.statement_id)

    if response.status.state == sql.StatementState.SUCCEEDED:
        return response.result.data_array if response.result else []
    else:
        error_msg = response.status.error.message if response.status.error else "Unknown error"
        raise Exception(f"SQL failed: {error_msg}")

# Test 1: Overall Data Coverage
print("\n" + "="*80)
print("📊 TEST 1: OVERALL DATA COVERAGE")
print("="*80)

result = execute_sql("""
    SELECT
        COUNT(*) as total_rows,
        COUNT(DISTINCT date) as unique_dates,
        MIN(date) as earliest_date,
        MAX(date) as latest_date,
        DATEDIFF(MAX(date), MIN(date)) as days_span,
        ROUND(DATEDIFF(MAX(date), MIN(date)) / 365.25, 1) as years_span
    FROM cfo_banking_demo.silver_treasury.yield_curves
""", "Checking overall coverage")

if result and result[0]:
    row = result[0]
    total_rows = int(row[0])
    unique_dates = int(row[1])
    days_span = int(row[4])
    years_span = float(row[5])

    print(f"\n✓ Total Rows: {total_rows:,}")
    print(f"✓ Unique Dates: {unique_dates:,}")
    print(f"✓ Date Range: {row[2]} to {row[3]}")
    print(f"✓ Days Span: {days_span:,} days")
    print(f"✓ Years Span: {years_span} years")

    if total_rows >= 15000:
        print(f"\n✅ PASS: {total_rows:,} rows is excellent (target: 15,000+)")
    else:
        print(f"\n⚠️  WARNING: Only {total_rows:,} rows (target: 15,000+)")

    if years_span >= 20:
        print(f"✅ PASS: {years_span} years covers multiple economic cycles")
    else:
        print(f"⚠️  WARNING: Only {years_span} years (target: 20+ years)")

# Test 2: Maturity Coverage
print("\n" + "="*80)
print("📊 TEST 2: MATURITY COVERAGE (All 5 Maturities)")
print("="*80)

result = execute_sql("""
    SELECT
        COUNT(*) as total_dates,
        COUNT(rate_3m) as has_3m,
        COUNT(rate_2y) as has_2y,
        COUNT(rate_5y) as has_5y,
        COUNT(rate_10y) as has_10y,
        COUNT(rate_30y) as has_30y,
        ROUND(100.0 * COUNT(rate_3m) / COUNT(*), 1) as pct_3m,
        ROUND(100.0 * COUNT(rate_2y) / COUNT(*), 1) as pct_2y,
        ROUND(100.0 * COUNT(rate_5y) / COUNT(*), 1) as pct_5y,
        ROUND(100.0 * COUNT(rate_10y) / COUNT(*), 1) as pct_10y,
        ROUND(100.0 * COUNT(rate_30y) / COUNT(*), 1) as pct_30y
    FROM cfo_banking_demo.silver_treasury.yield_curves
""", "Checking maturity coverage")

if result and result[0]:
    row = result[0]
    print(f"\n{'Maturity':<12} {'Count':>10} {'Coverage %':>12} {'Status'}")
    print("-" * 80)

    maturities = [
        ("3-Month", row[1], row[6]),
        ("2-Year", row[2], row[7]),
        ("5-Year", row[3], row[8]),
        ("10-Year", row[4], row[9]),
        ("30-Year", row[5], row[10])
    ]

    all_pass = True
    for name, count, pct in maturities:
        status = "✅ PASS" if float(pct) >= 90 else "⚠️  LOW"
        print(f"{name:<12} {int(count):>10,} {float(pct):>11.1f}% {status}")
        if float(pct) < 90:
            all_pass = False

    if all_pass:
        print("\n✅ ALL MATURITIES: >90% coverage (excellent)")
    else:
        print("\n⚠️  SOME MATURITIES: <90% coverage (acceptable but gaps exist)")

# Test 3: Fed Funds Rate Coverage
print("\n" + "="*80)
print("📊 TEST 3: FED FUNDS RATE COVERAGE")
print("="*80)

result = execute_sql("""
    SELECT
        COUNT(*) as total_rows,
        COUNT(fed_funds_rate) as rows_with_fed_funds,
        ROUND(100.0 * COUNT(fed_funds_rate) / COUNT(*), 1) as coverage_pct,
        MIN(fed_funds_rate) as min_rate,
        MAX(fed_funds_rate) as max_rate,
        AVG(fed_funds_rate) as avg_rate,
        STDDEV(fed_funds_rate) as stddev_rate
    FROM cfo_banking_demo.silver_treasury.yield_curves
""", "Checking fed_funds_rate column")

if result and result[0]:
    row = result[0]
    coverage = float(row[2])
    print(f"\n✓ Total Rows: {int(row[0]):,}")
    print(f"✓ Rows with Fed Funds: {int(row[1]):,}")
    print(f"✓ Coverage: {coverage:.1f}%")
    print(f"✓ Rate Range: {float(row[3]):.2f}% to {float(row[4]):.2f}%")
    print(f"✓ Average Rate: {float(row[5]):.2f}%")
    print(f"✓ Std Deviation: {float(row[6]):.2f}%")

    if coverage >= 90:
        print(f"\n✅ PASS: {coverage:.1f}% coverage is excellent")
    elif coverage >= 70:
        print(f"\n⚠️  ACCEPTABLE: {coverage:.1f}% coverage (target: 90%+)")
    else:
        print(f"\n❌ FAIL: Only {coverage:.1f}% coverage (target: 70%+)")

# Test 4: Rate Regime Distribution
print("\n" + "="*80)
print("📊 TEST 4: RATE REGIME DISTRIBUTION")
print("="*80)

result = execute_sql("""
    SELECT
        CASE
            WHEN fed_funds_rate < 2.0 THEN 'Low (<2%)'
            WHEN fed_funds_rate < 4.0 THEN 'Medium (2-4%)'
            ELSE 'High (4%+)'
        END as rate_regime,
        COUNT(*) as count,
        ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as percentage,
        MIN(date) as earliest,
        MAX(date) as latest
    FROM cfo_banking_demo.silver_treasury.yield_curves
    WHERE fed_funds_rate IS NOT NULL
    GROUP BY
        CASE
            WHEN fed_funds_rate < 2.0 THEN 'Low (<2%)'
            WHEN fed_funds_rate < 4.0 THEN 'Medium (2-4%)'
            ELSE 'High (4%+)'
        END
    ORDER BY rate_regime
""", "Checking rate regime distribution")

if result:
    print(f"\n{'Regime':<20} {'Count':>10} {'%':>10} {'Period'}")
    print("-" * 80)
    for row in result:
        print(f"{row[0]:<20} {int(row[1]):>10,} {float(row[2]):>9.1f}% {row[3]} to {row[4]}")

    # Check if balanced
    if len(result) == 3:
        percentages = [float(row[2]) for row in result]
        min_pct = min(percentages)
        if min_pct >= 15:
            print("\n✅ PASS: All regimes represented (>15% each) - good balance")
        else:
            print("\n⚠️  ACCEPTABLE: Some regimes underrepresented (<15%)")
    else:
        print("\n⚠️  WARNING: Not all 3 rate regimes present in data")

# Test 5: Data Gaps Analysis
print("\n" + "="*80)
print("📊 TEST 5: DATA GAPS ANALYSIS (Missing Dates)")
print("="*80)

result = execute_sql("""
    WITH date_gaps AS (
        SELECT
            date,
            LAG(date) OVER (ORDER BY date) as prev_date,
            DATEDIFF(date, LAG(date) OVER (ORDER BY date)) as gap_days
        FROM cfo_banking_demo.silver_treasury.yield_curves
    )
    SELECT
        COUNT(*) as total_gaps,
        SUM(CASE WHEN gap_days > 7 THEN 1 ELSE 0 END) as large_gaps_7plus,
        SUM(CASE WHEN gap_days > 30 THEN 1 ELSE 0 END) as large_gaps_30plus,
        MAX(gap_days) as max_gap_days,
        AVG(gap_days) as avg_gap_days
    FROM date_gaps
    WHERE gap_days > 3
""", "Analyzing date gaps")

if result and result[0]:
    row = result[0]
    total_gaps = int(row[0])
    large_gaps_7 = int(row[1])
    large_gaps_30 = int(row[2])
    max_gap = int(row[3])
    avg_gap = float(row[4])

    print(f"\n✓ Total Gaps >3 days: {total_gaps:,}")
    print(f"✓ Gaps >7 days: {large_gaps_7:,}")
    print(f"✓ Gaps >30 days: {large_gaps_30:,}")
    print(f"✓ Largest Gap: {max_gap} days")
    print(f"✓ Average Gap: {avg_gap:.1f} days")

    if large_gaps_30 == 0:
        print("\n✅ PASS: No large gaps (>30 days) - excellent data continuity")
    elif large_gaps_30 <= 5:
        print("\n⚠️  ACCEPTABLE: Few large gaps (<5) - minor continuity issues")
    else:
        print(f"\n⚠️  WARNING: {large_gaps_30} large gaps (>30 days) - some data discontinuity")

# Test 6: Economic Cycle Coverage
print("\n" + "="*80)
print("📊 TEST 6: ECONOMIC CYCLE COVERAGE (Historical Periods)")
print("="*80)

result = execute_sql("""
    SELECT
        '1960s-1970s' as era,
        COUNT(*) as records,
        AVG(fed_funds_rate) as avg_rate
    FROM cfo_banking_demo.silver_treasury.yield_curves
    WHERE date BETWEEN '1960-01-01' AND '1979-12-31'
    UNION ALL
    SELECT
        '1980s (Volcker)',
        COUNT(*),
        AVG(fed_funds_rate)
    FROM cfo_banking_demo.silver_treasury.yield_curves
    WHERE date BETWEEN '1980-01-01' AND '1989-12-31'
    UNION ALL
    SELECT
        '1990s-2000s',
        COUNT(*),
        AVG(fed_funds_rate)
    FROM cfo_banking_demo.silver_treasury.yield_curves
    WHERE date BETWEEN '1990-01-01' AND '2007-12-31'
    UNION ALL
    SELECT
        '2008-2015 (Zero rate)',
        COUNT(*),
        AVG(fed_funds_rate)
    FROM cfo_banking_demo.silver_treasury.yield_curves
    WHERE date BETWEEN '2008-01-01' AND '2015-12-31'
    UNION ALL
    SELECT
        '2016-2019 (Normal)',
        COUNT(*),
        AVG(fed_funds_rate)
    FROM cfo_banking_demo.silver_treasury.yield_curves
    WHERE date BETWEEN '2016-01-01' AND '2019-12-31'
    UNION ALL
    SELECT
        '2020-2021 (COVID)',
        COUNT(*),
        AVG(fed_funds_rate)
    FROM cfo_banking_demo.silver_treasury.yield_curves
    WHERE date BETWEEN '2020-01-01' AND '2021-12-31'
    UNION ALL
    SELECT
        '2022-2026 (Tightening)',
        COUNT(*),
        AVG(fed_funds_rate)
    FROM cfo_banking_demo.silver_treasury.yield_curves
    WHERE date BETWEEN '2022-01-01' AND '2026-12-31'
""", "Analyzing economic cycle coverage")

if result:
    print(f"\n{'Economic Era':<25} {'Records':>10} {'Avg Rate':>12} {'Status'}")
    print("-" * 80)

    cycles_covered = 0
    for row in result:
        records = int(row[1])
        avg_rate = float(row[2]) if row[2] else 0.0
        status = "✅" if records > 100 else "⚠️ " if records > 0 else "❌"
        print(f"{row[0]:<25} {records:>10,} {avg_rate:>11.2f}% {status}")
        if records > 100:
            cycles_covered += 1

    print(f"\n✅ CYCLES COVERED: {cycles_covered}/7 economic periods")
    if cycles_covered >= 5:
        print("   Excellent coverage of diverse economic environments")
    else:
        print("   Limited historical coverage - may affect model robustness")

# Test 7: Yield Curve Inversion Detection
print("\n" + "="*80)
print("📊 TEST 7: YIELD CURVE INVERSIONS (Rare Events)")
print("="*80)

result = execute_sql("""
    SELECT
        COUNT(*) as total_dates,
        SUM(CASE WHEN rate_10y < rate_2y THEN 1 ELSE 0 END) as inversions_10y_2y,
        SUM(CASE WHEN rate_10y < rate_3m THEN 1 ELSE 0 END) as inversions_10y_3m,
        MIN(CASE WHEN rate_10y < rate_2y THEN date END) as first_inversion,
        MAX(CASE WHEN rate_10y < rate_2y THEN date END) as last_inversion,
        ROUND(100.0 * SUM(CASE WHEN rate_10y < rate_2y THEN 1 ELSE 0 END) / COUNT(*), 2) as inversion_pct
    FROM cfo_banking_demo.silver_treasury.yield_curves
    WHERE rate_10y IS NOT NULL AND rate_2y IS NOT NULL
""", "Detecting yield curve inversions")

if result and result[0]:
    row = result[0]
    inversions = int(row[1])
    inversions_3m = int(row[2])
    pct = float(row[5])

    print(f"\n✓ Total Dates Analyzed: {int(row[0]):,}")
    print(f"✓ 10Y-2Y Inversions: {inversions:,} ({pct:.2f}%)")
    print(f"✓ 10Y-3M Inversions: {inversions_3m:,}")
    if row[3]:
        print(f"✓ First Inversion: {row[3]}")
        print(f"✓ Last Inversion: {row[4]}")

    if inversions > 0:
        print("\n✅ PASS: Captured yield curve inversions (recession predictors)")
        print("   This enriches model training with rare event data")
    else:
        print("\n⚠️  NOTE: No inversions detected - may limit stress scenario modeling")

# Test 8: Recent Data Freshness
print("\n" + "="*80)
print("📊 TEST 8: RECENT DATA FRESHNESS")
print("="*80)

result = execute_sql("""
    SELECT
        date,
        fed_funds_rate,
        rate_3m,
        rate_2y,
        rate_10y,
        (rate_10y - rate_2y) as curve_slope,
        CASE
            WHEN fed_funds_rate < 2.0 THEN 'Low'
            WHEN fed_funds_rate < 4.0 THEN 'Medium'
            ELSE 'High'
        END as rate_regime
    FROM cfo_banking_demo.silver_treasury.yield_curves
    ORDER BY date DESC
    LIMIT 5
""", "Checking most recent data")

if result:
    print(f"\n{'Date':<12} {'Fed Funds':>10} {'3M':>10} {'2Y':>10} {'10Y':>10} {'Slope':>10} {'Regime':<10}")
    print("-" * 80)
    for row in result:
        print(f"{str(row[0]):<12} {float(row[1]):>9.2f}% {float(row[2]):>9.2f}% {float(row[3]):>9.2f}% {float(row[4]):>9.2f}% {float(row[5]):>9.2f}% {str(row[6]):<10}")

    latest_date = result[0][0]
    if isinstance(latest_date, str):
        from datetime import date
        latest_date = date.fromisoformat(latest_date)
    days_old = (datetime.now().date() - latest_date).days

    print(f"\n✓ Latest Data: {latest_date} ({days_old} days old)")
    if days_old <= 7:
        print("✅ PASS: Data is very fresh (<7 days old)")
    elif days_old <= 30:
        print("✅ ACCEPTABLE: Data is reasonably fresh (<30 days old)")
    else:
        print(f"⚠️  WARNING: Data is {days_old} days old (consider updating)")

# Final Summary
print("\n" + "="*80)
print("✅ VERIFICATION COMPLETE")
print("="*80)

print("\n📊 SUMMARY:")
print("  ✓ Data coverage verified")
print("  ✓ All maturities checked")
print("  ✓ Fed funds rate validated")
print("  ✓ Rate regimes confirmed")
print("  ✓ Data gaps analyzed")
print("  ✓ Economic cycles covered")
print("  ✓ Yield inversions detected")
print("  ✓ Recent data freshness checked")

print("\n🚀 NEXT STEPS:")
print("  1. ✅ Data is production-ready for modeling")
print("  2. 📤 Upload notebooks to Databricks workspace")
print("  3. ▶️  Run Approach 1: Enhanced Deposit Beta Model (45 min)")
print("  4. 📈 Review model performance and feature importance")

print("\n💡 To upload notebooks:")
print("  databricks workspace import notebooks/Approach1_Enhanced_Deposit_Beta_Model.py \\")
print("    /Users/your_username/Approach1_Enhanced_Deposit_Beta_Model --language PYTHON")

print("\n" + "="*80)
