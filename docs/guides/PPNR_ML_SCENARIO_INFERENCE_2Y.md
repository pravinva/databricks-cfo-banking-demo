# PPNR Scenario Planning (ML-Driven NonII/NonIE) — 2Y Driver

## Purpose

Generate scenario-specific **Non-Interest Income** and **Non-Interest Expense** projections using the existing **UC-registered MLflow models**, under the same 2Y rate paths used for scenario planning.

## Inputs

- Scenario drivers (2Y paths):
  - `cfo_banking_demo.gold_finance.ppnr_scenario_drivers_quarterly`
- Full NII repricing output:
  - `cfo_banking_demo.gold_finance.nii_projection_quarterly`
- Training feature tables (for latest-state feature anchoring):
  - `cfo_banking_demo.ml_models.non_interest_income_training_data`
  - `cfo_banking_demo.ml_models.non_interest_expense_training_data`
- UC models:
  - `cfo_banking_demo.models.non_interest_income_model@champion`
  - `cfo_banking_demo.models.non_interest_expense_model@champion`

## Outputs

In `cfo_banking_demo.gold_finance`:
- `ppnr_ml_projection_monthly`
- `ppnr_projection_quarterly_ml`

## How to run

- Run `notebooks/PPNR_Scenario_ML_Inference_2Y.py`

This notebook:
- anchors on the latest training row (“portfolio state”)
- rolls forward 27 months (9 quarters)
- applies scenario `rate_2y_pct` per quarter to the fee-income model’s `avg_2y_rate`
- iterates monthly so `prior_month_*` features use the prior predicted values (per scenario)

