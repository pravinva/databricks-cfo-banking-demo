# Data Requirements Analysis for Deposit Beta Modeling

**Date:** 2026-01-31
**Analysis:** Comprehensive review of existing tables vs notebook requirements
**Decision Framework:** Evidence-based, no false assumptions

---

## Executive Summary

**Question:** Do we need to add data to existing tables? Create new tables? Use AlphaVantage API?

**Answer:**
1. ✅ **Existing tables are sufficient** - No new permanent tables required beyond what notebooks create
2. ⚠️ **Need to enrich existing data** - Missing columns for relationship features, competitive rates, and fed funds rate
3. ✅ **YES - Use AlphaVantage API** - Required for fed funds rate and historical yield curve backfill

---

## Part 1: Existing Tables Inventory

### Bronze Layer (Core Banking)
- ✅ `deposit_accounts` - 402,000 current accounts
- ✅ `loan_portfolio` - Available
- ✅ `chart_of_accounts` - Available
- ✅ `deposit_behavior_history` - Available
- ✅ `balance_sheet_daily` - Available

### Silver Layer (Treasury & Finance)
- ✅ `silver_treasury.yield_curves` - 27 days of data (2025-12-12 to 2026-01-22)
- ✅ `silver_finance.general_ledger` - 9,216 rows (backfilled)
- ✅ `silver_finance.deposit_portfolio` - Available

### Gold Layer (Finance)
- ✅ `gold_finance.profitability_metrics` - Available
- ✅ `gold_finance.capital_structure` - Available
- ✅ `gold_finance.liquidity_coverage_ratio` - Available

---

## Part 2: Schema Analysis

### 2.1 Deposit Accounts - Existing Columns (Good!)

**Base Account Info:**
- ✅ `account_id`, `customer_id`, `product_type`, `account_open_date`
- ✅ `current_balance`, `average_balance_30d`, `average_balance_90d`
- ✅ `stated_rate`, `beta`, `decay_rate`
- ✅ `transaction_count_30d`, `last_transaction_date`

**Relationship Features (Present):**
- ✅ `relationship_balance` - Total customer balance across products
- ✅ `has_online_banking` - Boolean flag
- ✅ `has_mobile_banking` - Boolean flag
- ✅ `autopay_enrolled` - Boolean flag

**Good news:** Many features exist! Sample row shows:
```
Customer: CUST-394735
Product: Wealth_Builder_Savings
Balance: $82,128
Relationship Balance: $471,467 (customer has multiple accounts!)
Beta: 0.3384
Online/Mobile: false/false
Autopay: false
Account Age: 2020-05-24 (5.7 years)
```

### 2.2 Deposit Accounts - Missing Columns (Need Workarounds)

**Missing Relationship Features:**
❌ `product_count` - Number of products per customer
❌ `relationship_length_years` - Years since first account
❌ `relationship_score` - Composite score (0-25)
❌ `relationship_category` - Strategic/Tactical/Expendable
❌ `primary_bank_flag` - Is this their primary bank?
❌ `direct_deposit_flag` - Do they have direct deposit?

**Missing Competitive Features:**
❌ `competitor_avg_rate` - Average competitor rate for product type
❌ `online_bank_avg_rate` - Online bank rates (typically higher)
❌ `market_rate_spread` - Spread vs market
❌ `competitor_rate_spread` - Spread vs competitors

**Missing Market Regime Features:**
❌ `rate_regime` - Low/Medium/High classification
❌ `rate_change_velocity_3m` - Rate of change
❌ `yield_curve_slope` - 10Y - 2Y spread
❌ `yield_curve_inverted` - Boolean flag

### 2.3 Yield Curves - Critical Data Gap

**Current State:**
```
Columns: date, rate_3m, rate_2y, rate_5y, rate_10y, rate_30y
Date Range: 2025-12-12 to 2026-01-22 (only 27 days!)
Latest Data: 2026-01-22
  rate_3m: 3.71%
  rate_2y: 3.61%
  rate_10y: 4.26%
```

**Critical Issues:**
1. ❌ **Missing `fed_funds_rate` column** - Required for rate regime classification
2. ❌ **Only 27 days of data** - Need 24+ months for model training
3. ⚠️ **Column naming mismatch** - Notebooks expect `treasury_3m` but table has `rate_3m`

**Why This Matters:**
- Phase 1 needs fed_funds_rate to classify rate regimes (low <2%, medium 2-4%, high >4%)
- Phase 2 needs 24+ months for cohort analysis
- Phase 3 needs multi-year data for stress testing calibration

### 2.4 General Ledger - Minor Schema Issue

**Schema:**
✅ Table exists with 9,216 rows
⚠️ Column is `account_num` not `account_number` (minor fix needed)

---

## Part 3: What Notebooks Expect vs What We Have

### Phase 1: Enhanced Deposit Beta Model

**Expected Inputs:**
```sql
SELECT
    d.account_id,
    d.beta,
    d.stated_rate,
    d.product_type,
    d.customer_segment,
    d.current_balance,

    -- Relationship features (NEED TO COMPUTE)
    r.product_count,                    -- ❌ Missing
    r.relationship_length_years,        -- ❌ Missing
    r.relationship_score,               -- ❌ Missing
    r.relationship_category,            -- ❌ Missing

    -- Competitive features (NEED TO ADD)
    c.competitor_avg_rate,              -- ❌ Missing
    c.online_bank_avg_rate,             -- ❌ Missing
    (d.stated_rate - c.competitor_avg_rate) as competitor_rate_spread,

    -- Market regime features (NEED TO DERIVE)
    m.fed_funds_rate,                   -- ❌ Missing
    m.rate_regime,                      -- ❌ Missing
    m.yield_curve_slope                 -- ❌ Missing

FROM deposit_accounts d
LEFT JOIN customer_relationships r     -- ❌ Need to compute
LEFT JOIN competitive_rates c          -- ❌ Need to add
LEFT JOIN market_conditions m          -- ❌ Need to derive
```

**Reality Check:**
✅ Core deposit data exists
⚠️ Relationship features can be computed from existing data
❌ Competitive rates need hardcoding or external API
❌ Fed funds rate needs AlphaVantage API

### Phase 2: Vintage Analysis & Decay Modeling

**Expected Inputs:**
```sql
-- Cohort analysis by quarter
SELECT
    DATE_TRUNC('quarter', account_open_date) as cohort_quarter,
    relationship_category,                    -- ❌ Need to compute
    months_since_open,
    AVG(current_balance) as avg_balance,
    COUNT(DISTINCT account_id) as account_count
FROM deposit_accounts
GROUP BY cohort_quarter, relationship_category, months_since_open
```

**Reality Check:**
✅ account_open_date exists (can compute cohorts)
✅ Current balance tracked over time
⚠️ relationship_category needs to be computed
✅ Can derive from existing data

### Phase 3: Dynamic Beta & Stress Testing

**Expected Inputs:**
```sql
-- Historical beta-rate relationships
SELECT
    d.date,
    d.beta,
    m.fed_funds_rate,                         -- ❌ Missing
    m.rate_3m,                                -- ✅ Have (as rate_3m)
    m.rate_10y,                               -- ✅ Have
    (m.rate_10y - m.rate_2y) as curve_slope   -- ✅ Can compute
FROM deposit_beta_history d
LEFT JOIN yield_curves m ON d.date = m.date
WHERE d.date >= DATE_SUB(CURRENT_DATE(), 730)  -- ❌ Only have 27 days!
```

**Reality Check:**
✅ Yield curve data structure is good
❌ Missing fed_funds_rate column
❌ Insufficient historical data (27 days vs 730 needed)
✅ Can compute derived features from existing columns

---

## Part 4: Solutions - What Do We Need to Do?

### 4.1 Option A: Compute Features in Notebooks (RECOMMENDED)

**Advantages:**
- No schema changes required
- Flexible feature engineering
- Easy to version control

**Implementation:**
Notebooks can compute missing features using SQL/PySpark:

```sql
-- Compute relationship features on-the-fly
WITH customer_product_counts AS (
    SELECT
        customer_id,
        COUNT(DISTINCT account_id) as product_count,
        MIN(account_open_date) as first_account_date,
        SUM(current_balance) as total_relationship_balance
    FROM deposit_accounts
    WHERE is_current = true
    GROUP BY customer_id
),
relationship_scores AS (
    SELECT
        customer_id,
        product_count,
        DATEDIFF(CURRENT_DATE(), first_account_date) / 365.25 as relationship_length_years,
        -- Scoring formula: product diversity (0-10) + tenure (0-10) + balance (0-5)
        (LEAST(product_count, 5) * 2) +
        LEAST(DATEDIFF(CURRENT_DATE(), first_account_date) / 365.25, 10) +
        LEAST(total_relationship_balance / 100000, 5) as relationship_score
    FROM customer_product_counts
)
SELECT
    d.*,
    r.product_count,
    r.relationship_length_years,
    r.relationship_score,
    CASE
        WHEN r.relationship_score >= 15 THEN 'Strategic'
        WHEN r.relationship_score >= 8 THEN 'Tactical'
        ELSE 'Expendable'
    END as relationship_category
FROM deposit_accounts d
LEFT JOIN relationship_scores r ON d.customer_id = r.customer_id
WHERE d.is_current = true
```

**Status:** ✅ No action needed - notebooks already do this

### 4.2 Add Fed Funds Rate to Yield Curves (REQUIRED)

**Problem:** Notebooks need fed_funds_rate for rate regime classification

**Solution 1: Derive from 3M Treasury (Quick Fix)**
```sql
-- Add fed_funds_rate column derived from rate_3m
ALTER TABLE cfo_banking_demo.silver_treasury.yield_curves
ADD COLUMN fed_funds_rate DOUBLE;

UPDATE cfo_banking_demo.silver_treasury.yield_curves
SET fed_funds_rate = rate_3m - 0.15;  -- Typical spread: 3M Treasury ≈ Fed Funds + 15bps
```

**Solution 2: Fetch from AlphaVantage (Accurate)**
Use AlphaVantage FRED API to get actual Federal Funds Rate:
```
URL: https://www.alphavantage.co/query?function=FEDERAL_FUNDS_RATE&apikey=YOUR_KEY
```

**Recommendation:** ✅ Use Solution 1 for demo, Solution 2 for production

### 4.3 Backfill Historical Yield Curves (REQUIRED)

**Problem:** Only 27 days of data, need 24+ months

**Solution: AlphaVantage Treasury Yield API**

Create a backfill script:
```python
import requests
import pandas as pd
from databricks.sdk import WorkspaceClient

# AlphaVantage API endpoints
ALPHAVANTAGE_KEY = "YOUR_API_KEY"
MATURITIES = ["3month", "2year", "5year", "10year", "30year"]

def fetch_treasury_yields(maturity):
    url = f"https://www.alphavantage.co/query"
    params = {
        "function": "TREASURY_YIELD",
        "interval": "daily",
        "maturity": maturity,
        "apikey": ALPHAVANTAGE_KEY
    }
    response = requests.get(url, params=params)
    return response.json()

def fetch_fed_funds():
    url = f"https://www.alphavantage.co/query"
    params = {
        "function": "FEDERAL_FUNDS_RATE",
        "apikey": ALPHAVANTAGE_KEY
    }
    response = requests.get(url, params=params)
    return response.json()

# Fetch and merge all data
# ... (implementation details)

# Insert into yield_curves table
spark.createDataFrame(historical_data).write.mode("append").saveAsTable(
    "cfo_banking_demo.silver_treasury.yield_curves"
)
```

**Timeline:** 2-3 hours to implement and backfill

**Recommendation:** ✅ Use AlphaVantage for historical backfill (one-time), then update weekly

### 4.4 Add Competitive Rates (OPTIONAL - Can Hardcode)

**Problem:** Notebooks expect competitor_avg_rate and online_bank_avg_rate

**Solution 1: Hardcode Typical Rates (Quick)**
```sql
-- Add as constants in notebooks
competitor_avg_rate = CASE product_type
    WHEN 'DDA' THEN 0.01      -- Checking: 0.01%
    WHEN 'Savings' THEN 2.50  -- Savings: 2.50%
    WHEN 'MMDA' THEN 3.00     -- MMDA: 3.00%
    WHEN 'CD' THEN 4.50       -- CD: 4.50%
    ELSE 1.00
END

online_bank_avg_rate = CASE product_type
    WHEN 'Savings' THEN 4.00  -- Online savings: 4.00%
    WHEN 'MMDA' THEN 4.25     -- Online MMDA: 4.25%
    WHEN 'CD' THEN 5.00       -- Online CD: 5.00%
    ELSE 2.00
END
```

**Solution 2: External API (Production)**
- RateWatch API (paid service)
- DepositAccounts.com API
- FDIC Rate Survey data

**Recommendation:** ✅ Use Solution 1 for demo (hardcode), Solution 2 for production monitoring

### 4.5 Fix General Ledger Schema Mismatch (MINOR)

**Problem:** Notebooks expect `account_number`, table has `account_num`

**Solution: Update notebooks to use actual column name**
- Find/replace: `account_number` → `account_num`
- No table changes needed

**Recommendation:** ✅ Fix in notebooks (easier than altering table)

---

## Part 5: AlphaVantage API Requirements

### 5.1 Do We Need AlphaVantage?

**YES** - AlphaVantage is required for:

1. **Federal Funds Rate** (CRITICAL)
   - Notebooks need this for rate regime classification
   - Endpoint: `FEDERAL_FUNDS_RATE`
   - Frequency: Weekly updates

2. **Historical Treasury Yields** (CRITICAL)
   - Need 24+ months of data for model training
   - Current: 27 days
   - Endpoint: `TREASURY_YIELD` (3month, 2year, 10year, 30year)
   - Frequency: One-time backfill, then weekly updates

3. **Real-Time Stress Testing** (NICE-TO-HAVE)
   - Phase 3 stress tests need current market rates
   - Can use existing data with manual updates for demo

### 5.2 AlphaVantage Implementation Plan

**Step 1: Get API Key**
- Sign up at https://www.alphavantage.co/
- Free tier: 25 requests/day (sufficient for demo)
- Premium: $50/month for 1200 requests/day

**Step 2: Create Backfill Script**
```python
# File: scripts/backfill_yield_curves_alphavantage.py

import requests
from datetime import datetime, timedelta
from databricks.sdk import WorkspaceClient

ALPHAVANTAGE_KEY = "YOUR_KEY_HERE"
WAREHOUSE_ID = "8baced1ff014912d"

def backfill_yield_curves():
    """
    Backfill 24 months of treasury yields + fed funds rate
    """
    # Fetch fed funds rate
    fed_funds = fetch_federal_funds_rate()

    # Fetch treasury yields
    yields_3m = fetch_treasury_yield("3month")
    yields_2y = fetch_treasury_yield("2year")
    yields_5y = fetch_treasury_yield("5year")
    yields_10y = fetch_treasury_yield("10year")
    yields_30y = fetch_treasury_yield("30year")

    # Merge all data by date
    merged_data = merge_treasury_data(
        fed_funds, yields_3m, yields_2y, yields_5y, yields_10y, yields_30y
    )

    # Insert into yield_curves table (only dates not already present)
    insert_yield_curves(merged_data)

    print(f"✓ Backfilled {len(merged_data)} days of yield curve data")

if __name__ == "__main__":
    backfill_yield_curves()
```

**Step 3: Schedule Weekly Updates**
- Databricks Job: Run every Monday 6am
- Fetch latest week of data
- Upsert into yield_curves table

### 5.3 AlphaVantage API Endpoints

**Federal Funds Rate:**
```
GET https://www.alphavantage.co/query
Parameters:
  function: FEDERAL_FUNDS_RATE
  apikey: YOUR_KEY

Response:
{
  "name": "Federal Funds Rate",
  "data": [
    {"date": "2026-01-22", "value": "4.58"},
    {"date": "2026-01-15", "value": "4.58"},
    ...
  ]
}
```

**Treasury Yield:**
```
GET https://www.alphavantage.co/query
Parameters:
  function: TREASURY_YIELD
  interval: daily
  maturity: 3month | 2year | 5year | 10year | 30year
  apikey: YOUR_KEY

Response:
{
  "name": "Daily Treasury Yield Rates (3-month)",
  "data": [
    {"date": "2026-01-22", "value": "3.71"},
    {"date": "2026-01-21", "value": "3.70"},
    ...
  ]
}
```

**Rate Limits:**
- Free: 25 API calls/day, 5 calls/minute
- Premium: 1200 API calls/day, 75 calls/minute

**Strategy:** Batch requests efficiently
- 1 call for fed funds
- 5 calls for treasuries (3m, 2y, 5y, 10y, 30y)
- Total: 6 API calls for full backfill

---

## Part 6: Summary & Action Plan

### 6.1 Do We Need to Add Data to Existing Tables?

**Answer: PARTIAL - Only yield_curves needs enrichment**

1. ✅ **deposit_accounts** - No changes needed, compute features in notebooks
2. ⚠️ **yield_curves** - Need to add `fed_funds_rate` column and backfill historical data
3. ✅ **general_ledger** - No changes needed, fix column name reference in notebooks

### 6.2 Do We Need Extra Tables?

**Answer: NO - Notebooks create all necessary tables**

**Tables created by notebooks:**
- Phase 1: `ml_models.deposit_beta_training_enhanced`, `ml_models.deposit_beta_predictions_phase1`
- Phase 2: `ml_models.deposit_cohort_analysis`, `ml_models.cohort_survival_rates`, `ml_models.component_decay_metrics`
- Phase 3: `ml_models.dynamic_beta_parameters`, `ml_models.stress_test_results`, `ml_models.gap_analysis_results`

### 6.3 Do We Need AlphaVantage API?

**Answer: YES - Critical for production-ready modeling**

**Required for:**
1. ✅ **Fed funds rate backfill** - 24 months historical (one-time)
2. ✅ **Treasury yields backfill** - 24 months historical (one-time)
3. ✅ **Weekly rate updates** - Ongoing (scheduled job)

**Optional for:**
- Real-time competitive intelligence (can hardcode for demo)
- Economic indicators (GDP, inflation, unemployment)

### 6.4 Action Plan - Priority Order

#### HIGH PRIORITY (Required for Phase 1)

1. **Add fed_funds_rate to yield_curves**
   - Effort: 15 minutes
   - Method: Derive from rate_3m (quick fix)
   ```sql
   ALTER TABLE cfo_banking_demo.silver_treasury.yield_curves
   ADD COLUMN fed_funds_rate DOUBLE;

   UPDATE cfo_banking_demo.silver_treasury.yield_curves
   SET fed_funds_rate = rate_3m - 0.15;
   ```

2. **Fix general_ledger column reference**
   - Effort: 5 minutes
   - Method: Update notebooks to use `account_num` instead of `account_number`

3. **Hardcode competitive rates**
   - Effort: 10 minutes
   - Method: Add CASE statements in Phase 1 notebook

#### MEDIUM PRIORITY (Required for Phases 2-3)

4. **Backfill yield curves with AlphaVantage**
   - Effort: 2-3 hours
   - Method: Create backfill script using AlphaVantage API
   - Target: 24 months of historical data (2024-01-01 to 2026-01-31)

5. **Update fed_funds_rate with actual data**
   - Effort: Included in step 4
   - Method: Replace derived values with AlphaVantage FRED data

#### LOW PRIORITY (Nice-to-Have)

6. **Set up weekly rate updates**
   - Effort: 1 hour
   - Method: Databricks scheduled job
   - Frequency: Every Monday 6am

7. **Add competitive rate monitoring**
   - Effort: 4-6 hours
   - Method: Integrate RateWatch or DepositAccounts.com API

### 6.5 Estimated Effort & Timeline

**Minimum Viable Product (MVP):**
- Time: 30 minutes
- Tasks: Steps 1-3 above
- Result: Phase 1 notebook runs successfully with derived/hardcoded data

**Production Ready:**
- Time: 3-4 hours
- Tasks: Steps 1-5 above
- Result: All 3 phases run with historical data

**Full Production:**
- Time: 5-6 hours
- Tasks: All steps above
- Result: Automated weekly updates, competitive monitoring

---

## Part 7: Detailed Implementation Scripts

### Script 1: Add Fed Funds Rate Column (Quick Fix)

```sql
-- File: sql/01_add_fed_funds_rate_column.sql

-- Add column if not exists
ALTER TABLE cfo_banking_demo.silver_treasury.yield_curves
ADD COLUMN IF NOT EXISTS fed_funds_rate DOUBLE;

-- Derive from 3M Treasury rate
-- Typical spread: Fed Funds ≈ 3M Treasury - 15bps
UPDATE cfo_banking_demo.silver_treasury.yield_curves
SET fed_funds_rate = rate_3m - 0.15
WHERE fed_funds_rate IS NULL;

-- Verify results
SELECT
    date,
    rate_3m,
    fed_funds_rate,
    rate_2y,
    rate_10y,
    (rate_10y - rate_2y) as curve_slope
FROM cfo_banking_demo.silver_treasury.yield_curves
ORDER BY date DESC
LIMIT 10;
```

### Script 2: Backfill Yield Curves with AlphaVantage

```python
#!/usr/bin/env python3
"""
File: scripts/backfill_yield_curves_alphavantage.py

Backfill 24 months of treasury yields and fed funds rate from AlphaVantage.
Requires: ALPHAVANTAGE_API_KEY environment variable
"""

import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import sql

# Configuration
ALPHAVANTAGE_KEY = os.getenv("ALPHAVANTAGE_API_KEY", "YOUR_KEY_HERE")
WAREHOUSE_ID = "8baced1ff014912d"
CATALOG = "cfo_banking_demo"
SCHEMA = "silver_treasury"
TABLE = "yield_curves"

w = WorkspaceClient()

def fetch_federal_funds_rate():
    """Fetch Federal Funds Rate from AlphaVantage FRED API."""
    print("📊 Fetching Federal Funds Rate...")
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "FEDERAL_FUNDS_RATE",
        "apikey": ALPHAVANTAGE_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "data" not in data:
        raise ValueError(f"API Error: {data}")

    df = pd.DataFrame(data["data"])
    df["date"] = pd.to_datetime(df["date"])
    df["fed_funds_rate"] = df["value"].astype(float)
    df = df[["date", "fed_funds_rate"]]

    print(f"✓ Fetched {len(df)} days of Fed Funds data")
    return df

def fetch_treasury_yield(maturity):
    """
    Fetch Treasury Yield from AlphaVantage.

    maturity: 3month, 2year, 5year, 10year, 30year
    """
    print(f"📊 Fetching Treasury Yield: {maturity}...")
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TREASURY_YIELD",
        "interval": "daily",
        "maturity": maturity,
        "apikey": ALPHAVANTAGE_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "data" not in data:
        raise ValueError(f"API Error: {data}")

    df = pd.DataFrame(data["data"])
    df["date"] = pd.to_datetime(df["date"])

    # Map maturity to column name
    maturity_map = {
        "3month": "rate_3m",
        "2year": "rate_2y",
        "5year": "rate_5y",
        "10year": "rate_10y",
        "30year": "rate_30y"
    }
    column_name = maturity_map[maturity]

    df[column_name] = df["value"].astype(float)
    df = df[["date", column_name]]

    print(f"✓ Fetched {len(df)} days of {maturity} Treasury data")
    return df

def backfill_yield_curves(start_date="2024-01-01"):
    """
    Backfill yield curves from start_date to today.
    """
    print("\n" + "="*80)
    print("🚀 STARTING YIELD CURVE BACKFILL")
    print("="*80)
    print(f"Start Date: {start_date}")
    print(f"API Key: {ALPHAVANTAGE_KEY[:10]}...")

    # Fetch all data
    fed_funds = fetch_federal_funds_rate()
    yield_3m = fetch_treasury_yield("3month")
    yield_2y = fetch_treasury_yield("2year")
    yield_5y = fetch_treasury_yield("5year")
    yield_10y = fetch_treasury_yield("10year")
    yield_30y = fetch_treasury_yield("30year")

    # Merge all data on date
    print("\n📊 Merging all yield curve data...")
    merged = fed_funds
    merged = merged.merge(yield_3m, on="date", how="outer")
    merged = merged.merge(yield_2y, on="date", how="outer")
    merged = merged.merge(yield_5y, on="date", how="outer")
    merged = merged.merge(yield_10y, on="date", how="outer")
    merged = merged.merge(yield_30y, on="date", how="outer")

    # Filter to start_date
    merged = merged[merged["date"] >= start_date]
    merged = merged.sort_values("date")

    # Add ingestion timestamp
    merged["ingestion_timestamp"] = datetime.now()

    print(f"✓ Merged {len(merged)} days of data")
    print(f"\nDate Range: {merged['date'].min()} to {merged['date'].max()}")
    print(f"\nSample data:")
    print(merged.head(3))

    # Insert into Databricks
    print("\n📊 Inserting into Databricks...")

    # Create temp view
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.getOrCreate()

    spark_df = spark.createDataFrame(merged)
    spark_df.createOrReplaceTempView("temp_yield_curves")

    # Upsert into target table
    upsert_query = f"""
    MERGE INTO {CATALOG}.{SCHEMA}.{TABLE} as target
    USING temp_yield_curves as source
    ON target.date = source.date
    WHEN MATCHED THEN
        UPDATE SET
            target.fed_funds_rate = source.fed_funds_rate,
            target.rate_3m = source.rate_3m,
            target.rate_2y = source.rate_2y,
            target.rate_5y = source.rate_5y,
            target.rate_10y = source.rate_10y,
            target.rate_30y = source.rate_30y,
            target.ingestion_timestamp = source.ingestion_timestamp
    WHEN NOT MATCHED THEN
        INSERT (date, fed_funds_rate, rate_3m, rate_2y, rate_5y, rate_10y, rate_30y, ingestion_timestamp)
        VALUES (source.date, source.fed_funds_rate, source.rate_3m, source.rate_2y, source.rate_5y, source.rate_10y, source.rate_30y, source.ingestion_timestamp)
    """

    spark.sql(upsert_query)

    print("✓ Data inserted successfully")

    # Verify results
    print("\n📊 Verification:")
    result = spark.sql(f"""
        SELECT
            MIN(date) as earliest_date,
            MAX(date) as latest_date,
            COUNT(*) as total_rows,
            COUNT(DISTINCT date) as unique_dates
        FROM {CATALOG}.{SCHEMA}.{TABLE}
    """)
    result.show()

    print("\n" + "="*80)
    print("✅ BACKFILL COMPLETE")
    print("="*80)

if __name__ == "__main__":
    backfill_yield_curves(start_date="2024-01-01")
```

### Script 3: Weekly Yield Curve Update Job

```python
#!/usr/bin/env python3
"""
File: scripts/weekly_yield_curve_update.py

Weekly job to update yield curves with latest data from AlphaVantage.
Schedule: Every Monday 6am via Databricks Jobs
"""

import os
from datetime import datetime, timedelta
from scripts.backfill_yield_curves_alphavantage import backfill_yield_curves

# Update only last 7 days
start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

print(f"🔄 Running weekly yield curve update")
print(f"Fetching data from {start_date} to today")

backfill_yield_curves(start_date=start_date)

print("✅ Weekly update complete")
```

---

## Appendix A: AlphaVantage API Costs

### Free Tier
- 25 API calls per day
- 5 API calls per minute
- Cost: $0

**Sufficient for:**
- Initial backfill (6 API calls × 1 day = complete)
- Weekly updates (6 API calls/week = well within limit)

### Premium Tier
- 1200 API calls per day
- 75 API calls per minute
- Cost: $49.99/month

**Needed for:**
- Real-time intraday updates
- Multiple data sources (stocks, forex, crypto)
- High-frequency stress testing

### Recommendation
✅ Start with free tier for demo and MVP
⚠️ Upgrade to premium for production if need real-time updates

---

## Appendix B: Alternative Data Sources

If AlphaVantage is not available:

### Federal Reserve Economic Data (FRED)
- Free API from Federal Reserve Bank of St. Louis
- URL: https://fred.stlouisfed.org/docs/api/fred/
- Series IDs:
  - Federal Funds Rate: DFF
  - 3-Month Treasury: DGS3MO
  - 2-Year Treasury: DGS2
  - 10-Year Treasury: DGS10

### U.S. Treasury Department
- Free data from Treasury.gov
- URL: https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics
- Daily XML files available

### Manual Hardcoding (Demo Only)
If no API available, use recent averages:
```python
# As of January 2026
fed_funds_rate = 4.58
rate_3m = 3.71
rate_2y = 3.61
rate_10y = 4.26
```

---

## Conclusion

**Summary of Answers:**

1. **Do we need to add data to existing tables?**
   - ⚠️ YES - Add `fed_funds_rate` column to `yield_curves`
   - ⚠️ YES - Backfill 24 months of historical yield curve data
   - ✅ NO - Relationship features computed in notebooks

2. **Do we need extra tables?**
   - ✅ NO - Notebooks create all necessary ML tables

3. **Do we need AlphaVantage API?**
   - ✅ YES - Required for fed funds rate and treasury yields
   - ✅ YES - Free tier sufficient for demo/MVP
   - ⚠️ OPTIONAL - Premium tier for production real-time updates

**Next Steps:**
1. Add `fed_funds_rate` column (15 min)
2. Fix `account_num` references (5 min)
3. Hardcode competitive rates (10 min)
4. ← Run Phase 1 notebook (should work!)
5. Implement AlphaVantage backfill (2-3 hours)
6. ← Run Phases 2-3 notebooks (should work!)

**Total effort to MVP: 30 minutes**
**Total effort to production: 3-4 hours**
