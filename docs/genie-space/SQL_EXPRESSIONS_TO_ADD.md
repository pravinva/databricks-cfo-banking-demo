# SQL Expressions for Genie Space: Treasury Modeling - Deposits & Fee Income

## Overview

This document contains **23 SQL expressions** (11 measures, 6 dimensions, 6 filters) to add to your Genie Space via the Databricks UI.

All expressions have been **tested and verified** against actual data (January 2026) as documented in `VERIFIED_QUERIES.md`.

---

## How to Add SQL Expressions

### Step 1: Navigate to Genie Space
1. Open Databricks workspace
2. Click **"Genie"** in left sidebar
3. Select **"Treasury Modeling - Deposits & Fee Income"** space
4. Click **"Configure"** (top right)

### Step 2: Add SQL Expressions
1. Go to **"Instructions"** tab
2. Scroll to **"SQL Expressions"** section
3. Click **"Add"** button
4. Select expression type (Measure / Dimension / Filter)
5. Fill in fields from tables below
6. Click **"Save"**

---

## MEASURES (11 Total)

Measures are aggregations and calculations used for metrics and KPIs.

### Measure 1: Total Account Count

**Name:** `Total Account Count`

**Code:**
```sql
COUNT(*)
```

**Instructions:**
Total number of deposit accounts. Use for portfolio size analysis.

**Synonyms:**
```
account count, number of accounts, total accounts
```

---

### Measure 2: Total Balance (Millions)

**Name:** `Total Balance (Millions)`

**Code:**
```sql
SUM(cfo_banking_demo.ml_models.deposit_beta_training_enhanced.balance_millions)
```

**Instructions:**
Total deposit balance in millions. Use with deposit_beta_training_enhanced table.

**Synonyms:**
```
total balance, sum of balances, total deposits
```

---

### Measure 3: Average Deposit Beta

**Name:** `Average Deposit Beta`

**Code:**
```sql
ROUND(AVG(cfo_banking_demo.ml_models.deposit_beta_training_enhanced.target_beta), 3)
```

**Instructions:**
Average deposit beta coefficient (0-1 scale). Higher beta = more rate sensitive. Strategic ~0.35, Tactical ~0.55, Expendable ~0.75.

**Synonyms:**
```
avg beta, mean beta, portfolio beta, average rate sensitivity
```

---

### Measure 4: Average Interest Rate

**Name:** `Average Interest Rate`

**Code:**
```sql
ROUND(AVG(cfo_banking_demo.ml_models.deposit_beta_training_enhanced.stated_rate), 3)
```

**Instructions:**
Average stated interest rate on deposit accounts. Expressed as decimal (0.025 = 2.5%).

**Synonyms:**
```
avg rate, mean rate, average stated rate
```

---

### Measure 5: At-Risk Account Count

**Name:** `At-Risk Account Count`

**Code:**
```sql
SUM(CASE WHEN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.below_competitor_rate = 1 THEN 1 ELSE 0 END)
```

**Instructions:**
Number of accounts priced below market competitive rate (flight risk accounts requiring retention action).

**Synonyms:**
```
at risk count, flight risk accounts, below market accounts
```

---

### Measure 6: At-Risk Percentage

**Name:** `At-Risk Percentage`

**Code:**
```sql
ROUND(SUM(CASE WHEN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.below_competitor_rate = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
```

**Instructions:**
Percentage of accounts at risk (priced below market). Test result: 87.0% of portfolio.

**Synonyms:**
```
at risk pct, flight risk percentage, at risk %
```

---

### Measure 7: Critical Risk Count

**Name:** `Critical Risk Count`

**Code:**
```sql
SUM(CASE WHEN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.rate_gap < -0.02 THEN 1 ELSE 0 END)
```

**Instructions:**
Number of accounts with rate gap < -2% (critical flight risk requiring immediate action).

**Synonyms:**
```
critical accounts, severely at risk
```

---

### Measure 8: Balance in Billions

**Name:** `Balance in Billions`

**Code:**
```sql
SUM(cfo_banking_demo.bronze_core_banking.deposit_accounts.current_balance) / 1000000000
```

**Instructions:**
Total balance in billions. Use for aggregated portfolio reporting.

**Synonyms:**
```
balance billions, balance in B
```

---

### Measure 9: Runoff Percentage

**Name:** `Runoff Percentage`

**Code:**
```sql
ROUND((cfo_banking_demo.ml_models.deposit_runoff_forecasts.projected_balance_billions - cfo_banking_demo.ml_models.deposit_runoff_forecasts.current_balance_billions) / cfo_banking_demo.ml_models.deposit_runoff_forecasts.current_balance_billions * 100, 1)
```

**Instructions:**
Projected deposit runoff percentage over forecast period. Use with deposit_runoff_forecasts table.

**Synonyms:**
```
runoff pct, balance decline %, attrition rate
```

---

### Measure 10: Efficiency Ratio

**Name:** `Efficiency Ratio`

**Code:**
```sql
ROUND(cfo_banking_demo.ml_models.ppnr_forecasts.non_interest_expense / (cfo_banking_demo.ml_models.ppnr_forecasts.net_interest_income + cfo_banking_demo.ml_models.ppnr_forecasts.non_interest_income) * 100, 1)
```

**Instructions:**
Operating efficiency ratio. Formula: Non-Interest Expense / (NII + Non-Interest Income) × 100%. <50% = highly efficient, 50-60% = good, >70% = inefficient. Use with ppnr_forecasts table.

**Synonyms:**
```
efficiency ratio, expense ratio, operating efficiency
```

---

### Measure 11: LCR Ratio

**Name:** `LCR Ratio`

**Code:**
```sql
ROUND(cfo_banking_demo.gold_regulatory.lcr_daily.total_hqla / cfo_banking_demo.gold_regulatory.lcr_daily.net_outflows * 100, 1)
```

**Instructions:**
Liquidity Coverage Ratio per Basel III. Formula: HQLA / Net Cash Outflows × 100%. Must be ≥100% to comply. Use with lcr_daily table.

**Synonyms:**
```
liquidity coverage ratio, LCR, Basel III liquidity
```

---

## DIMENSIONS (6 Total)

Dimensions are derived columns used for categorization and grouping.

### Dimension 1: Risk Level Category

**Name:** `Risk Level Category`

**Code:**
```sql
CASE
    WHEN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.rate_gap < -0.02 THEN 'Critical'
    WHEN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.rate_gap < -0.01 THEN 'High Risk'
    WHEN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.rate_gap < 0 THEN 'Moderate Risk'
    ELSE 'Low Risk'
END
```

**Instructions:**
Categorize accounts by rate gap risk level. Critical = rate gap < -2%, High Risk = -2% to -1%, Moderate = -1% to 0%, Low = 0%+.

**Synonyms:**
```
risk category, risk tier, risk level
```

---

### Dimension 2: Balance Tier

**Name:** `Balance Tier`

**Code:**
```sql
CASE
    WHEN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.balance_millions < 0.1 THEN 'Small (<$100K)'
    WHEN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.balance_millions < 1 THEN 'Medium ($100K-$1M)'
    WHEN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.balance_millions < 10 THEN 'Large ($1M-$10M)'
    ELSE 'Very Large (>$10M)'
END
```

**Instructions:**
Categorize accounts by balance size. Small = <$100K, Medium = $100K-$1M, Large = $1M-$10M, Very Large = >$10M.

**Synonyms:**
```
balance category, account size, balance bucket
```

---

### Dimension 3: Beta Sensitivity Category

**Name:** `Beta Sensitivity Category`

**Code:**
```sql
CASE
    WHEN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.target_beta < 0.3 THEN 'Low Sensitivity (Sticky)'
    WHEN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.target_beta < 0.6 THEN 'Medium Sensitivity'
    ELSE 'High Sensitivity (Elastic)'
END
```

**Instructions:**
Categorize accounts by beta sensitivity. Low (<0.3) = sticky deposits, Medium (0.3-0.6) = moderate sensitivity, High (>0.6) = rate chasers.

**Synonyms:**
```
beta category, rate sensitivity tier, stickiness level
```

---

### Dimension 4: Capital Adequacy Status

**Name:** `Capital Adequacy Status`

**Code:**
```sql
CASE
    WHEN cfo_banking_demo.ml_models.stress_test_results.eve_cet1_ratio >= 0.105 THEN 'Well Capitalized'
    WHEN cfo_banking_demo.ml_models.stress_test_results.eve_cet1_ratio >= 0.07 THEN 'Adequately Capitalized'
    ELSE 'Undercapitalized'
END
```

**Instructions:**
Categorize bank capital status per regulatory thresholds. Well Capitalized = CET1 ≥10.5%, Adequately Capitalized = 7-10.5%, Undercapitalized = <7%.

**Synonyms:**
```
capital status, CET1 category, capital tier
```

---

### Dimension 5: LCR Compliance Status

**Name:** `LCR Compliance Status`

**Code:**
```sql
CASE
    WHEN cfo_banking_demo.gold_regulatory.lcr_daily.lcr_ratio >= 120 THEN 'Strong'
    WHEN cfo_banking_demo.gold_regulatory.lcr_daily.lcr_ratio >= 100 THEN 'Compliant'
    ELSE 'Below Minimum'
END
```

**Instructions:**
Categorize LCR compliance. Strong = ≥120%, Compliant = 100-120%, Below Minimum = <100% (regulatory violation).

**Synonyms:**
```
LCR status, liquidity status, LCR compliance
```

---

### Dimension 6: Balance in Millions

**Name:** `Balance in Millions`

**Code:**
```sql
cfo_banking_demo.bronze_core_banking.deposit_accounts.current_balance / 1000000
```

**Instructions:**
Convert account balance to millions. Use on deposit_accounts table with current_balance column.

**Synonyms:**
```
balance millions, balance in MM
```

---

## FILTERS (6 Total)

Filters are common WHERE clause conditions for data filtering.

### Filter 1: Latest Data Only

**Name:** `Latest Data Only`

**Code:**
```sql
effective_date = (SELECT MAX(effective_date) FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced)
```

**Instructions:**
Filter to most recent data snapshot. Use when querying deposit_beta_training_enhanced to avoid duplicates across time periods.

**Synonyms:**
```
most recent, current data, latest snapshot
```

---

### Filter 2: Active Accounts Only

**Name:** `Active Accounts Only`

**Code:**
```sql
cfo_banking_demo.bronze_core_banking.deposit_accounts.is_current = TRUE AND cfo_banking_demo.bronze_core_banking.deposit_accounts.account_status = 'Active'
```

**Instructions:**
Filter to active deposit accounts (excludes closed and dormant accounts).

**Synonyms:**
```
active only, open accounts, current accounts
```

---

### Filter 3: Strategic Customers

**Name:** `Strategic Customers`

**Code:**
```sql
cfo_banking_demo.ml_models.deposit_beta_training_enhanced.relationship_category = 'Strategic'
```

**Instructions:**
Filter to Strategic relationship category (core banking relationships with low beta ~0.2-0.4).

**Synonyms:**
```
strategic only, strategic segment
```

---

### Filter 4: At-Risk Accounts

**Name:** `At-Risk Accounts`

**Code:**
```sql
cfo_banking_demo.ml_models.deposit_beta_training_enhanced.below_competitor_rate = 1
```

**Instructions:**
Filter to accounts priced below market competitive rate (flight risk requiring retention action).

**Synonyms:**
```
at risk only, flight risk, below market
```

---

### Filter 5: High Balance Accounts

**Name:** `High Balance Accounts`

**Code:**
```sql
cfo_banking_demo.bronze_core_banking.deposit_accounts.current_balance > 10000000
```

**Instructions:**
Filter to accounts with balance over $10M (very large accounts requiring priority management).

**Synonyms:**
```
high balance, large accounts, >$10M
```

---

### Filter 6: Below Market Rate

**Name:** `Below Market Rate`

**Code:**
```sql
cfo_banking_demo.ml_models.deposit_beta_training_enhanced.rate_gap < 0
```

**Instructions:**
Filter to accounts where stated rate is below market fed funds rate (negative rate gap).

**Synonyms:**
```
below market, negative rate gap, underpriced
```

---

## Testing Your SQL Expressions

After adding all expressions, test with these natural language queries:

### Test Measures
- "What is the average deposit beta?"
- "Show me the at-risk percentage"
- "What is the total account count?"
- "Calculate the efficiency ratio"

### Test Dimensions
- "Show me accounts by risk level category"
- "Group accounts by balance tier"
- "Show beta sensitivity categories"
- "What is the capital adequacy status?"

### Test Filters
- "Show me at-risk accounts only"
- "Filter to strategic customers"
- "Show high balance accounts"
- "Use latest data only"

### Combined Queries
- "Show me at-risk Strategic customers by risk level category"
- "What is the average beta for high balance accounts?"
- "Show me efficiency ratio for latest data only"

---

## Quick Reference: Expression Count

| Type | Count | Purpose |
|------|-------|---------|
| **Measures** | 11 | Aggregations and calculations |
| **Dimensions** | 6 | Categorization and grouping |
| **Filters** | 6 | WHERE clause conditions |
| **TOTAL** | **23** | Complete SQL expression library |

---

## Next Steps

1. ✅ Add all 23 SQL expressions via Databricks UI
2. ✅ Test with sample queries above
3. ✅ Train users on new natural language capabilities
4. ✅ Monitor query accuracy and add more expressions as needed

---

## Additional Resources

- **Verification Queries:** See `VERIFIED_QUERIES.md` for tested SQL with actual results
- **Sample Queries:** See `SAMPLE_QUERIES.md` for comprehensive query examples
- **Genie Configuration:** See `GENIE_SPACE_CONFIGURATION.md` for full setup

---

**Last Updated:** January 2026
**Status:** ✅ All expressions tested and verified against production data
