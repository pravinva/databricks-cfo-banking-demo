# Data Requirements Summary - Deposit Beta Modeling

**Date:** 2026-01-31
**Status:** Analysis Complete ✅

---

## Quick Answers

### 1. Do we need to add data to existing tables?

**YES - Limited additions required:**

- ⚠️ **yield_curves table** - Add `fed_funds_rate` column + backfill 24 months of historical data
- ✅ **deposit_accounts** - No changes needed (compute features in notebooks)
- ✅ **general_ledger** - No changes needed (fix column reference in notebooks)

### 2. Do we need extra tables?

**NO** - All required tables will be created by the notebooks:

**Phase 1 creates:**
- `ml_models.deposit_beta_training_enhanced`
- `ml_models.deposit_beta_predictions_phase1`

**Phase 2 creates:**
- `ml_models.deposit_cohort_analysis`
- `ml_models.cohort_survival_rates`
- `ml_models.component_decay_metrics`
- `ml_models.deposit_beta_training_phase2`
- `ml_models.deposit_runoff_forecasts`

**Phase 3 creates:**
- `ml_models.dynamic_beta_parameters`
- `ml_models.stress_test_results`
- `ml_models.taylor_sensitivity_analysis`
- `ml_models.gap_analysis_results`

### 3. Do we need to retrieve market data from AlphaVantage API?

**YES** - AlphaVantage is required for:

1. ✅ **Federal Funds Rate** - Critical for rate regime classification
2. ✅ **Historical Treasury Yields** - Need 24 months (currently only have 27 days)
3. ✅ **Weekly Updates** - Keep data current for ongoing modeling

**API Usage:** 6 calls for backfill (within free tier 25 calls/day)

---

## Current State Analysis

### Existing Tables ✅

| Schema | Table | Status | Notes |
|--------|-------|--------|-------|
| bronze_core_banking | deposit_accounts | ✅ Good | 402,000 accounts, has beta/decay_rate |
| bronze_core_banking | loan_portfolio | ✅ Good | Available |
| silver_treasury | yield_curves | ⚠️ Incomplete | Only 27 days (2025-12-12 to 2026-01-22) |
| silver_finance | general_ledger | ✅ Good | 9,216 rows (backfilled) |
| gold_finance | profitability_metrics | ✅ Good | Available |

### Data Gaps Identified

**Critical (Blocks model training):**
1. ❌ Missing `fed_funds_rate` in yield_curves table
2. ❌ Only 27 days of yield curve data (need 730+ days)

**Can be computed (No blockers):**
3. ⚠️ Relationship features (product_count, relationship_score, etc.) - computed in notebooks
4. ⚠️ Competitive rates (competitor_avg_rate, online_bank_avg_rate) - hardcoded in notebooks
5. ⚠️ Market regime features (rate_regime, yield_curve_slope) - derived in notebooks

---

## Action Plan - Priority Order

### HIGH PRIORITY (Required for Phase 1 to run)

**1. Add fed_funds_rate column (15 minutes)**
```bash
# Run SQL script to add column and derive from rate_3m
databricks sql execute -f sql/01_add_fed_funds_rate_column.sql \
  --warehouse-id 4b9b953939869799
```

**2. Fix column name references (5 minutes)**
- Update notebooks: `account_number` → `account_num`
- File: notebooks/Train_PPNR_Models.py (already fixed)

**3. Add hardcoded competitive rates (10 minutes)**
- Already implemented in Phase 1 notebook
- No action required ✅

**Result after HIGH PRIORITY steps:**
- ✅ Phase 1 notebook can run (with derived/limited data)
- ⚠️ Phase 2-3 need more historical data

---

### MEDIUM PRIORITY (Required for Phases 2-3)

**4. Backfill 24 months of yield curves (2-3 hours)**

**Step 1: Get AlphaVantage API key**
- Sign up at https://www.alphavantage.co/support/#api-key
- Free tier: 25 calls/day (sufficient)

**Step 2: Set environment variable**
```bash
export ALPHAVANTAGE_API_KEY="your_key_here"
```

**Step 3: Run backfill script**
```bash
python3 scripts/backfill_yield_curves_alphavantage.py
```

**What this does:**
- Fetches Federal Funds Rate (1 API call)
- Fetches Treasury Yields: 3M, 2Y, 5Y, 10Y, 30Y (5 API calls)
- Total: 6 API calls
- Backfills from 2024-01-01 to present (~390 days)
- Upserts into yield_curves table

**Result after MEDIUM PRIORITY steps:**
- ✅ All 3 phase notebooks can run with full historical data
- ✅ Accurate cohort analysis (Phase 2)
- ✅ Stress testing calibration (Phase 3)

---

### LOW PRIORITY (Production enhancements)

**5. Schedule weekly yield curve updates**
```bash
# Create Databricks job to run every Monday 6am
# Script: scripts/weekly_yield_curve_update.py
```

**6. Monitor competitive rates**
- Integrate RateWatch API or DepositAccounts.com
- Update hardcoded rates quarterly

---

## Estimated Timeline

| Scenario | Time | Outcome |
|----------|------|---------|
| **MVP (Demo)** | 30 min | Phase 1 runs with derived data |
| **Production Ready** | 3-4 hours | All phases run with historical data |
| **Full Production** | 5-6 hours | Automated updates + monitoring |

---

## AlphaVantage Details

### Why AlphaVantage?

**Federal Funds Rate:**
- Not available in our current yield_curves table
- Required for rate regime classification (Low <2%, Medium 2-4%, High >4%)
- AlphaVantage provides via FRED API

**Historical Treasury Yields:**
- Current data: 27 days (insufficient)
- Required: 24+ months for model training
- AlphaVantage provides daily data since 2000

### API Endpoints Used

**1. Federal Funds Rate**
```
GET https://www.alphavantage.co/query
Parameters:
  function: FEDERAL_FUNDS_RATE
  apikey: YOUR_KEY

Response: Daily fed funds rate (effective rate)
```

**2. Treasury Yields**
```
GET https://www.alphavantage.co/query
Parameters:
  function: TREASURY_YIELD
  interval: daily
  maturity: 3month | 2year | 5year | 10year | 30year
  apikey: YOUR_KEY

Response: Daily treasury yields by maturity
```

### Cost Analysis

**Free Tier (Recommended for demo/MVP):**
- 25 API calls per day
- 5 calls per minute
- Cost: $0
- ✅ Sufficient for backfill (6 calls) + weekly updates (6 calls/week)

**Premium Tier (If needed for production):**
- 1200 API calls per day
- 75 calls per minute
- Cost: $49.99/month
- Only needed if requiring intraday real-time updates

---

## Schema Details

### yield_curves - Current Schema
```sql
date                   DATE
rate_3m                DOUBLE
rate_2y                DOUBLE
rate_5y                DOUBLE
rate_10y               DOUBLE
rate_30y               DOUBLE
ingestion_timestamp    TIMESTAMP
```

### yield_curves - After Adding fed_funds_rate
```sql
date                   DATE
fed_funds_rate         DOUBLE    -- ← NEW COLUMN
rate_3m                DOUBLE
rate_2y                DOUBLE
rate_5y                DOUBLE
rate_10y               DOUBLE
rate_30y               DOUBLE
ingestion_timestamp    TIMESTAMP
```

### deposit_accounts - Existing Columns Used
```sql
-- Core account data (already present)
account_id, customer_id, product_type, account_open_date
current_balance, average_balance_30d, average_balance_90d
stated_rate, beta, decay_rate
relationship_balance, has_online_banking, has_mobile_banking

-- Computed features (notebooks derive these)
product_count              -- COUNT per customer_id
relationship_length_years  -- DATEDIFF from account_open_date
relationship_score         -- Formula based on products/tenure/balance
relationship_category      -- Strategic/Tactical/Expendable classification
```

---

## Files Created

### Documentation
- ✅ `docs/Data_Requirements_Analysis.md` - Comprehensive 1,000+ line analysis
- ✅ `docs/DATA_REQUIREMENTS_SUMMARY.md` - This file (executive summary)

### SQL Scripts
- ✅ `sql/01_add_fed_funds_rate_column.sql` - Add fed_funds_rate to yield_curves

### Python Scripts
- ✅ `scripts/backfill_yield_curves_alphavantage.py` - AlphaVantage backfill script
- ✅ `check_data_requirements.py` - Analysis script (ran to generate findings)
- ✅ `analyze_schema_gaps.py` - Schema validation script

### Notebooks (Already Created)
- ✅ `notebooks/Approach1_Enhanced_Deposit_Beta_Model.py` - 853 lines
- ✅ `notebooks/Approach2_Vintage_Analysis_and_Decay_Modeling.py` - 892 lines
- ✅ `notebooks/Approach3_Dynamic_Beta_and_Stress_Testing.py` - Comprehensive

---

## Next Steps - Recommended Order

**For immediate MVP (30 min):**
1. Run `sql/01_add_fed_funds_rate_column.sql` to add derived fed_funds_rate
2. Test Phase 1 notebook (should work with limited data)

**For production deployment (3-4 hours):**
1. Get AlphaVantage API key (5 min)
2. Run `scripts/backfill_yield_curves_alphavantage.py` (30 min)
3. Test all 3 phase notebooks (2-3 hours including review)

**For ongoing production (ongoing):**
1. Schedule weekly AlphaVantage updates
2. Monitor competitive rates quarterly
3. Review model performance monthly

---

## Conclusion

**Summary:**
- ✅ Existing tables are mostly sufficient
- ⚠️ Need to enrich yield_curves with fed_funds_rate and historical data
- ✅ AlphaVantage API required (free tier sufficient)
- ✅ No new permanent tables needed (notebooks create ML tables)

**Critical Path:**
1. Add fed_funds_rate column (15 min) → Phase 1 works
2. Backfill historical data (2-3 hrs) → Phases 2-3 work
3. Schedule weekly updates (1 hr) → Production ready

**Total Time to Production: 3-4 hours**

---

## References

- Full Analysis: `docs/Data_Requirements_Analysis.md`
- Research Synthesis: `docs/Deposit_Beta_Modeling_Research_Synthesis.md`
- Implementation: `docs/Deposit_Modeling_Implementation_Summary.md`
- AlphaVantage API: https://www.alphavantage.co/documentation/
