# Genie Space Table Comments Scripts

This directory contains scripts for managing Unity Catalog table and column comments to enhance the Genie Space natural language query experience.

## Files

### 1. `update_genie_table_comments.py`
**Purpose:** Automated script to verify schemas and generate SQL COMMENT statements for all 12 Genie Space tables.

**What it does:**
- Queries actual table schemas from Databricks Unity Catalog
- Validates column names and data types
- Generates comprehensive SQL COMMENT statements
- Creates both table-level and column-level comments

**Usage:**
```bash
python3 scripts/update_genie_table_comments.py
```

**Output:**
- `scripts/genie_table_comments.sql` - Ready-to-execute SQL statements
- `scripts/genie_schema_summary.txt` - Human-readable schema summary

### 2. `genie_table_comments.sql`
**Purpose:** Generated SQL COMMENT statements for all 12 tables in the Genie Space.

**What it contains:**
- Table-level comments with business context
- Column-level comments for all 205+ columns across 12 tables
- Ready to copy-paste into Databricks SQL Editor

**How to use:**
1. Open Databricks SQL Editor
2. Copy the SQL statements from this file
3. Execute in the `cfo_banking_demo` catalog
4. Verify comments appear in Unity Catalog Data Explorer

**Tables covered:**
1. `ml_models.deposit_beta_training_enhanced` (41 columns)
2. `bronze_core_banking.deposit_accounts` (36 columns)
3. `ml_models.component_decay_metrics` (12 columns)
4. `ml_models.cohort_survival_rates` (16 columns)
5. `ml_models.deposit_runoff_forecasts` (10 columns)
6. `ml_models.dynamic_beta_parameters` (6 columns)
7. `ml_models.stress_test_results` (10 columns)
8. `gold_regulatory.lcr_daily` (12 columns)
9. `gold_regulatory.hqla_inventory` (7 columns)
10. `ml_models.ppnr_forecasts` (7 columns)
11. `ml_models.non_interest_income_training_data` (27 columns)
12. `ml_models.non_interest_expense_training_data` (21 columns)

### 3. `genie_schema_summary.txt`
**Purpose:** Human-readable summary of all table schemas.

**What it contains:**
- Complete list of all columns per table
- Data types for each column
- Total column count per table

**Use this for:**
- Quick reference when writing queries
- Documentation updates
- Verifying schema accuracy

## Workflow: Updating Table Comments

### Step 1: Run the Script
```bash
cd /Users/pravin.varma/Documents/Demo/databricks-cfo-banking-demo
python3 scripts/update_genie_table_comments.py
```

Expected output:
```
Processing cfo_banking_demo.ml_models.deposit_beta_training_enhanced...
  ✓ Found 41 columns
Processing cfo_banking_demo.bronze_core_banking.deposit_accounts...
  ✓ Found 36 columns
...
✅ SQL statements written to: scripts/genie_table_comments.sql
✅ Schema summary written to: scripts/genie_schema_summary.txt
```

### Step 2: Review Generated SQL
Open `scripts/genie_table_comments.sql` and review the COMMENT statements.

Example:
```sql
COMMENT ON TABLE cfo_banking_demo.ml_models.deposit_beta_training_enhanced IS
'Phase 1 Deposit Beta Model - Training dataset with 41 features for XGBoost model achieving 7.2% MAPE accuracy...';

COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.target_beta IS
'Deposit beta coefficient (DOUBLE)';
```

### Step 3: Execute in Databricks
1. Navigate to Databricks SQL Editor
2. Ensure you're connected to the correct workspace
3. Copy all SQL statements from `genie_table_comments.sql`
4. Execute the statements (should complete in seconds)

### Step 4: Verify in Unity Catalog
1. Go to Data Explorer in Databricks
2. Navigate to `cfo_banking_demo` catalog
3. Browse to any table (e.g., `ml_models.deposit_beta_training_enhanced`)
4. Check that table and column comments are visible

### Step 5: Test in Genie Space
1. Open the "Treasury Modeling - Deposits & Fee Income" Genie Space
2. Ask natural language questions
3. Verify Genie can understand and reference the enriched metadata

Example queries to test:
- "Show me accounts with high deposit beta"
- "What tables contain PPNR forecasts?"
- "Explain the target_beta column"

## Why This Matters

### For Genie Space
- **Better NLP understanding:** Comments help Genie interpret user intent
- **Accurate table selection:** Descriptions guide which tables to query
- **Column disambiguation:** Comments clarify similar column names across tables
- **Business context:** Explains what data means, not just technical schema

### For Data Users
- **Self-service discovery:** Users can explore data without tribal knowledge
- **Query accuracy:** Clear metadata reduces misinterpretation
- **Documentation:** Single source of truth for column meanings

### For Data Governance
- **Metadata completeness:** Unity Catalog as comprehensive data dictionary
- **Regulatory compliance:** Clear documentation for audits (CCAR, DFAST)
- **Knowledge retention:** Reduces dependency on specific team members

## Maintenance

### When to Re-run
Run `update_genie_table_comments.py` when:
- New tables are added to Genie Space
- Table schemas change (columns added/removed)
- Column names are renamed
- Business definitions change

### How to Customize Comments
Edit the `TABLE_COMMENTS` dictionary in `update_genie_table_comments.py`:

```python
TABLE_COMMENTS = {
    "cfo_banking_demo.ml_models.deposit_beta_training_enhanced":
        "Your custom description here...",
    # ... more tables
}
```

For column-level customization, edit the `infer_column_comment()` function.

## Troubleshooting

### Error: "Could not retrieve schema"
**Cause:** Databricks CLI authentication issue or table doesn't exist

**Fix:**
```bash
databricks auth login
databricks tables get cfo_banking_demo.ml_models.deposit_beta_training_enhanced
```

### Error: "Permission denied"
**Cause:** Your Databricks user lacks Unity Catalog permissions

**Fix:** Contact workspace admin to grant:
- `USE CATALOG` on `cfo_banking_demo`
- `USE SCHEMA` on relevant schemas
- `MODIFY` permission to update comments

### Comments Not Showing in Genie
**Cause:** Genie Space metadata cache not refreshed

**Fix:**
1. Edit the Genie Space configuration
2. Remove and re-add one table
3. Save changes (forces metadata refresh)

## Related Documentation

- [Genie Space Configuration](../docs/genie-space/GENIE_SPACE_CONFIGURATION.md)
- [Quick Start Guide](../docs/genie-space/QUICK_START_GENIE.md)
- [Unity Catalog Best Practices](https://docs.databricks.com/data-governance/unity-catalog/index.html)

---

**Last Updated:** February 4, 2026
**Maintainer:** Treasury Modeling Team
