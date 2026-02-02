# Development & Utility Scripts

This directory contains development, diagnostic, and utility scripts used during the project's development phase. These scripts are kept for reference and troubleshooting purposes.

## 📊 Demo Data Setup & Catalog Management

**Purpose**: Scripts for creating, populating, and managing demo data in Unity Catalog

- `generate_deposit_history.py` - Generates historical deposit snapshots for treasury modeling
- `backfill_historical_yields.py` - Backfills treasury yield curves from Alpha Vantage API
- `add_fed_funds_rate.py` - Adds Federal Funds Rate data to yield curve tables
- `run_gl_backfill.py` - Backfills general ledger entries for historical transactions
- `explore_catalog.py` - Explores Unity Catalog structure, tables, and metadata

**Permissions Management**:
- `grant_all_users.py` - Grants Unity Catalog permissions to all workspace users
- `grant_permissions.py` - Manages fine-grained table/schema permissions
- `grant_warehouse_access.py` - Grants SQL Warehouse access for query execution

## ✅ Data Validation & Quality Checks

**Purpose**: Validate data integrity, schema compliance, and quality

- `check_data_requirements.py` - Validates that all required tables and data exist
- `check_schema.py` - Validates table schemas match specifications
- `check_gl_data.py` - Checks general ledger data quality and balance validation
- `check_training_columns.py` - Verifies ML training data has required columns
- `check_yield_curves_schema.py` - Validates treasury yield curve table schema
- `verify_fed_funds_rate.py` - Verifies Federal Funds Rate data completeness
- `verify_historical_data_quality.py` - Comprehensive historical data quality checks
- `verify_historical_table.py` - Validates historical deposit data table
- `check_existing_alphavantage_data.py` - Checks Alpha Vantage API data cache

## 🔍 Diagnostics & Troubleshooting

**Purpose**: Debug treasury modeling calculations and ML model data

- `diagnose_abgr.py` - Diagnoses Account Beta Growth Rate (ABGR) calculations
- `diagnose_cohort_survival.py` - Diagnoses vintage cohort survival analysis data
- `diagnose_component_decay.py` - Diagnoses deposit component decay model data
- `analyze_schema_gaps.py` - Identifies missing schema elements or table inconsistencies

## 🤖 ML Model Serving

**Purpose**: Create and configure ML model serving endpoints

- `create_endpoint_simple.py` - Creates simple ML model serving endpoint
- `create_serving_endpoint.py` - Creates full-featured model serving endpoint with autoscaling

## Usage Notes

- These scripts were primarily used during development and may have dependencies on specific Databricks workspace configurations or external APIs (Alpha Vantage)
- Most functionality has been consolidated into production notebooks (`/notebooks/`) and organized scripts (`/outputs/scripts/`)
- These scripts are kept for reference, troubleshooting, and understanding the data generation process

## Production Alternatives

For production data generation and pipeline management, use:
- `/notebooks/Phase_1_Bronze_Tables.py` - Production data generation
- `/notebooks/Phase_2_DLT_Pipelines.py` - Delta Live Tables pipelines
- `/notebooks/Phase_3_*` - ML model training, deployment, and batch inference
- `/outputs/scripts/` - Production-ready scripts organized by category

## Running Scripts

All scripts expect to be run from the repository root:

```bash
cd /path/to/databricks-cfo-banking-demo
python3 dev-scripts/backfill_historical_yields.py
```

Ensure Databricks authentication is configured:
```bash
export DATABRICKS_HOST="https://<workspace-url>"
export DATABRICKS_TOKEN="<your-token>"
```
