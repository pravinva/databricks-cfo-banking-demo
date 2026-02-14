# PPNR Scenario Planning (2Y Driver)

## Decision: Macro Driver

We standardize scenario planning on the **2Y U.S. Treasury rate** (`silver_treasury.yield_curves.rate_2y`) as the single primary macro driver for:
- Scenario definitions (rate path / shock)
- PPNR scenario deltas (via an auditable NII sensitivity)
- Cross-artifact alignment (deposit beta, stress tests, PPNR views)

## What to Create (MVP)

### 1) Notebook
- `notebooks/PPNR_Scenario_Planning_Engine.py`

Purpose: create/refresh the scenario tables and compute quarterly scenario projections from the existing monthly PPNR forecast series.

### 2) Tables (Unity Catalog)

All in `cfo_banking_demo.gold_finance`:

- `ppnr_scenario_catalog`
  - Scenario metadata (what the scenario is, when created)

- `ppnr_scenario_drivers_quarterly`
  - The scenario “inputs” per quarter
  - Key driver: `rate_2y_pct` (percent, e.g., `3.53`)
  - Optional levers: `fee_income_multiplier`, `expense_multiplier`

- `ppnr_sensitivity_assumptions`
  - An auditable assumption set for translating `rate_2y` moves into quarterly NII deltas

- `ppnr_projection_quarterly`
  - Baseline vs scenario results per quarter, with deltas

### 3) Optional: Setup Script (for CI / laptop)
- `scripts/setup_ppnr_scenario_planning.py`

Runs the same SQL logic via a SQL Warehouse using the Databricks SDK.

## One-line Assumption (for the 2Y-driven NII delta)

For the MVP, **a 100 bps move in the 2Y rate changes quarterly deposit interest expense by**
\( \Delta IE_{qtr,100bps} = (\sum balance \times predicted\_beta)\times 0.01 / 4 \),
and we apply that directly to baseline NII (asset repricing is not modeled in MVP).

## Why this is the right MVP shape

- Uses the **existing** PPNR baseline you already generate (`ml_models.ppnr_forecasts`)
- Keeps the scenario layer **transparent and editable** by treasury users
- Aligns the demo on a single macro driver (2Y) that you already use across deposit beta + stress narratives

