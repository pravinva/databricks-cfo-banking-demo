# Remove week-based “phases” roadmap from end-to-end demo

## Objective
Update the end-to-end notebook so it does **not** imply a maturity sequence (“weeks 1–4”, “phase 2”, etc.). Replace with a maturity-agnostic message: banks can choose among **three approaches** regardless of size.

## In scope
- `notebooks/End_to_End_CFO_Demo.py`

## Required changes
- Replace the “Phase 1/2/3 (Weeks …)” roadmap section with:
  - A short narrative: “Three approaches banks adopt depending on current state”
  - Bullets describing Approach 1/2/3 deposit modeling (aligned to `docs/workstreams/00_umbrella_treasury_modeling.md`)
  - Explicit statement: “Not sequential; choose what fits your current maturity”

## Checklist
- [ ] Remove week-based timeline language
- [ ] Replace “Phase” wording with “Approach”
- [ ] Ensure no mention of “model serving” as the default (batch-first for treasury)

## Acceptance criteria
- Repo-wide search for `Weeks 1-4` / `Weeks` / `Phase 1:` / `Phase 2:` / `Phase 3:` in this notebook returns 0.

