# SQL Expressions Quick Add Guide

## Quick Reference for Copy-Paste

This condensed guide is designed for efficiently adding all 23 SQL expressions to your Genie Space.

**Space:** Treasury Modeling - Deposits & Fee Income
**Space ID:** 01f101adda151c09835a99254d4c308c

---

## 📊 MEASURES (11)

### M1: Total Account Count
```
Name: Total Account Count
Code: COUNT(*)
Instructions: Total number of deposit accounts. Use for portfolio size analysis.
Synonyms: account count, number of accounts, total accounts
```

### M2: Total Balance (Millions)
```
Name: Total Balance (Millions)
Code: SUM(cfo_banking_demo.ml_models.deposit_beta_training_enhanced.balance_millions)
Instructions: Total deposit balance in millions. Use with deposit_beta_training_enhanced table.
Synonyms: total balance, sum of balances, total deposits
```

### M3: Average Deposit Beta
```
Name: Average Deposit Beta
Code: ROUND(AVG(cfo_banking_demo.ml_models.deposit_beta_training_enhanced.target_beta), 3)
Instructions: Average deposit beta coefficient (0-1 scale). Higher beta = more rate sensitive. Strategic ~0.35, Tactical ~0.55, Expendable ~0.75.
Synonyms: avg beta, mean beta, portfolio beta, average rate sensitivity
```

### M4: Average Interest Rate
```
Name: Average Interest Rate
Code: ROUND(AVG(cfo_banking_demo.ml_models.deposit_beta_training_enhanced.stated_rate), 3)
Instructions: Average stated interest rate on deposit accounts. Expressed as decimal (0.025 = 2.5%).
Synonyms: avg rate, mean rate, average stated rate
```

### M5: At-Risk Account Count
```
Name: At-Risk Account Count
Code: SUM(CASE WHEN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.below_competitor_rate = 1 THEN 1 ELSE 0 END)
Instructions: Number of accounts priced below market competitive rate (flight risk accounts requiring retention action).
Synonyms: at risk count, flight risk accounts, below market accounts
```

### M6: At-Risk Percentage
```
Name: At-Risk Percentage
Code: ROUND(SUM(CASE WHEN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.below_competitor_rate = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
Instructions: Percentage of accounts at risk (priced below market). Test result: 87.0% of portfolio.
Synonyms: at risk pct, flight risk percentage, at risk %
```

### M7: Critical Risk Count
```
Name: Critical Risk Count
Code: SUM(CASE WHEN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.rate_gap < -0.02 THEN 1 ELSE 0 END)
Instructions: Number of accounts with rate gap < -2% (critical flight risk requiring immediate action).
Synonyms: critical accounts, severely at risk
```

### M8: Balance in Billions
```
Name: Balance in Billions
Code: SUM(cfo_banking_demo.bronze_core_banking.deposit_accounts.current_balance) / 1000000000
Instructions: Total balance in billions. Use for aggregated portfolio reporting.
Synonyms: balance billions, balance in B
```

### M9: Runoff Percentage
```
Name: Runoff Percentage
Code: ROUND((cfo_banking_demo.ml_models.deposit_runoff_forecasts.projected_balance_billions - cfo_banking_demo.ml_models.deposit_runoff_forecasts.current_balance_billions) / cfo_banking_demo.ml_models.deposit_runoff_forecasts.current_balance_billions * 100, 1)
Instructions: Projected deposit runoff percentage over forecast period. Use with deposit_runoff_forecasts table.
Synonyms: runoff pct, balance decline %, attrition rate
```

### M10: Efficiency Ratio
```
Name: Efficiency Ratio
Code: ROUND(cfo_banking_demo.ml_models.ppnr_forecasts.non_interest_expense / (cfo_banking_demo.ml_models.ppnr_forecasts.net_interest_income + cfo_banking_demo.ml_models.ppnr_forecasts.non_interest_income) * 100, 1)
Instructions: Operating efficiency ratio. Formula: Non-Interest Expense / (NII + Non-Interest Income) × 100%. <50% = highly efficient, 50-60% = good, >70% = inefficient. Use with ppnr_forecasts table.
Synonyms: efficiency ratio, expense ratio, operating efficiency
```

### M11: LCR Ratio
```
Name: LCR Ratio
Code: ROUND(cfo_banking_demo.gold_regulatory.lcr_daily.total_hqla / cfo_banking_demo.gold_regulatory.lcr_daily.net_outflows * 100, 1)
Instructions: Liquidity Coverage Ratio per Basel III. Formula: HQLA / Net Cash Outflows × 100%. Must be ≥100% to comply. Use with lcr_daily table.
Synonyms: liquidity coverage ratio, LCR, Basel III liquidity
```

---

## 🏷️ DIMENSIONS (6)

### D1: Risk Level Category
```
Name: Risk Level Category
Code: CASE WHEN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.rate_gap < -0.02 THEN 'Critical' WHEN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.rate_gap < -0.01 THEN 'High Risk' WHEN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.rate_gap < 0 THEN 'Moderate Risk' ELSE 'Low Risk' END
Instructions: Categorize accounts by rate gap risk level. Critical = rate gap < -2%, High Risk = -2% to -1%, Moderate = -1% to 0%, Low = 0%+.
Synonyms: risk category, risk tier, risk level
```

### D2: Balance Tier
```
Name: Balance Tier
Code: CASE WHEN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.balance_millions < 0.1 THEN 'Small (<$100K)' WHEN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.balance_millions < 1 THEN 'Medium ($100K-$1M)' WHEN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.balance_millions < 10 THEN 'Large ($1M-$10M)' ELSE 'Very Large (>$10M)' END
Instructions: Categorize accounts by balance size. Small = <$100K, Medium = $100K-$1M, Large = $1M-$10M, Very Large = >$10M.
Synonyms: balance category, account size, balance bucket
```

### D3: Beta Sensitivity Category
```
Name: Beta Sensitivity Category
Code: CASE WHEN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.target_beta < 0.3 THEN 'Low Sensitivity (Sticky)' WHEN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.target_beta < 0.6 THEN 'Medium Sensitivity' ELSE 'High Sensitivity (Elastic)' END
Instructions: Categorize accounts by beta sensitivity. Low (<0.3) = sticky deposits, Medium (0.3-0.6) = moderate sensitivity, High (>0.6) = rate chasers.
Synonyms: beta category, rate sensitivity tier, stickiness level
```

### D4: Capital Adequacy Status
```
Name: Capital Adequacy Status
Code: CASE WHEN cfo_banking_demo.ml_models.stress_test_results.eve_cet1_ratio >= 0.105 THEN 'Well Capitalized' WHEN cfo_banking_demo.ml_models.stress_test_results.eve_cet1_ratio >= 0.07 THEN 'Adequately Capitalized' ELSE 'Undercapitalized' END
Instructions: Categorize bank capital status per regulatory thresholds. Well Capitalized = CET1 ≥10.5%, Adequately Capitalized = 7-10.5%, Undercapitalized = <7%.
Synonyms: capital status, CET1 category, capital tier
```

### D5: LCR Compliance Status
```
Name: LCR Compliance Status
Code: CASE WHEN cfo_banking_demo.gold_regulatory.lcr_daily.lcr_ratio >= 120 THEN 'Strong' WHEN cfo_banking_demo.gold_regulatory.lcr_daily.lcr_ratio >= 100 THEN 'Compliant' ELSE 'Below Minimum' END
Instructions: Categorize LCR compliance. Strong = ≥120%, Compliant = 100-120%, Below Minimum = <100% (regulatory violation).
Synonyms: LCR status, liquidity status, LCR compliance
```

### D6: Balance in Millions
```
Name: Balance in Millions
Code: cfo_banking_demo.bronze_core_banking.deposit_accounts.current_balance / 1000000
Instructions: Convert account balance to millions. Use on deposit_accounts table with current_balance column.
Synonyms: balance millions, balance in MM
```

---

## 🔍 FILTERS (6)

### F1: Latest Data Only
```
Name: Latest Data Only
Code: effective_date = (SELECT MAX(effective_date) FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced)
Instructions: Filter to most recent data snapshot. Use when querying deposit_beta_training_enhanced to avoid duplicates across time periods.
Synonyms: most recent, current data, latest snapshot
```

### F2: Active Accounts Only
```
Name: Active Accounts Only
Code: cfo_banking_demo.bronze_core_banking.deposit_accounts.is_current = TRUE AND cfo_banking_demo.bronze_core_banking.deposit_accounts.account_status = 'Active'
Instructions: Filter to active deposit accounts (excludes closed and dormant accounts).
Synonyms: active only, open accounts, current accounts
```

### F3: Strategic Customers
```
Name: Strategic Customers
Code: cfo_banking_demo.ml_models.deposit_beta_training_enhanced.relationship_category = 'Strategic'
Instructions: Filter to Strategic relationship category (core banking relationships with low beta ~0.2-0.4).
Synonyms: strategic only, strategic segment
```

### F4: At-Risk Accounts
```
Name: At-Risk Accounts
Code: cfo_banking_demo.ml_models.deposit_beta_training_enhanced.below_competitor_rate = 1
Instructions: Filter to accounts priced below market competitive rate (flight risk requiring retention action).
Synonyms: at risk only, flight risk, below market
```

### F5: High Balance Accounts
```
Name: High Balance Accounts
Code: cfo_banking_demo.bronze_core_banking.deposit_accounts.current_balance > 10000000
Instructions: Filter to accounts with balance over $10M (very large accounts requiring priority management).
Synonyms: high balance, large accounts, >$10M
```

### F6: Below Market Rate
```
Name: Below Market Rate
Code: cfo_banking_demo.ml_models.deposit_beta_training_enhanced.rate_gap < 0
Instructions: Filter to accounts where stated rate is below market fed funds rate (negative rate gap).
Synonyms: below market, negative rate gap, underpriced
```

---

## ✅ Checklist

Progress: `[ ]` = Not started, `[x]` = Complete

### Measures
- [ ] M1: Total Account Count
- [ ] M2: Total Balance (Millions)
- [ ] M3: Average Deposit Beta
- [ ] M4: Average Interest Rate
- [ ] M5: At-Risk Account Count
- [ ] M6: At-Risk Percentage
- [ ] M7: Critical Risk Count
- [ ] M8: Balance in Billions
- [ ] M9: Runoff Percentage
- [ ] M10: Efficiency Ratio
- [ ] M11: LCR Ratio

### Dimensions
- [ ] D1: Risk Level Category
- [ ] D2: Balance Tier
- [ ] D3: Beta Sensitivity Category
- [ ] D4: Capital Adequacy Status
- [ ] D5: LCR Compliance Status
- [ ] D6: Balance in Millions

### Filters
- [ ] F1: Latest Data Only
- [ ] F2: Active Accounts Only
- [ ] F3: Strategic Customers
- [ ] F4: At-Risk Accounts
- [ ] F5: High Balance Accounts
- [ ] F6: Below Market Rate

**Total: 0/23 complete**

---

## 🚀 Test Queries After Adding

```
"What is the average deposit beta?"
"Show me at-risk accounts by risk level category"
"What is the LCR ratio status?"
"Show me balance tiers for Strategic customers"
"What is the efficiency ratio for latest data only?"
```

---

**Estimated Time to Add All 23:** ~15-20 minutes
**Source:** VERIFIED_QUERIES.md (all expressions tested January 2026)
