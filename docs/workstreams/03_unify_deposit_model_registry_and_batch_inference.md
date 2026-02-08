# Unify deposit beta model registry + batch inference

## Objective
Make the **deposit beta training notebook**, **batch inference notebook**, and **any other demo notebooks** use a single canonical MLflow / Unity Catalog model name and compatible feature engineering.

## Current inconsistency (must resolve)
- Training notebook registers: `cfo_banking_demo.models.deposit_beta_model`
- Batch inference loads: `cfo_banking_demo.models.deposit_beta_model`
- Mosaic demo references: `cfo_banking_demo.models.deposit_beta_model`

## Decisions (to implement)
1. Choose **one canonical model name** (recommend: `cfo_banking_demo.models.deposit_beta_model`).\n2. Update all notebooks and tooling to register/load that model name with alias `@champion`.\n3. Ensure the batch inference feature set matches the trained model’s expected schema.\n
## Required work
- Update Approach 1 training notebook registration + aliasing to the canonical name.\n- Update WS3 Mosaic demo to reference the canonical name.\n- Batch inference:\n  - Keep the feature set consistent with the canonical model.\n
## Verification
- Run-time sanity checks in notebooks:\n  - Model loads from `models:/<canonical>@champion`\n  - Scoring dataframe columns match model signature\n  - Output table `cfo_banking_demo.ml_models.deposit_beta_predictions` is produced successfully\n
## Acceptance criteria
- Exactly one deposit beta model name appears in active notebooks (not in archives).\n- Batch inference and reports consume the same prediction tables.\n- “40+ features” copy has been removed or updated to match the canonical model.\n
