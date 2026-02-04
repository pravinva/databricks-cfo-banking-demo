# PPNR Tables Status & Next Steps

## Current State Analysis ✅

### Good News: Most PPNR Infrastructure Already Exists!

**What Already Exists:**
1. ✅ **Train_PPNR_Models.py** notebook (generates PPNR model data)
2. ✅ **ml_models.non_interest_income_training_data** table
3. ✅ **ml_models.non_interest_expense_training_data** table
4. ✅ **ml_models.ppnr_forecasts** table

**What's Missing:**
- ❌ P&L statement aggregation tables (income_statement, nii_components, etc.)
- ❌ `gold_finance` schema is incomplete (exists but may not have all P&L tables)

---

## Data Flow: How PPNR Data is Generated

```
┌─────────────────────────────────────────────────────────────────┐
│  Source: Historical Data                                         │
├─────────────────────────────────────────────────────────────────┤
│  • bronze_core_banking.deposit_accounts_historical              │
│  • bronze_core_banking.loan_portfolio_historical                │
│  • External market data (GDP, unemployment, etc.)               │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  Train_PPNR_Models.py Notebook                                   │
├─────────────────────────────────────────────────────────────────┤
│  1. Creates training datasets:                                   │
│     • ml_models.non_interest_income_training_data               │
│     • ml_models.non_interest_expense_training_data              │
│                                                                   │
│  2. Trains ML models:                                            │
│     • XGBoost for non-interest income forecasting               │
│     • XGBoost for non-interest expense forecasting              │
│                                                                   │
│  3. Generates forecasts:                                         │
│     • ml_models.ppnr_forecasts (9-quarter projections)          │
│       - Baseline scenario                                        │
│       - Adverse scenario                                         │
│       - Severely Adverse scenario                                │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  Dashboard #5: CCAR/DFAST Regulatory Dashboard                   │
├─────────────────────────────────────────────────────────────────┤
│  Queries ml_models.ppnr_forecasts for:                          │
│  • PPNR KPI cards                                                │
│  • 9-quarter projections by scenario                             │
│  • PPNR components waterfall                                     │
│  • Efficiency ratio trends                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Missing P&L Tables (Optional Enhancement)

For complete P&L reporting, you could create these additional tables:

### 1. `gold_finance.income_statement`
**Purpose:** Core P&L aggregation
**Generated From:** GL transactions + calculated metrics

```sql
CREATE TABLE cfo_banking_demo.gold_finance.income_statement (
  statement_date DATE,
  period_type STRING,  -- 'monthly', 'quarterly', 'annual'

  -- Net Interest Income (from GL or calculated)
  interest_income DECIMAL(18,2),
  interest_expense DECIMAL(18,2),
  net_interest_income DECIMAL(18,2),

  -- Non-Interest Income (from ML model predictions)
  noninterest_income DECIMAL(18,2),

  -- Non-Interest Expense (from ML model predictions)
  noninterest_expense DECIMAL(18,2),

  -- PPNR = NII + Non-Interest Income - Non-Interest Expense
  ppnr DECIMAL(18,2),

  -- Provision for Credit Losses
  provision_for_credit_losses DECIMAL(18,2),

  -- Pre-Tax Income
  pretax_income DECIMAL(18,2),

  PRIMARY KEY (statement_date, period_type)
);
```

### 2. `gold_finance.nii_components`
**Purpose:** Detailed NII breakdown
**Generated From:** Loan/deposit portfolio historical data

### 3. `gold_finance.noninterest_income_actuals`
**Purpose:** Actual fee income by category
**Generated From:** GL transactions

### 4. `gold_finance.noninterest_expense_actuals`
**Purpose:** Actual operating expenses
**Generated From:** GL transactions

---

## Recommended Approach

### Option A: Use Existing Tables Only (RECOMMENDED ✅)

**What to do:**
1. ✅ Use existing `ml_models.ppnr_forecasts` for PPNR projections
2. ✅ Add PPNR queries to Dashboard #5 (I've provided 4 queries in the requirements doc)
3. ✅ Create Genie Space with existing tables

**Pros:**
- ✅ Zero development time - tables already exist!
- ✅ Data already generated by Train_PPNR_Models.py notebook
- ✅ Sufficient for CCAR/DFAST stress testing requirements

**Cons:**
- ⚠️ Missing granular P&L details (fee income by category, expense by department)
- ⚠️ Missing actuals vs forecast comparison

---

### Option B: Create Full P&L Tables (Optional Enhancement)

**What to do:**
1. Create `gold_finance.income_statement` table
2. Create `gold_finance.nii_components` table
3. Create `gold_finance.noninterest_income_actuals` table
4. Create `gold_finance.noninterest_expense_actuals` table
5. Build ETL pipeline to populate from GL transactions

**Pros:**
- Complete P&L reporting capability
- Actuals vs forecast variance analysis
- Granular drill-down by category

**Cons:**
- ❌ Requires building ETL pipeline
- ❌ 1-2 weeks development time
- ❌ May not have historical GL transaction data

---

## Decision: GO WITH OPTION A ✅

**Rationale:**
1. You already have PPNR forecasts in `ml_models.ppnr_forecasts`
2. Train_PPNR_Models.py notebook already generates the data
3. Sufficient for CCAR/DFAST regulatory requirements
4. Can add full P&L tables later if needed

---

## Next Steps (Immediate Action Items)

### Step 1: Verify Existing PPNR Data ✅
Run this query to check if ppnr_forecasts table has data:

```sql
SELECT
  scenario,
  COUNT(*) as row_count,
  MIN(forecast_date) as min_date,
  MAX(forecast_date) as max_date,
  COUNT(DISTINCT forecast_horizon_months) as quarters
FROM cfo_banking_demo.ml_models.ppnr_forecasts
GROUP BY scenario
```

**Expected Result:**
- 3 scenarios (Baseline, Adverse, Severely Adverse)
- 9 quarters per scenario (3, 6, 9, 12, 15, 18, 21, 24, 27 months)
- Recent forecast_date

---

### Step 2: Add PPNR Queries to Dashboard #5 🔧

Add these 4 queries to `dashboards/05_CCAR_DFAST_Regulatory_Dashboard.sql`:

#### Query 1: PPNR KPI Card
```sql
-- PPNR Current Quarter KPI
SELECT
  'PPNR (Current Quarter)' as metric_name,
  forecasted_ppnr / 1e6 as ppnr_millions,
  scenario,
  forecast_horizon_months / 3 as quarter
FROM cfo_banking_demo.ml_models.ppnr_forecasts
WHERE forecast_date = (SELECT MAX(forecast_date) FROM cfo_banking_demo.ml_models.ppnr_forecasts)
  AND scenario = 'Baseline'
  AND forecast_horizon_months = 3  -- Current quarter
```

#### Query 2: PPNR Components Waterfall
```sql
-- PPNR Components Waterfall (Baseline, Q1)
SELECT
  component,
  amount_millions,
  category
FROM (
  SELECT 1 as sort_order, 'Net Interest Income' as component,
         forecasted_nii / 1e6 as amount_millions, 'Income' as category
  FROM cfo_banking_demo.ml_models.ppnr_forecasts
  WHERE scenario = 'Baseline' AND forecast_horizon_months = 3

  UNION ALL

  SELECT 2, 'Non-Interest Income',
         forecasted_noninterest_income / 1e6, 'Income'
  FROM cfo_banking_demo.ml_models.ppnr_forecasts
  WHERE scenario = 'Baseline' AND forecast_horizon_months = 3

  UNION ALL

  SELECT 3, 'Non-Interest Expense',
         -forecasted_noninterest_expense / 1e6, 'Expense'
  FROM cfo_banking_demo.ml_models.ppnr_forecasts
  WHERE scenario = 'Baseline' AND forecast_horizon_months = 3

  UNION ALL

  SELECT 4, 'PPNR',
         forecasted_ppnr / 1e6, 'Total'
  FROM cfo_banking_demo.ml_models.ppnr_forecasts
  WHERE scenario = 'Baseline' AND forecast_horizon_months = 3
)
ORDER BY sort_order
```

#### Query 3: PPNR 9-Quarter Projection by Scenario
```sql
-- PPNR Forecast by Scenario (9 quarters for CCAR)
SELECT
  scenario,
  forecast_horizon_months / 3 as quarter,
  forecasted_ppnr / 1e6 as ppnr_millions,
  forecasted_nii / 1e6 as nii_millions,
  forecasted_noninterest_income / 1e6 as nonii_millions,
  forecasted_noninterest_expense / 1e6 as nie_millions
FROM cfo_banking_demo.ml_models.ppnr_forecasts
WHERE forecast_date = (SELECT MAX(forecast_date) FROM cfo_banking_demo.ml_models.ppnr_forecasts)
  AND forecast_horizon_months IN (3, 6, 9, 12, 15, 18, 21, 24, 27)  -- 9 quarters
  AND scenario IN ('Baseline', 'Adverse', 'Severely Adverse')
ORDER BY scenario, quarter
```

#### Query 4: Efficiency Ratio Projection
```sql
-- Efficiency Ratio = Noninterest Expense / (NII + Noninterest Income)
SELECT
  scenario,
  forecast_horizon_months / 3 as quarter,
  ROUND(forecasted_noninterest_expense /
        (forecasted_nii + forecasted_noninterest_income) * 100, 2)
    as efficiency_ratio_pct
FROM cfo_banking_demo.ml_models.ppnr_forecasts
WHERE forecast_date = (SELECT MAX(forecast_date) FROM cfo_banking_demo.ml_models.ppnr_forecasts)
  AND scenario = 'Baseline'
ORDER BY quarter
```

---

### Step 3: Create Genie Space 🤖

Use the configuration from `AI_BI_DASHBOARD_AND_GENIE_REQUIREMENTS.md`:

**Tables to include:**
1. Deposit Beta: `ml_models.deposit_beta_training_enhanced`
2. Vintage Analysis: `ml_models.component_decay_metrics`, `cohort_survival_rates`, `deposit_runoff_forecasts`
3. CCAR/DFAST: `ml_models.dynamic_beta_parameters`, `stress_test_results`, `gold_regulatory.lcr_daily`
4. **PPNR**: `ml_models.ppnr_forecasts` ✅ (already exists!)

---

## Summary

### ✅ What You Already Have:
- Train_PPNR_Models.py notebook
- ml_models.non_interest_income_training_data
- ml_models.non_interest_expense_training_data
- **ml_models.ppnr_forecasts** (this is the key table!)

### 🔧 What You Need to Do:
1. Add 4 PPNR queries to Dashboard #5
2. Create unified Genie Space with PPNR tables included

### ❌ What You DON'T Need:
- Don't create new `finance.income_statement` table (ppnr_forecasts is sufficient)
- Don't create new ETL pipelines (Train_PPNR_Models.py already does this)
- Don't create separate PPNR dashboard (use existing Dashboard #5)

### 📊 Expected Outcome:
- Dashboard #5 will show PPNR KPIs, 9-quarter projections, components waterfall
- Genie Space will allow natural language queries like "What is the forecasted PPNR for next quarter under adverse scenario?"
- Total development time: **2-3 hours** (just adding queries and Genie config)

---

## File Locations

**Notebook:** `/notebooks/Train_PPNR_Models.py`
**Dashboard to Update:** `/dashboards/05_CCAR_DFAST_Regulatory_Dashboard.sql`
**Requirements Doc:** `/dashboards/AI_BI_DASHBOARD_AND_GENIE_REQUIREMENTS.md`
**Existing Tables:**
- `cfo_banking_demo.ml_models.ppnr_forecasts`
- `cfo_banking_demo.ml_models.non_interest_income_training_data`
- `cfo_banking_demo.ml_models.non_interest_expense_training_data`
