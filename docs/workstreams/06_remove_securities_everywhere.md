# Remove investment portfolio references everywhere

## Objective
Remove investment portfolio references and surfaces across the entire demo. Keep the demo strictly focused on Treasury Modeling (deposits + PPNR).

## In scope (minimum)
### Frontend
- `frontend_app/app/page.tsx`:\n  - Remove investment-portfolio KPI\n  - Remove related navigation\n  - Remove related tooltip text\n
### Backend API
- `backend/main.py`:\n  - Remove investment-portfolio endpoint\n  - Remove any SQL queries against investment-portfolio tables\n
### Agent prompt + tool definitions
- `backend/claude_agent.py`:\n  - Remove investment-portfolio concepts from tool descriptions and system prompt schema.\n
### Tool library
- `outputs/agent_tools_library.py`:\n  - Update `get_portfolio_summary()` to exclude investment portfolio and not return that field.\n
### Notebooks + docs
- Remove investment-portfolio-related copy where it pollutes treasury deposit/PPNR scope.\n
## Checklist
- [ ] UI: remove investment portfolio KPI + copy\n- [ ] Backend: delete investment portfolio endpoint\n- [ ] Tools: remove investment portfolio from portfolio summary + agent prompt schema\n- [ ] Notebooks: remove stray investment-portfolio assumptions/copy\n- [ ] Docs: remove investment-portfolio sections and related terminology\n
## Acceptance criteria
- No user-facing surface references investment portfolio concepts.\n- App runs without investment-portfolio fields in portfolio summary.\n
