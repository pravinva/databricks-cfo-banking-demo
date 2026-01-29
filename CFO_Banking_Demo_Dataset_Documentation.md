# CFO Banking Demo - Complete Dataset Documentation

**Catalog:** `cfo_banking_demo`
**Purpose:** End-to-end banking data lakehouse demonstrating Treasury, ALM, Risk, and Regulatory reporting

---

## Table of Contents
1. [Bronze Layer - Core Banking](#bronze-layer---core-banking)
2. [Bronze Layer - Market Data](#bronze-layer---market-data)
3. [Silver Layer - Treasury](#silver-layer---treasury)
4. [Silver Layer - Finance](#silver-layer---finance)
5. [Silver Layer - Risk & Regulatory](#silver-layer---risk--regulatory)
6. [Gold Layer - Regulatory Reports](#gold-layer---regulatory-reports)
7. [Gold Layer - Analytics](#gold-layer---analytics)
8. [Gold Layer - Finance](#gold-layer---finance)
9. [ML Models](#ml-models)

---

## Bronze Layer - Core Banking
**Schema:** `bronze_core_banking`
**Purpose:** Raw source data from core banking systems

### 1. **balance_sheet_daily**
- **Purpose:** Daily balance sheet positions for GL reporting
- **Key Columns:**
  - `report_date` - Reporting date
  - `line_item` - Balance sheet line item (e.g., Cash_Vault, Goodwill)
  - `line_item_category` - Asset, Liability, Equity
  - `balance` - Current balance
  - `average_balance_qtd`, `average_balance_ytd` - Period averages
  - `regulatory_classification` - Regulatory treatment
  - `risk_weight` - Capital risk weighting
  - `hqla_classification` - High Quality Liquid Asset classification for LCR
  - `nsfr_classification` - Net Stable Funding Ratio classification
- **Usage:** Foundation for balance sheet, capital adequacy, and liquidity reports

### 2. **chart_of_accounts**
- **Purpose:** Master chart of accounts for GL mapping
- **Key Columns:**
  - `account_number` - GL account number
  - `account_name` - Account name
  - `account_type` - Asset, Liability, Equity, Revenue, Expense
  - `account_category` - Subcategory (e.g., Current_Asset, Long_Term_Debt)
  - `regulatory_code` - Regulatory reporting code mapping
  - `financial_statement` - Which statement it appears on
- **Usage:** Mapping source transactions to regulatory reports

### 3. **deposit_accounts**
- **Purpose:** Detailed deposit account information
- **Row Count:** ~500,000+ accounts
- **Key Columns:**
  - `account_id` - Unique account identifier
  - `customer_segment` - Retail, Commercial, Institutional, etc.
  - `product_type` - DDA, Savings, NOW, MMDA, CD
  - `current_balance` - Current account balance
  - `average_balance_30d`, `average_balance_90d` - Historical averages
  - `stated_rate` - Interest rate paid
  - `beta` - Rate sensitivity coefficient (0-1.5)
  - `decay_rate` - Balance decay rate
  - `account_status` - Active, Closed, Dormant
  - `fdic_insured` - FDIC insurance flag
  - `has_online_banking`, `has_mobile_banking` - Channel flags
- **Usage:** Source for deposit beta modeling, LCR cash outflows, ALM gap analysis

### 4. **deposit_behavior_history**
- **Purpose:** Historical deposit balance changes with rate environment
- **Key Columns:**
  - `account_id` - Account identifier
  - `period_date` - Observation period
  - `beginning_balance`, `ending_balance` - Period balances
  - `balance_change`, `balance_change_pct` - Balance movements
  - `fed_funds_rate` - Fed funds rate during period
  - `rate_change` - Rate change from prior period
- **Usage:** Training data for deposit beta modeling, churn prediction

### 5. **loan_origination_events**
- **Purpose:** Stream of new loan originations
- **Key Columns:**
  - `loan_id` - New loan identifier
  - `borrower_id`, `borrower_name` - Borrower information
  - `product_type` - Mortgage, Auto, CNI, etc.
  - `loan_amount` - Original loan amount
  - `interest_rate` - Loan interest rate
  - `term_months` - Loan term
  - `collateral_type`, `collateral_value` - Collateral details
  - `credit_score` - Borrower credit score
- **Usage:** Real-time loan origination tracking, credit risk modeling

### 6. **loan_portfolio**
- **Purpose:** Current loan portfolio holdings
- **Row Count:** ~50,000+ loans
- **Key Columns:**
  - `loan_id` - Unique loan identifier
  - `product_type` - Mortgage, Auto, CNI, CRE, Consumer
  - `origination_date`, `maturity_date` - Loan lifecycle dates
  - `original_amount`, `current_balance` - Loan amounts
  - `interest_rate` - Current interest rate
  - `rate_type` - Fixed, Variable
  - `days_past_due` - Delinquency status
  - `credit_score` - Current credit score
  - `risk_rating` - Internal risk rating
  - `pd`, `lgd`, `ead` - Credit risk parameters
  - `cecl_reserve` - CECL allowance
  - `collateral_type`, `collateral_value`, `ltv_ratio` - Collateral details
- **Usage:** Credit risk modeling, CECL calculations, ALM interest rate risk

### 7. **securities_portfolio**
- **Purpose:** Investment securities holdings (HTM, AFS, Trading)
- **Key Columns:**
  - `security_id`, `cusip`, `isin` - Security identifiers
  - `security_type` - Treasury, Agency, Municipal, Corporate, MBS
  - `issuer_name` - Issuer
  - `maturity_date` - Maturity date
  - `par_value`, `market_value`, `book_value` - Valuations
  - `coupon_rate`, `yield_to_maturity` - Yield information
  - `duration` - Interest rate sensitivity
  - `credit_rating` - Credit rating (AAA, AA, etc.)
  - `security_classification` - HTM, AFS, Trading
  - `unrealized_gain_loss`, `oci_adjustment` - AOCI tracking
- **Usage:** LCR HQLA calculations, interest rate risk, OCI reporting

---

## Bronze Layer - Market Data
**Schema:** `bronze_market_data`

### 8. **treasury_yields_raw**
- **Purpose:** Daily US Treasury yield curve data
- **Key Columns:**
  - `date` - Observation date
  - `maturity` - 3month, 2year, 5year, 10year, 30year
  - `value` - Yield rate (%)
  - `ingestion_timestamp` - Data load time
- **Usage:** Rate shock scenarios, yield curve construction, fair value calculations

### 9. **fx_rates_raw**
- **Purpose:** Foreign exchange rates for multi-currency operations
- **Key Columns:**
  - `date` - Rate date
  - `from_currency`, `to_currency` - Currency pair
  - `exchange_rate` - Spot rate
  - `bid_price`, `ask_price` - Market pricing
- **Usage:** FX risk calculations, multi-currency balance sheet translation

---

## Silver Layer - Treasury
**Schema:** `silver_treasury`
**Purpose:** Cleaned, enriched treasury and ALM data

### 10. **deposit_portfolio**
- **Purpose:** Cleansed deposit account data with calculated fields
- **Enhancements over Bronze:**
  - Rate sensitivity (beta) calculations
  - Behavioral decay rates
  - Customer segmentation
  - Repricing buckets
- **Usage:** Primary source for ALM gap analysis, deposit beta modeling

### 11. **yield_curves**
- **Purpose:** Structured yield curve data pivoted by tenor
- **Key Columns:**
  - `date` - Curve date
  - `rate_3m`, `rate_2y`, `rate_5y`, `rate_10y`, `rate_30y` - Yield rates by maturity
- **Usage:** Rate shock scenarios, discounting, fair value calculations

### 12. **loan_portfolio**
- **Purpose:** Cleansed loan portfolio with credit risk metrics
- **Enhancements:**
  - Calculated PD, LGD, EAD
  - CECL reserve calculations
  - Repricing dates and durations
- **Usage:** Credit risk modeling, ALM interest rate risk, CECL reporting

### 13. **securities_portfolio**
- **Purpose:** Cleansed securities with duration and convexity
- **Enhancements:**
  - Duration and convexity calculations
  - HQLA classifications
  - OCI tracking
- **Usage:** Interest rate risk, LCR HQLA, investment strategy

---

## Silver Layer - Finance
**Schema:** `silver_finance`

### 14. **general_ledger**
- **Purpose:** Cleaned GL transactions
- **Key Columns:**
  - `transaction_id` - Unique transaction ID
  - `account_number` - GL account
  - `transaction_date` - Transaction date
  - `debit_amount`, `credit_amount` - Entry amounts
  - `balance` - Running balance
- **Usage:** Financial statement preparation, account reconciliation

---

## Silver Layer - Risk & Regulatory
**Schema:** `silver_risk` and `silver_regulatory`

### 15. **credit_risk_metrics**
- **Purpose:** Credit risk calculations by segment
- **Key Columns:**
  - `calculation_date` - Calc date
  - `risk_segment` - Portfolio segment
  - `exposure_at_default` - EAD
  - `probability_of_default` - PD
  - `loss_given_default` - LGD
  - `expected_loss` - EL calculation
- **Usage:** Credit risk reporting, CECL modeling

### 16. **hqla_inventory**
- **Purpose:** High Quality Liquid Assets for LCR
- **Key Columns:**
  - `security_id` - Security identifier
  - `hqla_level` - Level 1, Level 2A, Level 2B
  - `fair_value` - Market value
  - `hqla_amount` - LCR-eligible amount (after haircuts)
  - `haircut_percentage` - Regulatory haircut
- **Usage:** FR 2052a Panel A (HQLA section)

---

## Gold Layer - Regulatory Reports
**Schema:** `gold_regulatory`
**Purpose:** Production regulatory reports (FR Y-9C, FR 2052a, FFIEC 101, etc.)

### 17. **fr_2052a_panel_a** (LCR - HQLA)
- **Purpose:** FR 2052a Panel A - High Quality Liquid Assets
- **Key Columns:**
  - `line_code` - Panel A line codes (A-1, A-2, A-3, A-TOTAL)
  - `line_description` - Line description
  - `fair_value` - Fair value of assets
  - `hqla_amount` - LCR-eligible amount
  - `hqla_percentage` - Haircut percentage
- **Regulatory Mapping:**
  - A-1: Level 1 HQLA (0% haircut)
  - A-2: Level 2A HQLA (15% haircut)
  - A-3: Level 2B HQLA (50% haircut)
- **Usage:** LCR numerator calculation, regulatory submission

### 18. **fr_2052a_panel_b** (LCR - Cash Outflows)
- **Purpose:** FR 2052a Panel B - Cash Outflows
- **Key Columns:**
  - `line_code` - Panel B line codes (B-1, B-2, B-TOTAL)
  - `line_description` - Outflow type
  - `deposit_balance` - Deposit balances
  - `stressed_outflow_amount` - 30-day stressed outflows
- **Regulatory Mapping:**
  - B-1: Retail deposit outflows (5-10% runoff)
  - B-2: Wholesale funding outflows (various rates)
- **Usage:** LCR denominator calculation (outflows)

### 19. **fr_2052a_panel_c** (LCR - Cash Inflows)
- **Purpose:** FR 2052a Panel C - Cash Inflows
- **Key Columns:**
  - `line_code` - Panel C line codes (C-1, C-TOTAL)
  - `contractual_inflow` - Contractual inflows
  - `expected_inflow` - Expected inflows (capped at 75% of outflows)
- **Usage:** LCR denominator calculation (inflows, capped)

### 20. **fr_2052a_summary**
- **Purpose:** FR 2052a Summary - Final LCR Calculation
- **Key Columns:**
  - `hqla_amount` - Total HQLA (numerator)
  - `gross_outflows` - Total cash outflows
  - `capped_inflows` - Capped cash inflows
  - `net_outflows` - Net outflows (denominator)
  - `lcr_ratio` - Final LCR ratio (must be ≥ 100%)
  - `lcr_status` - COMPLIANT / NON-COMPLIANT
- **Regulatory Requirement:** LCR ≥ 100%
- **Usage:** Primary regulatory metric for liquidity risk

### 21. **cash_outflows_30day**
- **Purpose:** Detailed 30-day cash outflows by account
- **Key Columns:**
  - `account_id` - Deposit account ID
  - `product_type` - Deposit product
  - `current_balance` - Account balance
  - `runoff_rate` - Stressed runoff rate (5%, 10%, 25%, 40%, 100%)
  - `stressed_outflow` - Expected outflow = balance × runoff_rate
- **Runoff Rates by Product:**
  - DDA (Retail): 5%
  - MMDA (Retail): 10%
  - MMDA (Non-Retail): 40%
  - Brokered Deposits: 100%
- **Usage:** Source for FR 2052a Panel B

### 22. **cash_inflows_30day**
- **Purpose:** Expected 30-day cash inflows from loans
- **Key Columns:**
  - `loan_id` - Loan identifier
  - `current_balance` - Loan balance
  - `maturity_date` - Maturity date
  - `days_to_maturity` - Days until maturity
  - `inflow_rate` - Inflow assumption (50% for performing loans)
  - `expected_inflow` - Expected cash inflow
- **Usage:** Source for FR 2052a Panel C (capped at 75% of outflows)

### 23. **ffiec_101_schedule_a** (Capital Components)
- **Purpose:** FFIEC 101 Schedule A - Regulatory Capital Components
- **Key Columns:**
  - `line_item_code` - Line codes (CET1_01, TIER1_01, TIER2_01)
  - `line_item_description` - Capital component description
  - `amount_current` - Current period amount
  - `amount_prior_quarter` - Prior quarter for comparison
- **Capital Components:**
  - CET1: Common stock, retained earnings, less deductions
  - Tier 1: CET1 + preferred stock
  - Tier 2: Subordinated debt, allowance for loan losses
- **Usage:** Capital adequacy reporting, Basel III compliance

### 24. **ffiec_101_schedule_b** (Risk-Weighted Assets)
- **Purpose:** FFIEC 101 Schedule B - RWA Calculation
- **Key Columns:**
  - `category_code` - RWA category (RWA_CREDIT, RWA_MARKET, RWA_OPERATIONAL)
  - `category_description` - RWA type
  - `rwa_amount` - Risk-weighted asset amount
- **RWA Categories:**
  - Credit RWA: Loans, securities (risk-weighted by type)
  - Market RWA: Trading book exposures
  - Operational RWA: Based on gross income
- **Usage:** Denominator for capital ratios

### 25. **capital_adequacy**
- **Purpose:** Calculated capital ratios
- **Key Columns:**
  - `cet1_capital`, `tier1_capital`, `total_capital` - Capital amounts
  - `total_rwa` - Total risk-weighted assets
  - `cet1_ratio_pct` - CET1 / RWA (min 4.5%)
  - `tier1_ratio_pct` - Tier 1 / RWA (min 6%)
  - `total_capital_ratio_pct` - Total Capital / RWA (min 8%)
  - `cet1_status`, `tier1_status`, `total_capital_status` - Compliance status
- **Regulatory Minimums:**
  - CET1: ≥ 4.5%
  - Tier 1: ≥ 6%
  - Total Capital: ≥ 8%
- **Usage:** Primary capital adequacy metric

### 26. **nsfr_report**
- **Purpose:** Net Stable Funding Ratio (NSFR) calculation
- **Key Columns:**
  - `available_stable_funding` - ASF (funding sources)
  - `required_stable_funding` - RSF (asset requirements)
  - `nsfr_ratio` - ASF / RSF (must be ≥ 100%)
  - `nsfr_status` - Compliance status
- **Regulatory Requirement:** NSFR ≥ 100%
- **Usage:** Long-term structural liquidity metric

### 27. **alm_gap_report**
- **Purpose:** Asset-Liability Management gap analysis
- **Key Columns:**
  - `time_bucket` - Repricing bucket (0-3M, 3-6M, 6-12M, 1-3Y, etc.)
  - `rate_sensitive_assets` - Assets repricing in bucket
  - `rate_sensitive_liabilities` - Liabilities repricing in bucket
  - `gap` - Asset - Liability gap
  - `cumulative_gap` - Running cumulative gap
- **Usage:** Interest rate risk management, NII sensitivity

### 28. **interest_rate_shock_scenarios**
- **Purpose:** Rate shock impact on NII and EVE
- **Key Columns:**
  - `scenario_name` - Scenario (e.g., "+200 bp parallel", "-100 bp twist")
  - `nii_impact_1yr` - Net Interest Income impact over 1 year
  - `eve_impact` - Economic Value of Equity impact
  - `nii_impact_pct` - % change in NII
  - `eve_impact_pct` - % change in EVE
- **Standard Scenarios:**
  - ±100 bp, ±200 bp parallel shifts
  - Steepener, flattener, twist
- **Usage:** OCC/Fed interest rate risk requirements

---

## Gold Layer - Analytics
**Schema:** `gold_analytics`
**Purpose:** Business intelligence and advanced analytics

### 29. **deposit_beta_statistics**
- **Purpose:** Statistical deposit beta calculations by product
- **Key Columns:**
  - `product_type` - DDA, MMDA, Savings, CD
  - `observation_count` - Number of observations
  - `avg_balance_change_pct` - Average balance change %
  - `correlation` - Correlation(balance_change, rate_change)
  - `statistical_beta` - Regression beta coefficient
  - `avg_assigned_beta` - Average model-assigned beta
- **Usage:** Validate model betas, understand rate sensitivity

### 30. **deposit_beta_by_segment**
- **Purpose:** Beta analysis by customer segment
- **Key Columns:**
  - `customer_segment` - Retail, Commercial, Institutional
  - `product_type` - Product type
  - `statistical_beta` - Observed beta from data
  - `avg_assigned_beta` - Model-predicted beta
- **Usage:** Segment-level rate sensitivity analysis

### 31. **deposit_beta_features**
- **Purpose:** Feature table for deposit beta ML training
- **Key Columns:**
  - `account_id` - Account ID
  - `product_type`, `customer_segment` - Categorical features
  - `balance_change_pct` - Balance change %
  - `rate_change` - Fed funds rate change
  - `rate_change_bps` - Rate change in basis points
  - `assigned_beta` - Target variable for ML model
- **Usage:** Training data for deposit_beta_model

### 32. **deposit_runoff_predictions**
- **Purpose:** Predicted deposit runoff under rate scenarios
- **Key Columns:**
  - `product_type` - Product type
  - `total_balance` - Current total balance
  - `avg_beta` - Average portfolio beta
  - `runoff_25bps`, `runoff_50bps`, `runoff_100bps`, `runoff_200bps` - Predicted runoff amounts
- **Usage:** Rate shock scenario planning, liquidity stress testing

### 33. **market_data_latest**
- **Purpose:** Latest market rates for dashboards
- **Key Columns:**
  - `date` - Latest date
  - `rate_3m`, `rate_2y`, `rate_5y`, `rate_10y`, `rate_30y` - Current yields
- **Usage:** Real-time dashboard displays

---

## Gold Layer - Finance
**Schema:** `gold_finance`
**Purpose:** Financial metrics and KPIs

### 34. **liquidity_coverage_ratio**
- **Purpose:** Simplified LCR summary for dashboards
- **Key Columns:**
  - `calculation_date` - Calc date
  - `hqla_total` - Total HQLA
  - `net_cash_outflows` - Net 30-day outflows
  - `lcr_ratio` - Final ratio
- **Usage:** Executive dashboards, trend analysis

### 35. **capital_structure**
- **Purpose:** Capital structure summary
- **Key Columns:**
  - `common_stock`, `retained_earnings`, `preferred_stock` - Equity components
  - `goodwill`, `intangibles` - Deductions
  - `tier1_capital`, `tier2_capital` - Regulatory capital
  - `risk_weighted_assets` - Total RWA
- **Usage:** Capital planning, regulatory reporting

### 36. **profitability_metrics**
- **Purpose:** P&L metrics
- **Key Columns:**
  - `net_interest_margin` - NIM %
  - `fee_revenue` - Non-interest income
  - `operating_expenses` - Operating costs
- **Usage:** Performance monitoring

---

## Gold Layer - Dashboards
**Schema:** `gold_dashboards`

### 37. **intraday_liquidity_summary**
- **Purpose:** Real-time liquidity position tracking
- **Key Columns:**
  - `position_date` - Date
  - `activity_type` - Loan_Originations, Deposits, Withdrawals
  - `transaction_count` - Number of transactions
  - `gross_amount` - Total transaction amount
  - `cash_impact` - Net cash impact
- **Usage:** Intraday liquidity management

---

## ML Models
**Schema:** `ml_models`

### 38. **deposit_beta_training_data**
- **Purpose:** Training dataset for deposit beta model
- **Row Count:** ~100,000+ observations
- **Features:**
  - Product features: `product_type_encoded`, `segment_encoded`
  - Account features: `current_balance`, `stated_rate`, `account_age_months`
  - Churn features: `churned`, `dormant`, `balance_volatility_30d`, `rate_gap`, `churn_risk_score`
  - Market features: `current_market_rate`, `market_rate_5y`, `market_rate_10y`
  - Balance features: `log_balance`, `balance_millions`, `balance_trend_30d`
  - Rate features: `rate_spread`, `rate_spread_x_balance`
  - Activity features: `transaction_count_30d`
- **Target:** `target_beta` (deposit rate sensitivity 0-1.5)
- **Usage:** Train XGBoost regression model for beta prediction

### 39. **deposit_beta_predictions**
- **Purpose:** Model predictions for current portfolio
- **Key Columns:**
  - `account_id` - Account ID
  - `product_type`, `customer_segment` - Account attributes
  - `current_balance`, `stated_rate` - Current state
  - `predicted_beta` - Model-predicted beta
  - `prediction_timestamp` - Prediction time
  - `model_version` - Model alias (@champion)
- **Usage:** Rate sensitivity for ALM, scenario analysis

---

## Model Registry
**Schema:** `models`

### 40. **deposit_beta_model**
- **Purpose:** Registered XGBoost model in Unity Catalog
- **Algorithm:** XGBoost Regressor
- **Training Metrics:**
  - RMSE: ~0.05-0.08
  - R²: ~0.85-0.90
  - MAE: ~0.04-0.06
- **Validation:**
  - 5-fold cross-validation
  - Train/test split (80/20)
  - Residual analysis
  - Feature importance tracking
- **Aliases:**
  - `@champion` - Production model
  - `@challenger` - Candidate model for A/B testing
- **Usage:** Batch inference for deposit beta prediction

---

## Data Flow Summary

### Medallion Architecture

```
BRONZE (Raw)                    SILVER (Cleansed)              GOLD (Business)
├── bronze_core_banking         ├── silver_treasury            ├── gold_regulatory
│   ├── deposit_accounts        │   ├── deposit_portfolio      │   ├── fr_2052a_panel_a (HQLA)
│   ├── loan_portfolio          │   ├── loan_portfolio         │   ├── fr_2052a_panel_b (Outflows)
│   ├── securities_portfolio    │   ├── securities_portfolio   │   ├── fr_2052a_panel_c (Inflows)
│   └── balance_sheet_daily     │   └── yield_curves           │   ├── fr_2052a_summary (LCR)
│                               │                               │   ├── ffiec_101_schedule_a
├── bronze_market_data          ├── silver_finance             │   ├── ffiec_101_schedule_b
│   ├── treasury_yields_raw     │   └── general_ledger         │   ├── capital_adequacy
│   └── fx_rates_raw            │                               │   ├── nsfr_report
│                               ├── silver_risk                │   └── alm_gap_report
                                │   └── credit_risk_metrics    │
                                │                               ├── gold_analytics
                                ├── silver_regulatory          │   ├── deposit_beta_statistics
                                    └── hqla_inventory         │   ├── deposit_runoff_predictions
                                                                │   └── market_data_latest
                                                                │
                                                                ├── gold_finance
                                                                │   ├── liquidity_coverage_ratio
                                                                │   ├── capital_structure
                                                                │   └── profitability_metrics
                                                                │
                                                                └── gold_dashboards
                                                                    └── intraday_liquidity_summary
```

### ML Workflow

```
SILVER DATA                      ML TRAINING                    ML INFERENCE
silver_treasury.deposit_portfolio
        ↓
silver_treasury.yield_curves     ml_models.deposit_beta        ml_models.deposit_beta
        ↓                        _training_data                _predictions
    [Feature Eng]                      ↓                             ↑
        ↓                        [XGBoost Training]                  |
ml_models.deposit_beta          [MLflow Tracking]                   |
_training_data                         ↓                             |
                                models.deposit_beta_model      [Batch Scoring]
                                   @champion                         |
                                                              [Spark UDF Apply]
                                                                      ↑
                                                          Current Portfolio
```

---

## Key Use Cases

### 1. **Liquidity Coverage Ratio (LCR)**
- **Source Tables:**
  - HQLA: `silver_regulatory.hqla_inventory` → `gold_regulatory.fr_2052a_panel_a`
  - Outflows: `silver_treasury.deposit_portfolio` → `gold_regulatory.cash_outflows_30day` → `gold_regulatory.fr_2052a_panel_b`
  - Inflows: `silver_treasury.loan_portfolio` → `gold_regulatory.cash_inflows_30day` → `gold_regulatory.fr_2052a_panel_c`
- **Final Report:** `gold_regulatory.fr_2052a_summary`
- **Requirement:** LCR ≥ 100%

### 2. **Capital Adequacy (Basel III)**
- **Source Tables:**
  - Capital: `bronze_core_banking.balance_sheet_daily` → `gold_regulatory.ffiec_101_schedule_a`
  - RWA: `silver_treasury.loan_portfolio`, `silver_treasury.securities_portfolio` → `gold_regulatory.ffiec_101_schedule_b`
- **Final Report:** `gold_regulatory.capital_adequacy`
- **Requirements:** CET1 ≥ 4.5%, Tier 1 ≥ 6%, Total ≥ 8%

### 3. **Deposit Beta Modeling**
- **Training:** `ml_models.deposit_beta_training_data` → `models.deposit_beta_model@champion`
- **Inference:** `silver_treasury.deposit_portfolio` → `ml_models.deposit_beta_predictions`
- **Analytics:** `gold_analytics.deposit_runoff_predictions` (rate shock scenarios)

### 4. **Interest Rate Risk**
- **Source:** `silver_treasury.loan_portfolio`, `silver_treasury.deposit_portfolio`, `silver_treasury.securities_portfolio`
- **Analysis:** `gold_regulatory.alm_gap_report`, `gold_regulatory.interest_rate_shock_scenarios`
- **Usage:** NII sensitivity, EVE sensitivity, OCC reporting

---

## Regulatory Mapping

| Regulatory Report | Source Tables | Gold Table | Frequency |
|-------------------|---------------|------------|-----------|
| **FR 2052a (LCR)** | deposit_portfolio, loan_portfolio, securities_portfolio, hqla_inventory | fr_2052a_summary | Daily |
| **FFIEC 101 (Capital)** | balance_sheet_daily, loan_portfolio, securities_portfolio | capital_adequacy | Quarterly |
| **FR 2900 (NSFR)** | balance_sheet_daily, deposit_portfolio | nsfr_report | Quarterly |
| **OCC Rate Risk** | loan_portfolio, deposit_portfolio, securities_portfolio | alm_gap_report, interest_rate_shock_scenarios | Quarterly |
| **CECL** | loan_portfolio | credit_risk_metrics | Monthly |

---

## Document Version
- **Created:** 2026-01-29
- **Catalog:** cfo_banking_demo
- **Total Schemas:** 18
- **Total Tables:** ~40+
- **Purpose:** Banking data lakehouse for Treasury, ALM, Risk, and Regulatory reporting
