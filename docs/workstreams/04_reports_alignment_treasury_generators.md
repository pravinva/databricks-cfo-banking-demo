# Align treasury report generators to the new umbrella

## Objective
Ensure report generators are aligned to:
- **Treasury Modeling with Databricks** umbrella (Deposit + PPNR/Fee Income)
- Terminology: **Approach 1/2/3** (never “Phase”)
- Data inputs: **portfolio + latest prediction tables**, not training tables

## In scope
- `notebooks/Generate_Treasury_Executive_Report.py`
- `notebooks/Generate_Deposit_Analytics_Report.py`
- `notebooks/Generate_Report_Executive_Layout.py`
- `notebooks/Generate_Report_Regulatory_Layout.py`

## Required changes
### Data sourcing
- Replace uses of training tables (e.g., `ml_models.deposit_beta_training_enhanced`) as the primary portfolio source.\n- Preferred pattern:\n  - Portfolio: `silver_treasury.deposit_portfolio`\n  - Predictions: `ml_models.deposit_beta_predictions`\n  - Runoff forecasts: `ml_models.deposit_runoff_forecasts` (Approach 2)\n  - Stress results: `ml_models.stress_test_results` (Approach 3)\n  - PPNR: `ml_models.ppnr_forecasts`\n
### Terminology
- Replace “Phase” strings with “Approach” in:\n  - Report subtitles\n  - Warnings (“run Phase 2 notebook”)\n  - Section headers\n
### PPNR consistency
- Ensure all “Treasury Analytics” style reports either:\n  - Include a small PPNR/Fee Income summary section, or\n  - Explicitly link to the PPNR report section powered by `ml_models.ppnr_forecasts`.\n
## Checklist
- [ ] Update deposit data source usage in all generators\n- [ ] Replace “Phase” → “Approach” in copy\n- [ ] Ensure PPNR is present/linked consistently\n- [ ] Verify report still runs when runoff or stress tables are missing (graceful warnings)\n
## Acceptance criteria
- No report generator references “Phase”.\n- No generator requires a training table as its primary input.\n- Executive and regulatory layouts both clearly state “Deposit Modeling & PPNR/Fee Income”.\n
