# Treasurer Meeting Guide - Deposit Analytics Demo

## Meeting Overview

**Audience**: Bank Treasurer (CFO-level executive responsible for funding and liquidity)

**Duration**: 30-45 minutes

**Objective**: Demonstrate how Databricks enables data-driven deposit funding strategy with real-time rate sensitivity analysis

**Key Value Proposition**: Transform deposit analytics from monthly Excel reports to real-time, scenario-based decision support

---

## Pre-Meeting Preparation

### 1. Customize the Report (5 minutes)

**File**: `notebooks/Generate_Treasury_Executive_Report.py`

**Update these variables** (lines 40-43):
```python
BANK_NAME = "First National Bank"  # Use actual bank name
REPORT_TITLE = "Treasury Deposit Funding Analysis"
REPORT_SUBTITLE = "Rate Sensitivity and Runoff Projections"
```

### 2. Run the Report

**Execute in Databricks**:
1. Open notebook: `notebooks/Generate_Treasury_Executive_Report.py`
2. Click "Run All"
3. Output: `dbfs:/FileStore/reports/treasury_executive_report.html`
4. Download and have ready to share screen

**Expected Runtime**: 2-3 minutes (processing 2.4M accounts)

### 3. Prepare Talking Points

Focus on **treasurer pain points**:
- Manual Excel-based deposit analysis (time-consuming, error-prone)
- Difficulty modeling rate shock scenarios
- Lack of real-time competitive rate monitoring
- Inability to identify at-risk deposits proactively
- Limited visibility into customer-level beta sensitivity

---

## Demo Flow (30 minutes)

### Opening (2 minutes)

**Setup Context**:
> "Most banks still rely on monthly Excel models for deposit forecasting. By the time you identify at-risk deposits, balances have already fled. We'll show you how Databricks transforms this into real-time, actionable intelligence."

**Ask Discovery Question**:
> "When Fed raises rates, how long does it take your team to model the funding impact across your deposit base?"

*(Expected answer: Days to weeks - this is your opening)*

---

### Section 1: Executive Dashboard (5 minutes)

**Screen Share**: Treasury Executive Report - Section 1

**Key Metrics to Highlight**:

1. **Funding Stability Score**: `72.4%`
   - Formula: `(% Core Funding) × (1 - Portfolio Beta) × (1 - % At-Risk)`
   - Treasurer Translation: "72% of your deposit base is stable funding"

2. **Portfolio Beta**: `0.452`
   - Translation: "For every 100 bps Fed rate increase, deposit rates rise 45 bps"
   - Industry Benchmark: 0.40-0.50 (you're in the middle)

3. **At-Risk Deposits**: `$8.7B (87% of portfolio)`
   - Definition: Accounts priced below market competitive rate
   - Treasurer Action Required: Rate adjustments or accept runoff

4. **Critical Risk**: `$2.1B (21% of portfolio)`
   - Definition: Accounts 200+ bps below market (flight risk)
   - Immediate Action: Tier 1 retention strategy

**Talking Point**:
> "This dashboard updates every Sunday night after batch scoring 2.4M accounts. Monday morning, your treasury team sees exactly where rate adjustments are needed - not 2 weeks later."

**Treasurer Question to Anticipate**:
> "How accurate is the beta calculation?"

**Answer**:
> "We train the model on 5 years of historical rate cycles using regression analysis. The model achieved 0.87 R-squared on holdout data, meaning it explains 87% of deposit rate variance. We segment by relationship category (Strategic, Tactical, Expendable) because beta varies significantly - Strategic customers have 0.35 beta vs Expendable at 0.75."

---

### Section 2: Deposit Composition - Core vs Non-Core (5 minutes)

**Screen Share**: Treasury Executive Report - Section 2

**Key Insight**:
- **Core Funding**: 68.2% ($6.8B) - Relationship-based, low beta
- **Non-Core Funding**: 31.8% ($3.2B) - Rate-sensitive, high beta

**Regulatory Context**:
> "For LCR and NSFR calculations, examiners view non-core deposits as less stable. Your 68% core funding is strong, but the 32% non-core is vulnerable in rising rate scenarios."

**Treasurer Pain Point**:
> "Most banks can't disaggregate core vs non-core at account-level granularity. You're stuck with product-level assumptions. Databricks lets you calculate this dynamically based on actual customer behavior - beta sensitivity, tenure, balance volatility, transaction patterns."

**Segmentation Breakdown**:
- **Strategic (Low Beta)**: 42% of portfolio, 0.35 beta - *Core funding*
- **Tactical (Medium Beta)**: 39% of portfolio, 0.55 beta - *Conditional stability*
- **Expendable (High Beta)**: 19% of portfolio, 0.75 beta - *Rate chasers*

**Treasurer Actionable**:
> "Protect the 42% Strategic segment at all costs. Tier 2 rate adjustments on Tactical. Let Expendable run off if cost of retention exceeds wholesale funding alternatives."

---

### Section 3: Rate Shock Scenarios (8 minutes)

**Screen Share**: Treasury Executive Report - Section 3

**Scenario Table** (show live in report):

| Scenario | Rate Shock | Projected Runoff | Funding Gap | Treasurer Action |
|----------|------------|------------------|-------------|------------------|
| **Current Environment** | 0 bps | $0 | None | Monitor market rates |
| **Fed +25 bps** | +25 bps | $287M | Moderate | Pre-emptive MMDA rate increase |
| **Fed +50 bps** | +50 bps | $531M | Significant | Secure wholesale funding backup |
| **Fed +100 bps** | +100 bps | $1.2B | Critical | Term FHLB advances, brokered CDs |

**Calculation Method**:
```
Projected Runoff = Σ (Account Balance × Beta × Rate Shock × (1 - Stickiness Factor))
```

**Deep Dive: Fed +50 bps Scenario**:
- **Runoff**: $531M over 6 months
- **Segments Most Affected**:
  - Expendable: $298M (56% of total runoff)
  - Tactical: $201M (38%)
  - Strategic: $32M (6%)
- **Cost of Retention** (if you match market rates):
  - Deposit rate increase: 50 bps × 0.55 beta = 27.5 bps average increase
  - Annual cost: $10B × 0.00275 = $27.5M additional interest expense
- **Cost of Wholesale Funding Alternative**:
  - FHLB advance: Fed Funds + 10 bps = 5.60% (assuming 5.50% FF rate)
  - Cost for $531M: $531M × 0.056 = $29.7M annually
- **Decision**: Selective retention is cheaper than wholesale funding

**Treasurer Insight**:
> "This is where Excel models break down. You can't manually calculate runoff for 2.4M accounts across 15 product types in 3 segments under 4 scenarios. Databricks processes this in 12 minutes every Sunday, automatically."

**Question to Ask Treasurer**:
> "What's your current contingency funding plan if you face $500M runoff in 6 months?"

*(This opens discussion on FHLB capacity, brokered CD appetite, and strategic planning)*

---

### Section 4: Competitive Positioning (5 minutes)

**Screen Share**: Treasury Executive Report - Section 4

**Rate Gap Analysis**:
- **Critical Gap (<-200 bps)**: $2.1B - *Immediate repricing needed*
- **High Risk (-100 to -200 bps)**: $3.8B - *Proactive adjustments*
- **Moderate Risk (-50 to -100 bps)**: $2.8B - *Monitor & defend*
- **Competitive (≥0 bps)**: $1.3B - *Maintain & optimize*

**Product-Level Breakdown** (example):
| Product | Avg Balance | Avg Rate | Market Rate | Gap (bps) | At-Risk % |
|---------|-------------|----------|-------------|-----------|-----------|
| MMDA | $3.2B | 2.10% | 4.50% | -240 | 92% |
| Savings | $2.8B | 0.75% | 3.00% | -225 | 95% |
| NOW | $1.9B | 0.10% | 1.50% | -140 | 78% |
| DDA | $2.1B | 0.00% | 0.00% | 0 | 12% |

**Treasurer Talking Point**:
> "Your MMDA and Savings books are 240 and 225 bps below market. These are your biggest vulnerabilities. But here's the key insight: not all accounts care equally. We can identify which specific accounts are at flight risk based on their historical beta, so you can target rate increases rather than blanket repricing."

**Targeted Repricing Strategy**:
- **Don't reprice everyone**: That's expensive and unnecessary
- **Segment by risk**:
  - Tier 1 (Critical): Immediate rate adjustment to market -50 bps
  - Tier 2 (High Risk): Rate adjustment to market -100 bps
  - Tier 3 (Moderate): Monitor, adjust if balances decline >10%
  - Tier 4 (Stable): No action, already competitive

**Cost Savings Example**:
- **Blanket repricing** (all $10B): Cost = $10B × 240 bps = $240M annually
- **Targeted repricing** (only Tier 1 & 2): Cost = $5.9B × 150 bps average = $88.5M annually
- **Savings**: $151.5M per year

**Treasurer Value Prop**:
> "This is where Databricks pays for itself. You save $150M+ annually by only repricing accounts that matter, not the entire portfolio."

---

### Section 5: Retention Strategies (3 minutes)

**Screen Share**: Treasury Executive Report - Section 5

**4-Tier Framework**:

**Tier 1: Critical Risk** ($2.1B, 21% of portfolio)
- **Criteria**: Beta > 0.70, rate gap < -200 bps, balance > $1M
- **Action**: Immediate outreach, offer market rate +10 bps, relationship manager involvement
- **Timeline**: 30 days
- **Expected Retention**: 60-70%

**Tier 2: High Risk** ($3.8B, 38% of portfolio)
- **Criteria**: Beta 0.50-0.70, rate gap -100 to -200 bps
- **Action**: Proactive rate adjustment to market -50 bps
- **Timeline**: 60 days
- **Expected Retention**: 75-85%

**Tier 3: Moderate Risk** ($2.8B, 28% of portfolio)
- **Criteria**: Beta 0.30-0.50, rate gap -50 to -100 bps
- **Action**: Monitor for balance decline, adjust if runoff >10%
- **Timeline**: 90 days
- **Expected Retention**: 85-95%

**Tier 4: Stable** ($1.3B, 13% of portfolio)
- **Criteria**: Beta < 0.30, rate gap ≥0 bps
- **Action**: Maintain current pricing, focus on deepening relationship
- **Timeline**: Ongoing
- **Expected Retention**: 95%+

**Treasurer Talking Point**:
> "This tiered approach is data-driven, not guesswork. Every Monday, your treasury team gets a refreshed list of accounts in each tier, with specific actions. Your relationship managers get alerts for Tier 1 accounts requiring outreach."

---

### Section 6: Liquidity Impact (2 minutes)

**Screen Share**: Treasury Executive Report - Section 6

**LCR Impact Analysis**:
- **Current LCR**: 125% (Basel III minimum: 100%)
- **After $500M runoff (Fed +50 bps scenario)**: 112%
- **Buffer**: 12% above minimum (adequate but tighter)

**HQLA Implications**:
- **Current HQLA**: $12.5B
- **Projected Net Outflows (30-day stress)**: $10.0B
- **After runoff**: Net outflows increase to $10.5B
- **HQLA needed**: $10.5B ÷ 1.00 = $10.5B minimum
- **Recommendation**: Maintain Level 1 HQLA buffer at $12.5B+

**Treasurer Talking Point**:
> "Deposit runoff doesn't just impact your funding gap - it directly affects your LCR ratio. This model projects both funding needs and regulatory compliance impact, so you're never surprised by examiner questions."

---

### Closing (2 minutes)

**Summary**:
> "In 30 minutes, we've shown you how Databricks transforms deposit analytics from monthly Excel reports to real-time strategic intelligence. Your treasury team gets actionable insights every Monday morning, with specific retention strategies and funding gap projections."

**3 Key Takeaways**:
1. **Real-time rate sensitivity**: 2.4M accounts scored in 12 minutes, not 2 weeks
2. **Targeted repricing**: Save $150M+ annually by only adjusting at-risk accounts
3. **Regulatory compliance**: LCR impact analysis built into every scenario

**Call to Action**:
> "We'd like to schedule a follow-up technical session with your treasury team to walk through the model methodology and discuss integration with your core banking system. We can have a proof-of-concept running on your data within 4 weeks."

**Question for Treasurer**:
> "What would it mean to your funding strategy if you could see this report every Monday morning, updated with Friday's deposit balances?"

---

## Anticipated Questions & Answers

### Q1: "How accurate are these beta estimates?"

**Answer**:
"We train the model on 5 years of historical rate cycles using multivariate regression. The model achieved 0.87 R-squared on holdout data. We validate by comparing predicted vs actual deposit rate changes each quarter. For the past 8 quarters, our model has been within ±5 bps of actual portfolio beta."

**Follow-up**: "We recommend retraining the model quarterly to capture evolving customer behavior."

---

### Q2: "What data do you need from our core banking system?"

**Answer**:
"We need 4 tables:
1. **Deposit accounts**: account_id, product_type, current_balance, stated_rate, open_date
2. **Customer demographics**: account_id, relationship_category, tenure, total_relationship_balances
3. **Rate history**: account_id, effective_date, stated_rate (last 5 years)
4. **Fed funds rate**: date, rate (public data, we can provide)

This data is typically available from core systems like Jack Henry, FIS, or Fiserv. We've integrated with all major platforms."

---

### Q3: "How much does this cost?"

**Answer**:
"Databricks pricing is based on compute usage. For your 2.4M accounts:
- **Weekly batch scoring**: 12 minutes runtime = ~$15/week = $780/year
- **Training/retraining**: Quarterly, 30 minutes = ~$50/quarter = $200/year
- **Storage**: Minimal, ~$100/year
- **Total**: ~$1,100/year in compute costs

The Databricks platform license is typically $50K-$150K annually depending on features and support level.

**ROI**: If targeted repricing saves even $1M annually (vs blanket repricing), ROI is 10-150x."

---

### Q4: "Can this integrate with our Power BI dashboards?"

**Answer**:
"Yes, two integration paths:
1. **Direct SQL query**: Power BI connects to Databricks SQL warehouse, queries Delta tables in real-time
2. **Scheduled export**: We write results to Azure Blob/S3, Power BI refreshes on schedule

Most banks use option 1 for real-time dashboards. Refresh time is <5 seconds for aggregated views."

---

### Q5: "What if we want to add custom scenarios?"

**Answer**:
"The model is fully customizable. You define:
- **Rate shock magnitude**: +25, +50, +100 bps (or custom)
- **Timeline**: 3-month, 6-month, 12-month projections
- **Geographic scenarios**: Regional rate variations (e.g., California vs Texas)
- **Product-specific scenarios**: MMDA +50 bps, Savings +25 bps

Scenarios are defined in Python configuration (5 minutes to add a new scenario). No code changes needed for routine scenario planning."

---

### Q6: "How do you handle data privacy and security?"

**Answer**:
"Databricks runs in your Azure/AWS environment, never in our cloud. Your data never leaves your tenant. We implement:
- **Unity Catalog**: Table-level access controls (ACLs)
- **Encryption**: At rest (AES-256) and in transit (TLS 1.3)
- **Audit logging**: All data access tracked and logged
- **PII masking**: Account numbers and customer names can be tokenized

Many banks run Databricks in production for CCAR-style regulatory stress testing (DFAST is legacy terminology) and AML use cases. It's FedRAMP, SOC 2 Type II, and ISO 27001 certified."

---

### Q7: "What's the implementation timeline?"

**Answer**:
"Typical timeline for deposit beta modeling:

**Week 1-2**: Data integration and schema mapping
- Work with your IT team to extract 4 core tables
- Validate data quality (completeness, accuracy)

**Week 3-4**: Model training and validation
- Train beta model on your historical data
- Validate against known rate cycles
- Calibrate thresholds (at-risk criteria, risk tiers)

**Week 5-6**: Dashboard and report development
- Build Power BI dashboards
- Configure automated report delivery
- User acceptance testing with treasury team

**Week 7-8**: Production deployment and training
- Deploy to production environment
- Train treasury analysts on how to interpret results
- Establish weekly monitoring cadence

**Total**: 8 weeks from kickoff to production."

---

## Technical Deep-Dive (If Requested)

### Model Architecture

**Step 1: Feature Engineering**
```python
# Features used to predict account-level beta
features = [
    'relationship_category',  # Strategic/Tactical/Expendable
    'product_type',           # MMDA, Savings, NOW, DDA
    'balance_tier',           # <$100K, $100K-$1M, $1M+
    'tenure_years',           # Account age
    'rate_gap',               # Current rate vs market
    'balance_volatility',     # Std dev of monthly balances
    'transaction_frequency'   # Transactions per month
]
```

**Step 2: Beta Calculation**
```python
# Multivariate regression
beta = OLS(y=deposit_rate_change, X=fed_funds_rate_change + features).fit()

# Account-level beta
account_beta = model.predict(account_features)
```

**Step 3: Runoff Projection**
```python
# For each scenario (e.g., Fed +50 bps)
runoff = account_balance × account_beta × rate_shock × (1 - stickiness_factor)

# Stickiness factor based on relationship depth
stickiness = f(total_relationship_balances, tenure, product_count)
```

---

## Post-Meeting Follow-Up

### 1. Send Thank You Email (Same Day)

**Subject**: Databricks Deposit Analytics - Follow-Up Materials

**Body**:
> Thank you for taking the time to review the Databricks deposit analytics demo today. As discussed, I'm attaching:
>
> 1. Sample Treasury Executive Report (HTML)
> 2. Technical architecture overview (PDF)
> 3. Data requirements checklist
> 4. Pricing estimate for your 2.4M account portfolio
>
> Next steps:
> - Schedule technical deep-dive with your treasury team (proposed: [date])
> - Discuss data integration approach with your IT team
> - Provide proof-of-concept timeline and resource requirements
>
> Please let me know if you have any questions or would like to schedule the technical session.

### 2. Prepare for Technical Deep-Dive (Week 2)

**Audience**: Treasury analysts and IT team

**Focus**:
- Data extraction from core banking system
- Model training methodology
- Power BI integration approach
- Security and compliance requirements

**Duration**: 60-90 minutes

---

## Success Metrics

**Meeting Successful If**:
- Treasurer understands value proposition (real-time insights vs monthly Excel)
- Technical deep-dive scheduled with treasury team
- Data requirements shared with IT team for feasibility assessment
- POC timeline discussed (4-8 weeks)

**Red Flags**:
- "We already have this" (unlikely - most banks don't have account-level beta modeling)
- "Too complex for our team" (position as no-code solution for business users)
- "We can't share data" (discuss data privacy and on-premises deployment)

---

## Additional Resources

**Demo Files**:
- `../../notebooks/Generate_Treasury_Executive_Report.py` - Main report generator
- `docs/guides/STRESS_TEST_TERMINOLOGY.md` - CCAR regulatory context

**Reference Materials**:
- CCAR Stress Testing Framework (Federal Reserve)
- Basel III LCR requirements
- Deposit beta academic research (Chen Component Decay Model)

---

**Last Updated**: February 2026
**Status**: ✅ Ready for treasurer meeting
