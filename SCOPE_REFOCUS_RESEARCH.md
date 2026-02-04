# Scope Refocus Research: Treasury Modeling with Databricks

## Directive from Nehal Bharodia (Feb 4, 2026)

**Key Changes Requested:**
1. **Focus on Deposits ONLY** - Remove loan modeling from scope
2. **Remove Securities** - AFS (Available-For-Sale) and HTM (Held-To-Maturity) are out of scope
3. **New Positioning:** "Treasury Modeling with Databricks"
   - Focus Area 1: Deposit Modeling
   - Focus Area 2: PPNR - Fee Income Modeling

---

## Current State Analysis

### What Currently Includes Loans (TO BE REMOVED/DE-EMPHASIZED)

#### 1. **Backend System Prompt** (`backend/claude_agent.py`)
**Lines 79-80, 100-101, 122-127, 181-183, 191-194, 203-205:**
- Tool descriptions mention "loan_portfolio" table
- Bronze Layer documentation includes loan portfolio
- Portfolio Analysis section shows loan portfolio
- Credit Risk section based on loan_portfolio
- Recent Activity section shows recent loan originations

**Action Required:** Update system prompt to de-emphasize loans, focus on deposits

#### 2. **PPNR Training Notebook** (`notebooks/Train_PPNR_Models.py`)
**Lines 66-77, 91-94:**
- Includes `loan_metrics` CTE that aggregates loan data
- Uses loan portfolio historical data for feature engineering
- Joins loan metrics with deposit metrics for fee income prediction

**Action Required:** Document that loans are used ONLY for calculating fee income drivers (e.g., origination fees, servicing fees), not for loan modeling itself

#### 3. **Genie Space Configuration** (`GENIE_SPACE_CONFIGURATION.md`)
**Throughout document:**
- Current name: "CFO Deposit & Stress Modeling" (OK)
- Does not include loan tables (GOOD)
- But descriptions mention loans in PPNR context

**Action Required:** Clarify that loan data is used only for fee income calculation, not loan modeling

#### 4. **Frontend Components**
**Multiple files:**
- `frontend_app/components/tables/LoanTable.tsx` - Loan-specific UI component
- `frontend_app/components/panels/LoanDetailPanel.tsx` - Loan detail panel
- `frontend_app/app/page.tsx` - Main dashboard includes loan portfolio section

**Action Required:** Document that loan UI components can be hidden or repositioned as "fee income sources" rather than "loan portfolio analysis"

---

### What Currently Includes Securities (TO BE REMOVED)

#### 1. **Backend System Prompt** (`backend/claude_agent.py`)
**Lines 79-80, 131-133:**
- Tool descriptions mention "securities_portfolio" table
- Silver Layer documentation includes securities portfolio with AFS/HTM
- Lists available tables including securities_portfolio

**Action Required:** Remove securities references from system prompt

#### 2. **Genie Space Configuration** (`GENIE_SPACE_CONFIGURATION.md`)
**Current state:**
- Does NOT include securities tables (GOOD - no changes needed)
- No references to AFS/HTM in Genie instructions

**Action Required:** None - already correctly scoped

#### 3. **Frontend Components**
**Files checked:**
- `frontend_app/app/page.tsx` - May include securities portfolio section

**Action Required:** Document that securities section should be hidden/removed from Treasury demo

---

## Phase 1, 2, 3 Models - Detailed Breakdown

### Phase 1: Deposit Beta Model (Rate Sensitivity)
**Table:** `ml_models.deposit_beta_training_enhanced`
**Model Type:** XGBoost with 40+ features
**Accuracy:** MAPE 7.2% (41% improvement over baseline)

**What It Does:**
- Predicts deposit beta coefficient (0-1 scale) for each deposit account
- Higher beta = more rate sensitive (e.g., 0.8 means 80% of rate changes pass through)
- Categorizes customers: Strategic (0.2-0.4), Tactical (0.4-0.7), Expendable (0.7-0.9)

**Use Cases:**
- Rate shock analysis: "If Fed raises rates 100 bps, how much deposit runoff?"
- Pricing strategy: Identify accounts that need rate increases to retain
- Customer retention: Flag at-risk accounts priced below market

**Demo Focus:** ✅ KEEP - Core deposit modeling

---

### Phase 2: Vintage Analysis (Cohort Decay Model)
**Tables:**
- `ml_models.component_decay_metrics` - λ closure rates and g (ABGR)
- `ml_models.cohort_survival_rates` - Kaplan-Meier survival curves
- `ml_models.deposit_runoff_forecasts` - 3-year projections

**Model Type:** Chen Component Decay Model + Kaplan-Meier statistical analysis

**Formula:** D(t+1) = D(t) × (1-λ) × (1+g)
- λ (lambda) = Account closure rate per period
- g (ABGR) = Average Balance Growth Rate for remaining accounts

**What It Does:**
- Tracks deposit cohorts over time (accounts opened in same period)
- Separates account attrition (closures) from balance changes (growth/shrinkage)
- Forecasts long-term deposit runoff by relationship category

**Use Cases:**
- Long-term liquidity planning: "How much deposit funding in 3 years?"
- Vintage performance: "Which opening regimes produced sticky deposits?"
- Relationship analysis: Strategic customers have 5% λ, Expendable have 25% λ

**Demo Focus:** ✅ KEEP - Core deposit modeling

---

### Phase 3: CCAR Stress Testing (Regulatory Scenarios)
**Tables:**
- `ml_models.dynamic_beta_parameters` - Sigmoid function coefficients
- `ml_models.stress_test_results` - 9-quarter capital projections

**Model Type:** Dynamic Beta Model with rate-dependent response curves

**Formula:** β(Rm) = β_min + (β_max - β_min) / [1 + exp(-k*(Rm-R0))]
- β_min = Minimum beta at very low rates
- β_max = Maximum beta at very high rates
- k = Steepness of sigmoid curve
- R0 = Inflection point (rate at which beta response changes most rapidly)

**What It Does:**
- Models how deposit beta changes with market rate environment
- Runs 9-quarter projections under 3 regulatory scenarios:
  - Baseline (0 bps rate shock)
  - Adverse (+200 bps rate shock)
  - Severely Adverse (+300 bps rate shock)
- Calculates CET1 capital ratio, NII impact, deposit runoff, LCR

**Regulatory Context:**
- **CCAR** = Comprehensive Capital Analysis and Review (Federal Reserve requirement)
- **DFAST** = Dodd-Frank Act Stress Testing (the regulation behind CCAR, but term is deprecated)
- "Stress Testing" is the broader term - CCAR is the specific Fed program

**Use Cases:**
- Regulatory compliance: Pass/fail determination (CET1 ≥ 7.0%)
- Capital planning: How much capital needed under severely adverse?
- Risk management: Understand deposit behavior in crisis scenarios

**Demo Focus:** ✅ KEEP - Core deposit stress testing

---

## What Should REMAIN (Core Focus Areas)

### ✅ Focus Area 1: Deposit Modeling

**Phase 1: Deposit Beta (Rate Sensitivity)**
- Table: `ml_models.deposit_beta_training_enhanced`
- Purpose: Predict deposit runoff based on rate changes
- Use Cases: Rate shock analysis, pricing strategy, customer retention
- **KEEP AS-IS** - Core deposit modeling

**Phase 2: Vintage Analysis (Cohort Decay)**
- Tables: `ml_models.component_decay_metrics`, `cohort_survival_rates`, `deposit_runoff_forecasts`
- Purpose: Long-term deposit runoff forecasting by vintage cohort
- Chen Component Decay Model: D(t+1) = D(t) × (1-λ) × (1+g)
- **KEEP AS-IS** - Core deposit modeling

**Phase 3: CCAR Stress Testing**
- Tables: `ml_models.dynamic_beta_parameters`, `stress_test_results`
- Purpose: Regulatory stress testing with dynamic beta curves for CCAR (Comprehensive Capital Analysis and Review)
- Regulatory Context: CCAR is mandated by Dodd-Frank Act (formerly called DFAST, but that term is now deprecated)
- **KEEP AS-IS** - Core deposit modeling under stress scenarios

---

### ✅ Focus Area 2: PPNR - Fee Income Modeling

**PPNR Components:**
1. **Net Interest Income (NII)** - Interest earned on deposits (and loans)
   - **Deposit Side:** Interest paid on deposits (expense)
   - **Loan Side:** Interest earned on loans (revenue) - ONLY as a driver for NII calculation

2. **Non-Interest Income** - Fee revenue
   - Service charges on deposit accounts
   - Card interchange fees
   - Wealth management fees
   - Investment banking fees
   - Mortgage origination/servicing fees (derived from loan activity but focus is on FEE income)

3. **Non-Interest Expense** - Operating costs
   - Salaries & benefits
   - Occupancy costs
   - Technology expenses
   - Marketing costs

**Key Tables:**
- `ml_models.ppnr_forecasts` - 9-quarter PPNR projections
- `ml_models.non_interest_income_training_data` - Fee income training data
- `ml_models.non_interest_expense_training_data` - Operating expense training data

**How Loans Fit (CLARIFICATION NEEDED):**
- Loans are NOT being modeled for credit risk, loan portfolio management, etc.
- Loans ARE used as a data source to calculate:
  - Origination fee income (when new loans are originated)
  - Servicing fee income (ongoing)
  - Mortgage-related fee income
- **Positioning:** "Fee income driven by banking activity" not "loan portfolio modeling"

---

## Recommended Documentation Updates

### 1. **Update Genie Space Name & Description**

**Current:**
```
Name: CFO Deposit & Stress Modeling
Description: Natural language queries for deposit modeling, vintage analysis, CCAR/DFAST stress testing, and PPNR forecasting
```

**Recommended:**
```
Name: Treasury Modeling - Deposits & Fee Income
Description: Natural language queries for deposit modeling (beta, vintage, CCAR stress testing) and PPNR fee income forecasting. Focus on deposit rate sensitivity, runoff forecasting, and non-interest income projections.

Note: CCAR (Comprehensive Capital Analysis and Review) is the Federal Reserve's stress testing program. DFAST is the underlying Dodd-Frank regulation, but the term is deprecated. Use "Stress Testing" as the general term.
```

---

### 2. **Update Backend System Prompt** (`backend/claude_agent.py`)

**Changes Needed:**

**Line 79-80 - Tool Description:**
```python
# BEFORE:
"description": "SQL query to execute. Must be a SELECT statement. Available tables include loan_portfolio, deposit_accounts, securities_portfolio, yield_curves, deposit_runoff_predictions, lcr_daily, hqla_inventory."

# AFTER:
"description": "SQL query to execute. Must be a SELECT statement. Available tables include deposit_accounts, deposit_runoff_predictions, lcr_daily, hqla_inventory, yield_curves, ppnr_forecasts, non_interest_income_training_data."
```

**Line 99-101 - Capabilities:**
```python
# BEFORE:
- **Portfolio Analysis**: Provide comprehensive views of securities, loans, and deposits

# AFTER:
- **Portfolio Analysis**: Provide comprehensive views of deposits and PPNR components
```

**Line 122-133 - Bronze/Silver Layer:**
```python
# BEFORE (remove loan_portfolio, securities_portfolio):
### Bronze Layer (Core Banking Data)
- **bronze_core_banking.loan_portfolio**: Raw loan data
- **bronze_core_banking.deposit_accounts**: Raw deposit data

### Silver Layer (Treasury & Market Data)
- **silver_treasury.securities_portfolio**: Securities holdings
- **silver_treasury.yield_curves**: Historical yield curve data

# AFTER (focus on deposits):
### Bronze Layer (Core Banking Data)
- **bronze_core_banking.deposit_accounts**: Raw deposit data
  - Columns: account_id, customer_id, current_balance, product_type (MMDA/DDA/NOW/Savings), account_status, open_date
- **bronze_core_banking.deposit_accounts_historical**: Historical deposit snapshots for vintage analysis

### Silver Layer (Treasury & Market Data)
- **silver_treasury.yield_curves**: Historical yield curve data
  - Columns: date, rate_3m, rate_2y, rate_5y, rate_10y, rate_30y
```

**Line 179-187 - Portfolio Analysis Section:**
```python
# BEFORE:
### 1. Portfolio Analysis
**Data Sources:**
- **Loan Portfolio**: cfo_banking_demo.bronze_core_banking.loan_portfolio
  - Query: GROUP BY product_type, aggregate current_balance, interest_rate, cecl_reserve
  - Shows: Breakdown by Commercial, Consumer, Mortgage, etc.
- **Deposit Portfolio**: cfo_banking_demo.bronze_core_banking.deposit_accounts
  - Query: GROUP BY product_type, aggregate current_balance, stated_rate
  - Shows: Breakdown by MMDA, DDA, NOW, Savings

# AFTER:
### 1. Deposit Portfolio Analysis
**Data Sources:**
- **Deposit Portfolio**: cfo_banking_demo.bronze_core_banking.deposit_accounts
  - Query: GROUP BY product_type, aggregate current_balance, stated_rate
  - Shows: Breakdown by MMDA, DDA, NOW, Savings
- **Deposit Rate Sensitivity**: cfo_banking_demo.ml_models.deposit_beta_training_enhanced
  - Query: GROUP BY product_type, AVG(predicted_beta), COUNT(*) as accounts
  - Shows: Beta distribution by product type
```

**Line 189-199 - Risk Analysis Section:**
```python
# BEFORE:
### 2. Risk Analysis
**Data Sources:**
- **Credit Risk by Product**: cfo_banking_demo.bronze_core_banking.loan_portfolio
  - Metrics: NPL rate (days_past_due > 90), CECL reserves, reserve ratio
  - Query: GROUP BY product_type, calculate NPL%, reserve_billions, reserve_ratio%
- **Rate Shock Stress**: call_deposit_beta_model tool with 100 bps shock

# AFTER:
### 2. Deposit Risk Analysis
**Data Sources:**
- **Rate Shock Stress Testing**: call_deposit_beta_model tool with 100 bps shock
  - Shows: Deposit runoff by product type (MMDA, DDA, NOW, Savings)
  - Displays: Beta coefficients, runoff amounts, runoff percentages
- **Deposit Runoff Forecasts**: cfo_banking_demo.ml_models.deposit_runoff_forecasts
  - Query: GROUP BY relationship_category, forecast_horizon_months
  - Shows: 3-year runoff projections by Strategic/Tactical/Expendable segments
```

**Line 201-206 - Recent Activity Section:**
```python
# BEFORE:
### 3. Recent Activity
**Data Sources:**
- **Recent Loan Originations**: cfo_banking_demo.bronze_core_banking.loan_portfolio
  - Query: WHERE is_current = true, ORDER BY origination_date DESC, LIMIT 10
  - Shows: Latest loan transactions with product type, amount, date

# AFTER:
### 3. Recent Deposit Activity
**Data Sources:**
- **Recent Deposit Account Openings**: cfo_banking_demo.bronze_core_banking.deposit_accounts
  - Query: WHERE is_current = true, ORDER BY account_open_date DESC, LIMIT 10
  - Shows: Latest deposit accounts with product type, balance, opening date
```

---

### 3. **Update PPNR Documentation**

**File:** `PPNR_STATUS_AND_NEXT_STEPS.md`

**Add Clarification Section:**
```markdown
## PPNR Modeling Scope Clarification

**What PPNR Includes:**
1. **Net Interest Income (NII)** - Interest margin from deposit and loan portfolios
   - NOTE: Loan data is used ONLY to calculate NII, not for loan portfolio modeling
   - Focus is on deposit-driven interest expense and net margin analysis

2. **Non-Interest Income (Fee Revenue)** - PRIMARY FOCUS
   - Service charges on deposit accounts
   - Card interchange fees
   - Wealth management fees
   - Investment banking fees
   - Mortgage origination/servicing fees (fee income only, not loan modeling)

3. **Non-Interest Expense (Operating Costs)** - SECONDARY FOCUS
   - Salaries & benefits
   - Occupancy costs
   - Technology expenses
   - Marketing costs

**What PPNR Does NOT Include:**
- ❌ Loan portfolio credit risk modeling
- ❌ Loan loss provisioning (CECL modeling)
- ❌ Securities portfolio modeling (AFS/HTM)
- ❌ Investment portfolio management

**Key Message:**
"PPNR modeling in this demo focuses on FEE INCOME forecasting driven by deposit relationships and banking activity. Loan data is used ONLY as a source for calculating origination and servicing fee income, not for comprehensive loan portfolio analysis."
```

---

### 4. **Update Genie Space Instructions**

**File:** `GENIE_SPACE_CONFIGURATION.md`

**Update Section 4 (PPNR Modeling):**
```markdown
### 4. PPNR MODELING (Focus on Fee Income)

**What is PPNR?**
Pre-Provision Net Revenue = Net Interest Income + Non-Interest Income - Non-Interest Expense

**This Genie Space Focuses On:**
- **Non-Interest Income (Fee Revenue)** - PRIMARY FOCUS
  - Service charges on deposits
  - Card interchange fees
  - Wealth management fees
  - Banking activity-driven fee income

- **Non-Interest Expense (Operating Costs)** - SECONDARY FOCUS
  - Salaries, occupancy, technology costs

- **Net Interest Income (NII)** - Contextual
  - Interest margin analysis (deposit-focused)
  - NOTE: Loan data used only for NII calculation, not loan modeling

**Out of Scope:**
- Loan portfolio credit risk modeling
- Loan loss provisioning (CECL)
- Securities portfolio modeling (AFS/HTM)

**Sample Queries:**
- "What is the forecasted non-interest income for next quarter?"
- "Show me fee income trends by category over the last 12 months"
- "What is the predicted PPNR under adverse scenario?"
- "Compare service charge income across deposit product types"
```

---

### 5. **Update Quick Start Guide**

**File:** `QUICK_START_GENIE.md`

**Update Title and Description:**
```markdown
# Quick Start: Create Treasury Modeling Genie Space in 5 Minutes

## TL;DR
Create a Genie Space for **Treasury Modeling** focused on:
1. **Deposit Modeling** - Rate sensitivity, vintage analysis, stress testing
2. **PPNR Fee Income Modeling** - Non-interest income forecasting

Everything is ready. Just follow these 6 steps.

---

## What This Genie Space Covers

**✅ IN SCOPE:**
- Deposit Beta Modeling (Phase 1) - Rate sensitivity analysis
- Vintage Analysis (Phase 2) - Cohort-based runoff forecasting
- CCAR/DFAST Stress Testing (Phase 3) - Regulatory scenarios
- PPNR Fee Income Modeling (Phase 4) - Non-interest income projections

**❌ OUT OF SCOPE:**
- Loan portfolio credit risk modeling
- Securities portfolio modeling (AFS/HTM)
- Loan loss provisioning (CECL)

**NOTE:** Loan data is used ONLY for calculating fee income drivers (origination fees, servicing fees), not for loan portfolio analysis.
```

---

### 6. **Frontend UI Updates (Documentation Only)**

**File to Create:** `TREASURY_DEMO_UI_UPDATES.md`

```markdown
# Treasury Demo UI Updates

## Sections to Hide/Remove

### 1. Portfolio Analysis Tab
**Current:** Shows 3 sections - Loans, Deposits, Securities
**Recommended:** Show ONLY Deposits section
- Hide "Loan Portfolio" card
- Hide "Securities Portfolio" card
- Expand "Deposit Portfolio" to full width

### 2. Risk Analysis Tab
**Current:** Shows Credit Risk (loans) + Rate Shock Stress (deposits) + LCR
**Recommended:** Show ONLY deposit-related risk
- Hide "Credit Risk by Product" (loan NPL rates)
- Keep "Rate Shock Stress Testing" (deposits)
- Keep "LCR Stress Test" (liquidity risk)

### 3. Recent Activity Tab
**Current:** Shows Recent Loan Originations
**Recommended:** Replace with Recent Deposit Activity
- Show recent deposit account openings
- Show recent large deposit inflows/outflows
- Show recent rate changes on deposit products

### 4. Main Dashboard
**Current:** 6 sections including loan and securities references
**Recommended:** Rename to "Treasury Dashboard"
- Section 1: "Deposit Portfolio Overview" (not "Portfolio Analysis")
- Section 2: "Deposit Risk Analysis" (not "Risk Analysis")
- Section 3: "Recent Deposit Activity" (not "Recent Activity")
- Section 4: Deposit Beta (Phase 1) - NO CHANGES
- Section 5: Vintage Analysis (Phase 2) - NO CHANGES
- Section 6: CCAR Stress Testing + PPNR (Phase 3 & 4) - Add PPNR Fee Income focus
  - Use "CCAR" or "Stress Testing" (not "DFAST" which is deprecated)

## New Naming Convention

**Before:** "CFO Banking Demo"
**After:** "Treasury Modeling Demo - Deposits & Fee Income"

**Before:** "Portfolio Analysis"
**After:** "Deposit Portfolio Analysis"

**Before:** "Risk Analysis"
**After:** "Deposit & Liquidity Risk"

**Before:** "CCAR/DFAST Stress Testing"
**After:** "CCAR Stress Testing + PPNR Fee Income"

**Note:** DFAST (Dodd-Frank Act Stress Testing) is the regulation behind CCAR, but the term "DFAST" is deprecated. Use "Stress Testing" as the broader term, and "CCAR" for the specific Federal Reserve program.
```

---

## Summary of Required Updates

### 🔴 HIGH PRIORITY (Core Documentation)

1. **backend/claude_agent.py** - Update system prompt
   - Remove loan_portfolio and securities_portfolio references
   - Focus on deposit-centric language
   - Update dashboard section descriptions

2. **GENIE_SPACE_CONFIGURATION.md** - Update Genie instructions
   - Add PPNR fee income clarification
   - Remove loan/securities emphasis
   - Update sample queries

3. **PPNR_STATUS_AND_NEXT_STEPS.md** - Add scope clarification
   - Explain loan data usage (fee income only)
   - Clarify what's in scope vs out of scope

### 🟡 MEDIUM PRIORITY (User-Facing Documentation)

4. **QUICK_START_GENIE.md** - Update quick start guide
   - Change title to "Treasury Modeling"
   - Add scope clarification

5. **GENIE_SPACE_IMPLEMENTATION_SUMMARY.md** - Update summary
   - Change positioning to "Treasury Modeling"
   - Update example queries

### 🟢 LOW PRIORITY (Frontend UI - Documentation Only)

6. **Create TREASURY_DEMO_UI_UPDATES.md** - Document UI changes
   - List sections to hide/remove
   - Suggest new naming conventions
   - No actual code changes (just documentation)

---

## Key Messaging

**Old Positioning:**
"CFO Banking Demo with Deposit Modeling, Vintage Analysis, CCAR/DFAST, and PPNR"

**New Positioning:**
"Treasury Modeling with Databricks - Focus on Deposit Modeling and PPNR Fee Income Forecasting"

**Elevator Pitch:**
"Demonstrate how Databricks enables comprehensive treasury modeling for deposit portfolios and fee income forecasting. Use ML-based deposit beta models, vintage cohort analysis, CCAR/DFAST stress testing, and PPNR projections to optimize deposit pricing, manage liquidity risk, and forecast non-interest income."

**What's Different:**
- Deposit-first narrative (not loan portfolio management)
- Fee income forecasting (not loan credit risk)
- Treasury operations (not comprehensive CFO analytics)
- Exclude securities portfolio (AFS/HTM out of scope)

---

## Files That DO NOT Need Changes

✅ **notebooks/Batch_Inference_Deposit_Beta_Model.py** - 100% deposit-focused, perfect scope
✅ **notebooks/Train_PPNR_Models.py** - Loan data usage is appropriate for fee income calculation
✅ **ml_models.ppnr_forecasts** - Table is correctly scoped
✅ **ml_models.deposit_beta_training_enhanced** - Deposit-focused, no changes needed
✅ **All Phase 2 Vintage Analysis tables** - Deposit-focused, no changes needed
✅ **All Phase 3 CCAR tables** - Appropriate for stress testing

---

**Document Created:** February 4, 2026
**Status:** Research Complete - Ready for Documentation Updates
