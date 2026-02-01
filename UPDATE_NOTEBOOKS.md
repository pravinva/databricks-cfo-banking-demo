# How to Update Databricks Notebooks from GitHub

The notebooks in your Databricks workspace are **out of date**. They don't have the latest changes from GitHub.

## Problem
You ran Phase 1 notebook, but it doesn't have the `cohort_quarter` column that was added in commit af03a9f.

## Solution: Re-import Updated Notebooks

### Option 1: Using Databricks UI
1. **Delete old notebooks** in Databricks workspace:
   - Navigate to `/Users/pravin.varma@databricks.com/`
   - Delete (or rename) the old Phase 1, 2, and 3 notebooks

2. **Re-import from local files**:
   - Click "Import" in Databricks workspace
   - Select `notebooks/Phase1_Enhanced_Deposit_Beta_Model.py` (updated version)
   - Select `notebooks/Phase2_Vintage_Analysis_and_Decay_Modeling.py` (updated version)
   - Select `notebooks/Phase3_Dynamic_Beta_and_Stress_Testing.py` (updated version)

### Option 2: Using Databricks CLI (Faster)
```bash
# Upload Phase 1 (with cohort_quarter added)
databricks workspace import \
  notebooks/Phase1_Enhanced_Deposit_Beta_Model.py \
  /Users/pravin.varma@databricks.com/Phase1_Enhanced_Deposit_Beta_Model \
  --language PYTHON \
  --overwrite

# Upload Phase 2 (with is_closed filter and proper JOINs)
databricks workspace import \
  notebooks/Phase2_Vintage_Analysis_and_Decay_Modeling.py \
  /Users/pravin.varma@databricks.com/Phase2_Vintage_Analysis_and_Decay_Modeling \
  --language PYTHON \
  --overwrite

# Upload Phase 3
databricks workspace import \
  notebooks/Phase3_Dynamic_Beta_and_Stress_Testing.py \
  /Users/pravin.varma@databricks.com/Phase3_Dynamic_Beta_and_Stress_Testing \
  --language PYTHON \
  --overwrite
```

## What Changed

### Phase 1 (commit af03a9f)
**Line 186-188** - Added:
```sql
-- Cohort information (for Phase 2 vintage analysis)
d.account_open_date,
DATE_TRUNC('quarter', d.account_open_date) as cohort_quarter,
```

### Phase 2 (multiple commits)
- Added `is_closed` field to account_history CTE
- Fixed ABGR calculation to use `WHERE is_closed = FALSE`
- Fixed Step 3.1 JOINs to use proper cohort_quarter matching

## After Re-importing

1. **Re-run Phase 1 Step 2.1** (Create Enhanced Training Dataset)
   - This will regenerate the training table with `cohort_quarter`

2. **Continue Phase 2 from Step 3.1**
   - The JOIN error will be resolved

## Verification

After re-running Phase 1, check that the column exists:
```sql
DESCRIBE TABLE cfo_banking_demo.ml_models.deposit_beta_training_enhanced
```

You should see:
- `account_open_date` (date)
- `cohort_quarter` (date)
