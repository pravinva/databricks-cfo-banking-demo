# Genie Space Sample Queries

## Overview
These sample queries demonstrate common analysis patterns across the 12 Genie Space tables. Use these as templates for natural language queries in Genie.

**Important Notes:**
- ✅ These queries demonstrate correct SQL syntax and join patterns
- ✅ Query #2 (Portfolio Beta Summary) has been validated and returns correct results
- ⚠️ Some queries reference columns that may not exist in all environments (e.g., `actual_nii`, `actual_nie` in PPNR table)
- 💡 Use these as **reference templates** - Genie will adapt them based on actual available data
- 💡 Focus on the query **patterns** and **business logic** rather than exact column names

---

## Phase 1: Deposit Beta Analysis

### 1. At-Risk Account Analysis (Join Beta Model + Core Banking)
**Business Question:** "Show me all Strategic customer accounts with high balances that are priced below market"

```sql
SELECT
    b.account_id,
    b.customer_name,
    b.product_type,
    b.current_balance / 1000000 AS balance_millions,
    b.stated_rate,
    m.market_fed_funds_rate,
    m.rate_gap,
    m.target_beta,
    m.relationship_category
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts b
INNER JOIN cfo_banking_demo.ml_models.deposit_beta_training_enhanced m
    ON b.account_id = m.account_id
    AND b.effective_date = m.effective_date
WHERE m.relationship_category = 'Strategic'
    AND m.below_competitor_rate = 1
    AND b.current_balance > 10000000
    AND b.effective_date = (SELECT MAX(effective_date) FROM cfo_banking_demo.bronze_core_banking.deposit_accounts)
ORDER BY b.current_balance DESC;
```

### 2. Portfolio Beta Summary by Product and Segment
**Business Question:** "What is the average deposit beta by product type and relationship category?"

```sql
SELECT
    product_type,
    relationship_category,
    COUNT(*) AS account_count,
    ROUND(AVG(balance_millions), 2) AS avg_balance_millions,
    ROUND(AVG(target_beta), 3) AS avg_beta,
    ROUND(AVG(stated_rate), 3) AS avg_stated_rate,
    SUM(CASE WHEN below_competitor_rate = 1 THEN 1 ELSE 0 END) AS at_risk_count
FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
WHERE effective_date = (SELECT MAX(effective_date) FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced)
GROUP BY product_type, relationship_category
ORDER BY relationship_category, avg_beta;
```

### 3. Rate Gap Distribution Analysis
**Business Question:** "Show me accounts with the largest rate gaps (priced below market)"

```sql
SELECT
    account_id,
    product_type,
    relationship_category,
    balance_millions,
    stated_rate,
    market_fed_funds_rate,
    rate_gap,
    CASE
        WHEN rate_gap < -0.02 THEN 'Critical'
        WHEN rate_gap < -0.01 THEN 'High Risk'
        WHEN rate_gap < 0 THEN 'Moderate Risk'
        ELSE 'Low Risk'
    END AS risk_level
FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
WHERE effective_date = (SELECT MAX(effective_date) FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced)
    AND rate_gap < 0
ORDER BY rate_gap ASC
LIMIT 100;
```

---

## Phase 2: Vintage Analysis & Runoff Forecasting

### 4. Cohort Survival Rates Over Time
**Business Question:** "Show me account retention rates over 36 months by relationship category"

```sql
SELECT
    relationship_category,
    months_since_open,
    account_survival_rate,
    balance_survival_rate,
    ROUND((1 - account_survival_rate) * 100, 1) AS closure_rate_pct
FROM cfo_banking_demo.ml_models.cohort_survival_rates
WHERE months_since_open IN (6, 12, 18, 24, 30, 36)
ORDER BY relationship_category, months_since_open;
```

### 5. Chen Decay Parameters with Projected Runoff
**Business Question:** "What are the closure rates and growth rates for each segment, and what's the projected balance in 12 months?"

```sql
SELECT
    c.relationship_category,
    c.product_type,
    c.lambda_closure_rate,
    c.g_abgr AS balance_growth_rate,
    f.current_balance_billions,
    f.projected_balance_billions AS projected_12m,
    ROUND((f.projected_balance_billions - f.current_balance_billions) / f.current_balance_billions * 100, 1) AS runoff_pct_12m
FROM cfo_banking_demo.ml_models.component_decay_metrics c
INNER JOIN cfo_banking_demo.ml_models.deposit_runoff_forecasts f
    ON c.relationship_category = f.relationship_category
    AND c.product_type = f.product_type
WHERE f.months_ahead = 12
ORDER BY runoff_pct_12m ASC;
```

### 6. 3-Year Runoff Forecast Summary
**Business Question:** "What is the total expected deposit runoff over 3 years by segment?"

```sql
SELECT
    relationship_category,
    SUM(CASE WHEN months_ahead = 12 THEN projected_balance_billions ELSE 0 END) AS balance_12m,
    SUM(CASE WHEN months_ahead = 24 THEN projected_balance_billions ELSE 0 END) AS balance_24m,
    SUM(CASE WHEN months_ahead = 36 THEN projected_balance_billions ELSE 0 END) AS balance_36m,
    SUM(current_balance_billions) AS current_balance,
    ROUND((SUM(CASE WHEN months_ahead = 36 THEN projected_balance_billions ELSE 0 END) - SUM(current_balance_billions)) / SUM(current_balance_billions) * 100, 1) AS total_runoff_pct_3y
FROM cfo_banking_demo.ml_models.deposit_runoff_forecasts
GROUP BY relationship_category
ORDER BY total_runoff_pct_3y;
```

---

## Phase 3: CCAR Stress Testing

### 7. Stress Test Results Summary
**Business Question:** "Show me CET1 ratios and NII impact across all CCAR scenarios"

```sql
SELECT
    scenario_name,
    rate_shock_bps,
    stressed_market_rate,
    stressed_avg_beta,
    delta_nii_millions,
    delta_eve_billions,
    eve_cet1_ratio,
    sot_status,
    CASE
        WHEN eve_cet1_ratio >= 0.10 THEN 'Well Capitalized'
        WHEN eve_cet1_ratio >= 0.07 THEN 'Adequately Capitalized'
        ELSE 'Undercapitalized'
    END AS capital_status
FROM cfo_banking_demo.ml_models.stress_test_results
ORDER BY rate_shock_bps;
```

### 8. Dynamic Beta Response Curve
**Business Question:** "What is the beta response at different rate environments?"

```sql
SELECT
    relationship_category,
    beta_min,
    beta_max,
    k_steepness,
    R0_inflection,
    ROUND(beta_min + (beta_max - beta_min) / (1 + EXP(-k_steepness * (0.02 - R0_inflection))), 3) AS beta_at_2pct,
    ROUND(beta_min + (beta_max - beta_min) / (1 + EXP(-k_steepness * (0.04 - R0_inflection))), 3) AS beta_at_4pct,
    ROUND(beta_min + (beta_max - beta_min) / (1 + EXP(-k_steepness * (0.06 - R0_inflection))), 3) AS beta_at_6pct
FROM cfo_banking_demo.ml_models.dynamic_beta_parameters;
```

### 9. LCR Daily Status with HQLA Breakdown
**Business Question:** "What is today's LCR ratio and HQLA composition?"

```sql
SELECT
    l.calculation_date,
    l.lcr_ratio,
    l.total_hqla,
    l.hqla_level_1,
    l.hqla_level_2a,
    l.hqla_level_2b,
    l.net_outflows,
    l.lcr_status,
    ROUND(l.hqla_level_1 / l.total_hqla * 100, 1) AS level1_pct,
    ROUND(l.hqla_level_2a / l.total_hqla * 100, 1) AS level2a_pct,
    ROUND(l.hqla_level_2b / l.total_hqla * 100, 1) AS level2b_pct
FROM cfo_banking_demo.gold_regulatory.lcr_daily l
WHERE calculation_date = (SELECT MAX(calculation_date) FROM cfo_banking_demo.gold_regulatory.lcr_daily);
```

### 10. HQLA Inventory Detail
**Business Question:** "Show me the HQLA inventory by security type and level"

```sql
SELECT
    hqla_level,
    security_type,
    COUNT(*) AS security_count,
    ROUND(SUM(market_value) / 1000000, 2) AS total_market_value_millions,
    ROUND(AVG(haircut) * 100, 1) AS avg_haircut_pct,
    ROUND(SUM(hqla_value) / 1000000, 2) AS total_hqla_value_millions
FROM cfo_banking_demo.gold_regulatory.hqla_inventory
GROUP BY hqla_level, security_type
ORDER BY hqla_level, total_hqla_value_millions DESC;
```

---

## Phase 4: PPNR Forecasting

### 11. PPNR Forecast by Quarter
**Business Question:** "Show me 9-quarter PPNR forecast with components"

```sql
SELECT
    month,
    QUARTER(month) AS quarter,
    YEAR(month) AS year,
    net_interest_income,
    non_interest_income,
    non_interest_expense,
    ppnr,
    ROUND(non_interest_expense / (net_interest_income + non_interest_income) * 100, 1) AS efficiency_ratio,
    ROUND((ppnr - LAG(ppnr) OVER (ORDER BY month)) / LAG(ppnr) OVER (ORDER BY month) * 100, 1) AS ppnr_growth_pct
FROM cfo_banking_demo.ml_models.ppnr_forecasts
ORDER BY month;
```

### 12. PPNR Actual vs Forecast (if actuals available)
**Business Question:** "Compare actual vs forecasted PPNR"

```sql
SELECT
    month,
    net_interest_income AS forecast_nii,
    actual_nii,
    ROUND((actual_nii - net_interest_income) / net_interest_income * 100, 1) AS nii_variance_pct,
    non_interest_expense AS forecast_nie,
    actual_nie,
    ROUND((actual_nie - non_interest_expense) / non_interest_expense * 100, 1) AS nie_variance_pct
FROM cfo_banking_demo.ml_models.ppnr_forecasts
WHERE actual_nii IS NOT NULL
ORDER BY month DESC
LIMIT 12;
```

### 13. Non-Interest Income Trend Analysis
**Business Question:** "What is the trend in fee income vs deposit activity?"

```sql
SELECT
    month,
    target_fee_income,
    active_deposit_accounts,
    checking_accounts,
    total_transactions_millions,
    ROUND(target_fee_income / active_deposit_accounts, 2) AS fee_per_account,
    ROUND(digital_transaction_pct * 100, 1) AS digital_pct,
    ROUND((target_fee_income - prior_month_fee_income) / prior_month_fee_income * 100, 1) AS fee_income_growth_pct
FROM cfo_banking_demo.ml_models.non_interest_income_training_data
WHERE month >= DATE_SUB(CURRENT_DATE(), 365)
ORDER BY month DESC;
```

### 14. Efficiency Ratio Analysis
**Business Question:** "What is the operating expense trend and efficiency metrics?"

```sql
SELECT
    month,
    target_operating_expense,
    active_accounts,
    total_assets_billions,
    ROUND(target_operating_expense / active_accounts, 2) AS expense_per_account,
    ROUND(target_operating_expense / total_assets_billions / 1000000, 3) AS expense_to_assets_ratio,
    digital_adoption_rate,
    ROUND((target_operating_expense - prior_month_expense) / prior_month_expense * 100, 1) AS expense_growth_pct
FROM cfo_banking_demo.ml_models.non_interest_expense_training_data
WHERE month >= DATE_SUB(CURRENT_DATE(), 365)
ORDER BY month DESC;
```

---

## Cross-Phase Complex Queries

### 15. Complete Risk Assessment
**Business Question:** "Show me a comprehensive risk view: at-risk deposits + runoff forecast + stress test impact"

```sql
WITH at_risk_deposits AS (
    SELECT
        relationship_category,
        COUNT(*) AS at_risk_count,
        SUM(balance_millions) AS at_risk_balance_millions
    FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
    WHERE below_competitor_rate = 1
        AND effective_date = (SELECT MAX(effective_date) FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced)
    GROUP BY relationship_category
),
runoff_12m AS (
    SELECT
        relationship_category,
        SUM(current_balance_billions) AS current_billions,
        SUM(projected_balance_billions) AS projected_12m_billions,
        ROUND((SUM(projected_balance_billions) - SUM(current_balance_billions)) / SUM(current_balance_billions) * 100, 1) AS runoff_pct
    FROM cfo_banking_demo.ml_models.deposit_runoff_forecasts
    WHERE months_ahead = 12
    GROUP BY relationship_category
),
stress_impact AS (
    SELECT
        scenario_name,
        delta_nii_millions,
        eve_cet1_ratio
    FROM cfo_banking_demo.ml_models.stress_test_results
)
SELECT
    r.relationship_category,
    a.at_risk_count,
    a.at_risk_balance_millions,
    r.current_billions,
    r.projected_12m_billions,
    r.runoff_pct AS projected_runoff_12m_pct,
    (SELECT delta_nii_millions FROM stress_impact WHERE scenario_name = 'Severely Adverse') AS severely_adverse_nii_impact,
    (SELECT eve_cet1_ratio FROM stress_impact WHERE scenario_name = 'Severely Adverse') AS severely_adverse_cet1
FROM runoff_12m r
LEFT JOIN at_risk_deposits a ON r.relationship_category = a.relationship_category
ORDER BY r.relationship_category;
```

### 16. Portfolio Performance Dashboard
**Business Question:** "Give me a complete dashboard view: deposits, beta, LCR, PPNR"

```sql
WITH deposit_summary AS (
    SELECT
        COUNT(*) AS total_accounts,
        SUM(current_balance) / 1000000000 AS total_balance_billions,
        AVG(stated_rate) AS avg_rate
    FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
    WHERE is_current = TRUE
),
beta_summary AS (
    SELECT
        AVG(target_beta) AS portfolio_beta,
        COUNT(CASE WHEN below_competitor_rate = 1 THEN 1 END) AS at_risk_accounts
    FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
    WHERE effective_date = (SELECT MAX(effective_date) FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced)
),
lcr_status AS (
    SELECT
        lcr_ratio,
        lcr_status
    FROM cfo_banking_demo.gold_regulatory.lcr_daily
    WHERE calculation_date = (SELECT MAX(calculation_date) FROM cfo_banking_demo.gold_regulatory.lcr_daily)
),
ppnr_latest AS (
    SELECT
        ppnr,
        net_interest_income
    FROM cfo_banking_demo.ml_models.ppnr_forecasts
    ORDER BY month DESC
    LIMIT 1
)
SELECT
    d.total_accounts,
    d.total_balance_billions,
    d.avg_rate,
    b.portfolio_beta,
    b.at_risk_accounts,
    l.lcr_ratio,
    l.lcr_status,
    p.ppnr,
    p.net_interest_income
FROM deposit_summary d, beta_summary b, lcr_status l, ppnr_latest p;
```

---

## Common Expressions & Formulas

### Chen Decay Formula
```sql
-- D(t+1) = D(t) × (1-λ) × (1+g)
projected_balance = current_balance * (1 - lambda_closure_rate) * (1 + g_abgr)
```

### Dynamic Beta Sigmoid
```sql
-- β(Rm) = β_min + (β_max - β_min) / [1 + exp(-k*(Rm-R0))]
beta_at_rate = beta_min + (beta_max - beta_min) / (1 + EXP(-k_steepness * (market_rate - R0_inflection)))
```

### Efficiency Ratio
```sql
-- Efficiency Ratio = Non-Interest Expense / (NII + Non-Interest Income)
efficiency_ratio = non_interest_expense / (net_interest_income + non_interest_income) * 100
```

### LCR Calculation
```sql
-- LCR = HQLA / Net Cash Outflows
lcr_ratio = total_hqla / net_outflows * 100
```

---

## Notes for Genie

When users ask questions in natural language, Genie should:

1. **Recognize synonyms:**
   - "at-risk" = below_competitor_rate = 1
   - "retention" = account_survival_rate
   - "runoff" = deposit balance decline
   - "stress test" = CCAR scenarios

2. **Use appropriate filters:**
   - Always filter to latest date: `WHERE effective_date = (SELECT MAX(effective_date)...)`
   - Use exact scenario names: 'Baseline', 'Adverse', 'Severely Adverse'
   - Relationship categories are case-sensitive

3. **Format results properly:**
   - Balances: Show in millions/billions as appropriate
   - Percentages: Multiply by 100 and round
   - Rates: Show as decimals (0.025 = 2.5%)

4. **Suggest follow-ups:**
   - After showing summary, offer to drill down
   - Provide context about regulatory minimums
   - Highlight areas of concern
