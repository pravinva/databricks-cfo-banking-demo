# Add Tables to Genie Space - Complete Guide

## ⚠️ IMPORTANT: Start Here!

Your Genie Space **"Treasury Modeling - Deposits & Fee Income"** currently has **0 tables** configured. Tables must be added first before SQL expressions or sample questions will work.

**Error you're seeing:**
```
"There are currently no tables available in the database"
```

**Solution:** Add all 12 tables through the Databricks UI.

---

## 📋 Quick Steps (5 minutes)

### Step 1: Open Genie Space Configuration
1. Go to Databricks → **Genie** → "Treasury Modeling - Deposits & Fee Income"
2. Click **"Configure"** button (top right)
3. Go to **"Tables"** tab

### Step 2: Add All 12 Tables

Click **"Add tables"** and add these tables one by one (or use search to add multiple):

```
cfo_banking_demo.ml_models.deposit_beta_training_enhanced
cfo_banking_demo.bronze_core_banking.deposit_accounts
cfo_banking_demo.ml_models.component_decay_metrics
cfo_banking_demo.ml_models.cohort_survival_rates
cfo_banking_demo.ml_models.deposit_runoff_forecasts
cfo_banking_demo.ml_models.dynamic_beta_parameters
cfo_banking_demo.ml_models.stress_test_results
cfo_banking_demo.gold_regulatory.lcr_daily
cfo_banking_demo.gold_regulatory.hqla_inventory
cfo_banking_demo.ml_models.ppnr_forecasts
cfo_banking_demo.ml_models.non_interest_income_training_data
cfo_banking_demo.ml_models.non_interest_expense_training_data
```

### Step 3: Save
Click **"Save"** button

### Step 4: Test
Try query: `"What is the average deposit beta?"`

**Estimated time:** 5 minutes

---

## 📊 Tables by Domain

### Deposit Beta Modeling (2 tables)
```
cfo_banking_demo.ml_models.deposit_beta_training_enhanced
cfo_banking_demo.bronze_core_banking.deposit_accounts
```

**Purpose:** Rate sensitivity analysis, at-risk account identification, customer segmentation

---

### Vintage Analysis (3 tables)
```
cfo_banking_demo.ml_models.component_decay_metrics
cfo_banking_demo.ml_models.cohort_survival_rates
cfo_banking_demo.ml_models.deposit_runoff_forecasts
```

**Purpose:** Chen component decay model, Kaplan-Meier survival curves, 3-year runoff projections

---

### Stress Testing (4 tables)
```
cfo_banking_demo.ml_models.dynamic_beta_parameters
cfo_banking_demo.ml_models.stress_test_results
cfo_banking_demo.gold_regulatory.lcr_daily
cfo_banking_demo.gold_regulatory.hqla_inventory
```

**Purpose:** CCAR stress scenarios, CET1 capital ratios, LCR compliance, HQLA reporting

---

### PPNR Modeling (3 tables)
```
cfo_banking_demo.ml_models.ppnr_forecasts
cfo_banking_demo.ml_models.non_interest_income_training_data
cfo_banking_demo.ml_models.non_interest_expense_training_data
```

**Purpose:** Pre-provision net revenue forecasting, fee income analysis, efficiency ratios

---

## ✅ Checklist

Track your progress as you add tables:

### Deposit Beta
- [ ] cfo_banking_demo.ml_models.deposit_beta_training_enhanced
- [ ] cfo_banking_demo.bronze_core_banking.deposit_accounts

### Vintage Analysis
- [ ] cfo_banking_demo.ml_models.component_decay_metrics
- [ ] cfo_banking_demo.ml_models.cohort_survival_rates
- [ ] cfo_banking_demo.ml_models.deposit_runoff_forecasts

### Stress Testing
- [ ] cfo_banking_demo.ml_models.dynamic_beta_parameters
- [ ] cfo_banking_demo.ml_models.stress_test_results
- [ ] cfo_banking_demo.gold_regulatory.lcr_daily
- [ ] cfo_banking_demo.gold_regulatory.hqla_inventory

### PPNR Modeling
- [ ] cfo_banking_demo.ml_models.ppnr_forecasts
- [ ] cfo_banking_demo.ml_models.non_interest_income_training_data
- [ ] cfo_banking_demo.ml_models.non_interest_expense_training_data

**Progress: 0/12 complete**

---

## 🧪 Test Queries After Adding Tables

Once all 12 tables are added, test with these queries:

### Basic Tests
```
What is the average deposit beta?
How many deposit accounts do we have?
What is the LCR ratio?
```

### Cross-Table Tests
```
Show me at-risk accounts for Strategic customers
What is the 3-year runoff forecast by segment?
What is the CET1 ratio under severely adverse scenario?
```

### Expected Results
- Queries should return actual data (not "no tables available")
- Genie should generate SQL using the 12 tables
- Results should show deposit betas, account counts, ratios, etc.

---

## 🔧 Troubleshooting

### Problem: "No tables available"
**Solution:** Tables not added yet. Follow Step 1-3 above.

### Problem: "Table not found" error
**Solution:** Check table exists in Unity Catalog:
```bash
databricks tables list --catalog cfo_banking_demo --schema ml_models
```

### Problem: Permission denied
**Solution:** Grant SELECT permission on tables:
```sql
GRANT SELECT ON TABLE cfo_banking_demo.ml_models.* TO `users`;
GRANT SELECT ON TABLE cfo_banking_demo.bronze_core_banking.* TO `users`;
GRANT SELECT ON TABLE cfo_banking_demo.gold_regulatory.* TO `users`;
```

### Problem: Tables added but queries still fail
**Solution:**
1. Refresh Genie Space (click refresh icon)
2. Wait 1-2 minutes for indexing
3. Try query again

---

## 📚 Table Descriptions

### 1. deposit_beta_training_enhanced
**Rows:** ~402,000 accounts
**Key Columns:** `target_beta`, `balance_millions`, `rate_gap`, `relationship_category`, `below_competitor_rate`
**Use For:** Rate sensitivity analysis, at-risk identification

### 2. deposit_accounts
**Rows:** ~400,000 accounts
**Key Columns:** `current_balance`, `product_type`, `account_status`, `stated_rate`
**Use For:** Portfolio reporting, balance aggregations

### 3. component_decay_metrics
**Rows:** 15 (by relationship_category x product_type)
**Key Columns:** `lambda_closure_rate`, `g_abgr`, `relationship_category`
**Use For:** Chen decay model parameters

### 4. cohort_survival_rates
**Rows:** ~180 (36 months x 5 segments)
**Key Columns:** `account_survival_rate`, `months_since_open`, `relationship_category`
**Use For:** Kaplan-Meier survival curves

### 5. deposit_runoff_forecasts
**Rows:** ~45 (3 forecast horizons x 15 segments)
**Key Columns:** `projected_balance_billions`, `months_ahead`, `relationship_category`
**Use For:** 3-year runoff projections

### 6. dynamic_beta_parameters
**Rows:** 3 (one per relationship_category)
**Key Columns:** `beta_min`, `beta_max`, `k_steepness`, `R0_inflection`
**Use For:** Sigmoid beta response curves

### 7. stress_test_results
**Rows:** 3 (one per scenario)
**Key Columns:** `eve_cet1_ratio`, `delta_nii_millions`, `scenario_name`
**Use For:** CCAR stress test results

### 8. lcr_daily
**Rows:** ~365 (daily snapshots)
**Key Columns:** `lcr_ratio`, `total_hqla`, `net_outflows`
**Use For:** Daily LCR monitoring

### 9. hqla_inventory
**Rows:** ~500 securities
**Key Columns:** `hqla_level`, `market_value`, `security_type`
**Use For:** HQLA composition analysis

### 10. ppnr_forecasts
**Rows:** ~27 (9 quarters x 3 scenarios)
**Key Columns:** `ppnr`, `net_interest_income`, `non_interest_expense`
**Use For:** PPNR projections

### 11. non_interest_income_training_data
**Rows:** ~60 months
**Key Columns:** `target_fee_income`, `active_deposit_accounts`, `total_transactions_millions`
**Use For:** Fee income forecasting

### 12. non_interest_expense_training_data
**Rows:** ~60 months
**Key Columns:** `target_operating_expense`, `active_accounts`, `total_assets_billions`
**Use For:** Operating expense forecasting

---

## 🎯 After Tables Are Added

Once all 12 tables are successfully added:

### Next Steps:
1. ✅ **Add SQL Expressions** (23 expressions) - See `SQL_EXPRESSIONS_QUICK_ADD.md`
2. ✅ **Add Sample Questions** (26 questions) - See `SAMPLE_QUESTIONS_TO_ADD.md`
3. ✅ **Test Queries** - Verify Genie generates correct SQL
4. ✅ **Train Users** - Show team how to use Genie Space

### Total Setup Time:
- **Add Tables:** 5 minutes (this document)
- **Add SQL Expressions:** 20 minutes
- **Add Sample Questions:** 10 minutes
- **Total:** ~35 minutes

---

## 🚀 Summary

**Current Status:** 0/12 tables ❌
**Required:** 12/12 tables ✅

**To fix the "no tables available" error:**
1. Open Genie Space → Configure → Tables tab
2. Add all 12 tables listed above
3. Save
4. Test with: "What is the average deposit beta?"

**Once tables are added, your Genie Space will work! 🎉**
