# Treasury Modeling with Databricks (Deposits + PPNR)

This repository contains a focused demo for **Treasury Modeling with Databricks**, centered on:

- **Deposit modeling** (Approach 1–3)
- **PPNR / fee income modeling** (non-interest income + non-interest expense → PPNR)

## What’s in scope
- **Approach 1**: Static deposit beta model (segmentation + sensitivity)
- **Approach 2**: Vintage analysis + component decay runoff forecasting
- **Approach 3**: Dynamic beta + stress testing scenarios
- **Batch scoring**: Portfolio scoring via `notebooks/Batch_Inference_Deposit_Beta_Model.py`
- **Reporting**: Executive + regulatory report generators
- **App**: `frontend_app/` (Next.js) + `backend/` (FastAPI)

## Quickstart (local)

### Backend
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt

python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

### Frontend
```bash
cd frontend_app
npm install
npm run dev
```

## Key notebooks (Databricks)
- **Approach 1**: `notebooks/Approach1_Enhanced_Deposit_Beta_Model.py`
- **Approach 2**: `notebooks/Approach2_Vintage_Analysis_and_Decay_Modeling.py`
- **Approach 3**: `notebooks/Approach3_Dynamic_Beta_and_Stress_Testing.py`
- **PPNR**: `notebooks/Train_PPNR_Models.py`
- **Scenario planning**: `notebooks/PPNR_Scenario_Planning_Engine.py`
- **NII repricing**: `notebooks/NII_Repricing_Engine_2Y.py`
- **Scenario ML inference**: `notebooks/PPNR_Scenario_ML_Inference_2Y.py`
- **Batch scoring**: `notebooks/Batch_Inference_Deposit_Beta_Model.py`

## Create / refresh demo data (Unity Catalog) + Alpha Vantage yield curves

The UI and scenario planning flows assume core data exists in Unity Catalog under the `cfo_banking_demo` catalog.

### 1) Databricks auth (required)

All scripts/notebooks use Databricks SDK auth. The repo generally assumes your Databricks CLI profile works (for example `DEFAULT`):

```bash
export DATABRICKS_CONFIG_PROFILE=DEFAULT
```

### 2) Treasury curve data (Alpha Vantage → `silver_treasury.yield_curves`)

The frontend **does not call Alpha Vantage directly**. It calls `GET /api/data/yield-curve`, and the backend **prefers the UC table**:
- `cfo_banking_demo.silver_treasury.yield_curves`

To backfill yields from Alpha Vantage:

```bash
export ALPHAVANTAGE_API_KEY="..."
python scripts/backfill_yield_curves_alphavantage.py
```

This script makes Alpha Vantage calls for:
- `TREASURY_YIELD` (3M/2Y/5Y/10Y/30Y)
- `FEDERAL_FUNDS_RATE`

and upserts into `cfo_banking_demo.silver_treasury.yield_curves`.

### 3) Core portfolio history tables (demo generators)

These create/refresh the historical “bronze” inputs used by modeling:

```bash
python dev-scripts/generate_deposit_history.py
python dev-scripts/generate_loan_history.py
```

Optional (only if you need GL-driven targets/actuals):

```bash
python dev-scripts/backfill_gl_complete.py
```

### 4) Derived modeling / scenario tables (recommended run order in Databricks)

Run these notebooks in the workspace:
- `notebooks/Approach1_Enhanced_Deposit_Beta_Model.py`
- `notebooks/Batch_Inference_Deposit_Beta_Model.py` (creates `ml_models.deposit_beta_predictions`)
- `notebooks/Approach2_Vintage_Analysis_and_Decay_Modeling.py` (creates `ml_models.deposit_runoff_forecasts`)
- `notebooks/Train_PPNR_Models.py` (creates PPNR training tables + registers UC models)
- `notebooks/PPNR_Scenario_Planning_Engine.py`
- `notebooks/NII_Repricing_Engine_2Y.py`
- re-run `notebooks/PPNR_Scenario_Planning_Engine.py` (rebuild PPNR using repriced NII)
- `notebooks/PPNR_Scenario_ML_Inference_2Y.py` (creates `gold_finance.ppnr_projection_quarterly_ml`)

You can also refresh the scenario planning tables from a laptop/CI using:
- `scripts/setup_ppnr_scenario_planning.py`
- `scripts/setup_nii_repricing_2y.py`

## Documentation
Start at `docs/README.md`.

## Dashboard (adds a new page)
To add the **PPNR Scenario Planning** page into the existing **CFO Deposit Portfolio Suite** dashboard:
- `dev-scripts/add_ppnr_scenario_page_to_portfolio_suite.py`
- `dev-scripts/update_ppnr_scenario_page_no_loans.py` (enforces no loan references on that page)

## Frontend scenario planning layout
- The command-center homepage now prioritizes **PPNR Scenario Planning** visibility:
  - compact **Yield Curve** panel (left)
  - wider **PPNR Scenario Snapshot (ALCO)** panel (right)
- Scenario snapshot is sourced from:
  - `GET /api/data/ppnr-scenario-summary`
  - primary table: `cfo_banking_demo.gold_finance.ppnr_projection_quarterly_ml`
  - fallback: `cfo_banking_demo.gold_finance.ppnr_projection_quarterly`

## Repository layout
```
.
├── backend/                 # FastAPI API + treasury AI assistant integration
├── frontend_app/            # Next.js treasury UI (Databricks Apps)
├── notebooks/               # Training, scoring, reporting notebooks
└── docs/
    ├── README.md            # Documentation index
    ├── demo/                # Demo script + glossary
    ├── reports/             # Report generator documentation
    ├── requirements/        # Data requirements + quality notes
    ├── guides/              # Setup and terminology guides
    ├── treasurer/           # Meeting materials (one-pager, guide, index)
    ├── workstreams/         # Implementation TODO workstreams (historical)
    └── archive/             # Legacy/archived docs
```

