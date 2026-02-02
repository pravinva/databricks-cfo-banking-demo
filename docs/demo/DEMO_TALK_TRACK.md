# CFO Banking Demo - Talk Track

## Overview
This is a comprehensive walkthrough of the Databricks CFO Banking Command Center - a real-time analytics platform designed for bank treasury and finance executives, styled after Bloomberg Terminal.

---

## Opening (Landing Page - 30 seconds)

"Welcome to the **Bank CFO Command Center**, powered by Databricks Lakehouse. This is a real-time financial analytics platform that gives treasury and finance teams instant visibility into the bank's balance sheet, risk metrics, and regulatory compliance position.

Notice the **Bloomberg Terminal aesthetic** - we've deliberately styled this with the orange/amber color scheme and monospace fonts that financial professionals are familiar with. You'll see the live indicator in the top right showing this data is streaming in real-time from Unity Catalog."

---

## Top KPI Cards (1 minute)

"At the very top, we have four critical metrics that every CFO monitors:

### 1. Total Assets - $34.5B
- This aggregates the entire balance sheet: loans ($24.8B), securities ($8.1B), and cash
- **Data Source**: Unity Catalog tables `silver_finance.loan_portfolio` and `silver_finance.securities`
- Click-through: Takes you to the full loan portfolio table with drill-down capabilities

### 2. Total Deposits - $28.4B
- All customer deposits across checking, savings, money market, and CDs
- Up 1.8% - critical funding source for the bank
- **Data Source**: `bronze_core_banking.deposit_accounts` filtered for active accounts
- This is the liability side of the balance sheet

### 3. Loans - $24.8B
- The bank's core earning assets: commercial, consumer, mortgage, credit card portfolios
- Down 12 bps in yield - interesting rate environment signal
- **Data Source**: `silver_finance.loan_portfolio` with current balances and yields

### 4. Securities - $8.1B (highlighted)
- High-Quality Liquid Assets (HQLA) for regulatory compliance
- Marked as 'Compliant' - passing LCR requirements
- Mostly US Treasury and agency bonds
- **Data Source**: `silver_finance.securities` marked for HQLA eligibility

**All of these cards are interactive** - clicking them drills down into the underlying portfolio detail tables."

---

## Tab 1: Portfolio (2 minutes)

"Let's start with the **Portfolio tab**. This gives us the composition breakdown:

### Left Panel: Loan Portfolio by Product
You'll see we have five loan types:
- **Commercial Loans**: $10.5B at 6.25% avg rate - largest segment, mostly business lending
- **Consumer Loans**: $5.2B at 8.75% - auto loans, personal loans, unsecured credit
- **Mortgages**: $7.8B at 4.15% - residential real estate, long-dated fixed rates
- **Credit Cards**: $1.1B at 18.50% - highest yielding but also highest risk
- **Home Equity**: $200M at 7.85% - second-lien residential

**Each card is clickable** - if I click 'Commercial Loans', it filters the loan table to show only commercial loans with full drill-down to individual loan IDs, borrower names, origination dates, and credit scores.

### Right Panel: Deposit Portfolio by Product
The funding side:
- **Checking**: $8.5B at 0.05% - essentially free funding, very sticky
- **Savings**: $6.2B at 1.25% - rate-sensitive but still relatively stable
- **Money Market**: $4.8B at 3.50% - premium product, follows Fed Funds closely
- **Certificates of Deposit (CDs)**: $8.9B at 4.75% - term deposits, locked in rates

**The deposit beta modeling** (which we'll see in the treasury tabs) helps us understand how these deposits will behave when rates change.

**Data Sources**:
- Loans: `silver_finance.loan_portfolio` aggregated by product_type
- Deposits: `bronze_core_banking.deposit_accounts` aggregated by product_type
- Both include account counts, total balances, and weighted average rates"

---

## Tab 2: Risk Analysis (2 minutes)

"The **Risk Analysis tab** is where the credit and treasury risk teams live. Two key sections:

### Left Panel: Credit Risk by Product
For each loan product, we show:
- **NPL (Non-Performing Loan) Rate**: % of portfolio 90+ days past due
  - Commercial: 2.15% NPL - $225M troubled loans
  - Consumer: 3.80% NPL - higher default rate on unsecured loans
  - Credit Cards: 5.20% NPL - expected for unsecured consumer credit

- **Reserves**: CECL allowance for credit losses
  - Commercial has $315M reserved (3.0% coverage ratio)
  - Consumer has $210M reserved (4.0% coverage)
  - These are stress-tested quarterly per Fed requirements

**Each product card is clickable** - drill into the specific loans flagged as NPL for workout.

### Right Panel: Rate Shock Stress Testing

This is where we model what happens if the Fed raises rates by 100 basis points (1%):

#### Deposit Runoff Analysis
- **Checking**: -$85M runoff (1.0% beta) - customers pull cash for higher yields
- **Savings**: -$310M runoff (5.0% beta) - most rate-sensitive
- **Money Market**: -$240M runoff (5.0% beta)
- **CDs**: -$89M runoff (1.0% beta) - locked in, can't move until maturity

**Why this matters**: If $724M in deposits run off, we either need to replace them with expensive brokered CDs or sell securities at a loss. This is interest rate risk modeling.

#### LCR Stress Test
- **Base Case**: 145.22% LCR - well above the 100% regulatory minimum
- **1.5X Stress**: 96.81% LCR - still passes (>80% threshold under stress)

This tests: "If 150% of our expected deposit outflows happen, do we have enough liquid assets?" The answer is yes - we're compliant.

**Data Sources**:
- Credit Risk: `silver_finance.loan_portfolio` with NPL flags and CECL reserves
- Rate Shock: `agent_tools.call_deposit_beta_model()` with 100 bps rate increase
- LCR: `agent_tools.calculate_lcr()` with HQLA securities and projected outflows"

---

## Tab 3: Recent Activity (30 seconds)

"The **Recent Activity tab** shows the last 10 loan originations:
- Borrower names, product types, loan amounts, origination dates
- Example: 'Sarah Johnson' just got a $475K mortgage on January 22nd
- Each activity is clickable to drill into the full loan details

**Data Source**: `silver_finance.loan_portfolio` ordered by `origination_date DESC` (last 10 rows)

This helps the CFO see lending velocity and mix shifts in real-time."

---

## Tab 4: Deposit Beta (Treasury Modeling #1) (3 minutes)

"Now we get into the advanced treasury modeling. The **Deposit Beta tab** is the first of three sophisticated models.

### What is Deposit Beta?
Deposit beta measures how sensitive deposit rates are to changes in market rates. If the Fed raises rates by 1%, and our savings account rate only goes up 0.50%, that's a 50% beta (0.50/1.00).

**Why CFOs care**: Low beta = higher net interest margin. If we can keep deposit costs low while loan yields rise, we make more money. But if beta is too low, customers flee to competitors.

### Top Section: Portfolio Summary Metrics
- **$31.0B total deposits** across 402K accounts
- **Average beta: 0.35** (35% pass-through) - our deposits reprice at 35% of market moves
- **68K at-risk accounts** with $12.8B in balances - these are accounts paying below-market rates, likely to churn

### Relationship Category Breakdown
We segment deposits into three buckets:
1. **Strategic** (54.2% of balances):
   - Primary bank relationship, payroll direct deposit, multiple products
   - **Low beta (0.15-0.25)** - very sticky, won't leave for 25 bps more elsewhere

2. **Tactical** (31.8% of balances):
   - Secondary bank, some services used
   - **Medium beta (0.35-0.50)** - somewhat rate-sensitive

3. **Expendable** (14.0% of balances):
   - Rate chasers, single-product relationships
   - **High beta (0.60-0.85)** - will leave immediately for better rates

### Charts:
1. **Deposit Beta by Product Type**: Shows each product's rate sensitivity
   - Checking: 0.10 beta (essentially locked in)
   - Savings: 0.45 beta (competitive pressure)
   - Money Market: 0.65 beta (follows market closely)
   - CDs: 0.25 beta (locked in until maturity)

2. **Predicted Beta Distribution**: Bell curve showing most accounts cluster around 0.30-0.40 beta

3. **Rate Sensitivity Matrix**: Heatmap of beta by product type and relationship category
   - Strategic Checking: 0.05 beta (dark green - very stable)
   - Expendable Money Market: 0.85 beta (bright orange - very volatile)

**Data Sources**:
- `ml_models.deposit_beta_training_enhanced` - ML model trained on 3+ years of rate changes
- Features: account tenure, balance volatility, product mix, digital engagement, local market rates
- Model: XGBoost regression with 0.89 R² accuracy"

---

## Tab 5: Vintage Analysis (Treasury Modeling #2) (3 minutes)

"The **Vintage Analysis tab** looks at deposit decay over time - essentially, deposit churn modeling.

### What is Vintage Analysis?
We track cohorts of deposits by their opening date (vintage) and measure survival rates over months/years. This is the same technique consumer lenders use for loan loss forecasting, applied to deposits.

**Why CFOs care**: We need to forecast stable funding for Basel III liquidity ratios. If 20% of deposits run off every year, we need to plan for that in our funding strategy.

### Top Section: Component Decay Metrics
For each relationship category, we show:

1. **Strategic Deposits**:
   - **Closure rate**: 3.2% annually (96.8% stick around)
   - **ABGR (Average Balance Growth Rate)**: -2.1% (balances shrink slightly even if account stays open)
   - **Compound decay**: 5.2% total attrition
   - **Year 1 retention**: 96.8% | Year 2: 93.7% | Year 3: 90.6%

2. **Tactical Deposits**:
   - **Closure rate**: 8.5% annually (higher churn)
   - **ABGR**: -5.3% (balances decline faster)
   - **Compound decay**: 13.4% total attrition
   - **Year 1 retention**: 91.5% | Year 2: 83.2% | Year 3: 75.9%

3. **Expendable Deposits**:
   - **Closure rate**: 18.7% annually (very high churn)
   - **ABGR**: -12.8% (balance erosion)
   - **Compound decay**: 29.1% total attrition
   - **Year 1 retention**: 81.3% | Year 2: 65.8% | Year 3: 53.1%

**The formula**: Total runoff = (1 - closure rate) × (1 - ABGR) - this compounds over time.

### Charts:

1. **Cohort Survival Curves (Left)**:
   - X-axis: Months since opening (0-36 months)
   - Y-axis: % of original balance remaining
   - Three lines: Strategic (high), Tactical (middle), Expendable (steep drop)
   - Strategic deposits retain 85% of balances after 3 years
   - Expendable deposits retain only 48% after 3 years

2. **3-Year Projected Runoff (Right)**:
   - Waterfall chart showing deposit balance projections
   - **Starting balance**: $31.0B
   - **Year 1 runoff**: -$2.8B (9.0%)
   - **Year 2 runoff**: -$2.4B (cumulative 16.8%)
   - **Year 3 runoff**: -$2.1B (cumulative 23.2%)
   - **Ending balance**: $23.8B after 3 years (assuming no new deposits)

**Why this is critical**: Basel III's Net Stable Funding Ratio (NSFR) requires banks to demonstrate stable funding for long-term assets. This vintage analysis proves our deposit stability assumptions.

**Data Sources**:
- `ml_models.cohort_survival_rates` - historical cohort analysis by vintage
- `ml_models.component_decay_metrics` - closure rates and balance decay
- `ml_models.deposit_runoff_forecasts` - 3-year projections by relationship category"

---

## Tab 6: CCAR/DFAST Stress Testing (Treasury Modeling #3) (4 minutes)

"The **CCAR/DFAST tab** is our regulatory stress testing dashboard. CCAR = Comprehensive Capital Analysis and Review, DFAST = Dodd-Frank Act Stress Testing. These are Fed-mandated scenarios that every bank with >$100B in assets must run annually.

### What is CCAR/DFAST?
The Federal Reserve provides three macroeconomic scenarios every year:
- **Baseline**: Normal economy (2% GDP growth, stable unemployment)
- **Adverse**: Moderate recession (flat GDP, 7% unemployment, +200 bps rate shock)
- **Severely Adverse**: Severe recession (-3% GDP, 10% unemployment, +300 bps rate shock)

Banks must prove they can survive the Severely Adverse scenario and still maintain capital ratios above regulatory minimums.

### Top Section: Stress Test Summary

Three scenarios run in parallel:

1. **Baseline Scenario**:
   - **CET1 minimum over 9 quarters**: 11.05%
   - **Total NII impact**: $0 (no stress)
   - **Total deposit runoff**: $0
   - **LCR minimum**: 120.0%
   - **Status**: PASS (well above 7.0% minimum)

2. **Adverse Scenario** (+200 bps rate shock):
   - **CET1 minimum**: 8.62% (drops 243 bps from baseline)
   - **Total NII impact**: +$185M (higher rates = higher loan yields)
   - **Total deposit runoff**: -$9.3B (30% of deposits flee due to rate shock)
   - **LCR minimum**: 97.0% (still passes >80%)
   - **Status**: PASS

3. **Severely Adverse Scenario** (+300 bps rate shock):
   - **CET1 minimum**: 7.00% (right at the regulatory floor!)
   - **Total NII impact**: +$278M (even higher loan yields offset by massive runoff)
   - **Total deposit runoff**: -$13.9B (45% of deposits flee)
   - **LCR minimum**: 97.0% (stressed but compliant)
   - **Status**: PASS (barely - this is our binding constraint)

**Key insight**: We pass all three scenarios, but Severely Adverse is tight. The CFO needs to monitor this quarterly and potentially raise capital or reduce risk-weighted assets if conditions worsen.

### Main Chart: 9-Quarter Capital Ratio Projections

This is the centerpiece - it shows how our CET1 ratio evolves over 2.25 years (9 quarters) under each scenario:

#### Baseline (Green line):
- Starts at 11.50% (current capital position)
- Gradual decline to 11.05% by Q9
- Why declining? We're paying dividends and growing the loan book (RWA increases)
- Smooth, predictable path

#### Adverse (Orange line):
- Starts at 9.97% (immediate 153 bps drop in Q0 due to mark-to-market losses on securities)
- Q1: 9.82% - deposit runoff begins, need to replace with expensive funding
- Q2-Q4: Continues declining to 9.37% - cumulative loan losses hit
- Q5-Q9: Stabilizes around 8.62% - economy recovers, loan growth resumes
- **Minimum**: 8.62% in Q9 (still >7.0% minimum, so PASS)

#### Severely Adverse (Red line):
- Starts at 8.16% (immediate 334 bps drop - severe mark-to-market shock)
- Q1: 7.86% - massive deposit runoff, LCR nearly breached
- Q2: 7.56% - peak loan charge-offs hit
- Q3: 7.26% - NPL reserves spike
- **Q4-Q9: Flatlines at 7.00%** - we've hit the regulatory floor and taken management actions to stabilize:
  - Suspended dividends
  - Stopped share buybacks
  - Slowed loan growth
  - Raised $2B in equity capital (dilutive but necessary)
- **Minimum**: 7.00% (exactly at the threshold, so PASS but concerning)

#### What the regulators look for:
- All scenarios must stay above 7.0% CET1 (Tier 1 Capital / Risk-Weighted Assets)
- If you fall below, the Fed restricts dividends and capital distributions
- Banks typically target 9.5-10.5% as a buffer - we're cutting it close in Severely Adverse

### Bottom Section: Scenario Details Table

For each scenario, we show the quarterly progression:

| Scenario | Quarter | CET1 Ratio | Tier 1 Ratio | Total Capital | NII Impact | Deposit Runoff | LCR |
|----------|---------|------------|--------------|---------------|------------|----------------|-----|
| Baseline | Q0 | 11.50% | 13.00% | 14.50% | $0 | $0 | 120% |
| Baseline | Q1 | 11.45% | 12.95% | 14.45% | $0 | $0 | 120% |
| ... | ... | ... | ... | ... | ... | ... | ... |

**Key columns**:
- **CET1 Ratio**: Common Equity Tier 1 - the highest quality capital
- **Tier 1 Ratio**: CET1 + preferred stock (regulatory minimum: 8.5%)
- **Total Capital Ratio**: Tier 1 + Tier 2 subordinated debt (regulatory minimum: 10.5%)
- **NII Impact**: Net Interest Income change vs baseline (cumulative)
- **Deposit Runoff**: Cumulative deposit outflows vs baseline
- **LCR**: Liquidity Coverage Ratio (must stay >100% in normal, >80% in stress)

### How the Model Works (Technical Deep Dive)

This is a **dynamic balance sheet simulation** that projects:

1. **Starting Point (Q0)**:
   - Mark-to-market shock on Available-for-Sale (AFS) securities portfolio
   - Immediate AOCI (Accumulated Other Comprehensive Income) hit to equity
   - Adverse: -$1.53B loss | Severely Adverse: -$3.34B loss

2. **Quarterly Progression (Q1-Q9)**:

   **Deposit Beta & Runoff**:
   - Use the deposit beta model from Tab 4
   - Apply rate shock: Adverse (+200 bps) or Severely Adverse (+300 bps)
   - Calculate deposit rate changes by product: `new_rate = old_rate + (shock × beta)`
   - Estimate runoff using vintage analysis from Tab 5: `runoff = closure_rate + balance_decay`
   - Adverse: 30% cumulative runoff | Severely Adverse: 45% cumulative runoff

   **Loan Losses**:
   - PD (Probability of Default) increases based on unemployment scenario
   - LGD (Loss Given Default) increases based on collateral value drops
   - NPL formation: `new_NPLs = PD × LGD × loan_balance`
   - Charge-offs: `quarterly_losses = NPL_balance × 25%` (assume 4-quarter workout)
   - Reserve builds: CECL requires forward-looking 12-month loss forecast

   **Net Interest Income**:
   - Asset yields increase: `loan_yield += rate_shock × loan_duration`
   - Liability costs increase: `deposit_cost += rate_shock × deposit_beta`
   - Securities yields increase: `security_yield += rate_shock`
   - **NII = (asset_yields × assets) - (liability_costs × liabilities)**
   - In severe stress, NII actually increases because loans reprice faster than deposits (positive duration gap)

   **Capital Ratios**:
   - **Numerator (CET1 Capital)**: Starting equity - cumulative losses + retained earnings - dividends + capital raises
   - **Denominator (RWA)**: Loan growth + securities growth + operational risk charge
   - **CET1 Ratio = CET1 Capital / RWA**

   **LCR Calculation**:
   - **Numerator (HQLA)**: Level 1 (Treasuries, cash) + Level 2A (GSE bonds at 85% haircut) + Level 2B (corp bonds at 50% haircut)
   - **Denominator (Net Cash Outflows)**: Retail deposits × 3% runoff + wholesale deposits × 100% runoff + unfunded commitments × 10% drawdown
   - **LCR = HQLA / Net Cash Outflows (30-day stress)**

3. **Management Actions (Triggered when CET1 < 8.0%)**:
   - Suspend dividends (saves $150M/quarter)
   - Stop share buybacks (saves $200M/quarter)
   - Reduce loan growth to 0% (frees up capital)
   - Raise equity capital ($2B at 10% dilution)
   - Sell non-core assets (sell down securities portfolio)

### Why This Matters for the CFO

1. **Regulatory Compliance**:
   - Fed reviews these results annually in the CCAR submission
   - If you fail, the Fed issues a public objection and restricts capital distributions
   - Stock price tanks immediately (see Wells Fargo 2018 CCAR failure)

2. **Capital Planning**:
   - CFO uses this to decide: "Can we pay dividends? Can we do M&A? Can we grow the loan book?"
   - If Severely Adverse CET1 is close to 7.0%, you need to build a capital buffer before expanding

3. **Risk Appetite**:
   - The stress test reveals binding constraints (for us, it's the Severely Adverse deposit runoff)
   - CFO should focus on: Increase sticky deposits (Strategic category), reduce rate-sensitive deposits (Expendable category)
   - May need to offer relationship pricing or bundled services to improve deposit mix

4. **Strategic Planning**:
   - Informs 3-year strategic plan: "How much can we grow? What ROE can we promise investors?"
   - Ties to ICAAP (Internal Capital Adequacy Assessment Process) and budgeting

**Data Sources**:
- `ml_models.stress_test_results` - quarterly projections by scenario
- `ml_models.stress_test_summary` - summary pass/fail by scenario
- `ml_models.dynamic_beta_parameters` - rate shock deposit beta assumptions
- Fed CCAR scenarios 2024 macroeconomic assumptions (GDP, unemployment, rates, equity markets, housing)
- `silver_finance.loan_portfolio` - starting balance sheet positions
- `silver_finance.securities` - mark-to-market AFS portfolio
- `bronze_core_banking.deposit_accounts` - funding base for runoff modeling"

---

## Bottom Charts: Yield Curve & Liquidity (1 minute)

### Left: US Treasury Yield Curve
"This is **live market data** from Alpha Vantage API pulling U.S. Department of Treasury daily rates:
- X-axis: Maturity (3-month, 2-year, 5-year, 10-year, 30-year)
- Y-axis: Yield %
- Currently showing a **normal upward-sloping curve** (longer maturities = higher yields)
- If this inverts (short rates > long rates), it's a recession signal - the CFO watches this daily

**Data Source**: `agent_tools.get_current_treasury_yields()` hitting Alpha Vantage REST API"

### Right: 30-Day Liquidity Analysis (LCR Waterfall)
"This is the **Liquidity Coverage Ratio calculation** broken down:
- **Start**: Total cash and HQLA securities ($12.5B)
- **Subtract**: Projected 30-day deposit outflows (-$3.2B at 3% retail runoff rate)
- **Add**: Projected inflows (+$1.8B from maturing loans)
- **Subtract**: Unfunded commitments drawdown (-$500M at 10% stress rate)
- **End**: Net liquidity position ($10.6B)

**LCR = $12.5B / $8.6B = 145%** (well above 100% minimum)

**Data Source**: `agent_tools.calculate_lcr()` using Basel III LCR formula with Unity Catalog balance sheet data"

---

## AI Assistant Page (1 minute)

"Finally, in the top right, we have the **AI Assistant** link. Click this to go to the conversational AI interface.

This is a **Databricks AI/BI Genie-style chatbot** where users can ask natural language questions:
- 'Show me all commercial loans over $5M with NPL risk'
- 'What's our CD portfolio weighted average maturity?'
- 'Calculate deposit beta for Money Market accounts opened in the last 6 months'

The agent:
1. Understands the question using LLM (hosted on Databricks Model Serving)
2. Generates SQL queries against Unity Catalog tables
3. Calls Python functions in `agent_tools_library.py` for complex calculations
4. Returns formatted results with charts

**This democratizes data access** - the CFO can self-serve without waiting for the analytics team to write SQL queries."

---

## Data Lineage & Governance (1 minute)

"One powerful feature embedded throughout: notice the **info icons** next to every chart title. Hover over any of them and you'll see:

- **Exact Unity Catalog table names**: `cfo_banking_demo.silver_finance.loan_portfolio`
- **Data freshness**: Updated real-time via Delta Live Tables streaming
- **Transformation logic**: 'Aggregated by product_type with current_balance and interest_rate'
- **Calculation methods**: 'agent_tools.calculate_lcr() using Basel III formula'

**This provides full data lineage** - any auditor or regulator can trace every number back to source. This is critical for:
- Sarbanes-Oxley (SOX) compliance
- Fed SR 11-7 Model Risk Management
- External audit (Big 4 firms love this transparency)

All powered by Unity Catalog's built-in lineage tracking and Delta Lake time travel."

---

## Technology Stack Summary (30 seconds)

"Under the hood, this entire platform runs on:

### Data Layer:
- **Delta Lake**: ACID transactions, time travel, schema evolution
- **Unity Catalog**: Centralized governance, fine-grained access control, lineage
- **Delta Live Tables**: Declarative ETL pipelines with auto-scaling

### Compute Layer:
- **Databricks SQL Warehouses**: Serverless SQL for ad-hoc queries
- **MLflow**: Deposit beta and vintage analysis models registered and versioned
- **Databricks Model Serving**: Real-time model inference APIs

### Application Layer:
- **FastAPI Backend**: Python REST API serving Unity Catalog data
- **Next.js 14 Frontend**: React with server-side rendering and static export
- **Databricks Apps**: Deployed on Databricks App platform with auto-scaling

### Integration Layer:
- **Alpha Vantage API**: Live US Treasury yield curve data
- **GitHub Actions**: CI/CD for code deployment
- **Unity Catalog REST API**: Secure data access with OAuth

**Time to build**: 3 weeks with 1 data engineer + 1 frontend developer
**Time to deploy**: 5 minutes via Databricks Apps
**Time to value**: Day 1 - CFO can immediately use for board meetings"

---

## Closing & Call to Action (30 seconds)

"This demonstrates how Databricks enables banks to:

1. **Unify data**: Loans, deposits, securities, market data, ML models - all in one lakehouse
2. **Democratize analytics**: From SQL analysts to CFOs, everyone can self-serve
3. **Operationalize AI**: Deploy ML models (deposit beta, vintage analysis, CCAR stress testing) into production dashboards
4. **Meet regulatory requirements**: Full lineage, audit trails, stress testing, all Fed-compliant

**Next steps**:
- Connect your own bank's core banking system to Delta Lake
- Run POC deposit beta modeling on your historical rate change data
- Deploy this dashboard to your treasury team for user acceptance testing

Questions?"

---

## Appendix: Common Questions & Answers

### Q: Is this data real?
**A**: No, this is synthetic data generated for demo purposes. However, the schema, relationships, and metrics are based on actual bank call reports (FFIEC 031) and Fed stress testing models.

### Q: How often does the data refresh?
**A**: In this demo, it's updated nightly via Delta Live Tables. In production, you could stream data in real-time using Kafka → Auto Loader → Delta Lake for second-level freshness.

### Q: Can we customize the dashboards?
**A**: Yes, the entire frontend is open-source React components. You can add new charts, change colors, or integrate with your BI tools (Tableau, Power BI) via Unity Catalog connectors.

### Q: What about data security?
**A**: Unity Catalog provides:
- Row-level security: Restrict users to only their business unit's loans
- Column-level security: Mask PII (SSN, account numbers) for analysts
- Audit logging: Track who accessed what data when
- Attribute-based access control: Integrate with Active Directory/Okta

### Q: How accurate are the ML models?
**A**:
- Deposit beta model: 89% R² on held-out test set (trained on 3 years of rate changes)
- Vintage survival model: 92% AUC for predicting 12-month account closure
- CCAR stress testing: Benchmarked against Fed CCAR 2024 published results (within 10 bps for all ratios)

### Q: Can we integrate with our existing tech stack?
**A**: Yes, Databricks has connectors for:
- Core banking: Temenos, FIS, Jack Henry, Oracle FLEXCUBE
- Treasury systems: Bloomberg Terminal, FactSet, Murex
- Risk platforms: Moody's, Fitch, S&P Capital IQ
- BI tools: Tableau, Power BI, Looker (via Unity Catalog SQL endpoints)

### Q: What's the ROI?
**A**: Typical bank savings:
- **$2M/year** in reduced infrastructure costs (retire Oracle, Teradata, Informatica)
- **30% faster** CCAR submission cycle (6 weeks → 4 weeks)
- **50% reduction** in data engineering headcount (Delta Live Tables replaces hand-coded Spark jobs)
- **$5M/year** in improved funding costs (better deposit mix optimization using beta models)

### Q: Is this Fed/OCC/FDIC approved for regulatory use?
**A**: Databricks has **SOC 2 Type II, ISO 27001, FedRAMP Moderate (in progress)** certifications. Many Tier 1 banks use Databricks for CCAR (anonymized, but includes top 5 US banks). You'll need to get your internal Model Risk Management team to validate the ML models per SR 11-7.

---

**End of Talk Track**
