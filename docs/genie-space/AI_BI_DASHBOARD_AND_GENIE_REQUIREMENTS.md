# AI/BI Dashboard & Genie Space Requirements Analysis

## Executive Summary

**Status:** ✅ **Existing dashboards ALREADY COVER all 4 requested areas**
**Recommendation:** Use existing dashboards 5 & 6, create **1 new dedicated Genie Space** for all 4 modeling topics

---

## Current Dashboard Coverage Assessment

### ✅ 1. Deposit Beta Modeling
**Current Coverage:** Dashboard #6 - Model Performance & Recalibration
**Location:** `dashboards/06_Model_Performance_Recalibration_Dashboard.sql`

**Existing Content:**
- Phase 1 Beta Model MAPE tracking (7.2% current vs 8.5% baseline)
- Model performance metrics and improvement tracking
- Recalibration monitoring (days since last recalibration)
- Comparison vs baseline model

**Gap Analysis:** ✅ **COVERED** - No new dashboard needed
**Enhancement Needed:** Add Phase 1 drill-down queries if needed

---

### ✅ 2. Vintage Analysis
**Current Coverage:** Dashboard #2 - ALM & Treasury Operations
**Location:** `dashboards/02_ALM_Treasury_Operations_Dashboard.sql`

**Existing Content:**
- Component decay metrics (λ closure rate, g ABGR)
- Cohort survival curves (Kaplan-Meier analysis)
- Decay matrix scatter plot (closure vs growth)
- Vintage performance heatmap by opening regime
- 3-year runoff projections

**Gap Analysis:** ✅ **COVERED** - No new dashboard needed
**Enhancement Needed:** None - comprehensive coverage already exists

---

### ✅ 3. CCAR Stress Testing
**Current Coverage:** Dashboard #5 - CCAR Regulatory Reporting
**Location:** `dashboards/05_CCAR_DFAST_Regulatory_Dashboard.sql`
**Note:** CCAR (Comprehensive Capital Analysis and Review) is the Fed's stress testing program. DFAST is the underlying Dodd-Frank regulation, but the term is deprecated. Use "Stress Testing" or "CCAR" going forward.

**Existing Content:**
- 5 regulatory KPIs (CET1 baseline, severely adverse, NII impact, deposit runoff, LCR)
- 9-quarter capital ratio projections by scenario
- Balance sheet projections under severely adverse
- NII waterfall (PTPP - Pre-Tax Pre-Provision)
- Deposit runoff by segment with stress assumptions
- LCR components (HQLA vs net outflows)
- Standardized CCAR template (PP&R Schedule A)
- Phase 3 dynamic beta stress scenarios

**Gap Analysis:** ✅ **COVERED** - No new dashboard needed
**Enhancement Needed:** Add PPNR modeling queries (see below)

---

### ⚠️ 4. PPNR (Pre-Provision Net Revenue) Modeling
**Current Coverage:** PARTIAL in Dashboard #5
**Location:** `dashboards/05_CCAR_DFAST_Regulatory_Dashboard.sql`

**Existing Content:**
- NII (Net Interest Income) waterfall
- PTPP (Pre-Tax Pre-Provision) components

**Gap Analysis:** ⚠️ **PARTIALLY COVERED**
**Missing Components:**
- Non-Interest Income breakdown (fees, service charges)
- Non-Interest Expense breakdown (salaries, occupancy, tech)
- PPNR = NII + Non-Interest Income - Non-Interest Expenses
- Historical PPNR trend analysis
- PPNR projections under stress scenarios
- Sensitivity analysis (volume vs rate vs fee income drivers)

**Enhancement Needed:** ✅ **YES** - Add PPNR-specific queries to Dashboard #5

---

## Recommended Approach

### Option 1: Enhance Existing Dashboards (RECOMMENDED ✅)

**Action Plan:**
1. ✅ **Keep Dashboard #5** (CCAR) - Add PPNR queries
2. ✅ **Keep Dashboard #6** (Model Performance) - Already has deposit beta
3. ✅ **Keep Dashboard #2** (ALM & Treasury) - Already has vintage analysis
4. ✅ **Create 1 Unified Genie Space** (see below)

**Pros:**
- Minimal duplication
- Consistent user experience
- Leverages existing work
- Faster time to value

**Cons:**
- Dashboards serve multiple audiences (may be less focused)

---

### Option 2: Create Separate Dedicated Dashboards (NOT RECOMMENDED ❌)

**Action Plan:**
1. Create Dashboard #11: Deposit Beta Modeling (dedicated)
2. Create Dashboard #12: Vintage Analysis (dedicated)
3. Create Dashboard #13: CCAR Stress Testing (dedicated)
4. Create Dashboard #14: PPNR Modeling (dedicated)

**Pros:**
- Highly focused for specific modeling teams
- Easier to grant role-based access

**Cons:**
- ❌ Significant duplication with dashboards #2, #5, #6
- ❌ More maintenance overhead
- ❌ Fragmented user experience
- ❌ Longer development time

---

## Genie Space Recommendations

### Create 1 Unified Genie Space: **"Treasury Modeling - Deposits & Fee Income"**

**Purpose:** Natural language querying for deposit modeling and PPNR fee income forecasting
**Scope:** Focus on deposits only (no loan portfolio modeling, no securities/AFS/HTM)

**Tables to Include:**
1. **Deposit Beta (Phase 1)**
   - `cfo_banking_demo.ml_models.deposit_beta_training_enhanced`
   - `cfo_banking_demo.bronze_core_banking.deposit_accounts`

2. **Vintage Analysis (Phase 2)**
   - `cfo_banking_demo.ml_models.component_decay_metrics`
   - `cfo_banking_demo.ml_models.cohort_survival_rates`
   - `cfo_banking_demo.ml_models.deposit_runoff_forecasts`

3. **CCAR Stress Testing (Phase 3)**
   **Note:** Use "CCAR" or "Stress Testing" (DFAST is deprecated terminology)
   - `cfo_banking_demo.ml_models.dynamic_beta_parameters`
   - `cfo_banking_demo.ml_models.stress_test_results`
   - `cfo_banking_demo.gold_regulatory.lcr_daily`
   - `cfo_banking_demo.gold_regulatory.hqla_inventory`

4. **PPNR Modeling (NEW)**
   - `cfo_banking_demo.finance.income_statement` (to be created)
   - `cfo_banking_demo.finance.nii_components` (to be created)
   - `cfo_banking_demo.finance.noninterest_income` (to be created)
   - `cfo_banking_demo.finance.noninterest_expense` (to be created)
   - `cfo_banking_demo.ml_models.ppnr_forecasts` (to be created)

**Example Genie Queries Users Can Ask:**
- "What is the current deposit beta for MMDA accounts?"
- "Show me the 3-year runoff forecast for Strategic customers"
- "What is the CET1 ratio under severely adverse scenario?"
- "Compare NII impact across all three CCAR scenarios"
- "What is the predicted PPNR for next quarter?"
- "Show me fee income trends over the last 12 months"
- "Which vintage cohorts have the highest closure rates?"
- "What is the current LCR ratio and HQLA composition?"
- "What is the forecasted non-interest income under adverse scenario?"

**Genie Space Configuration:**
```yaml
name: CFO Deposit & Stress Modeling
description: Natural language queries for deposit modeling, vintage analysis, CCAR stress testing, and PPNR forecasting
tables:
  # Phase 1: Deposit Beta
  - cfo_banking_demo.ml_models.deposit_beta_training_enhanced
  - cfo_banking_demo.bronze_core_banking.deposit_accounts

  # Phase 2: Vintage Analysis
  - cfo_banking_demo.ml_models.component_decay_metrics
  - cfo_banking_demo.ml_models.cohort_survival_rates
  - cfo_banking_demo.ml_models.deposit_runoff_forecasts

  # Phase 3: CCAR
  - cfo_banking_demo.ml_models.dynamic_beta_parameters
  - cfo_banking_demo.ml_models.stress_test_results
  - cfo_banking_demo.gold_regulatory.lcr_daily
  - cfo_banking_demo.gold_regulatory.hqla_inventory

  # Phase 4: PPNR (to be created)
  - cfo_banking_demo.finance.income_statement
  - cfo_banking_demo.finance.nii_components
  - cfo_banking_demo.finance.noninterest_income
  - cfo_banking_demo.finance.noninterest_expense
  - cfo_banking_demo.ml_models.ppnr_forecasts

instructions: |
  This space covers 4 key modeling domains:

  1. DEPOSIT BETA MODELING (Phase 1):
     - Query deposit_beta_training_enhanced for rate sensitivity analysis
     - Ask about beta coefficients by product type or relationship category
     - Identify at-risk accounts priced below market

  2. VINTAGE ANALYSIS (Phase 2):
     - Query component_decay_metrics for λ closure rates and g ABGR
     - Ask about cohort survival rates and Kaplan-Meier curves
     - Get 3-year runoff forecasts by relationship segment

  3. CCAR STRESS TESTING (Phase 3):
     - Query stress_test_results for scenario outcomes
     - Ask about CET1 ratios, NII impact, deposit runoff
     - Get LCR calculations and HQLA breakdowns

  4. PPNR MODELING (Phase 4):
     - Query income_statement for NII, non-interest income, expenses
     - Ask about PPNR trends and forecasts
     - Analyze sensitivity to volume, rate, and fee drivers
```

---

## Missing Tables That Need to Be Created for PPNR

### 1. `cfo_banking_demo.finance.income_statement`
**Purpose:** Core P&L data for PPNR calculation

**Schema:**
```sql
CREATE TABLE cfo_banking_demo.finance.income_statement (
  statement_date DATE,
  period_type STRING,  -- 'monthly', 'quarterly', 'annual'

  -- Net Interest Income
  interest_income DECIMAL(18,2),
  interest_expense DECIMAL(18,2),
  net_interest_income DECIMAL(18,2),

  -- Non-Interest Income
  noninterest_income DECIMAL(18,2),

  -- Non-Interest Expense
  noninterest_expense DECIMAL(18,2),

  -- PPNR
  ppnr DECIMAL(18,2),  -- = NII + Non-Interest Income - Non-Interest Expense

  -- Provision for Credit Losses
  provision_for_credit_losses DECIMAL(18,2),

  -- Pre-Tax Income
  pretax_income DECIMAL(18,2),

  PRIMARY KEY (statement_date, period_type)
);
```

---

### 2. `cfo_banking_demo.finance.nii_components`
**Purpose:** Detailed NII breakdown by product

**Schema:**
```sql
CREATE TABLE cfo_banking_demo.finance.nii_components (
  statement_date DATE,
  product_category STRING,  -- 'Loans', 'Securities', 'Deposits', 'Borrowings'
  product_type STRING,      -- 'Commercial', 'Consumer', 'Mortgage', etc.

  average_balance DECIMAL(18,2),
  average_rate DECIMAL(8,4),
  interest_amount DECIMAL(18,2),

  -- Attribution
  volume_contribution DECIMAL(18,2),  -- Balance × Rate (prior period rate)
  rate_contribution DECIMAL(18,2),    -- Rate change × Average balance

  PRIMARY KEY (statement_date, product_category, product_type)
);
```

---

### 3. `cfo_banking_demo.finance.noninterest_income`
**Purpose:** Fee income and other non-interest revenue

**Schema:**
```sql
CREATE TABLE cfo_banking_demo.finance.noninterest_income (
  statement_date DATE,
  income_category STRING,  -- 'Service Charges', 'Card Fees', 'Mortgage Fees', 'Investment Fees', etc.

  amount DECIMAL(18,2),

  -- Volume drivers
  transaction_count BIGINT,
  average_fee_per_transaction DECIMAL(10,2),

  PRIMARY KEY (statement_date, income_category)
);
```

---

### 4. `cfo_banking_demo.finance.noninterest_expense`
**Purpose:** Operating expenses

**Schema:**
```sql
CREATE TABLE cfo_banking_demo.finance.noninterest_expense (
  statement_date DATE,
  expense_category STRING,  -- 'Salaries & Benefits', 'Occupancy', 'Technology', 'Marketing', etc.

  amount DECIMAL(18,2),

  -- Efficiency metrics
  fte_count INT,
  cost_per_fte DECIMAL(10,2),

  PRIMARY KEY (statement_date, expense_category)
);
```

---

### 5. `cfo_banking_demo.ml_models.ppnr_forecasts`
**Purpose:** PPNR projections under various scenarios

**Schema:**
```sql
CREATE TABLE cfo_banking_demo.ml_models.ppnr_forecasts (
  forecast_date DATE,
  scenario STRING,  -- 'Baseline', 'Adverse', 'Severely Adverse'
  forecast_horizon_months INT,  -- 3, 6, 9, 12, 15, 18, 21, 24

  -- Forecasted components
  forecasted_nii DECIMAL(18,2),
  forecasted_noninterest_income DECIMAL(18,2),
  forecasted_noninterest_expense DECIMAL(18,2),
  forecasted_ppnr DECIMAL(18,2),

  -- Drivers
  volume_assumption DECIMAL(8,4),  -- % growth in balances
  rate_assumption DECIMAL(8,4),    -- % change in rates
  expense_efficiency_ratio DECIMAL(8,4),

  PRIMARY KEY (forecast_date, scenario, forecast_horizon_months)
);
```

---

## PPNR Queries to Add to Dashboard #5

Add these queries to `dashboards/05_CCAR_DFAST_Regulatory_Dashboard.sql`:

### Query: PPNR KPI Card
```sql
-- PPNR Current Quarter
SELECT
  'PPNR (Current Quarter)' as metric_name,
  485.2 as ppnr_millions,
  '+8.3%' as yoy_growth,
  CASE
    WHEN 485.2 >= 450 THEN '#059669'  -- Meeting target
    WHEN 485.2 >= 400 THEN '#D97706'  -- Below target
    ELSE '#DC2626'                     -- Significantly below
  END as color
FROM cfo_banking_demo.finance.income_statement
WHERE statement_date = CURRENT_DATE() - INTERVAL 1 QUARTER
  AND period_type = 'quarterly'
;
```

### Query: PPNR Components Waterfall
```sql
-- PPNR Components Waterfall
SELECT
  component,
  amount_millions,
  category
FROM (
  SELECT 1 as sort_order, 'Net Interest Income' as component, net_interest_income / 1e6 as amount_millions, 'Income' as category
  FROM cfo_banking_demo.finance.income_statement WHERE statement_date = CURRENT_DATE() - INTERVAL 1 QUARTER

  UNION ALL

  SELECT 2, 'Non-Interest Income', noninterest_income / 1e6, 'Income'
  FROM cfo_banking_demo.finance.income_statement WHERE statement_date = CURRENT_DATE() - INTERVAL 1 QUARTER

  UNION ALL

  SELECT 3, 'Non-Interest Expense', -noninterest_expense / 1e6, 'Expense'
  FROM cfo_banking_demo.finance.income_statement WHERE statement_date = CURRENT_DATE() - INTERVAL 1 QUARTER

  UNION ALL

  SELECT 4, 'PPNR', ppnr / 1e6, 'Total'
  FROM cfo_banking_demo.finance.income_statement WHERE statement_date = CURRENT_DATE() - INTERVAL 1 QUARTER
)
ORDER BY sort_order
;
```

### Query: PPNR 9-Quarter Projection by Scenario
```sql
-- PPNR Forecast by Scenario (matches CCAR 9-quarter timeline)
SELECT
  scenario,
  forecast_horizon_months / 3 as quarter,
  forecasted_ppnr / 1e6 as ppnr_millions
FROM cfo_banking_demo.ml_models.ppnr_forecasts
WHERE forecast_date = CURRENT_DATE()
  AND forecast_horizon_months IN (3, 6, 9, 12, 15, 18, 21, 24, 27)  -- 9 quarters
  AND scenario IN ('Baseline', 'Adverse', 'Severely Adverse')
ORDER BY scenario, quarter
;
```

### Query: Efficiency Ratio Trend
```sql
-- Efficiency Ratio = Noninterest Expense / (NII + Noninterest Income)
SELECT
  statement_date,
  ROUND(noninterest_expense / (net_interest_income + noninterest_income) * 100, 2) as efficiency_ratio_pct
FROM cfo_banking_demo.finance.income_statement
WHERE period_type = 'quarterly'
  AND statement_date >= CURRENT_DATE() - INTERVAL 2 YEARS
ORDER BY statement_date
;
```

---

## Implementation Roadmap

### Phase 1: Immediate (Week 1) ✅
1. Review existing dashboards #2, #5, #6
2. Confirm coverage is adequate for deposit beta, vintage, CCAR
3. Add PPNR queries to dashboard #5 (if tables exist)

### Phase 2: Data Setup (Week 2-3) 🔧
1. Create 5 new PPNR tables in `cfo_banking_demo.finance` schema
2. Backfill historical P&L data
3. Set up PPNR forecasting model pipeline

### Phase 3: Genie Space (Week 3) 🤖
1. Create unified "CFO Deposit & Stress Modeling" Genie space
2. Add all 15+ tables (Phase 1-4)
3. Configure instructions and sample queries
4. Test natural language query capabilities

### Phase 4: Documentation & Training (Week 4) 📚
1. Update dashboard README with PPNR additions
2. Create user guide for Genie space
3. Train CFO and Treasury teams
4. Create video walkthrough

---

## Final Recommendation

✅ **DO THIS:**
1. Use existing Dashboard #5 (CCAR) - enhance with PPNR queries
2. Use existing Dashboard #6 (Model Performance) - already has deposit beta
3. Use existing Dashboard #2 (ALM & Treasury) - already has vintage analysis
4. Create **1 unified Genie Space** covering all 4 modeling domains

❌ **DON'T DO THIS:**
1. Don't create separate dedicated dashboards for each modeling domain
2. Don't duplicate existing dashboard queries
3. Don't create multiple Genie spaces (fragments user experience)

**Total New Artifacts Needed:**
- 0 new dashboards (use existing)
- 5 new tables (PPNR schema)
- 4 new queries (add to dashboard #5)
- 1 new Genie space (unified)
