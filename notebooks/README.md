# CFO Banking Demo - Notebook Catalog

This document provides a comprehensive guide to all production notebooks in the demo.

---

## 📊 **Approach 1-3: Treasury Deposit Beta Modeling** (Core Production)

### **Approach 1: Enhanced Deposit Beta Model**
**File**: `Approach1_Enhanced_Deposit_Beta_Model.py`

**Purpose**: Baseline static deposit beta prediction model

**What It Does**:
- Trains XGBoost regression model for deposit sensitivity (beta coefficients)
- Feature engineering: balance, rates, account age, customer segment, product type
- Registers model to Unity Catalog: `cfo_banking_demo.models.deposit_beta_model@champion`

**When to Use**:
- Initial model training for deposit sensitivity
- Operational ALM (day-to-day balance sheet management)
- Static beta assumptions for normal market conditions

**Output Tables**:
- `cfo_banking_demo.ml_models.deposit_beta_training_data`
- Model: `cfo_banking_demo.models.deposit_beta_model@champion`

**Runtime**: ~5-10 minutes

---

### **Approach 2: Vintage Analysis & Decay Modeling**
**File**: `Approach2_Vintage_Analysis_and_Decay_Modeling.py`

**Purpose**: Cohort-based deposit retention and runoff forecasting

**What It Does**:
- Vintage cohort survival curves (deposit retention over 24 months)
- Decay rate modeling for core vs non-core deposits
- Runoff forecasting by product type (DDA, MMDA, CD, Savings)
- Component decay metrics for liquidity stress testing

**When to Use**:
- Liquidity risk analysis (LCR, NSFR, FR 2052a)
- Deposit runoff projections
- Funding gap analysis
- Behavioral maturity modeling

**Output Tables**:
- `vintage_cohort_survival` - Cohort retention curves
- `component_decay_metrics` - Core vs non-core decay rates
- `deposit_runoff_forecasts` - Forward-looking runoff projections

**Runtime**: ~10-15 minutes

---

### **Approach 3: Dynamic Beta & Stress Testing**
**File**: `Approach3_Dynamic_Beta_and_Stress_Testing.py`

**Purpose**: Advanced stress testing with time-varying beta coefficients (regulatory compliance)

**What It Does**:
- **Chen (2025) Sigmoid Function**: Non-linear beta dynamics
  - β(Rm) = βmin + (βmax - βmin) / [1 + exp(-k*(Rm-R0))]
- **Basel III / CCAR stress scenarios** (DFAST is legacy terminology):
  - Baseline: Current trajectory
  - Adverse: +100bps gradual increase
  - Severely Adverse: +200bps rapid shock
  - Custom: +300bps extreme stress
- **Economic Value of Equity (EVE) sensitivity analysis**
- **Standard Outlier Test (SOT)**: EVE/CET1 ratio compliance

**When to Use**:
- CCAR-style regulatory stress testing
- Economic Value of Equity (EVE) analysis
- Multi-scenario capital planning
- Rapid rate shock impact assessment

**Output Tables**:
- `dynamic_beta_parameters` - Time-varying beta coefficients
- `stress_test_results` - 9-quarter CCAR projections
- `stress_test_summary` - Scenario summaries
- `eve_sensitivity_analysis` - Economic value impacts

**Runtime**: ~15-20 minutes

**⚠️ Important**: Dynamic betas increase EVE sensitivity 30-40% vs static models. Use for stress testing only, not day-to-day ALM.

---

## 💰 **PPNR Forecasting** (Pre-Provision Net Revenue)

### **PPNR Models: Non-Interest Income & Expense**
**File**: `Train_PPNR_Models.py`

**Purpose**: Predict non-interest income and operating expenses for stress testing

**What It Does**:
- **Non-Interest Income Model**: Predicts monthly fee revenue
  - Drivers: Transaction volume, account count, loan originations, digital adoption
  - Revenue categories: Service charges, card fees, loan fees, wealth management
- **Non-Interest Expense Model**: Predicts monthly operating costs
  - Drivers: Business scale (accounts, branches), digital adoption, delinquency rate
  - Expense categories: Personnel, occupancy, technology, marketing
- **PPNR Calculation**: NII + Non-Interest Income - Non-Interest Expense

**When to Use**:
- CCAR-style stress testing (9-quarter projections)
- Annual budgeting and financial planning
- Quarterly earnings forecasts
- Scenario analysis (recession, boom, baseline)

**Output Tables**:
- `cfo_banking_demo.ml_models.non_interest_income_training_data`
- `cfo_banking_demo.ml_models.non_interest_expense_training_data`
- `cfo_banking_demo.ml_models.ppnr_forecasts`

**Models Registered**:
- `cfo_banking_demo.models.non_interest_income_model@champion`
- `cfo_banking_demo.models.non_interest_expense_model@champion`

**Runtime**: ~15-20 minutes

---

## 🔄 **Batch Inference & Scoring**

### **Batch Inference: Deposit Beta Model**
**File**: `Batch_Inference_Deposit_Beta_Model.py`

**Purpose**: Score entire deposit portfolio using trained models (periodic batch job)

**What It Does**:
- Loads `@champion` model from Unity Catalog
- Scores all deposit accounts in portfolio
- Calculates rate shock scenarios (+100bps, +200bps, +300bps)
- Generates deposit runoff projections
- Writes predictions to Delta tables

- **When to Use**:
- Weekly/monthly portfolio scoring
- Post-model retraining validation
- Rate shock scenario analysis
- Dashboard data refresh

**Output Tables**:
- `deposit_beta_predictions` - Account-level beta predictions
- `rate_shock_analysis` - Scenario impact results

**Runtime**: ~5 minutes (scales with portfolio size)

**Note**: Batch approach is cost-effective vs real-time serving (no 24/7 compute costs)

---

## 📊 **Analytics & Reporting**

### **Deposit Analytics Report Generator**
**File**: `Generate_Deposit_Analytics_Report.py`

**Purpose**: Generate comprehensive HTML report showing impact of rate changes on deposit portfolio behavior

**What It Does**:
- **Executive Summary**: Portfolio metrics, beta, weighted avg rate
- **Portfolio Composition**: Product mix breakdown with rate sensitivity
- **Rate Shock Scenarios**: Expected runoff under +100bps, +200bps, +300bps shocks
- **Product-Level Analysis**: Runoff projections by product type
- **Vintage Analysis**: Cohort retention curves (if available)
- **Strategic Recommendations**: Liquidity contingency, product mix optimization
- **Visualizations**: Interactive charts (Plotly) - pie charts, bar charts, waterfall charts
- **Multiple Outputs**: HTML report, Delta tables, embedded charts

**When to Use**:
- ALCO (Asset Liability Committee) presentations
- Monthly/quarterly treasury reporting
- Regulatory stress testing documentation (CCAR-style; DFAST is legacy terminology)
- Executive briefings on deposit stability
- Board presentations on liquidity risk

**Output Files**:
- `/dbfs/FileStore/reports/deposit_analytics_report_[timestamp].html` - Formatted HTML report
- `cfo_banking_demo.gold_analytics.deposit_analytics_reports` - Report summaries (Delta)
- `cfo_banking_demo.gold_analytics.rate_shock_scenarios` - Scenario details (Delta)

**Runtime**: ~3-5 minutes

**Dependencies**: Run after `Batch_Inference_Deposit_Beta_Model.py` for latest predictions

**Scheduling Recommendation**:
- **Frequency**: Weekly (Sunday 11pm, after batch inference)
- **Alerting**: Email report link to ALCO members
- **Integration**: Query Delta tables for dashboard widgets

---

## 🎓 **Demo & Workshop Notebooks**

### **Mosaic AI Model Training Demo**
**File**: `WS3_Mosaic_AI_Model_Training_Demo.py`

**Purpose**: Demonstrate Databricks Mosaic AI / MLOps capabilities

**What It Does**:
- Full end-to-end MLOps workflow
- Model training with MLflow autolog
- Model evaluation and feature importance
- Unity Catalog model registration
- Model alias management (@champion, @challenger)
- ~~Model serving deployment~~ (REMOVED - batch only)
- Monitoring and drift detection

**When to Use**:
- Customer demos showcasing Databricks AI/ML capabilities
- MLOps training workshops
- Architecture reviews

**Runtime**: ~10-15 minutes

---

### **Data Science Agent Training**
**File**: `Train_Deposit_Beta_Model_with_Data_Science_Agent.py`

**Purpose**: Demonstrate Databricks Assistant (natural language model training)

**What It Does**:
- Prepares training dataset
- Uses **natural language prompts** to train models via Databricks Assistant
- Shows AI-assisted model development workflow
- Registers model to Unity Catalog

**When to Use**:
- Demonstrating Databricks Assistant capabilities
- Citizen data scientist / low-code ML demos
- Natural language AI demonstrations

**Example Prompt**:
```
Train a regression model to predict target_beta using XGBoost with 100 estimators,
evaluate using RMSE and R², and register to Unity Catalog as
cfo_banking_demo.models.deposit_beta_model with alias @champion.
```

**Runtime**: ~5-10 minutes (+ Assistant interaction time)

---

## 🏗️ **Data Foundation Notebooks**

### **Step 1: Bronze Tables (Data Generation)**
**File**: `Phase_1_Bronze_Tables.py`

**Purpose**: Generate synthetic banking data for demo

**What It Does**:
- Creates loan portfolio with realistic distributions
- Generates deposit accounts (DDA, MMDA, CD, Savings, NOW)
- Creates historical yield curves
- Generates customer and branch data

**When to Use**:
- Initial demo setup
- Data refresh after schema changes
- Scaling demo data volume

**Output**: All `bronze_*` schema tables

**Runtime**: ~10-15 minutes

---

### **Step 2: DLT Pipelines (Silver/Gold Transformations)**
**File**: `Phase_2_DLT_Pipelines.py`

**Purpose**: Delta Live Tables pipelines for data transformation and quality

**What It Does**:
- Bronze → Silver: Data cleansing, deduplication, validation
- Silver → Gold: Business logic, aggregations, metrics
- Real-time GL posting (loan originations → GL entries)
- Data quality checks and validation rules
- Streaming change data capture (CDC)

**When to Use**:
- Setting up data pipelines
- Demonstrating real-time data processing
- Data quality and governance demos

**Output**: All `silver_*` and `gold_*` schema tables

**Runtime**: ~15-20 minutes (initial), <1 min (incremental)

---

## 🎯 **Stress Testing & Regulatory Reporting**

### **CCAR Stress Testing**
**File**: `Generate_Stress_Test_Results.py`

**Purpose**: Generate 9-quarter stress test projections for regulatory compliance

**What It Does**:
- Applies CCAR scenarios (Baseline, Adverse, Severely Adverse)
- Projects capital ratios (CET1, Tier 1, Total Capital)
- Calculates NII sensitivity to rate shocks
- Generates PPNR projections under stress
- Produces regulatory reporting tables

**When to Use**:
- CCAR-style regulatory submissions (DFAST is legacy terminology)
- Capital planning and optimization
- Board-level stress test presentations

**Output Tables**:
- `stress_test_results` - 9-quarter projections
- `stress_test_summary` - Executive summaries

**Runtime**: ~10 minutes

---

### **Vintage Analysis Generation**
**File**: `Generate_Vintage_Analysis_Tables.py`

**Purpose**: Create deposit cohort survival curves for liquidity analysis

**What It Does**:
- Builds vintage cohorts (monthly originations)
- Tracks deposit retention over 24 months
- Calculates decay rates by product type
- Generates survival curves for dashboard

**When to Use**:
- Liquidity stress testing
- Deposit stability analysis
- Behavioral maturity modeling

**Output Tables**:
- `vintage_cohort_survival`
- `vintage_decay_rates`

**Runtime**: ~5-10 minutes

---

## 📋 **Execution Order for Full Demo Setup**

1. **Data Foundation**:
   - `Phase_1_Bronze_Tables.py` - Generate raw data
   - `Phase_2_DLT_Pipelines.py` - Transform to Silver/Gold

2. **Treasury Models (Approaches 1-3)**:
   - `Approach1_Enhanced_Deposit_Beta_Model.py` - Enhanced static beta model
   - `Approach2_Vintage_Analysis_and_Decay_Modeling.py` - Vintage + runoff forecasting
   - `Approach3_Dynamic_Beta_and_Stress_Testing.py` - Dynamic beta + stress testing

3. **PPNR Models**:
   - `Train_PPNR_Models.py` - Non-Interest Income & Expense

4. **Stress Testing**:
   - `Generate_Stress_Test_Results.py` - CCAR stress projections (DFAST is legacy term)
   - `Generate_Vintage_Analysis_Tables.py` - Vintage cohorts

5. **Batch Inference**:
   - `Batch_Inference_Deposit_Beta_Model.py` - Score portfolio

6. **Start Frontend**:
   - Backend API: `python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000`
   - Frontend: `cd frontend_app && npm run dev`

---

## 🔧 **Scheduled Jobs (Production)**

Recommended schedule for production deployment:

| Notebook | Frequency | Schedule | Purpose |
|----------|-----------|----------|---------|
| `Phase_2_DLT_Pipelines.py` | Continuous | Streaming | Real-time data processing |
| `Batch_Inference_Deposit_Beta_Model.py` | Weekly | Sunday 11pm | Portfolio scoring |
| `Generate_Deposit_Analytics_Report.py` | Weekly | Sunday 11:30pm | Analytics report (after inference) |
| `Generate_Vintage_Analysis_Tables.py` | Monthly | 1st of month | Cohort updates |
| `Generate_Stress_Test_Results.py` | Quarterly | End of quarter | CCAR projections (DFAST is legacy term) |
| `Approach1_Enhanced_Deposit_Beta_Model.py` | Quarterly | Mid-quarter | Model retraining |
| `Train_PPNR_Models.py` | Quarterly | Mid-quarter | PPNR model refresh |

---

## 📂 **Archived Notebooks**

For legacy/superseded notebooks, see `/notebooks/archive/README.md`

---

## 🎯 **Quick Reference: Which Notebook Do I Use?**

| Task | Notebook |
|------|----------|
| **Train deposit beta model** | `Approach1_Enhanced_Deposit_Beta_Model.py` |
| **Analyze deposit retention** | `Approach2_Vintage_Analysis_and_Decay_Modeling.py` |
| **Run CCAR stress test** | `Approach3_Dynamic_Beta_and_Stress_Testing.py` |
| **Forecast PPNR** | `Train_PPNR_Models.py` |
| **Score deposit portfolio** | `Batch_Inference_Deposit_Beta_Model.py` |
| **Generate analytics report** | `Generate_Deposit_Analytics_Report.py` |
| **Demo Mosaic AI** | `WS3_Mosaic_AI_Model_Training_Demo.py` |
| **Demo Databricks Assistant** | `Train_Deposit_Beta_Model_with_Data_Science_Agent.py` |
| **Generate demo data** | `Phase_1_Bronze_Tables.py` |
| **Set up data pipelines** | `Phase_2_DLT_Pipelines.py` |

---

**Last Updated**: February 2, 2026
