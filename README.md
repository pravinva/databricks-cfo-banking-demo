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
- **Batch scoring**: `notebooks/Batch_Inference_Deposit_Beta_Model.py`

## Documentation
Start at `docs/README.md`.

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

