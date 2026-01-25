# AutoML Training Instructions

## Overview
This document provides step-by-step instructions for training the Deposit Beta prediction model using Databricks AutoML in your workspace.

## Repository Information
- **GitHub Repo**: https://github.com/pravinva/databricks-cfo-banking-demo
- **Latest Commit**: 1927129 - "Add Phase 2 DLT Pipeline, Phase 3 ML Models, and Bloomberg Terminal styling"

## AutoML Notebook Location
The AutoML training notebook has been created at:
```
/Users/pravin.varma@databricks.com/Deposit_Beta_AutoML_Training
```

## Training Data Information
- **Table**: `cfo_banking_demo.ml_models.deposit_beta_training_data`
- **Records**: 4,068,060 training samples
- **Accounts**: 339,005 unique deposit accounts
- **Historical Period**: 12 months of synthetic behavior data

### Training Features
- **Rate Features**: `fed_funds_rate`, `rate_change`, `rate_direction`
- **Balance Features**: `beginning_balance`, `ending_balance`, `balance_tier`
- **Customer Features**: `product_type`, `customer_segment`, `has_online_banking`
- **Time Features**: `month`, `quarter`
- **Interaction Features**: `rate_balance_interaction`
- **Volatility Features**: `balance_volatility`

### Target Variable
- **Column**: `target` (alias for `balance_change_pct`)
- **Description**: Deposit balance change percentage in response to interest rate changes
- **Range**: -50% to +50% (outliers removed)

## Steps to Run AutoML Training

### 1. Clone Repository to Databricks Repos
```bash
# Navigate to Databricks Repos in your workspace
# Click "Add Repo"
# Enter: https://github.com/pravinva/databricks-cfo-banking-demo
```

### 2. Import Notebook
The notebook `notebooks/DLT_Loan_Origination_GL_Pipeline.py` is already in the repo, but the AutoML training notebook was uploaded directly to workspace.

**Option A: Use existing notebook** (already uploaded)
- Path: `/Users/pravin.varma@databricks.com/Deposit_Beta_AutoML_Training`

**Option B: Re-run the setup script** (if notebook is missing)
```python
python outputs/scripts/models/09_deposit_beta_model_automl.py
```

### 3. Attach to ML Runtime Cluster
- **Runtime**: ML Runtime 14.3 LTS or later
- **Node Type**: Standard_DS3_v2 or similar (minimum 14 GB memory)
- **Workers**: 2-4 workers recommended
- **Photon**: Enabled (recommended)

### 4. Run the Notebook
1. Open notebook: `/Users/pravin.varma@databricks.com/Deposit_Beta_AutoML_Training`
2. Click "Run All" or run cells sequentially
3. AutoML will:
   - Load training data from `cfo_banking_demo.ml_models.deposit_beta_training_data`
   - Train multiple algorithms (XGBoost, LightGBM, Random Forest, Linear Regression, etc.)
   - Perform hyperparameter tuning (30 minutes, 20 max trials)
   - Select best model based on R² score
   - Register model to Unity Catalog as `cfo_banking_demo.ml_models.deposit_beta_predictor`
   - Set `@champion` alias for production use

### 5. Expected Training Duration
- **AutoML Runtime**: 30-40 minutes
- **Total Notebook Runtime**: ~35-45 minutes

### 6. Expected Results
- **Best Model R²**: 0.65 - 0.85 (typical for deposit beta prediction)
- **Best Model MSE**: < 5.0
- **Algorithm**: Likely XGBoost or LightGBM (ensemble methods perform best)

## After Training Completes

### 1. Verify Model Registration
```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()

# List model versions
versions = list(w.model_versions.list(
    full_name="cfo_banking_demo.ml_models.deposit_beta_predictor"
))
print(f"Model has {len(versions)} version(s)")

# Check champion alias
for v in versions:
    print(f"Version {v.version}: aliases = {v.aliases}")
```

### 2. Deploy to Model Serving
Run the deployment script:
```bash
python outputs/scripts/models/13_deploy_model_serving.py
```

This will:
- Create a serverless Model Serving endpoint
- Deploy the `@champion` model version
- Enable auto-scaling with scale-to-zero
- Provide a REST API for real-time predictions

### 3. Test the Endpoint
```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()

# Sample prediction
test_data = {
    "dataframe_records": [{
        "fed_funds_rate": 4.5,
        "rate_change": 0.25,
        "rate_direction": "INCREASE",
        "beginning_balance": 50000.0,
        "product_type": "Savings",
        "customer_segment": "Mass_Market",
        "has_online_banking": True,
        "month": 1,
        "quarter": 1
    }]
}

response = w.serving_endpoints.query(
    name="deposit-beta-predictor-endpoint",
    dataframe_records=test_data["dataframe_records"]
)
print(response)
```

## Troubleshooting

### Training Data Not Found
If the training table doesn't exist, re-run the setup:
```bash
python outputs/scripts/models/09_deposit_beta_model_automl.py
```

### AutoML Fails with Memory Error
- Increase cluster size to Standard_DS4_v2 or larger
- Reduce `max_trials` in notebook from 20 to 10

### Model Registration Fails
- Verify Unity Catalog is enabled
- Verify schema exists: `cfo_banking_demo.ml_models`
- Check permissions on catalog

## Additional Resources

### Related Scripts
- **RWA Calculator**: `outputs/scripts/models/11_rwa_calculator.py`
- **Regulatory Reports**: `outputs/scripts/models/12_regulatory_reports.py`
- **DLT Pipeline Deployment**: `outputs/scripts/pipelines/deploy_dlt_pipeline.py`

### DLT Pipeline (Already Deployed)
- **Pipeline Name**: CFO_Banking_Demo_Loan_Origination_GL_Pipeline
- **Pipeline ID**: cd44f73d-85d2-433b-8142-9077e3068344
- **Status**: Running (processing loan origination events)

### Event Generator (Running in Background)
- **Rate**: 5 events/minute
- **Duration**: 30 minutes
- **Target Table**: `cfo_banking_demo.bronze_core_banking.loan_origination_events`

## Contact & Support
For questions or issues, refer to:
- Repository: https://github.com/pravinva/databricks-cfo-banking-demo
- Workspace: https://e2-demo-field-eng.cloud.databricks.com
