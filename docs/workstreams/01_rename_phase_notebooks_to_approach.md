# Rename “Phase” notebooks to “Approach” notebooks

## Objective
Rename the three deposit training notebooks (files + internal content) from **Phase 1/2/3** to **Approach 1/2/3**, and update all repo references accordingly.

## Files to rename
- `notebooks/Phase1_Enhanced_Deposit_Beta_Model.py` → `notebooks/Approach1_Enhanced_Deposit_Beta_Model.py`
- `notebooks/Phase2_Vintage_Analysis_and_Decay_Modeling.py` → `notebooks/Approach2_Vintage_Analysis_and_Decay_Modeling.py`
- `notebooks/Phase3_Dynamic_Beta_and_Stress_Testing.py` → `notebooks/Approach3_Dynamic_Beta_and_Stress_Testing.py`

## In-file content changes (high priority)
Inside each notebook:
- Update `%md` title headers (“# Phase X” → “# Approach X”)
- Replace printed strings (“Starting Phase X” → “Starting Approach X”)
- Replace cross-notebook references (e.g., “run Phase 2 notebook” → “run Approach 2 notebook”)
- Replace references like “Maintain Phase 1/Phase 2 models …” with “Maintain Approach 1/Approach 2 …”

## Repo-wide reference updates
Update links/references in:
- `notebooks/README.md`
- Repo `README.md`
- `docs/**` (treasurer materials, demo scripts, glossary/methodology, etc.)
- `frontend_app/**` labels that say PHASE 1/2/3 (should become APPROACH 1/2/3)
- `prompts/**` if they mention phases
- Any scripts that refer to old notebook filenames

## Implementation checklist
- [ ] Rename the three files
- [ ] Update notebook titles and internal strings
- [ ] Update all documentation references to new filenames
- [ ] Update UI labels to “Approach”
- [ ] Verify: repo-wide search for `Phase1_`/`Phase2_`/`Phase3_` returns only legacy/archive (or 0)
- [ ] Verify: repo-wide search for `PHASE` and `Phase ` returns 0 in user-facing content

## Acceptance criteria
- Old filenames do not exist in `notebooks/` (only under `notebooks/archive/` if needed).
- `notebooks/README.md` and repo `README.md` list **Approach 1/2/3**.
- UI shows **APPROACH 1/2/3** instead of **PHASE 1/2/3**.

