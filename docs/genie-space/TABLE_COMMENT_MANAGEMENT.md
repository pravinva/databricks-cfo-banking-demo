# Genie Space Table Comment Management

## Overview

This document provides instructions for managing Unity Catalog table and column comments for the **Treasury Modeling - Deposits & Fee Income** Genie Space. These comments are critical for enabling accurate natural language querying via Databricks Genie.

## Status

**✅ All Comments Applied Successfully**

- **Total Tables:** 12/12 (100% complete)
- **Total SQL Statements:** 217
  - Table-level comments: 12
  - Column-level comments: 205
- **Last Updated:** See git log for scripts/genie_table_comments.sql

## Table List

All 12 Genie Space tables have complete metadata:

1. ✅ `cfo_banking_demo.ml_models.deposit_beta_training_enhanced` (41 columns)
2. ✅ `cfo_banking_demo.bronze_core_banking.deposit_accounts` (36 columns)
3. ✅ `cfo_banking_demo.ml_models.component_decay_metrics` (12 columns)
4. ✅ `cfo_banking_demo.ml_models.cohort_survival_rates` (16 columns)
5. ✅ `cfo_banking_demo.ml_models.deposit_runoff_forecasts` (10 columns)
6. ✅ `cfo_banking_demo.ml_models.dynamic_beta_parameters` (6 columns)
7. ✅ `cfo_banking_demo.ml_models.stress_test_results` (10 columns)
8. ✅ `cfo_banking_demo.gold_regulatory.lcr_daily` (12 columns)
9. ✅ `cfo_banking_demo.gold_regulatory.hqla_inventory` (7 columns)
10. ✅ `cfo_banking_demo.ml_models.ppnr_forecasts` (7 columns)
11. ✅ `cfo_banking_demo.ml_models.non_interest_income_training_data` (27 columns)
12. ✅ `cfo_banking_demo.ml_models.non_interest_expense_training_data` (21 columns)

## Automated Scripts

### Location
All scripts are in `scripts/` directory:
- `scripts/update_genie_table_comments.py` - Main comment generator
- `scripts/genie_table_comments.sql` - Generated SQL statements
- `scripts/execute_all_comments.py` - Execution script
- `scripts/check_comment_status.py` - Verification script

### Script Descriptions

#### 1. `update_genie_table_comments.py`
**Purpose:** Query Unity Catalog schemas and generate SQL COMMENT statements

**What it does:**
- Queries Databricks CLI for actual table schemas
- Generates table-level comments (pre-defined)
- Generates column-level comments (inferred from column names)
- Outputs SQL to `scripts/genie_table_comments.sql`
- Outputs human-readable summary to `scripts/genie_schema_summary.txt`

**Usage:**
```bash
python3 scripts/update_genie_table_comments.py
```

**Output:**
```
Querying Databricks schemas...
✓ cfo_banking_demo.ml_models.deposit_beta_training_enhanced (41 columns)
✓ cfo_banking_demo.bronze_core_banking.deposit_accounts (36 columns)
...

Generated files:
  scripts/genie_table_comments.sql (217 statements)
  scripts/genie_schema_summary.txt (schema reference)
```

#### 2. `execute_all_comments.py`
**Purpose:** Execute all SQL COMMENT statements in Databricks

**What it does:**
- Reads `scripts/genie_table_comments.sql`
- Executes each COMMENT statement via Databricks CLI
- Shows progress with ✓/✗ indicators
- Handles rate limiting with delays

**Usage:**
```bash
python3 scripts/execute_all_comments.py
```

**Output:**
```
Reading SQL statements...
Found 217 COMMENT statements

Executing statements...
================================================================================
[1/217] ml_models.deposit_beta_training_enhanced... ✓
[2/217] ml_models.deposit_beta_training_enhanced.account_id... ✓
[3/217] ml_models.deposit_beta_training_enhanced.customer_id... ✓
...
[217/217] ml_models.non_interest_expense_training_data.prior_month_accounts... ✓

================================================================================
Execution Complete
  Success: 217/217
  Failed:  0/217
================================================================================

✅ All table and column comments updated successfully!

Verify in Databricks:
  1. Open Unity Catalog Data Explorer
  2. Navigate to cfo_banking_demo catalog
  3. Check table and column descriptions
```

#### 3. `check_comment_status.py`
**Purpose:** Verify which tables and columns have comments applied

**What it does:**
- Queries Unity Catalog for each table's metadata
- Counts columns with/without comments
- Shows completion percentage per table

**Usage:**
```bash
python3 scripts/check_comment_status.py
```

**Output:**
```
====================================================================================================
GENIE SPACE TABLE COMMENT STATUS
====================================================================================================

[1/12] ml_models.deposit_beta_training_enhanced
  ✓ Table comment: Phase 1 Deposit Beta Model - Training dataset with 41 features...
  ✓ Column comments: 41/41 (100%)

[2/12] bronze_core_banking.deposit_accounts
  ✓ Table comment: Bronze layer deposit account master data from core banking system...
  ✓ Column comments: 36/36 (100%)

...

[12/12] ml_models.non_interest_expense_training_data
  ✓ Table comment: Non-interest expense training data for PPNR forecasting models...
  ✓ Column comments: 21/21 (100%)
```

## Complete Workflow

### Initial Setup (One-Time)

1. **Generate SQL comments from schemas:**
   ```bash
   cd /Users/pravin.varma/Documents/Demo/databricks-cfo-banking-demo
   python3 scripts/update_genie_table_comments.py
   ```

2. **Execute all comment statements:**
   ```bash
   python3 scripts/execute_all_comments.py
   ```

3. **Verify completion:**
   ```bash
   python3 scripts/check_comment_status.py
   ```

### When Schemas Change

If table schemas change (new columns added, columns renamed, etc.):

1. **Regenerate SQL from current schemas:**
   ```bash
   python3 scripts/update_genie_table_comments.py
   ```

2. **Review the diff (optional but recommended):**
   ```bash
   git diff scripts/genie_table_comments.sql
   ```

3. **Apply updated comments:**
   ```bash
   python3 scripts/execute_all_comments.py
   ```

4. **Verify:**
   ```bash
   python3 scripts/check_comment_status.py
   ```

### When Comments Are Missing

If the verification script shows missing comments:

**Scenario 1: Partial completion (e.g., 10/21 columns)**
```bash
# Re-run the execution script (it will re-apply all comments, safe to run multiple times)
python3 scripts/execute_all_comments.py
```

**Scenario 2: Specific table needs updating**
```bash
# Extract specific table's comments from the SQL file
grep "cfo_banking_demo.ml_models.ppnr_forecasts" scripts/genie_table_comments.sql > /tmp/ppnr_comments.sql

# Apply manually via Databricks SQL Editor or CLI
databricks experimental apps-mcp tools query "$(cat /tmp/ppnr_comments.sql)"
```

## Manual Verification

### Via Databricks UI
1. Navigate to **Catalog** > **Data** in Databricks workspace
2. Select `cfo_banking_demo` catalog
3. Expand schema (e.g., `ml_models`)
4. Click on table (e.g., `deposit_beta_training_enhanced`)
5. View **Description** field for table comment
6. Click **Schema** tab to see column comments

### Via Databricks CLI
```bash
# Check specific table
databricks tables get cfo_banking_demo.ml_models.deposit_beta_training_enhanced --output json | jq '.comment'

# Check specific column
databricks tables get cfo_banking_demo.ml_models.deposit_beta_training_enhanced --output json | \
  jq '.columns[] | select(.name == "target_beta") | .comment'
```

### Via SQL
```sql
-- Check table comment
DESCRIBE TABLE EXTENDED cfo_banking_demo.ml_models.deposit_beta_training_enhanced;

-- Check column comments
DESCRIBE TABLE cfo_banking_demo.ml_models.deposit_beta_training_enhanced;
```

## Sample Comments

### Table-Level Comment Example
```sql
COMMENT ON TABLE cfo_banking_demo.ml_models.deposit_beta_training_enhanced IS
'Phase 1 Deposit Beta Model - Training dataset with 41 features for XGBoost model achieving 7.2% MAPE accuracy. Contains rate sensitivity analysis, relationship categorization (Strategic/Tactical/Expendable), and at-risk account identification. Use for: deposit pricing strategy, rate shock analysis, customer retention, and flight risk assessment.';
```

### Column-Level Comment Examples
```sql
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.target_beta IS
'Deposit beta coefficient (DOUBLE)';

COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.account_id IS
'Unique deposit account identifier';

COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.relationship_category IS
'Relationship Category (STRING)';
```

## Troubleshooting

### Issue: "databricks command not found"
**Solution:** Ensure Databricks CLI is installed and configured
```bash
databricks --version
databricks configure --token
```

### Issue: Execution script fails with timeout
**Solution:** Increase timeout in `execute_all_comments.py` line 34:
```python
timeout=30  # Change to 60 or higher
```

### Issue: "Table not found" errors
**Solution:** Verify table exists in Unity Catalog
```bash
databricks tables get cfo_banking_demo.ml_models.deposit_beta_training_enhanced
```

### Issue: Permission denied when running COMMENT statements
**Solution:** Ensure you have MODIFY permissions on Unity Catalog objects
```sql
GRANT MODIFY ON TABLE cfo_banking_demo.ml_models.deposit_beta_training_enhanced TO `your_user@example.com`;
```

### Issue: Comments not showing in Genie Space
**Solution:**
1. Verify comments are applied in Unity Catalog (see Manual Verification above)
2. Refresh Genie Space (may take a few minutes to sync)
3. If still not showing, recreate the Genie Space with updated tables

## Best Practices

1. **Always verify after execution:**
   Run `check_comment_status.py` after applying comments

2. **Version control your SQL:**
   Commit `scripts/genie_table_comments.sql` to git after regenerating

3. **Document schema changes:**
   Update GENIE_SPACE_CONFIGURATION.md when adding/removing tables

4. **Test comments in Genie:**
   After applying comments, test sample queries in Genie Space to ensure proper NLP understanding

5. **Keep comments business-focused:**
   Comments should explain what data means to business users, not just technical details

## Related Documentation

- **Genie Space Configuration:** `docs/genie-space/GENIE_SPACE_CONFIGURATION.md`
- **Script README:** `scripts/README.md`
- **SQL Output:** `scripts/genie_table_comments.sql`
- **Schema Summary:** `scripts/genie_schema_summary.txt`

## Support

If you encounter issues:
1. Check this documentation first
2. Review script output for error messages
3. Verify Unity Catalog permissions
4. Check Databricks CLI authentication
5. Review git history for recent changes: `git log -- scripts/`
