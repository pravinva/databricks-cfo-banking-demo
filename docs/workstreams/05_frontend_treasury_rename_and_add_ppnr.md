# Frontend: rename to “Approach” and add PPNR / Fee Income view

## Objective
Update the UI so the Treasury experience matches the umbrella:
- Deposit Modeling approaches 1/2/3 (terminology)
- Add **PPNR / Fee Income** tab/view
- Remove all investment-portfolio content (covered separately in `docs/workstreams/06_remove_securities_everywhere.md`)

## In scope
- `frontend_app/components/treasury/DepositBetaDashboard.tsx`
- `frontend_app/components/treasury/VintageAnalysisDashboard.tsx`
- `frontend_app/components/treasury/StressTestDashboard.tsx`
- `frontend_app/app/page.tsx` (tabs)
- Backend API additions as needed (see below)

## Required changes
### Rename “PHASE” → “APPROACH”
- Replace UI headers:\n  - “PHASE 1 MODEL PERFORMANCE” → “APPROACH 1 MODEL PERFORMANCE”\n  - “PHASE 2 RUNOFF FORECAST DETAILS” → “APPROACH 2 RUNOFF FORECAST DETAILS”\n  - “PHASE 3 REGULATORY COMPLIANCE” → “APPROACH 3 REGULATORY COMPLIANCE”\n- Replace any “Phase X Dynamic” copy with “Approach X …”.\n
### Add PPNR / Fee Income dashboard
- Add a new component (suggest): `frontend_app/components/treasury/PpnrDashboard.tsx`.\n- Add a new tab trigger + content in `frontend_app/app/page.tsx`:\n  - Tab label: “PPNR / Fee Income”.\n- Backend endpoint:\n  - Add `GET /api/data/ppnr` in `backend/main.py` (query `cfo_banking_demo.ml_models.ppnr_forecasts`).\n- UI should show:\n  - Current quarter baseline PPNR\n  - Scenario trend chart (9-quarter) if present\n  - Fee income / expense breakdown\n
## Checklist
- [ ] Rename Approach labels in existing Treasury dashboards\n- [ ] Implement PPNR tab + component\n- [ ] Add backend endpoint + wire fetch\n- [ ] Verify: UI has no remaining “Phase” strings\n
## Acceptance criteria
- PPNR tab visible and populated from `ml_models.ppnr_forecasts`.\n- Deposit dashboards use “Approach” terminology.\n
