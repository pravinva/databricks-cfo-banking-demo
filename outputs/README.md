# Outputs Directory

This directory contains all scripts, documentation, and configuration files generated for the CFO Banking Demo.

## Directory Structure

```
outputs/
├── scripts/              # Executable Python scripts
│   ├── agents/          # AI agent implementations
│   ├── dashboards/      # Dashboard generation scripts
│   ├── data_generation/ # Data population scripts
│   ├── frontend/        # Frontend setup scripts
│   ├── models/          # ML model scripts
│   ├── pipelines/       # Data pipeline scripts
│   └── utilities/       # Utility and setup scripts
├── docs/                # Documentation and guides
└── config/              # Configuration and audit files
```

## Scripts

### agents/
Agent implementations with tool libraries:
- `11_cfo_agent_demo.py` - CFO agent with treasury tools
- `15_test_agent_tools.py` - Agent tools testing
- `agent_tools_library.py` - Shared agent tools library

### dashboards/
Dashboard creation and query scripts:
- `17_dashboard_queries.sql` - SQL queries for all dashboards
- `17_design_system.py` - Dashboard design system and styling
- `17_plotly_chart_configs.py` - Plotly chart configurations
- `17_test_dashboard_queries.py` - Dashboard query testing
- `19_create_lakeview_dashboards.py` - Lakeview dashboard creation
- `20_create_dashboards_simple.py` - Simplified dashboard creation
- `21_create_queries_only.py` - Query-only generation

### data_generation/
Scripts for populating Unity Catalog tables:
- `02_generate_securities_portfolio.py` - Securities portfolio (153 securities)
- `03_generate_loan_portfolio.py` - Loan portfolio (97,200 loans)
- `04_generate_deposit_portfolio.py` - Deposit portfolio (402,000 accounts)
- `04b_complete_cd_accounts.py` - Complete CD accounts data
- `05_generate_balance_sheet.py` - Balance sheet and capital structure
- `06_setup_gl_subledger_schemas.py` - GL and subledger setup
- `18_create_missing_tables.py` - Create additional tables
- `26_complete_remaining_tasks.py` - Complete remaining regulatory tables

### frontend/
Frontend application setup:
- `16_create_react_frontend.py` - Next.js 14 frontend generator
- `16b_create_sophisticated_components.py` - React component generator
- `16c_test_and_run.sh` - Frontend test and run script

### models/
Machine learning model implementations:
- `09_deposit_beta_model.py` - Deposit beta ML model (XGBoost)
- `10_lcr_calculator.py` - LCR calculator and HQLA classification

### pipelines/
Data pipeline and integration scripts:
- `07_alpha_vantage_integration.py` - Market data integration
- `08_loan_origination_pipeline.py` - Loan origination pipeline
- `24_loan_origination_event_generator.py` - Event generator for streaming

### utilities/
Setup and utility scripts:
- `01_setup_unity_catalog.py` - Unity Catalog initialization
- `preflight_check.py` - Environment preflight check
- `verify_dependencies.py` - Dependency verification
- `verify_dependencies_ws1_06.py` - WS1 dependency verification

## Documentation

### docs/
- `17_LAKEVIEW_DASHBOARD_GUIDE.md` - Complete dashboard implementation guide
- `22_EXACT_DASHBOARD_SPECS.md` - Detailed dashboard specifications
- `23_GAP_ANALYSIS.md` - Workstream gap analysis
- `25_DEMO_NOTEBOOKS_SUMMARY.md` - Demo notebook guide
- `27_FINAL_COMPLETION_SUMMARY.md` - Project completion summary
- `WS6_REACT_FRONTEND_SUMMARY.md` - Frontend implementation summary

## Configuration

### config/
- `cfo_agent_audit_trail.json` - Agent execution audit trail
- `test_audit_trail.json` - Test execution audit trail
- `__pycache__/` - Python bytecode cache

## Usage

### Running Data Generation Scripts
```bash
# Example: Generate loan portfolio
source .venv/bin/activate
python outputs/scripts/data_generation/03_generate_loan_portfolio.py
```

### Running Model Scripts
```bash
# Example: Train deposit beta model
source .venv/bin/activate
python outputs/scripts/models/09_deposit_beta_model.py
```

### Running Agent Scripts
```bash
# Example: Run CFO agent demo
source .venv/bin/activate
python outputs/scripts/agents/11_cfo_agent_demo.py
```

## Execution Order

For complete setup, run scripts in this order:

1. **Utilities** (Setup)
   - `utilities/preflight_check.py`
   - `utilities/01_setup_unity_catalog.py`

2. **Data Generation** (WS1)
   - `data_generation/02_generate_securities_portfolio.py`
   - `data_generation/03_generate_loan_portfolio.py`
   - `data_generation/04_generate_deposit_portfolio.py`
   - `data_generation/05_generate_balance_sheet.py`
   - `data_generation/06_setup_gl_subledger_schemas.py`

3. **Pipelines** (WS2)
   - `pipelines/07_alpha_vantage_integration.py`
   - `pipelines/08_loan_origination_pipeline.py`
   - `pipelines/24_loan_origination_event_generator.py`

4. **Models** (WS3)
   - `models/09_deposit_beta_model.py`
   - `models/10_lcr_calculator.py`

5. **Regulatory Tables** (WS3 continued)
   - `data_generation/26_complete_remaining_tasks.py`

6. **Agents** (WS4)
   - `agents/11_cfo_agent_demo.py`

7. **Dashboards** (WS5)
   - `dashboards/21_create_queries_only.py`

8. **Frontend** (WS6)
   - `frontend/16_create_react_frontend.py`

## Notes

- All scripts use the Databricks SDK for Unity Catalog operations
- Scripts require `.alpha_vantage_key` file in project root for market data integration
- Frontend scripts generate Next.js 14 application with static export
- Agent scripts use Claude Sonnet 4.5 via Databricks Model Serving
- Dashboard scripts generate Lakeview dashboard specifications

## Related Directories

- `/notebooks/` - Databricks demo notebooks
- `/prompts/` - Ralph-Wiggum agent prompt files
- `/frontend_app/` - Next.js frontend application
- `/backend/` - FastAPI backend server
