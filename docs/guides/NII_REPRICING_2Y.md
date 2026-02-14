# Full NII Repricing (2Y Driver)

## Purpose

Provide an **auditable, end-to-end NII repricing engine** (assets + liabilities) driven by the **2Y rate path** used in treasury scenario planning.

This produces a quarterly `nii_projection_quarterly` table that downstream scenario planning (PPNR, stress views, dashboards) can consume.

## Inputs (existing demo tables)

- `cfo_banking_demo.bronze_core_banking.deposit_accounts_historical`
- `cfo_banking_demo.bronze_core_banking.loan_portfolio_historical`
- `cfo_banking_demo.ml_models.deposit_beta_predictions`
- `cfo_banking_demo.silver_treasury.yield_curves`
- `cfo_banking_demo.gold_finance.ppnr_scenario_drivers_quarterly` (scenario 2Y paths)

## Outputs (Unity Catalog)

In `cfo_banking_demo.gold_finance`:
- `deposit_repricing_assumptions`
- `loan_repricing_assumptions`
- `nii_projection_quarterly`

## Repricing assumptions (MVP)

- **Balances**: held constant at the latest `effective_date` snapshot.
- **Deposits**: `stated_rate` shifts by `predicted_beta × Δ(2Y)` with product-specific lags/caps/floors.
- **Loans**: `interest_rate` shifts by `pass_through × Δ(2Y)` based on `rate_type` with lags/caps/floors.
- **Quarterly interest**: computed as \(\text{balance} \times \text{rate} / 100 / 4\).

## How to run

### Option A: Notebook
- Run `notebooks/NII_Repricing_Engine_2Y.py`

### Option B: Local / CI via warehouse

1) Create scenario drivers (if you haven’t already):

```bash
DATABRICKS_CONFIG_PROFILE=DEFAULT python scripts/setup_ppnr_scenario_planning.py --warehouse-id 4b9b953939869799
```

2) Refresh NII repricing tables:

```bash
DATABRICKS_CONFIG_PROFILE=DEFAULT python scripts/setup_nii_repricing_2y.py --warehouse-id 4b9b953939869799
```

## Sanity check (SQL)

```sql
SELECT scenario_id, COUNT(*) AS quarters, MIN(quarter_start), MAX(quarter_start)
FROM cfo_banking_demo.gold_finance.nii_projection_quarterly
GROUP BY scenario_id
ORDER BY scenario_id;
```

