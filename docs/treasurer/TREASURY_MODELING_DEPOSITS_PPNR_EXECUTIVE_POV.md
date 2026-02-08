# Treasury Modeling with Databricks (Deposits + PPNR)
## Executive POV (Treasurer / ALCO)

### What this demo covers
- **Deposit modeling** (3 approaches you can adopt independently)
- **PPNR / fee income modeling** (non-interest income + non-interest expense → PPNR)
- **Batch scoring** (weekly/monthly portfolio refresh; no 24/7 serving)

### The decisions treasury needs to make (and how this helps)
- **Deposit pricing**: which segments/products to defend vs reprice vs let run off
- **Runoff & funding gap**: quantify expected outflows and contingency funding needs
- **Earnings under scenarios**: connect deposit strategy to **PPNR impact**

---

## When to use which approach

### Approach 1 — Static Deposit Beta (Operational sensitivity & segmentation)
**Use when**:
- You need an actionable **rate sensitivity baseline** by product/segment
- You want to identify **at‑risk balances** / repricing candidates quickly
- You’re refreshing weekly/monthly and want stability + explainability

**Outputs**:
- `cfo_banking_demo.ml_models.deposit_beta_predictions`

### Approach 2 — Vintage / Runoff (Liquidity planning & behavioral maturity)
**Use when**:
- You need **cohort-based runoff curves** for LCR/NSFR-style planning
- You want to separate retention dynamics by **tenure/vintage**
- You are building forward runoff projections (not just “beta today”)

**Outputs** (typical):
- `cfo_banking_demo.ml_models.cohort_survival_rates`
- `cfo_banking_demo.ml_models.deposit_runoff_forecasts`

### Approach 3 — Dynamic Beta + Stress Testing (Regulatory-style scenarios)
**Use when**:
- You need multi-scenario **stress testing** (CCAR-style; “DFAST” is the legacy regulation behind CCAR)
- You need time-varying beta behavior as market regimes shift
- You want to quantify downside tail behavior under rapid hikes/cuts

**Outputs** (typical):
- `cfo_banking_demo.ml_models.stress_test_results`

---

## PPNR: how it ties to deposits
PPNR answers: “Given our balance sheet + pricing strategy + scenario path, what happens to earnings?”

**Use when**:
- You want the “so what” for ALCO: earnings resilience under scenarios
- You need to connect deposit runoff/price defense decisions to fee income + expense

**Outputs**:
- `cfo_banking_demo.ml_models.ppnr_forecasts`

---

## How it runs in production (batch-first)
**Recommended operating cadence**:
- **Weekly** (Sunday night): batch score deposits using the current champion model
- **Monday morning**: ALCO pack/dashboard refreshed with latest beta/runoff + PPNR snapshot

**Batch notebook**:
- `notebooks/Batch_Inference_Deposit_Beta_Model.py`
  - Loads `models:/cfo_banking_demo.models.deposit_beta_model@champion`
  - Writes `cfo_banking_demo.ml_models.deposit_beta_predictions`

---

## Suggested “starting point” (what most banks do first)
- Start with **Approach 1** to get segmentation + a defend/reprice list.
- Add **Approach 2** once you need behavioral runoff curves for liquidity planning.
- Add **Approach 3** when you need regulatory-style stress narratives and multi-scenario projections.
- Bring in **PPNR** to quantify earnings impact of the deposit strategy.

