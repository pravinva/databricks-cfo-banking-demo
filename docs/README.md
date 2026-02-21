# Treasury Modeling Documentation

Complete documentation for the Databricks Treasury Modeling Demo focused on deposit modeling and PPNR fee income forecasting.

---

## Quick Navigation

### 📊 Reports & PDF Layouts
**Location:** `reports/`

- **[PPNR_AND_PDF_LAYOUTS_COMPLETE.md](reports/PPNR_AND_PDF_LAYOUTS_COMPLETE.md)** - Main implementation summary for PPNR and 2 PDF layouts
- **[REPORT_GENERATOR_ANALYSIS.md](reports/REPORT_GENERATOR_ANALYSIS.md)** - Analysis confirming report generator is deposit-focused
- **[PPNR_STATUS_AND_NEXT_STEPS.md](reports/PPNR_STATUS_AND_NEXT_STEPS.md)** - PPNR tables status and ready-to-use queries

### 🧭 Demo Script & Glossary
**Location:** `demo/`

- **[TREASURY_DEMO_SCRIPT.md](demo/TREASURY_DEMO_SCRIPT.md)** - Primary demo flow and talk track
- **[GLOSSARY_AND_METHODOLOGY.md](demo/GLOSSARY_AND_METHODOLOGY.md)** - Core terminology + modeling notes

### 🧾 Treasurer Meeting Materials
**Location:** `treasurer/`

- **[TREASURER_MATERIALS_INDEX.md](treasurer/TREASURER_MATERIALS_INDEX.md)** - Start here for meeting prep
- **[TREASURER_ONE_PAGER.md](treasurer/TREASURER_ONE_PAGER.md)** - 1-page overview (convert to PDF)
- **[TREASURER_MEETING_GUIDE.md](treasurer/TREASURER_MEETING_GUIDE.md)** - Full demo script and Q&A
- **[TREASURY_MODELING_DEPOSITS_PPNR_EXECUTIVE_POV.md](treasurer/TREASURY_MODELING_DEPOSITS_PPNR_EXECUTIVE_POV.md)** - Exec POV (Deposits + PPNR) + which approach to use when

### 🧰 Guides
**Location:** `guides/`

- **[STRESS_TEST_TERMINOLOGY.md](guides/STRESS_TEST_TERMINOLOGY.md)** - CCAR terminology + stress-testing terms
- **[UPDATE_NOTEBOOKS.md](guides/UPDATE_NOTEBOOKS.md)** - Notebook naming/renames and alignment notes
- **[UC_VOLUMES_MIGRATION.md](guides/UC_VOLUMES_MIGRATION.md)** - UC volumes migration notes
- **[DEPOSIT_MODELING_PPNR_MODELER_PLAYBOOK.md](guides/DEPOSIT_MODELING_PPNR_MODELER_PLAYBOOK.md)** - Modeler playbook + approach selection guidance
- **[PPNR_SCENARIO_PLANNING_2Y.md](guides/PPNR_SCENARIO_PLANNING_2Y.md)** - Scenario planning layer (curve drivers + integration notes)
- **[NII_REPRICING_2Y.md](guides/NII_REPRICING_2Y.md)** - Full NII repricing engine (curve + volume dynamics)
- **[PPNR_ML_SCENARIO_INFERENCE_2Y.md](guides/PPNR_ML_SCENARIO_INFERENCE_2Y.md)** - ML-driven NonII/NonIE scenario inference

---

## What Was Built

### 1. PPNR & Fee Income Analysis
Added comprehensive PPNR analysis to the main report generator:
- Current quarter PPNR, NII, Non-Interest Income, Efficiency Ratio
- 9-quarter forecasts by scenario (Baseline, Adverse, Severely Adverse)
- 3 new visualizations: waterfall, projections, efficiency trend
- Treasury impact analysis on fee income

**File:** `../notebooks/Generate_Deposit_Analytics_Report.py`

### 2. Executive Dashboard Layout (NEW)
Professional 2-page landscape report for presentations:
- Modern Databricks brand design
- Visual KPI cards with gradients
- 2-column layout for dense information
- Best for: Board meetings, ALCO, executive briefings

**File:** `../notebooks/Generate_Report_Executive_Layout.py`

### 3. Regulatory/Technical Layout (NEW)
Formal 10+ page portrait report for compliance:
- Traditional professional styling (Times New Roman)
- Complete methodology with formulas
- Regulatory references (SR 11-7, CCAR, 12 CFR Part 252)
- Signature blocks for attestation
- Best for: CCAR submissions, Federal Reserve filings, audits

**File:** `../notebooks/Generate_Report_Regulatory_Layout.py`

### 4. Genie Space Configuration
Natural-language analytics is provided via the **in-app AI assistant** (Databricks Apps) for deposits + PPNR.

---

## Treasury Modeling Scope

### ✅ What's IN Scope

**Deposit Modeling:**
- Approach 1: Deposit Beta (rate sensitivity)
- Approach 2: Vintage Analysis (cohort decay)
- Approach 3: Stress Testing (regulatory scenarios)

**PPNR Fee Income Modeling:**
- Non-interest income forecasting
- Non-interest expense projections
- Fee income driven by deposit relationships

### ❌ What's OUT of Scope

- Loan portfolio modeling (except for fee income calculation)
- Credit risk modeling
- Investment portfolio modeling
- Comprehensive P&L management

---

## Key Terminology

**CCAR** - Comprehensive Capital Analysis and Review (Federal Reserve stress testing)
**DFAST** - Legacy Dodd-Frank Act Stress Testing regulation (commonly referenced, but “CCAR stress testing” is the preferred label)
**PPNR** - Pre-Provision Net Revenue (NII + Non-Interest Income - Non-Interest Expense)
**Deposit Beta** - Rate sensitivity coefficient (0-1 scale)
**Vintage Analysis** - Cohort-based runoff forecasting
**Efficiency Ratio** - NIE / (NII + Non-Interest Income) × 100%

---

## File Structure

```
docs/
├── README.md                          ← You are here
├── reports/                           ← Report generation docs
│   ├── PPNR_AND_PDF_LAYOUTS_COMPLETE.md
│   ├── REPORT_GENERATOR_ANALYSIS.md
│   └── PPNR_STATUS_AND_NEXT_STEPS.md
├── demo/                              ← Demo scripts
│   ├── TREASURY_DEMO_SCRIPT.md
│   └── GLOSSARY_AND_METHODOLOGY.md
├── treasurer/                         ← Treasurer meeting materials
│   ├── TREASURER_MATERIALS_INDEX.md
│   ├── TREASURER_ONE_PAGER.md
│   └── TREASURER_MEETING_GUIDE.md
├── guides/                            ← Setup and terminology guides
│   ├── STRESS_TEST_TERMINOLOGY.md
│   ├── UPDATE_NOTEBOOKS.md
│   └── UC_VOLUMES_MIGRATION.md
└── requirements/                      ← Data requirements
    ├── DATA_REQUIREMENTS_SUMMARY.md
    └── Data_Requirements_Analysis.md
```

---

## Getting Started

### 1. Generate Reports
Run any of the 3 report notebooks in Databricks:
- `notebooks/Generate_Deposit_Analytics_Report.py` - Main report with PPNR
- `notebooks/Generate_Report_Executive_Layout.py` - Executive dashboard
- `notebooks/Generate_Report_Regulatory_Layout.py` - Regulatory submission

### 2. Explore Documentation
- [PPNR Implementation](reports/PPNR_AND_PDF_LAYOUTS_COMPLETE.md) - What was built

---

## Data Sources

All documentation references these Unity Catalog tables:

**Approach 1: Deposit Beta**
- `ml_models.deposit_beta_training_data`
- `bronze_core_banking.deposit_accounts`

**Approach 2: Vintage Analysis**
- `ml_models.component_decay_metrics`
- `ml_models.cohort_survival_rates`
- `ml_models.deposit_runoff_forecasts`

**Approach 3: Stress Testing**
- `ml_models.dynamic_beta_parameters`
- `ml_models.stress_test_results`
- `gold_regulatory.lcr_daily`

**PPNR Forecasting**
- `ml_models.ppnr_forecasts`
- `ml_models.non_interest_income_training_data`
- `ml_models.non_interest_expense_training_data`

---

## Support

For questions or issues:
1. Check the relevant documentation file above
2. Use the in-app AI assistant for natural-language exploration (Deposits + PPNR)
3. Verify Unity Catalog table permissions

---

**Last Updated:** February 4, 2026
**Demo Focus:** Treasury Modeling - Deposit Modeling & PPNR Fee Income Forecasting
