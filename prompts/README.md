# Ralph-Wiggum Agent Prompts

This directory contains the prompt files used with the Ralph-Wiggum agent system to generate the CFO Banking Demo workstreams.

## About Ralph-Wiggum

Ralph-Wiggum is an experimental agentic code generation tool that autonomously creates complex implementations from high-level prompts. These prompts were used to generate the various components of the CFO Banking Demo.

## Prompt Files

### Workstream 1: Data Foundation
- `ralph_ws1_01_prompt.txt`: Unity Catalog structure setup
- `ralph_ws1_02_prompt.txt`: Investment portfolio generation
- `ralph_ws1_03_prompt.txt`: Loan portfolio generation (97,200 records)
- `ralph_ws1_04_prompt.txt`: Deposit portfolio generation (402,000 records)
- `ralph_ws1_05_prompt.txt`: Balance sheet and capital structure
- `ralph_ws1_06_prompt.txt`: GL and subledger schemas

### Workstream 2: Real-Time Pipelines
- `ralph_ws2_01_prompt.txt`: Loan origination message generator
- `ralph_ws2_02_prompt.txt`: Delta Live Tables pipeline setup

### Workstream 3: Quant & Regulatory Logic
- `ralph_ws3_01_prompt.txt`: Deposit beta model and agent tools
- `ralph_ws3_02_lcr.txt`: LCR (Liquidity Coverage Ratio) calculator

### Workstream 4: Agent Tools
- `ralph_ws4_01_agent.txt`: CFO agent with treasury calculation tools

### Workstream 5: Dashboards
- `ralph_ws5_dashboards.txt`: Lakeview dashboard specifications and queries

### Workstream 6: React Frontend
- `ralph_ws6_react_app.txt`: Next.js 14 React frontend with AI assistant

## Helper Scripts

- `start_ralph.sh`: Shell script to launch Ralph-Wiggum agent sessions

## Usage

These prompt files are for reference and documentation purposes. They show the high-level requirements that were provided to the agent system to generate the complete demo implementation.

To regenerate components, you would:
```bash
./prompts/start_ralph.sh
```

Then load the appropriate prompt file.

## Note

The actual generated code is in the following directories:
- `/notebooks/`: Databricks demo notebooks
- `/outputs/`: Python scripts and data generators
- `/frontend_app/`: React frontend application
- `/backend/`: FastAPI backend server

This prompts directory is kept for:
1. Documentation of the generation process
2. Reference for understanding requirements
3. Reproducibility of the demo components
