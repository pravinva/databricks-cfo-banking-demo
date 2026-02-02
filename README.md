# CFO Banking Demo - Databricks Lakehouse Platform

A comprehensive demonstration of Databricks Lakehouse capabilities for banking CFO operations, featuring real-time data processing, AI/ML models, regulatory reporting automation, and executive analytics.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Components](#components)
- [Data Flow](#data-flow)
- [Setup and Installation](#setup-and-installation)
- [Demo Scenarios](#demo-scenarios)
- [Dashboards and Visualizations](#dashboards-and-visualizations)
- [Repository Structure](#repository-structure)
- [Technical Stack](#technical-stack)

---

## Overview

This demo showcases a modern data platform for banking CFO operations, addressing key challenges in treasury management, regulatory reporting, and risk analytics. The solution demonstrates:

- **Unified Data Platform**: Single source of truth for loans, deposits, securities, and market data
- **Real-Time Processing**: Sub-second ingestion and processing of loan origination events
- **AI-Powered Analytics**: Machine learning models for deposit beta prediction and scenario analysis
- **Regulatory Automation**: Automated generation of FFIEC 101, FR 2052a, and Basel III reports
- **Executive Analytics**: Interactive dashboards and AI-powered insights

### Key Metrics

- **500,000+ records**: Loans, deposits, securities across bronze/silver/gold layers
- **15+ tables**: Unity Catalog governed data with complete lineage
- **5 demo notebooks**: End-to-end demonstrations covering all workstreams
- **99.9% time reduction**: Regulatory reporting from 2 weeks to 2 minutes

---

## Architecture

### Lakehouse Medallion Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         BRONZE LAYER                            │
│                    (Raw Data Ingestion)                         │
├─────────────────────────────────────────────────────────────────┤
│ • loan_origination_events (streaming)                           │
│ • treasury_yields (daily)                                       │
│ • core_banking_extracts (batch)                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         SILVER LAYER                            │
│                   (Curated & Cleansed)                          │
├─────────────────────────────────────────────────────────────────┤
│ • loan_portfolio (97,200 records)                               │
│ • deposit_portfolio (402,000 records)                           │
│ • securities (1,000 records)                                    │
│ • gl_entries (double-entry validated)                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                          GOLD LAYER                             │
│                  (Business Aggregates)                          │
├─────────────────────────────────────────────────────────────────┤
│ • capital_structure (CET1, Tier 1, Total Capital)              │
│ • profitability_metrics (NIM, ROE, ROA)                        │
│ • liquidity_coverage_ratio (LCR compliance)                    │
│ • intraday_liquidity_position (real-time)                      │
│ • rwa_calculation (Basel III)                                  │
│ • ftp_rates (Funds Transfer Pricing)                           │
│ • product_profitability (P&L attribution)                      │
│ • ffiec_101_schedule_rc_r (regulatory)                         │
│ • fr_2052a_maturity_ladder (liquidity monitoring)              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    CONSUMPTION LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│ • Lakeview Dashboards (8 visualizations)                       │
│ • React Frontend (Next.js 14)                                  │
│ • AI Assistant (Claude Sonnet 4.5)                             │
│ • Databricks SQL (ad-hoc queries)                              │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Data Platform**:
- Delta Lake: ACID transactions, time travel, schema evolution
- Unity Catalog: Data governance, lineage, access control
- Delta Live Tables: Real-time streaming pipelines
- Databricks SQL: Serverless query engine with Photon acceleration

**AI/ML**:
- Mosaic AI: AutoML model training
- MLflow: Experiment tracking, model registry, serving
- Claude Sonnet 4.5: AI-powered analytics assistant

**Applications**:
- Next.js 14: React frontend with static export
- FastAPI: Python REST API backend
- Framer Motion: Animation library
- Lucide Icons: Icon library

---

## Components

### 1. Data Foundation (WS1)

**Purpose**: Establish Unity Catalog governance structure and generate realistic banking data

**Key Scripts**:
- `outputs/01_create_catalog_structure.py`: Create catalog and schemas
- `outputs/03_generate_loan_portfolio.py`: Generate 97,200 loan records
- `outputs/04_generate_deposit_portfolio.py`: Generate 402,000 deposit accounts
- `outputs/05_generate_securities_portfolio.py`: Generate 1,000 securities
- `outputs/06_generate_treasury_yields.py`: Generate 900 yield curve data points

**Data Generated**:
- Loan portfolio: $31B across 5 product types (Commercial RE, C&I, Residential Mortgage, Consumer Auto, Consumer Personal)
- Deposit portfolio: $28B across 5 product types (MMDA, DDA, NOW, Savings, CD)
- Securities: $8B across 5 security types (UST, Agency MBS, Agency CMO, Corporate Bonds, Municipal Bonds)
- Treasury yields: 10 tenors × 90 days of historical data

### 2. Real-Time Pipelines (WS2)

**Purpose**: Demonstrate streaming data ingestion and real-time processing

**Key Components**:
- `outputs/24_loan_origination_event_generator.py`: Generate streaming loan events
- Bronze ingestion: Delta table with ACID transactions
- GL posting: Double-entry bookkeeping validation
- Intraday liquidity: Cumulative cash flow tracking

**Event Structure**:
Each loan origination event includes:
- Event metadata (UUID, timestamp, source system)
- Borrower information (credit score, income, employment)
- Loan details (amount, rate, term, payment schedule)
- Risk assessment (PD, LGD, CECL reserve, risk rating)
- GL entries (Loans Receivable debit, Customer Deposit credit)
- Liquidity impact (cash outflow, balance sheet impact)
- Regulatory impact (RWA, ALLL reserve)

**Performance**:
- Event generation: 10 events/minute (configurable)
- Processing latency: <1 second
- GL posting: Real-time vs 24-hour batch (99.9% faster)

### 3. AI/ML Models (WS3)

**Purpose**: Train and deploy machine learning models for treasury analytics

**Deposit Beta Model**:
- **Algorithm**: XGBoost regressor
- **Features**: balance, rate, account age, product type, account size, tenure
- **Target**: Deposit beta coefficient (sensitivity to rate changes)
- **Performance**: R² ~0.95, RMSE ~0.05, MAE ~0.03
- **Use Case**: Predict deposit runoff for interest rate shock scenarios

**Model Lifecycle**:
1. Feature engineering from deposit portfolio
2. Train/test split (80/20)
3. XGBoost training with MLflow tracking
4. Model evaluation (R², RMSE, MAE, feature importance)
5. Registration in Unity Catalog (`cfo_banking_demo.models.deposit_beta@champion`)
6. Deployment to Model Serving endpoint
7. Real-time inference for scenario analysis
8. Monitoring for feature drift and model decay

**Example Use Case**:
```
Rate Shock: +100 bps Fed Funds increase
→ MMDA beta: 0.85 → 8.5% runoff expected
→ DDA beta: 0.20 → 2.0% runoff expected
→ Total funding gap: $2.5B
→ CFO Decision: Secure wholesale funding or reduce loan growth
```

### 4. Regulatory Reporting (WS3)

**Purpose**: Automate regulatory report generation with complete audit trail

**FFIEC 101 Schedule RC-R (Risk-Based Capital)**:
- Line 1.a.(1): Commercial & Industrial Loans
- Line 1.c.(1): Commercial Real Estate
- Line 1.c.(2)(a): 1-4 Family Residential Mortgages
- Line 1.d: Consumer Loans
- Calculation: Exposure × Risk Weight = RWA
- Risk Weights: 35% (residential A/B), 50% (residential C/D), 75% (commercial A/B), 100% (commercial C/D)

**FR 2052a (Liquidity Monitoring Report)**:
- Maturity buckets: Day 0-1, 2-7, 8-30, 31-90, 91-180, 180+
- Deposit runoff projections with stress rates
- HQLA classification (Level 1, 2A, 2B)
- Net cash outflow calculations

**Basel III Capital Ratios**:
- CET1 Ratio: (Common Stock + Retained Earnings - Goodwill - Intangibles) / RWA
- Tier 1 Ratio: Tier 1 Capital / RWA
- Total Capital Ratio: (Tier 1 + Tier 2) / RWA
- Thresholds: CET1 ≥ 7.0% (minimum), ≥ 8.5% (well capitalized)

**Liquidity Coverage Ratio (LCR)**:
- LCR = HQLA / Net Cash Outflows (30-day stress)
- HQLA: Level 1 (100% eligible), Level 2A (85%), Level 2B (50%)
- Outflows: Retail stable (3%), retail less stable (10%), wholesale (25%)
- Minimum: 100%

### 5. Funds Transfer Pricing (WS3)

**Purpose**: Calculate product-level profitability with matched-maturity funding costs

**FTP Methodology**:
```
FTP Rate = Funding Curve Rate + Liquidity Premium + Capital Charge
```

**Example FTP Rates**:
- Commercial RE (5-10Y): 4.50% + 0.25% + 0.15% = 4.90%
- C&I (1-5Y): 4.00% + 0.30% + 0.20% = 4.50%
- Residential Mortgage (20-30Y): 4.75% + 0.15% + 0.10% = 5.00%
- Consumer Auto (3-5Y): 5.50% + 0.50% + 0.30% = 6.30%

**Product Profitability**:
```
Pre-Tax Profit = Interest Income - FTP Charge + Fee Income - Operating Expenses - Credit Loss Provision
ROE = Pre-Tax Profit / (Balance × 8% Capital Requirement)
```

### 6. Agent Tools (WS4)

**Purpose**: Provide AI assistant with treasury calculation capabilities

**Available Tools** (`outputs/agent_tools_library.py`):
1. `call_deposit_beta_model(rate_change_bps, product_type)`: Calculate deposit runoff
2. `calculate_lcr(deposit_runoff_multiplier)`: Calculate Liquidity Coverage Ratio
3. `query_unity_catalog(sql_query)`: Execute SQL against Unity Catalog
4. `get_portfolio_summary(asset_class)`: Get portfolio aggregations
5. `get_treasury_yields(tenor)`: Fetch yield curve data from Alpha Vantage

**Integration**:
- Claude Sonnet 4.5 with MLflow tracing
- Professional response formatting
- Tool execution transparency (shows which tools were called)

### 7. React Frontend (WS6)

**Purpose**: Executive dashboard with AI-powered analytics

**Features**:
- Real-time KPIs (Total Assets, Deposits, NIM, LCR)
- Portfolio analytics with drill-down capabilities
- Risk metrics (credit risk, rate shock, LCR stress)
- Recent activity stream
- AI Assistant with natural language queries
- Data source transparency (hover tooltips show Unity Catalog lineage)

**Technology**:
- Next.js 14 with App Router
- Static export for Databricks Apps deployment
- Framer Motion for animations
- TailwindCSS for styling
- Professional design system (navy #1B3139, cyan #00A8E1, slate neutrals)

### 8. Lakeview Dashboards (WS5)

**Purpose**: Executive BI dashboards with Databricks SQL

**8 Visualizations** (`outputs/22_EXACT_DASHBOARD_SPECS.md`):
1. **KPI Scorecard**: Total Assets, Deposits, NIM, LCR (4 counter widgets)
2. **Treasury Yield Curve**: Line chart with area fill (10 tenors)
3. **Securities Portfolio Breakdown**: Table with security type, value, yield, duration
4. **Deposit Beta Sensitivity**: Horizontal bar chart colored by beta coefficient
5. **Capital Adequacy Ratios**: Bullet chart with minimum/target reference lines
6. **Liquidity Waterfall**: Waterfall chart showing HQLA sources and cash outflows
7. **Recent Loan Activity**: Table with product type, borrower, date, amount, rate
8. **NIM Components Waterfall**: Waterfall chart showing income/expense breakdown

**Design System**:
- Primary: Navy Dark (#1B3139), Cyan (#00A8E1), Lava (#FF3621)
- Data Viz: Green (#10B981), Red (#EF4444), Gold (#F59E0B)
- Neutrals: Slate Dark (#475569), Slate Med (#64748B), Gray BG (#F8FAFC)

---

## Data Flow

### Real-Time Loan Origination Flow

```
1. Event Generation
   ↓
   Loan Origination System generates JSON event
   (borrower, loan details, risk assessment)

2. Bronze Ingestion
   ↓
   Delta table: bronze_core_banking.loan_origination_events
   - ACID transactions
   - Schema enforcement
   - Audit trail with ingestion timestamp

3. Delta Live Tables Pipeline
   ↓
   Transformations:
   - Parse JSON structure
   - Extract GL entries (debit/credit)
   - Calculate liquidity impact
   - Determine regulatory impact

4. Silver Layer - GL Posting
   ↓
   silver_finance.gl_entries
   - Account 1100 (Loans Receivable) Debit
   - Account 2100 (Customer Deposit) Credit
   - Validation: Sum(Debits) = Sum(Credits)

5. Gold Layer - Aggregations
   ↓
   gold_finance.intraday_liquidity_position
   - Cumulative cash outflow by hour
   - Available HQLA balance
   - LCR ratio calculation
   - Stress test pass/fail

6. Consumption
   ↓
   - Lakeview dashboard updates (real-time)
   - React frontend refreshes (WebSocket or polling)
   - AI Assistant queries (on-demand)
```

### Batch Regulatory Reporting Flow

```
1. Data Sources
   ↓
   - silver_finance.loan_portfolio
   - silver_finance.deposit_portfolio
   - silver_finance.securities
   - gold_finance.capital_structure

2. RWA Calculation
   ↓
   For each loan:
   - Determine asset category
   - Assign risk weight based on credit score
   - Calculate RWA = Exposure × Risk Weight

3. Report Generation
   ↓
   FFIEC 101 Schedule RC-R:
   - Group by asset category
   - Sum exposures and RWA
   - Format per regulatory specifications

   FR 2052a Maturity Ladder:
   - Classify deposits by maturity bucket
   - Apply stress runoff rates
   - Calculate expected outflows

4. Validation
   ↓
   - Reconciliation checks (silver vs gold)
   - Balance validation (assets = liabilities + equity)
   - Threshold checks (LCR ≥ 100%, CET1 ≥ 7%)

5. Export
   ↓
   - gold_finance.ffiec_101_schedule_rc_r (persisted table)
   - gold_finance.fr_2052a_maturity_ladder (persisted table)
   - CSV export for regulatory submission (optional)
```

---

## Setup and Installation

### Prerequisites

- Databricks workspace (DBR 14.3 LTS ML or higher)
- Unity Catalog enabled
- SQL Warehouse (any size, Photon enabled recommended)
- Python 3.11+
- Node.js 18+ (for React frontend)

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd databricks-cfo-banking-demo
```

### Step 2: Set Up Python Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Key Dependencies**:
- databricks-sdk
- mlflow
- scikit-learn
- xgboost
- shap
- fastapi
- uvicorn

### Step 3: Configure Databricks Authentication

Create `.databrickscfg` or set environment variables:

```bash
export DATABRICKS_HOST="https://<workspace-url>"
export DATABRICKS_TOKEN="<your-token>"
```

Or use Databricks CLI:

```bash
databricks auth login --host <workspace-url>
```

### Step 4: Create Unity Catalog Structure

```bash
python outputs/01_create_catalog_structure.py
```

This creates:
- Catalog: `cfo_banking_demo`
- Schemas: `bronze_core_banking`, `bronze_market`, `silver_finance`, `gold_finance`, `gold_analytics`

### Step 5: Generate Data

Run data generation scripts in sequence:

```bash
python outputs/03_generate_loan_portfolio.py        # 97,200 loans (~5 min)
python outputs/04_generate_deposit_portfolio.py     # 402,000 deposits (~8 min)
python outputs/05_generate_securities_portfolio.py  # 1,000 securities (~1 min)
python outputs/06_generate_treasury_yields.py       # 900 yield data points (~1 min)
python outputs/18_create_missing_tables.py          # Capital, profitability, LCR tables
```

### Step 6: Generate Regulatory Tables

```bash
python outputs/26_complete_remaining_tasks.py
```

This creates:
- `gold_finance.intraday_liquidity_position`
- `gold_finance.rwa_calculation`
- `gold_finance.ftp_rates`
- `gold_finance.product_profitability`

### Step 7: Upload Notebooks to Databricks

```bash
databricks workspace import-dir \
  ./notebooks \
  /Users/<your-email>/cfo-banking-demo/notebooks
```

### Step 8: Deploy React Frontend (Optional)

```bash
cd frontend_app
npm install
npm run build
npm run export
```

Deploy to Databricks Apps or serve locally:

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8010
```

Access at: `http://localhost:8010`

---

## Demo Scenarios

### Scenario 1: Executive Dashboard (5 minutes)

**Objective**: Show unified treasury data hub with real-time KPIs

**Steps**:
1. Open React frontend: `http://localhost:8010`
2. Highlight key metrics:
   - Total Assets: $31.0B (+1.8%)
   - Total Deposits: $28.5B (-0.5%)
   - Net Interest Margin: 2.85% (+3 bps)
   - LCR Ratio: 125% (Compliant)
3. Demonstrate data source transparency:
   - Hover over metrics to see Unity Catalog lineage
   - Show "Source: cfo_banking_demo.silver_finance.loan_portfolio"
4. Navigate to Portfolio Analytics:
   - Drill down by product type
   - Show credit quality distribution
5. Ask AI Assistant: "What is our largest loan exposure?"

**Key Talking Points**:
- Single source of truth for all treasury data
- Real-time updates vs T+1 batch processing
- Complete data lineage for audit trail

### Scenario 2: Real-Time Loan Origination (10 minutes)

**Objective**: Demonstrate streaming event processing and GL posting

**Steps**:
1. Open notebook: `notebooks/WS2_RealTime_Streaming_Demo.py`
2. Run "Generate Sample Events" cell:
   - Show loan origination event structure
   - Highlight GL entries (double-entry bookkeeping)
   - Point out liquidity impact and RWA calculations
3. Generate 100 events and ingest to bronze layer
4. Run "GL Posting Logic" cells:
   - Show real-time GL entries
   - Validate debits = credits
5. Display intraday liquidity monitoring:
   - Cumulative cash outflow by hour
   - Available HQLA balance
   - LCR ratio tracking
6. Compare performance:
   - Traditional batch: 24+ hours
   - Databricks streaming: <1 second

**Key Talking Points**:
- Sub-second processing latency
- Immediate liquidity visibility (T+0 vs T+1)
- Automated GL reconciliation

### Scenario 3: Deposit Beta Model & Rate Shock (10 minutes)

**Objective**: Show AI/ML capabilities for treasury risk management

**Steps**:
1. Open notebook: `notebooks/WS3_Mosaic_AI_Model_Training_Demo.py`
2. Run "Feature Engineering" cells:
   - Show deposit portfolio data (402,000 accounts)
   - Explain features: balance, rate, age, product type
3. Run "Model Training" cells:
   - XGBoost training with MLflow tracking
   - Show model performance: R² ~0.95
   - Display feature importance chart
4. Run "Rate Shock Scenario Analysis" cells:
   - Scenario: +100 bps Fed Funds increase
   - MMDA runoff: 8.5% (high beta = rate sensitive)
   - DDA runoff: 2.0% (low beta = sticky deposits)
   - Total funding gap: $2.5B
5. Show model registration in Unity Catalog:
   - Model: `cfo_banking_demo.models.deposit_beta@champion`
   - Versioning and alias management
6. Demonstrate real-time inference for what-if scenarios

**Key Talking Points**:
- Predictive analytics vs historical static betas
- Immediate scenario analysis (seconds vs days)
- Model governance with Unity Catalog

### Scenario 4: Regulatory Reporting Automation (10 minutes)

**Objective**: Demonstrate automated regulatory report generation

**Steps**:
1. Open notebook: `notebooks/WS3_Regulatory_Reporting_Demo.py`
2. Run "FFIEC 101 Schedule RC-R" cells:
   - Show Risk-Based Capital Report
   - Line items: Commercial RE, C&I, Residential, Consumer
   - RWA calculation with Basel III risk weights
3. Run "FR 2052a Maturity Ladder" cells:
   - Liquidity monitoring by maturity bucket
   - Deposit runoff projections with stress rates
4. Run "Basel III Capital Ratios" cells:
   - CET1 Ratio: 12.5% (well capitalized, threshold 8.5%)
   - Tier 1 Ratio: 14.0% (well capitalized, threshold 10.0%)
   - Total Capital Ratio: 16.8% (well capitalized, threshold 13.0%)
5. Run "LCR Calculation" cells:
   - HQLA: $8.2B (Level 1, 2A, 2B classification)
   - Net Cash Outflows: $2.8B (30-day stress)
   - LCR: 293% (compliant, minimum 100%)
6. Show time savings:
   - Traditional process: 2 weeks of manual Excel compilation
   - Databricks automation: 2 minutes end-to-end

**Key Talking Points**:
- Complete audit trail with Unity Catalog lineage
- Elimination of manual errors
- Real-time regulatory compliance monitoring

### Scenario 5: Product Profitability with FTP (5 minutes)

**Objective**: Show product-level P&L attribution

**Steps**:
1. Query FTP rates table:
   ```sql
   SELECT product_type, maturity_bucket, ftp_rate
   FROM cfo_banking_demo.gold_finance.ftp_rates
   ```
2. Show FTP methodology:
   - Commercial RE (5-10Y): 4.90% FTP
   - Breakdown: 4.50% funding curve + 0.25% liquidity + 0.15% capital
3. Query product profitability:
   ```sql
   SELECT product_type, balance, interest_income, ftp_charge,
          net_interest_income, pre_tax_profit, roe
   FROM cfo_banking_demo.gold_finance.product_profitability
   ```
4. Explain P&L attribution:
   - Interest Income: What the bank earns
   - FTP Charge: What the product "pays" for funding
   - Net Interest Income: Contribution to NIM
   - ROE: Risk-adjusted return
5. Identify most/least profitable products

**Key Talking Points**:
- Matched-maturity funding costs
- Product-level decision support
- Customer segment optimization opportunities

---

## Dashboards and Visualizations

### Dashboard 1: Executive KPI Scorecard

**Purpose**: High-level financial health metrics updated in real-time

**Metrics Displayed**:
- Total Assets: $31.0B (+1.8% MoM)
- Total Deposits: $28.5B (-0.5% MoM)
- Net Interest Margin: 2.85% (+3 bps)
- LCR Ratio: 125% (Compliant ✓)

**Update Frequency**: Real-time (as new loans originated)

**Data Sources**:
- `cfo_banking_demo.silver_finance.loan_portfolio`
- `cfo_banking_demo.silver_finance.deposit_portfolio`
- `cfo_banking_demo.gold_finance.profitability_metrics`
- `cfo_banking_demo.gold_finance.liquidity_coverage_ratio`

**Business Value**: At-a-glance financial position for executive decision-making

### Dashboard 2: Treasury Yield Curve

**Purpose**: Monitor market interest rate environment

**Visualization**: Line chart with area fill
- X-axis: Maturity (3M, 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 20Y, 30Y)
- Y-axis: Yield (%)
- Historical comparison: Current vs 1 week ago vs 1 month ago

**Update Frequency**: Daily (market data refresh)

**Data Source**: `cfo_banking_demo.bronze_market.treasury_yields`

**Business Value**: Interest rate risk assessment and ALM planning

### Dashboard 3: Securities Portfolio Breakdown

**Purpose**: Detailed view of investment securities holdings

**Table Columns**:
- Security Type (UST, Agency MBS, Corporate Bonds, etc.)
- Market Value ($B)
- Average Yield (%)
- Effective Duration (years)
- HQLA Level (Level 1, 2A, 2B)

**Update Frequency**: Daily (mark-to-market)

**Data Source**: `cfo_banking_demo.silver_finance.securities`

**Business Value**: Portfolio composition and liquidity planning

### Dashboard 4: Deposit Beta Sensitivity Analysis

**Purpose**: Visualize deposit sensitivity to interest rate changes

**Visualization**: Horizontal bar chart
- Y-axis: Product types (MMDA, DDA, NOW, Savings, CD)
- X-axis: Balance ($B)
- Color: Deposit beta (green = stable, red = rate sensitive)

**Key Insights**:
- MMDA (beta 0.85): Most rate-sensitive, highest runoff risk
- DDA (beta 0.20): Most stable, core funding base
- Savings (beta 0.60): Moderate sensitivity

**Update Frequency**: Monthly (model retraining)

**Data Sources**:
- `cfo_banking_demo.silver_finance.deposit_portfolio`
- `cfo_banking_demo.models.deposit_beta` (ML model)

**Business Value**: Rate shock scenario planning and funding strategy

### Dashboard 5: Capital Adequacy Ratios

**Purpose**: Monitor regulatory capital compliance

**Visualization**: Bullet chart with reference lines
- Actual ratio (bold bar)
- Minimum threshold (red dashed line)
- Well-capitalized threshold (gold dashed line)
- Target threshold (green dashed line)

**Ratios Displayed**:
- CET1 Ratio: 12.5% (target ≥ 8.5%)
- Tier 1 Ratio: 14.0% (target ≥ 10.0%)
- Total Capital Ratio: 16.8% (target ≥ 13.0%)

**Update Frequency**: Daily

**Data Sources**:
- `cfo_banking_demo.gold_finance.capital_structure`
- `cfo_banking_demo.gold_finance.rwa_calculation`

**Business Value**: Ensure Basel III compliance and manage capital buffers

### Dashboard 6: Liquidity Waterfall

**Purpose**: Visualize LCR components and compliance

**Visualization**: Waterfall chart
- HQLA sources (positive, green): Level 1, Level 2A, Level 2B
- Cash outflows (negative, red): Retail runoff, Wholesale runoff
- Net result: LCR ratio

**Calculation Flow**:
```
Start: $0
+ Level 1 HQLA: +$6.5B (UST, Agency MBS)
+ Level 2A HQLA: +$1.2B (Agency CMO, GSE)
+ Level 2B HQLA: +$0.5B (Corporate/Muni bonds)
- Retail Runoff: -$0.8B (3% of retail deposits)
- Wholesale Runoff: -$2.0B (25% of wholesale funding)
= Net HQLA: $5.4B
÷ Net Outflows: $2.8B
= LCR: 193%
```

**Update Frequency**: Daily

**Data Sources**:
- `cfo_banking_demo.silver_finance.securities`
- `cfo_banking_demo.silver_finance.deposit_portfolio`
- `cfo_banking_demo.gold_finance.liquidity_coverage_ratio`

**Business Value**: Real-time liquidity monitoring and stress testing

### Dashboard 7: Recent Loan Activity

**Purpose**: Monitor daily loan origination activity

**Table Columns**:
- Product Type
- Borrower Name
- Origination Date
- Amount ($M)
- Interest Rate (%)
- Risk Rating (A/B/C/D)

**Filters**:
- Date range (last 7 days, 30 days, 90 days)
- Product type
- Amount threshold
- Risk rating

**Update Frequency**: Real-time (as loans originated)

**Data Source**: `cfo_banking_demo.silver_finance.loan_portfolio`

**Business Value**: Track loan production trends and credit quality

### Dashboard 8: Net Interest Margin Waterfall

**Purpose**: Decompose NIM into components

**Visualization**: Waterfall chart
- Income components (green): Loan interest, securities yield, fee income
- Expense components (red): Deposit interest, funding costs, operating expenses
- Net result: Net Interest Margin (%)

**Calculation Flow**:
```
Start: 0%
+ Loan Interest Income: +3.50%
+ Securities Yield: +0.45%
+ Fee Income: +0.15%
- Deposit Interest Expense: -1.20%
- Operating Expenses: -0.50%
- Credit Loss Provision: -0.25%
= Net Interest Margin: 2.15%
```

**Update Frequency**: Monthly

**Data Sources**:
- `cfo_banking_demo.silver_finance.loan_portfolio`
- `cfo_banking_demo.silver_finance.deposit_portfolio`
- `cfo_banking_demo.gold_finance.profitability_metrics`

**Business Value**: Identify NIM drivers and optimization opportunities

---

## Repository Structure

```
databricks-cfo-banking-demo/
│
├── notebooks/                          # 📊 Databricks Production Notebooks
│   ├── README.md                       # Complete notebook catalog with execution order
│   ├── Phase_1_Bronze_Tables.py        # Data foundation: Raw ingestion
│   ├── Phase_2_DLT_Pipelines.py        # Delta Live Tables ETL
│   ├── Phase1_Enhanced_Deposit_Beta_Model.py          # Treasury: Static beta (XGBoost)
│   ├── Phase2_Vintage_Analysis_and_Decay_Modeling.py  # Treasury: Cohort survival
│   ├── Phase3_Dynamic_Beta_and_Stress_Testing.py      # Treasury: CCAR/DFAST
│   ├── Train_PPNR_Models.py            # PPNR forecasting models
│   ├── Batch_Inference_*.py            # Weekly portfolio scoring
│   ├── Generate_*.py                   # Analytics report generators
│   ├── WS3_*.py                        # Workshop demo notebooks
│   └── archive/                        # Superseded notebooks
│
├── frontend_app/                       # 💻 Next.js React Frontend
│   ├── app/
│   │   ├── page.tsx                    # Main dashboard (6 tabs)
│   │   └── assistant/page.tsx          # AI chat interface
│   ├── components/
│   │   ├── treasury/                   # Treasury modeling dashboards
│   │   ├── charts/                     # Recharts visualizations
│   │   └── tables/                     # Data grid components
│   ├── out/                            # Static build output
│   └── package.json
│
├── backend/                            # 🔌 FastAPI Backend
│   ├── main.py                         # REST API + static serving
│   └── requirements.txt
│
├── dashboards/                         # 📈 Lakeview Dashboard SQL
│   ├── 01_Executive_Overview_Dashboard.sql
│   ├── 05_CCAR_DFAST_Regulatory_Dashboard.sql
│   ├── 08_Flight_Deck.sql              # Exported: Bank CFO Flight Deck
│   ├── 09_Portfolio_Suite.sql          # Exported: CFO Deposit Portfolio Suite
│   ├── 10_Regulatory_Reconciliation_Dashboard.sql  # NEW: Data quality & lineage
│   └── *.json                          # Raw dashboard exports
│
├── outputs/                            # 🛠️ Generated Scripts & Libraries
│   ├── agent_tools_library.py          # CFO agent tools (LCR, deposit beta)
│   └── scripts/models/                 # LCR/RWA calculators, regulatory reports
│
├── dev-scripts/                        # 🔧 Development Utilities
│   └── (dashboard export, data generation, validation)
│
├── docs/demo/                          # 📚 Demo Scripts & Coverage Matrix
│   ├── DEMO_TALK_TRACK.md              # 15-20 min walkthrough
│   └── TREASURY_DEMO_SCRIPT.md         # Treasury modeling deep dive
│
└── databricks.yml                      # Databricks Apps deployment config
```

### Key Directories

**notebooks/** - Databricks notebooks organized by function (see notebooks/README.md for full catalog):
- **Phase 1-3 Treasury Modeling**: Static deposit beta → Vintage analysis → Dynamic beta/stress testing (Chen sigmoid, CCAR/DFAST)
- **PPNR Models**: Non-Interest Income & Expense forecasting
- **Data Foundation**: Bronze ingestion (Phase_1) and DLT pipelines (Phase_2)
- **Batch Inference & Reporting**: Weekly portfolio scoring and analytics report generation
- **Demo/Workshop**: Mosaic AI training demo, Data Science Agent demo
- **archive/**: Superseded notebooks (Complete_Deposit_Beta_Model_Workflow, simplified versions)

**frontend_app/** - Next.js 14 React application:
- Bloomberg Terminal-inspired UI with navy/cyan color scheme
- 6 tabs: Portfolio, Risk Analysis, Recent Activity, Deposit Beta, Vintage Analysis, CCAR/DFAST
- Treasury modeling dashboards with advanced visualizations (survival curves, stress test projections)
- AI assistant chat interface powered by Claude Sonnet 4.5

**backend/** - FastAPI server:
- REST API endpoints for Unity Catalog data (`/api/data/*`)
- AI assistant chat endpoint (`/api/chat`)
- Serves static frontend files from `frontend_app/out/`
- Agent tools integration for deposit beta and LCR calculations

**outputs/** - Generated artifacts:
- `agent_tools_library.py`: Reusable Python functions for CFO agent (deposit beta model inference, LCR calculation, Unity Catalog queries)
- `scripts/`: Organized by subdirectory (agents, dashboards, data_generation, models, pipelines, utilities)
- `docs/`: Generated documentation and specifications

**docs/** - Documentation organized by category:
- `demo/`: Complete walkthrough scripts and reference materials
- `requirements/`: Data requirements and analysis
- `research/`: Treasury modeling research and implementation notes
- Root-level guides for AutoML, model validation, and notebook updates

---

## Code Flow

<details>
<summary><strong>⚡ Complete Application Flows</strong> (click to expand)</summary>

This section explains how data and user requests flow through the application across different scenarios.

### 1. User Request Flow (Frontend → Backend → Unity Catalog)

When a user interacts with the dashboard, requests flow through multiple layers:

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERACTION                        │
│                   (Browser: React Component)                    │
├─────────────────────────────────────────────────────────────────┤
│ User clicks "Portfolio Analytics" or changes filters            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND COMPONENT                         │
│            (frontend_app/app/page.tsx or components/)           │
├─────────────────────────────────────────────────────────────────┤
│ 1. React component calls useEffect() or event handler          │
│ 2. Executes fetch() to backend API endpoint                    │
│    Example: fetch('/api/data/portfolio-summary')               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                            │
│                   (backend/main.py endpoints)                   │
├─────────────────────────────────────────────────────────────────┤
│ 1. FastAPI route handler receives request                      │
│    @app.get("/api/data/portfolio-summary")                     │
│ 2. Constructs SQL query for Unity Catalog                      │
│ 3. Calls agent_tools.query_unity_catalog(sql)                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      AGENT TOOLS LIBRARY                        │
│              (outputs/agent_tools_library.py)                   │
├─────────────────────────────────────────────────────────────────┤
│ 1. CFOAgentTools.query_unity_catalog() method                  │
│ 2. Uses Databricks SDK to execute SQL                          │
│    w.statement_execution.execute_statement(statement=sql)      │
│ 3. Polls for result completion                                 │
│ 4. Returns structured response: {                              │
│      "success": True,                                           │
│      "columns": [],  # Note: Empty from Unity Catalog          │
│      "data": [['402000', '31017679072.0', '0.350']]            │
│    }                                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      UNITY CATALOG                              │
│         (Databricks Lakehouse - Delta Lake Tables)             │
├─────────────────────────────────────────────────────────────────┤
│ 1. SQL Warehouse executes query with Photon acceleration       │
│ 2. Reads from Delta tables:                                    │
│    - cfo_banking_demo.silver_finance.loan_portfolio            │
│    - cfo_banking_demo.silver_finance.deposit_portfolio         │
│    - cfo_banking_demo.gold_finance.profitability_metrics       │
│ 3. Returns query results as list of lists                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    RESPONSE PROCESSING                          │
│                   (backend/main.py endpoints)                   │
├─────────────────────────────────────────────────────────────────┤
│ 1. Backend processes raw data from Unity Catalog               │
│ 2. Maps array indices to field names (since columns[] empty)   │
│    row = result["data"][0]                                     │
│    data = {                                                     │
│      "total_accounts": int(row[0]),                            │
│      "total_balance": float(row[1]),                           │
│      "avg_beta": float(row[2])                                 │
│    }                                                            │
│ 3. Performs type conversions (str → int/float)                 │
│ 4. Returns JSON response to frontend                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND RENDERING                           │
│              (React component re-renders with data)             │
├─────────────────────────────────────────────────────────────────┤
│ 1. fetch() promise resolves with JSON data                     │
│ 2. React state updated via setState() or setData()             │
│ 3. Component re-renders with new data                          │
│ 4. Charts/tables display formatted results                     │
│ 5. Loading spinners removed, data visible to user              │
└─────────────────────────────────────────────────────────────────┘
```

**Example: Fetching Deposit Beta Metrics**

```typescript
// frontend_app/components/treasury/DepositBetaDashboard.tsx
useEffect(() => {
  fetch('/api/data/deposit-beta-metrics')
    .then(res => res.json())
    .then(data => setMetrics(data.data))
}, [])
```

```python
# backend/main.py
@app.get("/api/data/deposit-beta-metrics")
async def get_deposit_beta_metrics():
    query = """
    SELECT COUNT(*), SUM(balance), AVG(deposit_beta)
    FROM cfo_banking_demo.silver_finance.deposit_portfolio
    """
    result = agent_tools.query_unity_catalog(query)
    row = result["data"][0]
    return {
        "success": True,
        "data": {
            "total_accounts": int(row[0]),
            "total_balance": float(row[1]),
            "avg_beta": float(row[2])
        }
    }
```

### 2. Treasury Dashboard Flow

The treasury modeling tabs (Deposit Beta, Vintage Analysis, CCAR/DFAST Stress Testing) fetch data from ML model-generated tables:

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER CLICKS TREASURY TAB                    │
│         (Deposit Beta / Vintage Analysis / CCAR/DFAST)          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  TREASURY REACT COMPONENT                       │
│       (frontend_app/components/treasury/*.tsx)                  │
├─────────────────────────────────────────────────────────────────┤
│ 1. DepositBetaDashboard.tsx loads on mount                     │
│ 2. Fetches 9 different datasets in parallel:                   │
│    - /api/data/deposit-beta-metrics                            │
│    - /api/data/deposit-beta-distribution                       │
│    - /api/data/at-risk-deposits                                │
│    - /api/data/component-decay-metrics                         │
│    - /api/data/cohort-survival                                 │
│    - /api/data/runoff-forecasts                                │
│    - /api/data/dynamic-beta-parameters                         │
│    - /api/data/stress-test-results                             │
│    - /api/data/stress-test-summary                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   9 TREASURY API ENDPOINTS                      │
│                     (backend/main.py)                           │
├─────────────────────────────────────────────────────────────────┤
│ Each endpoint queries ML-generated tables:                      │
│                                                                 │
│ 1. deposit-beta-metrics:                                       │
│    FROM deposit_beta_predictions                               │
│    Aggregates: total accounts, balance, avg beta, at-risk %    │
│                                                                 │
│ 2. at-risk-deposits:                                           │
│    FROM deposit_beta_predictions WHERE deposit_beta > 0.6      │
│    Groups by product type with risk classification             │
│                                                                 │
│ 3. cohort-survival:                                            │
│    FROM vintage_cohort_survival                                │
│    Returns cohort survival curves by vintage quarter           │
│                                                                 │
│ 4. stress-test-results:                                        │
│    FROM stress_test_results                                    │
│    Returns 9-quarter capital ratio projections for CCAR        │
│                                                                 │
│ All endpoints:                                                  │
│ - Query Unity Catalog via agent_tools                          │
│ - Handle empty columns[] array with direct index access        │
│ - Perform type conversions (str → int/float)                   │
│ - Return structured JSON                                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│               ML MODEL-GENERATED TABLES                         │
│                    (Unity Catalog)                              │
├─────────────────────────────────────────────────────────────────┤
│ These tables are created by Phase 1-3 notebooks:               │
│                                                                 │
│ • deposit_beta_predictions:                                    │
│   - Generated by: Batch_Inference_Deposit_Beta_Model.py       │
│   - Uses @champion model from Unity Catalog                    │
│   - XGBoost model predicts deposit beta for each account       │
│   - Fields: account_id, product_type, balance, deposit_beta   │
│                                                                 │
│ • vintage_cohort_survival:                                     │
│   - Generated by: Phase2_Vintage_Analysis_and_Decay_Modeling.py│
│   - Tracks deposit cohort retention over time                  │
│   - Fields: vintage_quarter, months_aged, survival_rate       │
│                                                                 │
│ • stress_test_results:                                         │
│   - Generated by: Phase3_Dynamic_Beta_and_Stress_Testing.py   │
│   - CCAR/DFAST 9-quarter projections                          │
│   - Fields: scenario, quarter, cet1_ratio, nii_delta          │
│                                                                 │
│ • dynamic_beta_parameters:                                     │
│   - Generated by: Phase3_Dynamic_Beta_and_Stress_Testing.py   │
│   - Chen (2025) sigmoid function for time-varying beta        │
│   - Fields: product_type, rate_regime, beta_coefficient       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              TREASURY DASHBOARD VISUALIZATION                   │
│           (Recharts components in React)                        │
├─────────────────────────────────────────────────────────────────┤
│ 1. Deposit Beta Dashboard:                                     │
│    - Horizontal bar chart: Balance by product (colored by beta)│
│    - At-risk table: Accounts with beta > 0.6                  │
│                                                                 │
│ 2. Vintage Analysis Dashboard:                                 │
│    - Line chart: Cohort survival curves over 24 months        │
│    - Grouped by vintage quarter (2023-Q1 through 2024-Q4)     │
│                                                                 │
│ 3. Stress Test Dashboard (CCAR/DFAST):                         │
│    - Line chart: CET1 ratio projections over 9 quarters       │
│    - Multiple scenarios: Baseline, Adverse, Severely Adverse   │
│    - Delta NII and EVE impact tables                           │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Build & Deployment Flow

The application build and deployment process:

```
┌─────────────────────────────────────────────────────────────────┐
│                   DEVELOPMENT: npm run dev                      │
├─────────────────────────────────────────────────────────────────┤
│ 1. cd frontend_app && npm run dev                              │
│ 2. Next.js dev server starts on http://localhost:3000          │
│ 3. Hot Module Replacement (HMR) enabled                        │
│ 4. Component changes auto-reload in browser                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   PRODUCTION BUILD                              │
├─────────────────────────────────────────────────────────────────┤
│ 1. npm run build (in frontend_app/)                            │
│    ↓                                                            │
│    Next.js static export process begins                        │
│    ↓                                                            │
│ 2. Compiles TypeScript → JavaScript                            │
│    - app/page.tsx → JavaScript bundle                          │
│    - components/**/*.tsx → optimized modules                   │
│    ↓                                                            │
│ 3. Bundles with Webpack                                        │
│    - Code splitting by route                                   │
│    - Tree shaking (removes unused code)                        │
│    - Minification (reduces file size)                          │
│    ↓                                                            │
│ 4. Generates static HTML pages                                 │
│    - index.html (main dashboard)                               │
│    - assistant.html (AI chat page)                             │
│    ↓                                                            │
│ 5. Outputs to frontend_app/out/ directory                      │
│    - out/index.html                                            │
│    - out/assistant.html                                        │
│    - out/favicon.ico                                           │
│    - out/_next/static/chunks/*.js (JavaScript bundles)         │
│    - out/_next/static/css/*.css (stylesheets)                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   LOCAL FASTAPI SERVER                          │
├─────────────────────────────────────────────────────────────────┤
│ 1. python3 -m uvicorn backend.main:app --reload               │
│ 2. Starts on http://localhost:8000                             │
│ 3. Serves static files from frontend_app/out/                  │
│    - GET / → out/index.html                                    │
│    - GET /assistant → out/assistant.html                       │
│    - GET /favicon.ico → out/favicon.ico                        │
│    - GET /_next/static/* → out/_next/static/*                  │
│ 4. API endpoints:                                               │
│    - /api/data/* → Unity Catalog queries                       │
│    - /api/chat → Claude Sonnet 4.5 AI assistant                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              DATABRICKS APPS DEPLOYMENT                         │
├─────────────────────────────────────────────────────────────────┤
│ 1. Push code to GitHub:                                        │
│    git add . && git commit && git push                         │
│    ↓                                                            │
│ 2. Sync Databricks Workspace with GitHub:                      │
│    Repos → Pull changes from main branch                       │
│    ↓                                                            │
│ 3. Databricks Apps takes SNAPSHOT of Workspace path:           │
│    /Workspace/Users/<email>/databricks-cfo-banking-demo/       │
│    ↓                                                            │
│ 4. Reads databricks.yml configuration:                         │
│    command: ["python3", "-m", "uvicorn", "backend.main:app"]  │
│    ↓                                                            │
│ 5. Starts FastAPI server in Databricks Apps container          │
│    ↓                                                            │
│ 6. App accessible at:                                           │
│    https://cfo-banking-demo-<id>.aws.databricksapps.com       │
│    ↓                                                            │
│ 7. Authentication:                                              │
│    - Uses Databricks Workspace credentials                     │
│    - Unity Catalog access inherited from user permissions      │
│    - No separate API keys needed                               │
└─────────────────────────────────────────────────────────────────┘
```

**Important Notes**:
- `frontend_app/out/` directory MUST be committed to git (removed from `.gitignore`)
- Databricks Apps serves the SNAPSHOT at deployment time (not live GitHub)
- To update deployed app: Push code → Sync Workspace → Redeploy app
- Static export means no Next.js server-side features (no SSR, no ISR, no Edge Runtime)

### 4. AI Assistant Flow

The AI-powered chat assistant uses Claude Sonnet 4.5 with agent tools:

```
┌─────────────────────────────────────────────────────────────────┐
│                  USER TYPES QUESTION                            │
│     (frontend_app/app/assistant/page.tsx chat interface)       │
├─────────────────────────────────────────────────────────────────┤
│ User: "What is our LCR ratio with a 20% deposit runoff?"       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND CHAT COMPONENT                      │
├─────────────────────────────────────────────────────────────────┤
│ 1. User message added to messages[] state                      │
│ 2. POST request to /api/chat with:                             │
│    {                                                            │
│      "message": "What is our LCR ratio...",                    │
│      "history": [...previous messages]                         │
│    }                                                            │
│ 3. Shows "Claude is thinking..." loading state                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  /api/chat ENDPOINT                             │
│                  (backend/main.py)                              │
├─────────────────────────────────────────────────────────────────┤
│ 1. Receives user message and history                           │
│ 2. Constructs Claude API request with:                         │
│    - Model: claude-sonnet-4-5-20250929                         │
│    - System prompt: "You are a CFO assistant..."               │
│    - Tools: [calculate_lcr, call_deposit_beta_model,           │
│               query_unity_catalog, get_portfolio_summary]      │
│    - MLflow tracing enabled (auto-logs conversation)           │
│ 3. Sends request to Claude API                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              CLAUDE SONNET 4.5 REASONING                        │
├─────────────────────────────────────────────────────────────────┤
│ 1. Analyzes user question                                      │
│ 2. Identifies needed tools:                                    │
│    - "LCR ratio" → needs calculate_lcr()                       │
│    - "20% deposit runoff" → needs parameter 0.20               │
│ 3. Returns tool use request:                                   │
│    {                                                            │
│      "type": "tool_use",                                       │
│      "name": "calculate_lcr",                                  │
│      "input": {"deposit_runoff_multiplier": 0.20}              │
│    }                                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              TOOL EXECUTION (Backend)                           │
├─────────────────────────────────────────────────────────────────┤
│ 1. Backend recognizes tool_use request                         │
│ 2. Calls agent_tools.calculate_lcr(0.20)                       │
│ 3. CFOAgentTools.calculate_lcr() method:                       │
│    a. Queries securities for HQLA calculation                  │
│    b. Queries deposits for outflow calculation                 │
│    c. Applies 20% stress multiplier                            │
│    d. Calculates LCR = HQLA / Net Outflows                     │
│ 4. Returns result:                                              │
│    {                                                            │
│      "lcr_ratio": 0.95,                                        │
│      "hqla": 8200000000,                                       │
│      "net_outflows": 8631578947,                               │
│      "compliant": False,                                       │
│      "shortfall": 431578947                                    │
│    }                                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│            CLAUDE GENERATES RESPONSE                            │
├─────────────────────────────────────────────────────────────────┤
│ 1. Receives tool execution result                              │
│ 2. Formats professional response:                              │
│    "Based on the LCR calculation with a 20% deposit runoff    │
│     stress scenario, your bank's LCR would be 95%,            │
│     falling below the regulatory minimum of 100%.             │
│                                                                 │
│     - HQLA: $8.2B                                              │
│     - Net Cash Outflows (30-day): $8.6B                        │
│     - Shortfall: $431M                                         │
│                                                                 │
│     To achieve compliance, you would need to either:          │
│     1. Increase HQLA by $431M (issue/buy UST or Agency MBS)  │
│     2. Reduce net outflows by securing stable funding         │
│     3. Combination of both approaches"                         │
│ 3. Returns response to backend                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│               MLFLOW TRACING (Automatic)                        │
├─────────────────────────────────────────────────────────────────┤
│ 1. MLflow captures entire interaction:                         │
│    - User input                                                 │
│    - Tool calls with parameters                                │
│    - Tool execution results                                    │
│    - Model response                                            │
│    - Latency metrics                                           │
│ 2. Logged to mlflow.db (local) or Databricks tracking server  │
│ 3. Accessible via MLflow UI for debugging and monitoring      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              FRONTEND DISPLAYS RESPONSE                         │
├─────────────────────────────────────────────────────────────────┤
│ 1. POST /api/chat returns JSON:                                │
│    {"response": "Based on the LCR calculation..."}            │
│ 2. React adds assistant message to messages[] state           │
│ 3. Chat component re-renders with new message                 │
│ 4. Message appears in chat history with formatting            │
│ 5. "Tools used: calculate_lcr" badge shown for transparency   │
└─────────────────────────────────────────────────────────────────┘
```

**Available Agent Tools**:

1. **calculate_lcr(deposit_runoff_multiplier)**
   - Calculates Liquidity Coverage Ratio under stress
   - Queries: securities (HQLA) + deposits (outflows)
   - Returns: LCR ratio, HQLA, net outflows, compliance status

2. **call_deposit_beta_model(rate_change_bps, product_type)**
   - Predicts deposit runoff for rate shock scenarios
   - Uses deployed XGBoost model in Unity Catalog
   - Returns: Expected runoff %, funding gap

3. **query_unity_catalog(sql_query)**
   - Executes arbitrary SQL against Unity Catalog
   - Full access to all cfo_banking_demo tables
   - Returns: Query results as structured data

4. **get_portfolio_summary(asset_class)**
   - Aggregates portfolio metrics by asset class
   - Asset classes: loans, deposits, securities
   - Returns: Balance, count, avg rate, credit quality distribution

### 5. Real-Time Loan Origination Flow (Streaming)

For demonstrating streaming capabilities (not in production use in this demo):

```
┌─────────────────────────────────────────────────────────────────┐
│              EVENT GENERATION                                   │
│     (notebooks/WS2_RealTime_Streaming_Demo.py)                  │
├─────────────────────────────────────────────────────────────────┤
│ 1. Python script generates loan origination events             │
│ 2. Event structure (JSON):                                     │
│    {                                                            │
│      "event_id": "uuid",                                       │
│      "timestamp": "2025-01-25T14:30:00",                       │
│      "borrower": {...},                                        │
│      "loan": {...},                                            │
│      "gl_entries": [                                           │
│        {"account": "1100", "debit": 500000},                  │
│        {"account": "2100", "credit": 500000}                  │
│      ],                                                         │
│      "liquidity_impact": -500000,                              │
│      "regulatory_impact": {"rwa": 375000}                     │
│    }                                                            │
│ 3. Writes to bronze Delta table (ACID transaction)            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│           DELTA LIVE TABLES PIPELINE                            │
│          (notebooks/Phase_2_DLT_Pipelines.py)                   │
├─────────────────────────────────────────────────────────────────┤
│ 1. Bronze → Silver transformation:                             │
│    @dlt.table                                                   │
│    def silver_loan_originations():                             │
│      return (                                                   │
│        dlt.read_stream("bronze_core_banking.loan_events")     │
│          .selectExpr("event_id", "timestamp", "loan.*")       │
│      )                                                          │
│                                                                 │
│ 2. GL Posting:                                                  │
│    @dlt.table                                                   │
│    def silver_gl_entries():                                    │
│      return (                                                   │
│        dlt.read_stream("silver_loan_originations")            │
│          .selectExpr("explode(gl_entries) as entry")          │
│          .select("entry.account", "entry.debit", ...)         │
│      )                                                          │
│                                                                 │
│ 3. Validation:                                                  │
│    @dlt.expect_or_fail("balanced_entries",                     │
│                        "SUM(debit) = SUM(credit)")            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│           GOLD LAYER AGGREGATION                                │
├─────────────────────────────────────────────────────────────────┤
│ 1. Intraday Liquidity Position:                                │
│    Running sum of cash outflows by hour                        │
│    Compares to available HQLA                                  │
│    Calculates real-time LCR                                    │
│                                                                 │
│ 2. Portfolio Aggregations:                                      │
│    Updates total loan balance                                  │
│    Updates RWA calculation                                     │
│    Updates credit quality distribution                         │
│                                                                 │
│ 3. Dashboard Refresh:                                           │
│    Lakeview dashboards auto-refresh (WebSocket)               │
│    React frontend polls /api/data/portfolio-summary           │
│    Shows "Last updated: 2 seconds ago"                         │
└─────────────────────────────────────────────────────────────────┘
```

**Performance Comparison**:
- Traditional Batch (T+1): 24+ hours to reflect in GL and reports
- Databricks Streaming: <1 second end-to-end processing
- Dashboard updates: Real-time (as soon as transaction commits)

### 6. ML Model Training & Analytics Reporting Flow (Phase 1-3)

The deposit beta modeling and analytics reporting workflow follows a Train → Deploy → Analyze pattern:

```
┌─────────────────────────────────────────────────────────────────┐
│         PHASE 1: TRAIN STATIC DEPOSIT BETA MODEL                │
│     (notebooks/Phase1_Enhanced_Deposit_Beta_Model.py)           │
├─────────────────────────────────────────────────────────────────┤
│ 1. Feature Engineering:                                         │
│    - Historical deposit data: balance, rates, account age       │
│    - Customer segments: retail, commercial, wealth              │
│    - Product types: DDA, MMDA, CD, Savings, NOW                │
│    - Rate environment: Fed Funds Rate, Treasury yields          │
│    ↓                                                             │
│ 2. XGBoost Training with MLflow:                                │
│    - Model: XGBoost Regressor (100 estimators)                 │
│    - Target: deposit_beta (rate sensitivity coefficient)       │
│    - MLflow autolog: tracks params, metrics, artifacts         │
│    - Training metrics: RMSE, R², MAE                           │
│    ↓                                                             │
│ 3. Model Registration to Unity Catalog:                        │
│    - Model: cfo_banking_demo.models.deposit_beta               │
│    - Alias: @champion (production model)                       │
│    - Versioning: Automatic (v1, v2, v3...)                     │
│    ↓                                                             │
│ 4. Outputs:                                                      │
│    - Table: cfo_banking_demo.ml_models.deposit_beta_training_data│
│    - Model: Unity Catalog registered model                     │
│    - Artifacts: Feature importance, SHAP values                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│    PHASE 2: VINTAGE ANALYSIS & DECAY MODELING                   │
│  (notebooks/Phase2_Vintage_Analysis_and_Decay_Modeling.py)      │
├─────────────────────────────────────────────────────────────────┤
│ 1. Cohort Creation:                                             │
│    - Group deposits by origination quarter                      │
│    - Track balance retention over 24 months                     │
│    - Calculate survival rates by product type                   │
│    ↓                                                             │
│ 2. Decay Modeling:                                              │
│    - Core vs non-core deposit classification                    │
│    - Exponential decay curve fitting                            │
│    - Runoff rate calculation by cohort vintage                  │
│    ↓                                                             │
│ 3. Outputs:                                                      │
│    - Table: vintage_cohort_survival                             │
│    - Table: component_decay_metrics                             │
│    - Table: deposit_runoff_forecasts                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│    PHASE 3: DYNAMIC BETA & STRESS TESTING                       │
│   (notebooks/Phase3_Dynamic_Beta_and_Stress_Testing.py)         │
├─────────────────────────────────────────────────────────────────┤
│ 1. Chen (2025) Sigmoid Function for Dynamic Beta:              │
│    β(Rm) = βmin + (βmax - βmin) / [1 + exp(-k*(Rm-R0))]       │
│    - Time-varying beta based on rate environment               │
│    - Non-linear response to rate changes                       │
│    ↓                                                             │
│ 2. CCAR/DFAST Stress Scenarios:                                 │
│    - Baseline: Current trajectory (0 bps)                      │
│    - Adverse: Gradual increase (+100 bps)                      │
│    - Severely Adverse: Rapid shock (+200 bps)                  │
│    - Custom: Extreme stress (+300 bps)                         │
│    ↓                                                             │
│ 3. Economic Value of Equity (EVE) Analysis:                     │
│    - Interest rate sensitivity                                  │
│    - Capital impact projections (9 quarters)                   │
│    - CET1 ratio tracking under stress                          │
│    ↓                                                             │
│ 4. Outputs:                                                      │
│    - Table: dynamic_beta_parameters                             │
│    - Table: stress_test_results (9-quarter projections)        │
│    - Table: stress_test_summary (scenario summaries)           │
│    - Table: eve_sensitivity_analysis                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│           BATCH INFERENCE (WEEKLY PORTFOLIO SCORING)            │
│     (notebooks/Batch_Inference_Deposit_Beta_Model.py)           │
├─────────────────────────────────────────────────────────────────┤
│ 1. Load Model from Unity Catalog:                              │
│    model = mlflow.pyfunc.load_model(                           │
│        "models:/cfo_banking_demo.models.deposit_beta@champion" │
│    )                                                            │
│    ↓                                                             │
│ 2. Score Entire Portfolio (402,000 accounts):                  │
│    - Distributed inference using Spark UDFs                    │
│    - 12 minutes vs 16+ hours sequential                        │
│    ↓                                                             │
│ 3. Calculate Rate Shock Scenarios:                             │
│    - +100 bps: Expected runoff percentage                      │
│    - +200 bps: Moderate stress impact                          │
│    - +300 bps: Extreme stress impact                           │
│    ↓                                                             │
│ 4. Outputs:                                                      │
│    - Table: deposit_beta_predictions (account-level scores)    │
│    - Table: rate_shock_analysis (scenario impacts)             │
│    ↓                                                             │
│ Schedule: Sunday 11:00pm (weekly batch job)                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│       ANALYTICS REPORT GENERATION (HTML + DELTA TABLES)         │
│     (notebooks/Generate_Deposit_Analytics_Report.py)            │
├─────────────────────────────────────────────────────────────────┤
│ 1. Load Batch Inference Results:                               │
│    - Read deposit_beta_predictions table                       │
│    - Read vintage_cohort_survival (if available)               │
│    - Read stress_test_results (if available)                   │
│    ↓                                                             │
│ 2. Calculate Report Metrics:                                   │
│    - Portfolio composition (product mix, balances)             │
│    - Rate shock scenarios (runoff projections)                 │
│    - At-risk deposits (beta > 0.6 threshold)                   │
│    - Vintage analysis (cohort retention curves)                │
│    - Strategic recommendations                                  │
│    ↓                                                             │
│ 3. Generate Visualizations (Plotly):                           │
│    - Pie chart: Portfolio composition by product               │
│    - Bar chart: Runoff by rate shock scenario                  │
│    - Waterfall chart: Funding gap analysis                     │
│    - Line chart: Cohort survival curves                        │
│    - Grouped bar: Product-level runoff projections             │
│    ↓                                                             │
│ 4. Create HTML Report (Jinja2 Template):                       │
│    - Executive Summary with KPIs                               │
│    - Portfolio Composition section                             │
│    - Rate Shock Scenario Analysis                              │
│    - Product-Level Drill-Down                                  │
│    - Vintage Analysis (if data available)                      │
│    - Strategic Recommendations                                  │
│    ↓                                                             │
│ 5. Multiple Output Formats:                                     │
│    - HTML: /dbfs/FileStore/reports/deposit_analytics_report_   │
│              [timestamp].html                                   │
│    - Delta: cfo_banking_demo.gold_analytics.                   │
│              deposit_analytics_reports                          │
│    - Delta: cfo_banking_demo.gold_analytics.                   │
│              rate_shock_scenarios                               │
│    ↓                                                             │
│ Schedule: Sunday 11:30pm (after batch inference completes)      │
│ Use Case: ALCO presentations, regulatory reporting, executive  │
│           briefings                                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│          FRONTEND DASHBOARD CONSUMPTION                         │
│     (frontend_app/components/treasury/*.tsx)                    │
├─────────────────────────────────────────────────────────────────┤
│ 1. Deposit Beta Dashboard:                                     │
│    - Queries: deposit_beta_predictions table                   │
│    - Displays: Balance by product, at-risk accounts            │
│    ↓                                                             │
│ 2. Vintage Analysis Dashboard:                                 │
│    - Queries: vintage_cohort_survival table                    │
│    - Displays: Cohort survival curves over 24 months          │
│    ↓                                                             │
│ 3. CCAR/DFAST Stress Test Dashboard:                           │
│    - Queries: stress_test_results, stress_test_summary        │
│    - Displays: CET1 projections, NII sensitivity              │
└─────────────────────────────────────────────────────────────────┘
```

**Key Architectural Decisions**:

1. **No Real-Time Model Serving**: Batch inference approach eliminates 24/7 endpoint costs. Weekly scoring is sufficient for deposit portfolio (vs real-time fraud detection).

2. **Unity Catalog Model Registry**: Centralized model governance with `@champion` and `@challenger` aliases. Zero-code deployment: update alias, batch job auto-picks up new model.

3. **Phase 1-3 Progressive Complexity**:
   - Phase 1: Static beta (operational ALM, normal market conditions)
   - Phase 2: Cohort analysis (liquidity risk, runoff forecasting)
   - Phase 3: Dynamic beta + stress testing (regulatory compliance, CCAR/DFAST)

4. **Report Generation**: HTML reports for human consumption (ALCO presentations), Delta tables for dashboard/API consumption.

**Production Schedule**:
- **Sunday 11:00pm**: Batch inference scoring (12 minutes)
- **Sunday 11:30pm**: Report generation (3-5 minutes)
- **Monday 9:00am**: Dashboards updated, reports available to ALCO members

### 7. Data Lineage Visibility

Unity Catalog provides complete data lineage that flows through to the UI:

```
┌─────────────────────────────────────────────────────────────────┐
│                   USER HOVERS OVER METRIC                       │
│            (frontend_app/components/MetricCard.tsx)             │
├─────────────────────────────────────────────────────────────────┤
│ Tooltip displays:                                               │
│ "Source: cfo_banking_demo.silver_finance.loan_portfolio"       │
│ "Last Updated: 2025-01-25 14:30:00"                            │
│ "Records: 97,200"                                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              UNITY CATALOG LINEAGE GRAPH                        │
│           (Databricks UI: Catalog Explorer)                     │
├─────────────────────────────────────────────────────────────────┤
│ Upstream tables:                                                │
│ bronze_core_banking.loan_origination_events                    │
│   ↓ (DLT pipeline transformation)                              │
│ silver_finance.loan_portfolio                                  │
│   ↓ (aggregation query)                                        │
│ gold_finance.profitability_metrics                             │
│   ↓ (consumed by)                                              │
│ React Dashboard Metric Card                                    │
│                                                                 │
│ Audit trail:                                                    │
│ - Who created the table                                        │
│ - When it was last modified                                    │
│ - Which notebooks/jobs wrote to it                             │
│ - Who has access permissions                                   │
└─────────────────────────────────────────────────────────────────┘
```

This complete data flow documentation covers all major application paths and demonstrates how Databricks Lakehouse, Unity Catalog, ML models, and modern web technologies integrate seamlessly.

</details>

---

## Technical Stack

### Data Platform
- **Delta Lake**: ACID transactions, time travel, schema evolution
- **Unity Catalog**: Data governance, lineage, access control, audit
- **Databricks SQL**: Serverless query engine with Photon acceleration
- **Delta Live Tables**: Declarative streaming/batch ETL pipelines

### AI/ML
- **Mosaic AI**: AutoML model training and optimization
- **MLflow**: Experiment tracking, model registry, model serving
- **XGBoost**: Gradient boosting algorithm for deposit beta prediction
- **SHAP**: Model explainability for feature importance

### Applications
- **Next.js 14**: React framework with App Router and static export
- **FastAPI**: Modern Python REST API framework
- **Claude Sonnet 4.5**: Large language model for AI assistant
- **Framer Motion**: Animation library for React
- **TailwindCSS**: Utility-first CSS framework

### Development Tools
- **Python 3.11**: Core programming language
- **Node.js 18+**: JavaScript runtime for React
- **Databricks SDK**: Python SDK for Databricks API
- **Git**: Version control

---

## Performance Benchmarks

### Data Processing
- Loan portfolio generation: 97,200 records in ~5 minutes
- Deposit portfolio generation: 402,000 records in ~8 minutes
- Real-time event processing: <1 second latency
- Regulatory report generation: 2 minutes (vs 2 weeks manual)

### Query Performance
- Portfolio aggregation (97K rows): <2 seconds
- Cross-domain NIM calculation: <3 seconds
- Real-time GL validation: <1 second
- Regulatory report query: <5 seconds

### ML Model
- Training time: ~3 minutes (XGBoost on 320K samples)
- Inference latency: <100ms per prediction
- Model R² score: 0.95 (excellent predictive power)

---

## Future Enhancements

### Phase 1: Production Deployment
- Connect to real core banking system (CDC via Fivetran/Airbyte)
- Deploy Delta Live Tables pipelines for continuous streaming
- Train deposit beta model on 2+ years historical data
- Configure Model Serving endpoints for production load
- Set up Lakehouse Monitoring for drift detection

### Phase 2: Expand Coverage
- FR Y-9C Consolidated Financial Statements
- CECL (Current Expected Credit Loss) reserve calculations
- Interest rate risk models (NII at Risk, EVE at Risk)
- Credit risk models (PD, LGD, EAD)
- Stress testing scenarios (CCAR/DFAST)

### Phase 3: Advanced Analytics
- Customer segment profitability analysis
- Branch/channel attribution
- Hedging strategy optimization
- What-if scenario engine
- Predictive liquidity forecasting

---

## Support and Resources

### Documentation
- Unity Catalog: https://docs.databricks.com/en/data-governance/unity-catalog/
- Delta Live Tables: https://docs.databricks.com/en/delta-live-tables/
- Mosaic AI: https://docs.databricks.com/en/machine-learning/automl/
- Databricks SQL: https://docs.databricks.com/en/sql/

### Training
- Databricks Academy: https://www.databricks.com/learn/training
- Partner enablement sessions

### Contact
- Technical questions: Databricks Solutions Architecture team
- Demo requests: Your Databricks account team

---

## License

This demo is for educational and demonstration purposes. Contact Databricks for production deployment licensing.

---

**Built with Databricks Lakehouse Platform**

*Last Updated: January 25, 2026*
