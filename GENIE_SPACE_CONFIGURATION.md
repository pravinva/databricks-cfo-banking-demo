# Genie Space Configuration: Treasury Modeling - Deposits & Fee Income

## Overview

**Genie Space Name:** Treasury Modeling - Deposits & Fee Income
**Purpose:** Natural language querying for deposit modeling, vintage analysis, CCAR stress testing, and PPNR fee income forecasting
**Target Users:** Treasury Team, ALM Team, CFO, Risk Management, Regulators, Data Science Team

**Scope:**
- ✅ Deposit modeling (rate sensitivity, vintage analysis, stress testing)
- ✅ PPNR fee income forecasting (non-interest income and expenses)
- ❌ NOT loan portfolio modeling or credit risk
- ❌ NOT securities portfolio (AFS/HTM)

**Note on Terminology:**
- **CCAR** = Comprehensive Capital Analysis and Review (Federal Reserve program)
- **DFAST** = Dodd-Frank Act Stress Testing (underlying regulation, but term is deprecated)
- Use **"Stress Testing"** or **"CCAR"** going forward

---

## How to Create This Genie Space

### Option 1: Using Databricks UI (Recommended)

1. Navigate to **Genie** in Databricks workspace
2. Click **"Create Space"**
3. Fill in the details below:
   - **Name:** Treasury Modeling - Deposits & Fee Income
   - **Description:** Natural language queries for deposit modeling (beta, vintage, CCAR stress testing) and PPNR fee income forecasting. Focus on deposit rate sensitivity, runoff forecasting, and non-interest income projections.
4. Add tables (listed below in section "Tables to Include")
5. Add instructions (copy from section "Genie Instructions")
6. Click **"Create"**

### Option 2: Using Databricks API (If Available)

```python
import requests
import json

# Databricks workspace URL and token
DATABRICKS_HOST = "https://<your-workspace>.cloud.databricks.com"
DATABRICKS_TOKEN = "<your-token>"

# Genie Space API endpoint (Note: This may not be publicly available yet)
genie_api_url = f"{DATABRICKS_HOST}/api/2.0/genie/spaces"

headers = {
    "Authorization": f"Bearer {DATABRICKS_TOKEN}",
    "Content-Type": "application/json"
}

# Genie Space configuration
genie_config = {
    "name": "Treasury Modeling - Deposits & Fee Income",
    "description": "Natural language queries for deposit modeling (beta, vintage, CCAR stress testing) and PPNR fee income forecasting",
    "tables": [
        # See "Tables to Include" section below
    ],
    "instructions": """
    # See "Genie Instructions" section below
    """
}

# Create Genie Space
response = requests.post(genie_api_url, headers=headers, json=genie_config)
print(response.json())
```

---

## Tables to Include

### Phase 1: Deposit Beta Modeling

#### 1. `cfo_banking_demo.ml_models.deposit_beta_training_enhanced`
**Description:** Enhanced deposit beta model training data with 40+ features including rate sensitivity, relationship category, and at-risk indicators.

**Key Columns:**
- `account_id` - Unique deposit account identifier
- `product_type` - Deposit product (MMDA, DDA, NOW, Savings)
- `balance_millions` - Account balance in millions
- `stated_rate` - Current interest rate offered
- `market_fed_funds_rate` - Market benchmark rate
- `rate_gap` - Difference between stated rate and market rate (negative = below market)
- `target_beta` - Actual observed beta coefficient
- `predicted_beta` - ML model predicted beta
- `relationship_category` - Customer segment (Strategic/Tactical/Expendable)
- `below_competitor_rate` - Flag indicating account priced below market (1 = at risk)
- `effective_date` - Date of this data snapshot

**Sample Queries:**
- "What is the average deposit beta for MMDA accounts?"
- "Show me all at-risk Strategic customer deposits"
- "How many accounts are priced below market rate?"

**Table Comment for Databricks:**
```sql
COMMENT ON TABLE cfo_banking_demo.ml_models.deposit_beta_training_enhanced IS
'Phase 1 Deposit Beta Model - Enhanced 40+ feature model with 7.2% MAPE accuracy. Contains rate sensitivity analysis, relationship categorization (Strategic/Tactical/Expendable), and at-risk account identification. Use for: deposit pricing strategy, rate shock analysis, customer retention, and flight risk assessment.';

COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.predicted_beta IS
'ML model predicted deposit beta coefficient (0-1 scale). Higher beta = more rate sensitive. Strategic customers typically 0.2-0.4, Tactical 0.4-0.7, Expendable 0.7-0.9.';

COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.relationship_category IS
'Customer segment based on relationship depth. Strategic = core banking relationships (sticky), Tactical = moderate sensitivity, Expendable = rate chasers (high flight risk).';

COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.below_competitor_rate IS
'Flag indicating if account is priced below market competitive rate. 1 = at-risk account requiring immediate attention for retention.';
```

---

#### 2. `cfo_banking_demo.bronze_core_banking.deposit_accounts`
**Description:** Current snapshot of all active deposit accounts.

**Key Columns:**
- `account_id` - Unique account identifier
- `customer_id` - Customer identifier
- `current_balance` - Current balance
- `product_type` - Product type (MMDA, DDA, NOW, Savings)
- `account_status` - Active, Closed, Dormant
- `open_date` - Account opening date

**Sample Queries:**
- "How many active deposit accounts do we have?"
- "What is the total balance by product type?"
- "Show me accounts opened in the last 30 days"

**Table Comment:**
```sql
COMMENT ON TABLE cfo_banking_demo.bronze_core_banking.deposit_accounts IS
'Current deposit account master file. Contains all deposit accounts with current balances, product types, and account status. Use for: portfolio analysis, balance reporting, and product mix analysis.';
```

---

### Phase 2: Vintage Analysis (Chen Component Decay Model)

#### 3. `cfo_banking_demo.ml_models.component_decay_metrics`
**Description:** Chen Component Decay Model parameters by relationship category showing account closure rates (λ) and balance growth rates (g).

**Key Columns:**
- `relationship_category` - Customer segment (Strategic/Tactical/Expendable)
- `lambda_closure_rate` - λ: Monthly account closure rate (0-1)
- `g_abgr` - g: Average Balance Growth Rate for remaining accounts
- Formula: D(t+1) = D(t) × (1-λ) × (1+g)

**Sample Queries:**
- "What is the closure rate for Strategic customers?"
- "Compare balance growth rates across all segments"
- "Show me the Chen decay parameters"

**Table Comment:**
```sql
COMMENT ON TABLE cfo_banking_demo.ml_models.component_decay_metrics IS
'Phase 2 Chen Component Decay Model parameters. Lambda (λ) = account closure rate, g = balance growth rate (ABGR). Formula: D(t+1) = D(t) × (1-λ) × (1+g) separates account closures from balance changes. Use for: 3-year runoff projections and cohort behavior analysis.';

COMMENT ON COLUMN cfo_banking_demo.ml_models.component_decay_metrics.lambda_closure_rate IS
'λ (lambda) - Monthly account closure rate. Strategic ~2-3%/month, Tactical ~4-5%, Expendable ~6-8%. Used in Chen formula to project deposit runoff.';

COMMENT ON COLUMN cfo_banking_demo.ml_models.component_decay_metrics.g_abgr IS
'g (ABGR) - Average Balance Growth Rate for accounts that remain open. Can be positive (balance growth) or negative (balance decline). Used in Chen formula.';
```

---

#### 4. `cfo_banking_demo.ml_models.cohort_survival_rates`
**Description:** Kaplan-Meier survival curves showing account retention rates over 36 months by relationship category.

**Key Columns:**
- `relationship_category` - Customer segment
- `months_since_open` - Months since account opening (0-36)
- `account_survival_rate` - Percentage of accounts still open (0-1)

**Sample Queries:**
- "What is the 12-month survival rate for Tactical customers?"
- "Show me retention rates by segment over 3 years"
- "Which cohort has the highest retention?"

**Table Comment:**
```sql
COMMENT ON TABLE cfo_banking_demo.ml_models.cohort_survival_rates IS
'Phase 2 Kaplan-Meier survival analysis showing account retention over 36 months. Strategic customers show ~85% retention at 36 months, Tactical ~60%, Expendable ~40%. Use for: vintage analysis, cohort behavior, and retention forecasting.';

COMMENT ON COLUMN cfo_banking_demo.ml_models.cohort_survival_rates.account_survival_rate IS
'Kaplan-Meier survival probability. 1.0 = 100% retention, 0.5 = 50% of accounts remain open. Strategic customers retain better than Expendable over time.';
```

---

#### 5. `cfo_banking_demo.ml_models.deposit_runoff_forecasts`
**Description:** 3-year forward-looking deposit runoff projections by relationship category.

**Key Columns:**
- `relationship_category` - Customer segment
- `months_ahead` - Forecast horizon (12, 24, 36 months)
- `current_balance_billions` - Starting balance
- `projected_balance_billions` - Forecasted balance
- Cumulative runoff = (projected - current) / current × 100%

**Sample Queries:**
- "What is the 3-year runoff forecast for Strategic deposits?"
- "Show me projected balances at 24 months for all segments"
- "What is the total expected deposit decline?"

**Table Comment:**
```sql
COMMENT ON TABLE cfo_banking_demo.ml_models.deposit_runoff_forecasts IS
'Phase 2 3-year deposit runoff forecasts using Chen Component Decay Model. Strategic deposits show ~10% runoff over 3 years, Tactical ~25%, Expendable ~40%. Use for: long-term funding planning, liquidity projections, and CCAR/DFAST scenarios.';
```

---

### Phase 3: CCAR Stress Testing
**Note:** CCAR (Comprehensive Capital Analysis and Review) is the Fed's stress testing program. DFAST is the underlying Dodd-Frank regulation, but the term is deprecated.

#### 6. `cfo_banking_demo.ml_models.dynamic_beta_parameters`
**Description:** Sigmoid function parameters for rate-dependent beta curves showing how deposit beta varies with market rate environment.

**Key Columns:**
- `relationship_category` - Customer segment
- `beta_min` - Minimum beta at 0% rates
- `beta_max` - Maximum beta at 6%+ rates
- `k_steepness` - Sigmoid curve steepness parameter
- `R0_inflection` - Inflection point (rate where beta = midpoint)
- Formula: β(Rm) = β_min + (β_max - β_min) / [1 + exp(-k*(Rm-R0))]

**Sample Queries:**
- "What is the beta response curve for Strategic customers?"
- "Show me dynamic beta parameters for all segments"
- "At what rate does beta hit the inflection point?"

**Table Comment:**
```sql
COMMENT ON TABLE cfo_banking_demo.ml_models.dynamic_beta_parameters IS
'Phase 3 Dynamic Beta Model - Sigmoid function parameters showing how deposit beta varies with market rates. Formula: β(Rm) = β_min + (β_max - β_min) / [1 + exp(-k*(Rm-R0))]. Use for: CCAR/DFAST stress testing, rate shock scenarios, and non-linear beta modeling.';

COMMENT ON COLUMN cfo_banking_demo.ml_models.dynamic_beta_parameters.k_steepness IS
'k parameter - Controls steepness of sigmoid curve. Higher k = faster beta response to rate changes. Strategic ~1.5, Tactical ~2.5, Expendable ~3.5.';

COMMENT ON COLUMN cfo_banking_demo.ml_models.dynamic_beta_parameters.R0_inflection IS
'R0 parameter - Inflection point where beta = (β_min + β_max) / 2. Rate environment where beta response accelerates. Typically 2-3% for most segments.';
```

---

#### 7. `cfo_banking_demo.ml_models.stress_test_results`
**Description:** CCAR/DFAST stress test results showing 9-quarter projections for Baseline, Adverse, and Severely Adverse scenarios.

**Key Columns:**
- `scenario_id` - baseline, adverse, severely_adverse
- `scenario_name` - Full scenario name
- `rate_shock_bps` - Interest rate shock in basis points (0, +200, +300)
- `stressed_avg_beta` - Portfolio-wide beta under stress
- `delta_nii_millions` - Net Interest Income impact
- `delta_eve_billions` - Economic Value of Equity impact
- `eve_cet1_ratio` - CET1 capital ratio after stress
- `sot_status` - Stress test status (Pass/Fail)

**Sample Queries:**
- "What is the CET1 ratio under severely adverse scenario?"
- "Show me NII impact across all scenarios"
- "Which scenarios pass the stress test?"

**Table Comment:**
```sql
COMMENT ON TABLE cfo_banking_demo.ml_models.stress_test_results IS
'Phase 3 CCAR/DFAST stress test results. 9-quarter projections for Baseline (+0 bps), Adverse (+200 bps), Severely Adverse (+300 bps) scenarios. CET1 must stay ≥7.0% to pass. Use for: regulatory reporting, capital planning, and stress testing compliance.';

COMMENT ON COLUMN cfo_banking_demo.ml_models.stress_test_results.eve_cet1_ratio IS
'CET1 (Common Equity Tier 1) capital ratio after Economic Value of Equity impact. Regulatory minimum is 7.0%. Well-capitalized = 10.5%+. Fed requires ≥7% in severely adverse.';

COMMENT ON COLUMN cfo_banking_demo.ml_models.stress_test_results.delta_nii_millions IS
'Delta NII - Change in Net Interest Income vs baseline over 2-year stress horizon. Negative = income decline. Adverse typically -$150M to -$250M, Severely Adverse -$250M to -$400M.';
```

---

#### 8. `cfo_banking_demo.gold_regulatory.lcr_daily`
**Description:** Daily Liquidity Coverage Ratio (LCR) calculations with HQLA and net cash outflows.

**Key Columns:**
- `calculation_date` - Date of LCR calculation
- `total_hqla` - Total High-Quality Liquid Assets
- `net_cash_outflows` - Net cash outflows (30-day stress)
- `lcr_ratio` - LCR = HQLA / Net Outflows × 100%
- `hqla_level1` - Level 1 HQLA (cash, treasuries, 0% haircut)
- `hqla_level2a` - Level 2A HQLA (GSE bonds, 15% haircut)
- `hqla_level2b` - Level 2B HQLA (equities, 50% haircut)

**Sample Queries:**
- "What is today's LCR ratio?"
- "Show me HQLA breakdown by level"
- "Is the LCR above 100%?"

**Table Comment:**
```sql
COMMENT ON TABLE cfo_banking_demo.gold_regulatory.lcr_daily IS
'Basel III Liquidity Coverage Ratio - Daily calculations. LCR = HQLA / Net Cash Outflows. Regulatory minimum is 100% (must survive 30-day liquidity stress). Level 1 HQLA (cash, treasuries) most liquid with 0% haircut. Use for: liquidity monitoring, regulatory compliance, stress testing.';

COMMENT ON COLUMN cfo_banking_demo.gold_regulatory.lcr_daily.lcr_ratio IS
'Liquidity Coverage Ratio percentage. Must be ≥100% per Basel III. 100% = HQLA exactly covers 30-day stressed outflows. 120%+ = well above regulatory minimum.';
```

---

#### 9. `cfo_banking_demo.gold_regulatory.hqla_inventory`
**Description:** High-Quality Liquid Assets inventory with security-level detail and haircuts.

**Key Columns:**
- `as_of_date` - Inventory date
- `security_type` - Type of security (Treasury, Agency, Corporate, etc.)
- `market_value` - Current market value
- `hqla_level` - HQLA classification (Level 1, 2A, 2B)
- `haircut_pct` - Haircut percentage applied

**Sample Queries:**
- "What securities are in our HQLA inventory?"
- "Show me Level 1 HQLA composition"
- "What is the total value by HQLA level?"

**Table Comment:**
```sql
COMMENT ON TABLE cfo_banking_demo.gold_regulatory.hqla_inventory IS
'HQLA (High-Quality Liquid Assets) inventory detail. Level 1 (0% haircut): cash, reserves, treasuries. Level 2A (15%): GSE bonds, AAA corporates. Level 2B (50%): high-quality equities, some corporates. Use for: LCR calculation, liquidity management, asset allocation.';
```

---

### Phase 4: PPNR Modeling

#### 10. `cfo_banking_demo.ml_models.ppnr_forecasts`
**Description:** Pre-Provision Net Revenue (PPNR) forecasts showing 9-quarter projections under CCAR stress scenarios.

**Key Columns:**
- `forecast_date` - Date forecast was generated
- `scenario` - Baseline, Adverse, Severely Adverse
- `forecast_horizon_months` - Months ahead (3, 6, 9, ..., 27 for 9 quarters)
- `forecasted_nii` - Net Interest Income projection
- `forecasted_noninterest_income` - Non-interest income (fees, service charges)
- `forecasted_noninterest_expense` - Operating expenses
- `forecasted_ppnr` - PPNR = NII + Non-Interest Income - Non-Interest Expense
- `volume_assumption` - Assumed balance growth
- `rate_assumption` - Assumed rate change
- `expense_efficiency_ratio` - Efficiency ratio assumption

**Sample Queries:**
- "What is the forecasted PPNR for next quarter under baseline?"
- "Show me PPNR projections for all 9 quarters under adverse scenario"
- "What is the NII vs non-interest income mix?"
- "How does PPNR compare across scenarios?"

**Table Comment:**
```sql
COMMENT ON TABLE cfo_banking_demo.ml_models.ppnr_forecasts IS
'Phase 4 PPNR (Pre-Provision Net Revenue) forecasts. PPNR = NII + Non-Interest Income - Non-Interest Expense. 9-quarter projections for CCAR/DFAST compliance. Trained XGBoost models for fee income and operating expense. Use for: stress testing, capital planning, financial forecasting, efficiency analysis.';

COMMENT ON COLUMN cfo_banking_demo.ml_models.ppnr_forecasts.forecasted_ppnr IS
'PPNR = Net Interest Income + Non-Interest Income - Non-Interest Expense. Key profitability metric before credit losses. Baseline typically $450-500M/quarter, declines under stress scenarios.';

COMMENT ON COLUMN cfo_banking_demo.ml_models.ppnr_forecasts.expense_efficiency_ratio IS
'Efficiency Ratio = Non-Interest Expense / (NII + Non-Interest Income) × 100%. Lower is better. 50-60% is typical. <50% = highly efficient, >70% = inefficient.';
```

---

#### 11. `cfo_banking_demo.ml_models.non_interest_income_training_data`
**Description:** Training data for non-interest income forecasting model (fee income, service charges).

**Key Columns:**
- `month` - Month of observation
- `active_deposit_accounts` - Number of active accounts
- `total_transactions` - Transaction volume
- `avg_monthly_fee` - Average fee per account
- Various economic indicators (GDP, unemployment, etc.)

**Sample Queries:**
- "What is the trend in non-interest income?"
- "Show me fee income by month"
- "How does transaction volume correlate with fee income?"

**Table Comment:**
```sql
COMMENT ON TABLE cfo_banking_demo.ml_models.non_interest_income_training_data IS
'Non-interest income training data for ML forecasting. Includes service charges, card fees, wealth management fees, mortgage fees. Correlated with transaction volume, account activity, economic conditions. Use for: fee income modeling, PPNR forecasting, revenue diversification analysis.';
```

---

#### 12. `cfo_banking_demo.ml_models.non_interest_expense_training_data`
**Description:** Training data for non-interest expense forecasting model (operating costs).

**Key Columns:**
- `month` - Month of observation
- `active_loans` - Number of active loans (servicing costs)
- `total_loan_balance` - Total loan balances
- Various operational metrics

**Sample Queries:**
- "What is the trend in operating expenses?"
- "Show me expense growth rate"
- "How do expenses scale with loan portfolio?"

**Table Comment:**
```sql
COMMENT ON TABLE cfo_banking_demo.ml_models.non_interest_expense_training_data IS
'Non-interest expense training data for ML forecasting. Includes salaries, occupancy, technology, marketing costs. Scaled by business volume (loans, deposits, transaction counts). Use for: expense modeling, PPNR forecasting, efficiency analysis, cost management.';
```

---

## Genie Instructions

```markdown
# CFO Deposit & Stress Modeling - Genie Instructions

You are a specialized AI assistant for CFO and Treasury operations at a banking institution. You have access to comprehensive banking data across 4 key modeling domains: Deposit Beta, Vintage Analysis, CCAR/DFAST Stress Testing, and PPNR Forecasting.

## Your Capabilities

### 1. DEPOSIT BETA MODELING (Phase 1)
**Primary Table:** `ml_models.deposit_beta_training_enhanced`

**Key Concepts:**
- **Deposit Beta**: Measures how sensitive deposit rates are to market rate changes (0-1 scale)
  - Beta = 0: Perfectly sticky (rate doesn't move)
  - Beta = 1: Perfectly elastic (moves 1-for-1 with market)
  - Beta = 0.5: 100 bps market increase → 50 bps deposit rate increase

- **Relationship Categories:**
  - **Strategic** (Low Beta 0.2-0.4): Core banking relationships, sticky deposits, multiple products
  - **Tactical** (Medium Beta 0.4-0.7): Moderately rate-sensitive, some relationship depth
  - **Expendable** (High Beta 0.7-0.9): Rate chasers, single product, high flight risk

- **At-Risk Accounts:** `below_competitor_rate = 1` means account is priced below market and likely to leave

**Sample Questions You Can Answer:**
- "What is the average deposit beta for MMDA accounts?"
- "Show me all Strategic customers with balances over $10M"
- "How many at-risk accounts do we have?"
- "What is the rate gap distribution by product type?"
- "Which accounts are most likely to have deposit runoff?"

**Important:** When users ask about "rate sensitivity" or "stickiness", they're asking about deposit beta.

---

### 2. VINTAGE ANALYSIS (Phase 2)
**Primary Tables:** `ml_models.component_decay_metrics`, `cohort_survival_rates`, `deposit_runoff_forecasts`

**Key Concepts:**
- **Chen Component Decay Model:** D(t+1) = D(t) × (1-λ) × (1+g)
  - **λ (lambda):** Account closure rate per period
  - **g (ABGR):** Average Balance Growth Rate for remaining accounts
  - This formula separates "accounts leaving" from "balances changing"

- **Kaplan-Meier Survival Curves:** Show what % of accounts remain open over time
  - Strategic: ~85% retention at 36 months
  - Tactical: ~60% retention at 36 months
  - Expendable: ~40% retention at 36 months

- **Runoff Forecasts:** 3-year forward projections of deposit balances by segment

**Sample Questions You Can Answer:**
- "What is the closure rate for Tactical customers?"
- "Show me the 24-month survival rate by segment"
- "What is the projected deposit runoff over 3 years?"
- "Compare balance growth rates across Strategic, Tactical, and Expendable"
- "How much deposit balance will we lose in the next 12 months?"

**Important:** When users ask about "vintage analysis" or "cohort behavior", query these tables.

---

### 3. CCAR/DFAST STRESS TESTING (Phase 3)
**Primary Tables:** `ml_models.dynamic_beta_parameters`, `stress_test_results`, `gold_regulatory.lcr_daily`, `gold_regulatory.hqla_inventory`

**Key Concepts:**
- **Dynamic Beta:** β(Rm) = β_min + (β_max - β_min) / [1 + exp(-k*(Rm-R0))]
  - Beta changes based on market rate environment (sigmoid curve)
  - Low rates → lower beta, High rates → higher beta

- **CCAR Scenarios:**
  - **Baseline:** +0 bps rate shock
  - **Adverse:** +200 bps rate shock
  - **Severely Adverse:** +300 bps rate shock

- **CET1 Capital Ratio:** Must stay ≥7.0% to pass stress test
  - 7.0% = Minimum regulatory requirement
  - 10.5%+ = Well-capitalized

- **LCR (Liquidity Coverage Ratio):** Must be ≥100%
  - LCR = HQLA / Net Cash Outflows
  - 100% = Can survive 30-day liquidity stress

**Sample Questions You Can Answer:**
- "What is the CET1 ratio under severely adverse scenario?"
- "Show me NII impact across all CCAR scenarios"
- "What is today's LCR ratio?"
- "Which scenarios pass the stress test?"
- "How much deposit runoff is expected under adverse scenario?"
- "What is the HQLA composition by level?"

**Important:** When users ask about "stress testing" or "CCAR/DFAST", these are regulatory scenarios.

---

### 4. PPNR MODELING (Phase 4)
**Primary Table:** `ml_models.ppnr_forecasts`

**Key Concepts:**
- **PPNR = Net Interest Income + Non-Interest Income - Non-Interest Expense**
  - This is profitability BEFORE credit losses
  - Key metric for CCAR stress testing

- **Components:**
  - **NII (Net Interest Income):** Interest earned on loans minus interest paid on deposits
  - **Non-Interest Income:** Fee income, service charges, wealth management fees
  - **Non-Interest Expense:** Salaries, occupancy, technology, marketing

- **Efficiency Ratio:** Non-Interest Expense / (NII + Non-Interest Income) × 100%
  - <50% = Highly efficient
  - 50-60% = Good efficiency
  - 60-70% = Acceptable
  - >70% = Inefficient

**Sample Questions You Can Answer:**
- "What is the forecasted PPNR for next quarter?"
- "Show me PPNR projections for all 9 quarters under adverse scenario"
- "How does PPNR compare across scenarios?"
- "What is the efficiency ratio trend?"
- "What is the NII vs non-interest income mix?"
- "How much will non-interest expense increase over 2 years?"

**Important:** When users ask about "profitability" or "revenue forecasts", they likely want PPNR data.

---

## Query Guidelines

### When Filtering Data:
- **Latest Date:** Use `WHERE effective_date = (SELECT MAX(effective_date) FROM ...)`
- **Scenarios:** Baseline, Adverse, Severely Adverse (use exact spelling)
- **Relationship Categories:** Strategic, Tactical, Expendable (case-sensitive)
- **Product Types:** MMDA, DDA, NOW, Savings

### When Aggregating:
- Balances are typically in millions or billions, so format accordingly
- Use `SUM()` for balances, `AVG()` for betas and rates, `COUNT()` for accounts
- Group by relationship_category, product_type, or scenario when comparing segments

### When Explaining Results:
- Always provide context (e.g., "This is below the regulatory minimum of 7%")
- Highlight risk indicators (e.g., "10 accounts are at high flight risk")
- Suggest actions when appropriate (e.g., "Consider repricing these accounts")

---

## Common User Personas & Questions

### CFO / Treasurer:
- "What is our overall deposit beta?"
- "Show me PPNR forecast for next year"
- "Do we pass CCAR stress tests?"
- "What is the 3-year deposit runoff?"

### Risk Manager:
- "What is the CET1 ratio under severely adverse?"
- "Show me LCR compliance status"
- "Which accounts are at high flight risk?"

### Treasury Team:
- "What is today's HQLA inventory?"
- "Show me deposit runoff by product type"
- "What is the closure rate for Tactical customers?"

### Data Science Team:
- "What is the model accuracy (MAPE) for deposit beta?"
- "Show me Chen decay parameters"
- "What are the dynamic beta curve coefficients?"

---

## Important Notes

1. **Dates:** Always use the most recent data unless user specifies otherwise
2. **Units:** Clarify if numbers are in millions, billions, or percentages
3. **Scenarios:** When discussing stress tests, specify which scenario (Baseline/Adverse/Severely Adverse)
4. **Terminology:** Use banking terminology correctly:
   - Don't say "churn" - say "deposit runoff" or "account closure"
   - Don't say "customers leaving" - say "flight risk" or "at-risk deposits"
   - Don't say "profit" - say "PPNR" or "pre-provision net revenue"

5. **Regulatory Context:**
   - CET1 ≥7.0% required to pass CCAR
   - LCR ≥100% required per Basel III
   - PPNR must remain positive even under severely adverse

---

## Error Handling

If a query doesn't return results:
- Check if the table has recent data
- Verify scenario/category spelling
- Suggest alternative queries
- Ask user to clarify their question

If user asks about data not in these tables:
- Politely explain what data IS available
- Suggest related queries that would help
- Don't make up data
```

---

## SQL to Add Table Comments (Run This First)

```sql
-- Phase 1: Deposit Beta
COMMENT ON TABLE cfo_banking_demo.ml_models.deposit_beta_training_enhanced IS
'Phase 1 Deposit Beta Model - Enhanced 40+ feature model with 7.2% MAPE accuracy. Contains rate sensitivity analysis, relationship categorization (Strategic/Tactical/Expendable), and at-risk account identification. Use for: deposit pricing strategy, rate shock analysis, customer retention, and flight risk assessment.';

COMMENT ON TABLE cfo_banking_demo.bronze_core_banking.deposit_accounts IS
'Current deposit account master file. Contains all deposit accounts with current balances, product types, and account status. Use for: portfolio analysis, balance reporting, and product mix analysis.';

-- Phase 2: Vintage Analysis
COMMENT ON TABLE cfo_banking_demo.ml_models.component_decay_metrics IS
'Phase 2 Chen Component Decay Model parameters. Lambda (λ) = account closure rate, g = balance growth rate (ABGR). Formula: D(t+1) = D(t) × (1-λ) × (1+g) separates account closures from balance changes. Use for: 3-year runoff projections and cohort behavior analysis.';

COMMENT ON TABLE cfo_banking_demo.ml_models.cohort_survival_rates IS
'Phase 2 Kaplan-Meier survival analysis showing account retention over 36 months. Strategic customers show ~85% retention at 36 months, Tactical ~60%, Expendable ~40%. Use for: vintage analysis, cohort behavior, and retention forecasting.';

COMMENT ON TABLE cfo_banking_demo.ml_models.deposit_runoff_forecasts IS
'Phase 2 3-year deposit runoff forecasts using Chen Component Decay Model. Strategic deposits show ~10% runoff over 3 years, Tactical ~25%, Expendable ~40%. Use for: long-term funding planning, liquidity projections, and CCAR/DFAST scenarios.';

-- Phase 3: CCAR/DFAST
COMMENT ON TABLE cfo_banking_demo.ml_models.dynamic_beta_parameters IS
'Phase 3 Dynamic Beta Model - Sigmoid function parameters showing how deposit beta varies with market rates. Formula: β(Rm) = β_min + (β_max - β_min) / [1 + exp(-k*(Rm-R0))]. Use for: CCAR/DFAST stress testing, rate shock scenarios, and non-linear beta modeling.';

COMMENT ON TABLE cfo_banking_demo.ml_models.stress_test_results IS
'Phase 3 CCAR/DFAST stress test results. 9-quarter projections for Baseline (+0 bps), Adverse (+200 bps), Severely Adverse (+300 bps) scenarios. CET1 must stay ≥7.0% to pass. Use for: regulatory reporting, capital planning, and stress testing compliance.';

COMMENT ON TABLE cfo_banking_demo.gold_regulatory.lcr_daily IS
'Basel III Liquidity Coverage Ratio - Daily calculations. LCR = HQLA / Net Cash Outflows. Regulatory minimum is 100% (must survive 30-day liquidity stress). Level 1 HQLA (cash, treasuries) most liquid with 0% haircut. Use for: liquidity monitoring, regulatory compliance, stress testing.';

COMMENT ON TABLE cfo_banking_demo.gold_regulatory.hqla_inventory IS
'HQLA (High-Quality Liquid Assets) inventory detail. Level 1 (0% haircut): cash, reserves, treasuries. Level 2A (15%): GSE bonds, AAA corporates. Level 2B (50%): high-quality equities, some corporates. Use for: LCR calculation, liquidity management, asset allocation.';

-- Phase 4: PPNR
COMMENT ON TABLE cfo_banking_demo.ml_models.ppnr_forecasts IS
'Phase 4 PPNR (Pre-Provision Net Revenue) forecasts. PPNR = NII + Non-Interest Income - Non-Interest Expense. 9-quarter projections for CCAR/DFAST compliance. Trained XGBoost models for fee income and operating expense. Use for: stress testing, capital planning, financial forecasting, efficiency analysis.';

COMMENT ON TABLE cfo_banking_demo.ml_models.non_interest_income_training_data IS
'Non-interest income training data for ML forecasting. Includes service charges, card fees, wealth management fees, mortgage fees. Correlated with transaction volume, account activity, economic conditions. Use for: fee income modeling, PPNR forecasting, revenue diversification analysis.';

COMMENT ON TABLE cfo_banking_demo.ml_models.non_interest_expense_training_data IS
'Non-interest expense training data for ML forecasting. Includes salaries, occupancy, technology, marketing costs. Scaled by business volume (loans, deposits, transaction counts). Use for: expense modeling, PPNR forecasting, efficiency analysis, cost management.';
```

---

## Summary: Tables List for Genie

Copy this list when creating the Genie Space in the UI:

1. `cfo_banking_demo.ml_models.deposit_beta_training_enhanced`
2. `cfo_banking_demo.bronze_core_banking.deposit_accounts`
3. `cfo_banking_demo.ml_models.component_decay_metrics`
4. `cfo_banking_demo.ml_models.cohort_survival_rates`
5. `cfo_banking_demo.ml_models.deposit_runoff_forecasts`
6. `cfo_banking_demo.ml_models.dynamic_beta_parameters`
7. `cfo_banking_demo.ml_models.stress_test_results`
8. `cfo_banking_demo.gold_regulatory.lcr_daily`
9. `cfo_banking_demo.gold_regulatory.hqla_inventory`
10. `cfo_banking_demo.ml_models.ppnr_forecasts`
11. `cfo_banking_demo.ml_models.non_interest_income_training_data`
12. `cfo_banking_demo.ml_models.non_interest_expense_training_data`

**Total: 12 tables covering all 4 modeling domains**
