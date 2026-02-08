# Consolidate to a single frontend directory

## Objective
This repo currently has both `frontend/` and `frontend_app/`. Consolidate to **one supported frontend** (recommend: `frontend_app/`), and update docs/run instructions accordingly.

## Required changes
- Decide canonical UI:\n  - Preferred: `frontend_app/` (contains Treasury dashboards, assistant page, build output).\n- Mark the other directory as deprecated:\n  - Update its `README.md` (if present) to point to canonical UI.\n  - Update repo `README.md` and `notebooks/README.md` “Start Frontend” instructions.\n- Remove references to the deprecated directory in docs.\n
## Checklist
- [ ] Confirm canonical frontend (`frontend_app/`)\n- [ ] Update run instructions everywhere\n- [ ] Optionally: add a short `frontend/DEPRECATED.md`\n
## Acceptance criteria
- Only one frontend path is documented.\n- `npm run dev` instructions point to the canonical directory.\n
