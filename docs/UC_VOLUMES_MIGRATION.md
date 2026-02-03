# Unity Catalog Volumes Migration

## Summary

Successfully migrated deposit analytics report storage from DBFS to Unity Catalog Volumes for better governance, security, and data management.

## Changes Made

### 1. Created UC Volume
- **Location**: `cfo_banking_demo.gold_finance.reports`
- **Type**: Managed Volume
- **Purpose**: Store deposit analytics HTML reports and other finance reports
- **Storage**: Backed by S3 managed by Databricks

### 2. Updated Generate_Deposit_Analytics_Report.py

**Before (DBFS):**
```python
dbfs_path = f"/dbfs/FileStore/reports/{report_filename}"
report_url = f"https://{workspace_url}/files/reports/{report_filename}"
```

**After (UC Volumes):**
```python
volume_path = f"/Volumes/cfo_banking_demo/gold_finance/reports/{report_filename}"
report_url = f"https://{workspace_url}/explore/data/volumes/cfo_banking_demo/gold_finance/reports/{report_filename}"
```

### 3. New Scripts Created

#### `dev-scripts/check_volumes.py`
- Lists all volumes in the `cfo_banking_demo` catalog
- Shows volume types and schemas
- Useful for auditing volume configuration

#### `dev-scripts/setup_reports_volume.py`
- Creates the `reports` volume if it doesn't exist
- Handles idempotent creation (safe to run multiple times)
- Provides clear output with volume paths

## Benefits of UC Volumes

1. **Centralized Governance**: All data assets managed through Unity Catalog
2. **Access Control**: Fine-grained permissions using UC access controls
3. **Audit Trail**: Complete lineage and access tracking
4. **Data Discovery**: Reports visible in Catalog Explorer UI
5. **Cross-Workspace Access**: Volumes can be accessed from multiple workspaces
6. **Better Organization**: Files grouped by schema and purpose

## Usage

### Accessing Reports in Databricks UI
Reports are now accessible at:
```
https://<workspace-url>/explore/data/volumes/cfo_banking_demo/gold_finance/reports/<filename>
```

### Writing Files to the Volume
```python
# From notebook or job
volume_path = "/Volumes/cfo_banking_demo/gold_finance/reports/my_report.html"
with open(volume_path, 'w') as f:
    f.write(html_content)
```

### Reading Files from the Volume
```python
# From notebook or job
volume_path = "/Volumes/cfo_banking_demo/gold_finance/reports/my_report.html"
with open(volume_path, 'r') as f:
    html_content = f.read()
```

### Using Spark with UC Volumes
```python
# Read files using Spark
df = spark.read.text("/Volumes/cfo_banking_demo/gold_finance/reports/")

# Write files using Spark
df.write.text("/Volumes/cfo_banking_demo/gold_finance/reports/output/")
```

## Volume Structure

```
cfo_banking_demo (catalog)
└── gold_finance (schema)
    └── reports (volume)
        ├── deposit_analytics_report_20260203_114719.html
        ├── deposit_analytics_report_20260204_093045.html
        └── ... (future reports)
```

## Setup Instructions for New Environments

If deploying to a new workspace:

1. Run the setup script:
   ```bash
   cd dev-scripts
   python3 setup_reports_volume.py
   ```

2. Verify volume creation:
   ```bash
   python3 check_volumes.py
   ```

3. Grant permissions (if needed):
   ```sql
   GRANT READ, WRITE ON VOLUME cfo_banking_demo.gold_finance.reports TO `<user-or-group>`;
   ```

## Migration Notes

- **No breaking changes**: Existing notebooks will work with UC Volumes
- **Backwards compatible**: Volume paths are standard file paths
- **Performance**: Same or better performance compared to DBFS
- **Cost**: No additional cost for using UC Volumes vs DBFS

## Existing Volumes in Catalog

The `cfo_banking_demo` catalog has the following volumes:

| Schema               | Volume Name | Type    | Purpose                          |
|---------------------|-------------|---------|----------------------------------|
| bronze_core_banking | raw         | Managed | Raw core banking data            |
| bronze_market_data  | raw         | Managed | Raw market data feeds            |
| models              | artifacts   | Managed | ML model artifacts               |
| gold_finance        | reports     | Managed | Finance reports (newly created)  |

## Related Documentation

- [Unity Catalog Volumes Docs](https://docs.databricks.com/en/connect/unity-catalog/volumes.html)
- [Databricks File System Migration](https://docs.databricks.com/en/files/index.html)
- [Unity Catalog Best Practices](https://docs.databricks.com/en/data-governance/unity-catalog/best-practices.html)

## Commit Information

- **Commit**: a1d6cc1
- **Date**: 2026-02-03
- **Files Changed**:
  - `notebooks/Generate_Deposit_Analytics_Report.py`
  - `dev-scripts/check_volumes.py` (new)
  - `dev-scripts/setup_reports_volume.py` (new)
