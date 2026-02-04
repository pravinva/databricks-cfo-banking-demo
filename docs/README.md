# Treasury Modeling Documentation

Complete documentation for the Databricks Treasury Modeling Demo focused on deposit modeling and PPNR fee income forecasting.

---

## Quick Navigation

### 📊 Reports & PDF Layouts
**Location:** `docs/reports/`

- **[PPNR_AND_PDF_LAYOUTS_COMPLETE.md](reports/PPNR_AND_PDF_LAYOUTS_COMPLETE.md)** - Main implementation summary for PPNR and 2 PDF layouts
- **[REPORT_GENERATOR_ANALYSIS.md](reports/REPORT_GENERATOR_ANALYSIS.md)** - Analysis confirming report generator is deposit-focused
- **[PPNR_STATUS_AND_NEXT_STEPS.md](reports/PPNR_STATUS_AND_NEXT_STEPS.md)** - PPNR tables status and ready-to-use queries

### 🏦 Treasury Modeling Scope
**Location:** `docs/treasury-modeling/`

- **[SCOPE_REFOCUS_RESEARCH.md](treasury-modeling/SCOPE_REFOCUS_RESEARCH.md)** - Complete analysis of scope refocus to deposits only
- **[TREASURY_APP_REDESIGN_PLAN.md](treasury-modeling/TREASURY_APP_REDESIGN_PLAN.md)** - Frontend app redesign plan for treasury focus
- **[DOCUMENTATION_UPDATES_COMPLETE.md](treasury-modeling/DOCUMENTATION_UPDATES_COMPLETE.md)** - Summary of all documentation updates

### 🤖 Genie Space (Natural Language Queries)
**Location:** `docs/genie-space/`

- **[QUICK_START_GENIE.md](genie-space/QUICK_START_GENIE.md)** ⭐ **START HERE** - Create Genie Space in 5 minutes
- **[GENIE_SPACE_CONFIGURATION.md](genie-space/GENIE_SPACE_CONFIGURATION.md)** - Complete configuration with instructions
- **[GENIE_SPACE_IMPLEMENTATION_SUMMARY.md](genie-space/GENIE_SPACE_IMPLEMENTATION_SUMMARY.md)** - Implementation guide
- **[AI_BI_DASHBOARD_AND_GENIE_REQUIREMENTS.md](genie-space/AI_BI_DASHBOARD_AND_GENIE_REQUIREMENTS.md)** - Dashboard requirements

---

## What Was Built

### 1. PPNR & Fee Income Analysis
Added comprehensive PPNR analysis to the main report generator:
- Current quarter PPNR, NII, Non-Interest Income, Efficiency Ratio
- 9-quarter forecasts by scenario (Baseline, Adverse, Severely Adverse)
- 3 new visualizations: waterfall, projections, efficiency trend
- Treasury impact analysis on fee income

**File:** `notebooks/Generate_Deposit_Analytics_Report.py`

### 2. Executive Dashboard Layout (NEW)
Professional 2-page landscape report for presentations:
- Modern Databricks brand design
- Visual KPI cards with gradients
- 2-column layout for dense information
- Best for: Board meetings, ALCO, executive briefings

**File:** `notebooks/Generate_Report_Executive_Layout.py`

### 3. Regulatory/Technical Layout (NEW)
Formal 10+ page portrait report for compliance:
- Traditional professional styling (Times New Roman)
- Complete methodology with formulas
- Regulatory references (SR 11-7, CCAR, 12 CFR Part 252)
- Signature blocks for attestation
- Best for: CCAR submissions, Federal Reserve filings, audits

**File:** `notebooks/Generate_Report_Regulatory_Layout.py`

### 4. Genie Space Configuration
Ready-to-use natural language query interface:
- **Name:** "Treasury Modeling - Deposits & Fee Income"
- **12 Tables** covering Phase 1, 2, 3 models + PPNR
- **1,500+ lines** of comprehensive instructions
- **Example queries** for each modeling domain

---

## Treasury Modeling Scope

### ✅ What's IN Scope

**Deposit Modeling:**
- Phase 1: Deposit Beta (rate sensitivity)
- Phase 2: Vintage Analysis (cohort decay)
- Phase 3: CCAR Stress Testing (regulatory scenarios)

**PPNR Fee Income Modeling:**
- Non-interest income forecasting
- Non-interest expense projections
- Fee income driven by deposit relationships

### ❌ What's OUT of Scope

- Loan portfolio modeling (except for fee income calculation)
- Credit risk modeling
- Securities portfolio (AFS/HTM)
- Comprehensive P&L management

---

## Key Terminology

**CCAR** - Comprehensive Capital Analysis and Review (Federal Reserve stress testing)
**DFAST** - Dodd-Frank Act Stress Testing (deprecated term, underlying regulation)
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
├── treasury-modeling/                 ← Scope and design docs
│   ├── SCOPE_REFOCUS_RESEARCH.md
│   ├── TREASURY_APP_REDESIGN_PLAN.md
│   └── DOCUMENTATION_UPDATES_COMPLETE.md
└── genie-space/                       ← Genie Space setup
    ├── QUICK_START_GENIE.md          ⭐ START HERE
    ├── GENIE_SPACE_CONFIGURATION.md
    ├── GENIE_SPACE_IMPLEMENTATION_SUMMARY.md
    └── AI_BI_DASHBOARD_AND_GENIE_REQUIREMENTS.md
```

---

## Getting Started

### 1. Create Genie Space (5 minutes)
Follow [QUICK_START_GENIE.md](genie-space/QUICK_START_GENIE.md) to set up natural language queries.

### 2. Generate Reports
Run any of the 3 report notebooks in Databricks:
- `notebooks/Generate_Deposit_Analytics_Report.py` - Main report with PPNR
- `notebooks/Generate_Report_Executive_Layout.py` - Executive dashboard
- `notebooks/Generate_Report_Regulatory_Layout.py` - Regulatory submission

### 3. Explore Documentation
- [PPNR Implementation](reports/PPNR_AND_PDF_LAYOUTS_COMPLETE.md) - What was built
- [Scope Refocus](treasury-modeling/SCOPE_REFOCUS_RESEARCH.md) - Why deposits only
- [App Redesign Plan](treasury-modeling/TREASURY_APP_REDESIGN_PLAN.md) - Frontend roadmap

---

## Data Sources

All documentation references these Unity Catalog tables:

**Phase 1: Deposit Beta**
- `ml_models.deposit_beta_training_enhanced`
- `bronze_core_banking.deposit_accounts`

**Phase 2: Vintage Analysis**
- `ml_models.component_decay_metrics`
- `ml_models.cohort_survival_rates`
- `ml_models.deposit_runoff_forecasts`

**Phase 3: CCAR Stress Testing**
- `ml_models.dynamic_beta_parameters`
- `ml_models.stress_test_results`
- `gold_regulatory.lcr_daily`
- `gold_regulatory.hqla_inventory`

**PPNR Forecasting**
- `ml_models.ppnr_forecasts`
- `ml_models.non_interest_income_training_data`
- `ml_models.non_interest_expense_training_data`

---

## Support

For questions or issues:
1. Check the relevant documentation file above
2. Review Genie Space configuration for query examples
3. Verify Unity Catalog table permissions

---

**Last Updated:** February 4, 2026
**Demo Focus:** Treasury Modeling - Deposit Modeling & PPNR Fee Income Forecasting
