# Deposit Modeling + PPNR on Databricks
## Modeler Playbook (Treasury Analytics / Model Risk / Quant)

### Goal
Provide a pragmatic guide for bank modelers to choose and implement the right approach for **deposit behavior** and connect it to **PPNR** outputs.

---

## Data foundations (minimum viable)
### Deposits (account level)
Primary tables used in this demo:
- `cfo_banking_demo.bronze_core_banking.deposit_accounts` (current state)
- `cfo_banking_demo.bronze_core_banking.deposit_accounts_historical` (history/vintages)

Key fields:
- `account_id`, `product_type`, `customer_segment`, `account_open_date`
- `current_balance`, `average_balance_30d`, `stated_rate`, `transaction_count_30d`
- `effective_date`, `is_current`, `is_closed`, `account_status`

### Market rates
- `cfo_banking_demo.silver_treasury.yield_curves` (persisted)

### PPNR
- `cfo_banking_demo.silver_finance.general_ledger` (synthetic backfill for training)
- Output: `cfo_banking_demo.ml_models.ppnr_forecasts`

---

## Choosing the approach (model selection guidance)

### Approach 1 (Static beta)
**Use when**:
- You need stable, explainable sensitivity coefficients for ALM/treasury
- You want fast refresh cycles (weekly/monthly)

**Training**:
- Notebook: `notebooks/Approach1_Enhanced_Deposit_Beta_Model.py`
- Training table: `cfo_banking_demo.ml_models.deposit_beta_training_data`
- Registry: `cfo_banking_demo.models.deposit_beta_model@champion`

**Scoring (batch)**:
- Notebook: `notebooks/Batch_Inference_Deposit_Beta_Model.py`
- Output table: `cfo_banking_demo.ml_models.deposit_beta_predictions`

### Approach 2 (Vintage / survival + decay)
**Use when**:
- You need runoff curves by cohort/tenure for liquidity modeling
- You want to separate closure vs balance decay mechanics

**Notebook**:
- `notebooks/Approach2_Vintage_Analysis_and_Decay_Modeling.py`

**Typical outputs**:
- `cfo_banking_demo.ml_models.cohort_survival_rates`
- `cfo_banking_demo.ml_models.deposit_runoff_forecasts`

### Approach 3 (Dynamic beta + stress)
**Use when**:
- You need regime-conditional, non-linear beta behavior under stress scenarios
- You must produce stress narratives / multi-horizon outputs

**Terminology note**:
- **CCAR** is the current stress testing framework.
- **DFAST** is commonly referenced as the legacy regulation behind CCAR (avoid using DFAST as the primary label).

**Notebook**:
- `notebooks/Approach3_Dynamic_Beta_and_Stress_Testing.py`

---

## Model risk & governance (bank-friendly)
Recommended controls:
- **Champion/challenger** model governance via UC registry aliases
- **Reproducibility**: feature set versioning and deterministic scoring
- **Out-of-sample checks**:
  - product-level beta distributions
  - drift checks on key drivers (rate gaps, balances, segment mix)
- **Explainability**:
  - top feature contributions stored per account (optional)

---

## PPNR integration patterns
Use deposits to drive PPNR in two common ways:
1. **Volume effect**: runoff changes balances → NII and fee base changes
2. **Pricing effect**: deposit rate strategy changes interest expense and retention

Notebook:
- `notebooks/Train_PPNR_Models.py`

---

## Practical advice (what to implement first)
- Implement **Approach 1 + batch scoring** first (gets you segmentation and an operating cadence).
- Add **Approach 2** if treasury needs runoff curves for liquidity planning.
- Add **Approach 3** if you have a stress testing requirement and need non-linear behavior.
- Integrate **PPNR** once you need the earnings narrative for ALCO.

