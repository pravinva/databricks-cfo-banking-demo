# Quick Start: Create Treasury Modeling Genie Space in 5 Minutes

## TL;DR
Create a Genie Space for **Treasury Modeling** focused on deposit modeling and PPNR fee income forecasting.
Everything is ready. Just follow these 6 steps.

---

## Step 1: Open Databricks Genie (30 seconds)
1. Log into Databricks workspace
2. Click "Genie" in left sidebar
3. Click "Create Space"

---

## Step 2: Basic Settings (30 seconds)
- **Name:** Treasury Modeling - Deposits & Fee Income
- **Description:** Natural language queries for deposit modeling (beta, vintage, CCAR stress testing) and PPNR fee income forecasting

---

## Step 3: Add 12 Tables (2 minutes)
Copy-paste this list:

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

---

## Step 4: Add Instructions (1 minute)
Open `GENIE_SPACE_CONFIGURATION.md` and copy the entire "Genie Instructions" section (lines 65-500+) into the Instructions field.

---

## Step 5: Click Create (10 seconds)

---

## Step 6: Test with Sample Query (1 minute)
Try this: "What is the CET1 ratio under severely adverse scenario?"

---

## Done! ✅

Your Genie Space is now ready for natural language queries across all 4 modeling domains.

---

## Example Queries to Try

**Deposit Beta:**
- "What is the average deposit beta for MMDA accounts?"

**Vintage Analysis:**
- "Show me the 3-year runoff forecast for Strategic customers"

**CCAR/DFAST:**
- "Does the bank pass the severely adverse stress test?"

**PPNR:**
- "What is the forecasted PPNR for next quarter under adverse scenario?"

---

## Full Documentation
See `GENIE_SPACE_CONFIGURATION.md` for complete details.

---

**Estimated Total Time:** 5 minutes
