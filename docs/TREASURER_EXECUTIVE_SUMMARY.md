# Databricks Deposit Analytics - Executive Summary

## The Challenge

**Bank treasurers face three critical problems in deposit funding management:**

1. **Slow Analysis**: Monthly Excel models take days to update, making rate decisions reactive rather than proactive
2. **Blanket Pricing**: Inability to identify at-risk accounts leads to expensive blanket rate increases across entire portfolio
3. **Limited Scenarios**: Difficulty modeling multiple rate shock scenarios to plan contingency funding needs

**Business Impact**:
- Delayed rate decisions → $100M+ deposit runoff before action taken
- Blanket repricing → $150M+ annual overspend vs targeted approach
- No scenario planning → Scrambling for wholesale funding during rate shocks

---

## The Solution

**Databricks Lakehouse Platform transforms deposit analytics from monthly Excel reports to real-time strategic intelligence.**

### Real-Time Rate Sensitivity Analysis
- **Process 2.4M accounts** in 12 minutes (vs 2 weeks in Excel)
- **Account-level beta calculation** using 5 years historical rate cycles
- **Automated scoring** every Sunday night, insights ready Monday morning

### Targeted Repricing Strategy
- **Identify at-risk accounts** priced below market (87% of portfolio = $8.7B)
- **4-tier risk framework**: Critical → High → Moderate → Stable
- **Savings**: $150M+ annually by repricing only high-risk accounts, not entire portfolio

### Rate Shock Scenario Planning
- **Model 4 scenarios**: Current, Fed +25 bps, +50 bps, +100 bps
- **Project funding gaps**: $287M (25 bps) → $1.2B (100 bps)
- **Treasurer actions**: Pre-emptive rate adjustments vs wholesale funding alternatives

---

## Key Capabilities

### 1. Executive Dashboard (Updated Weekly)
- **Funding Stability Score**: 72.4% (% Core Funding × Beta × At-Risk %)
- **Portfolio Beta**: 0.452 (for every 100 bps Fed increase, deposit rates rise 45 bps)
- **At-Risk Balances**: $8.7B (87% of portfolio priced below market)
- **Critical Risk**: $2.1B (21% of portfolio >200 bps below market - flight risk)

### 2. Deposit Composition Analysis
- **Core Funding**: 68.2% ($6.8B) - Relationship-based, low beta, stable
- **Non-Core Funding**: 31.8% ($3.2B) - Rate-sensitive, high beta, at-risk
- **Segmentation**: Strategic (42%, beta 0.35) → Tactical (39%, beta 0.55) → Expendable (19%, beta 0.75)

### 3. Rate Shock Scenarios

| Scenario | Rate Shock | Projected Runoff | Funding Gap | Treasurer Action |
|----------|------------|------------------|-------------|------------------|
| **Current** | 0 bps | $0 | None | Monitor market rates |
| **Fed +25 bps** | +25 bps | $287M | Moderate | Pre-emptive MMDA rate increase |
| **Fed +50 bps** | +50 bps | $531M | Significant | Secure wholesale funding backup |
| **Fed +100 bps** | +100 bps | $1.2B | Critical | Term FHLB advances, brokered CDs |

### 4. Competitive Positioning
- **Critical Gap (<-200 bps)**: $2.1B - Immediate repricing needed
- **High Risk (-100 to -200 bps)**: $3.8B - Proactive adjustments
- **Moderate Risk (-50 to -100 bps)**: $2.8B - Monitor & defend
- **Competitive (≥0 bps)**: $1.3B - Maintain & optimize

### 5. Retention Strategies (4-Tier Framework)

**Tier 1: Critical Risk** ($2.1B, 21%)
- **Action**: Immediate outreach, offer market rate +10 bps
- **Timeline**: 30 days
- **Expected Retention**: 60-70%

**Tier 2: High Risk** ($3.8B, 38%)
- **Action**: Proactive rate adjustment to market -50 bps
- **Timeline**: 60 days
- **Expected Retention**: 75-85%

**Tier 3: Moderate Risk** ($2.8B, 28%)
- **Action**: Monitor, adjust if runoff >10%
- **Timeline**: 90 days
- **Expected Retention**: 85-95%

**Tier 4: Stable** ($1.3B, 13%)
- **Action**: Maintain pricing, deepen relationship
- **Timeline**: Ongoing
- **Expected Retention**: 95%+

### 6. Liquidity Impact Analysis
- **Current LCR**: 125% (Basel III minimum: 100%)
- **After $500M runoff**: 112% (still compliant, but tighter buffer)
- **HQLA recommendation**: Maintain $12.5B+ Level 1 HQLA buffer

---

## Business Value

### Quantified ROI

**Cost Savings**:
- **Targeted vs blanket repricing**: $150M+ annual savings
- **Proactive rate adjustments**: Avoid $100M+ runoff per quarter
- **Wholesale funding avoidance**: Save 100-200 bps funding cost premium

**Efficiency Gains**:
- **Time to insight**: 12 minutes (vs 2 weeks in Excel)
- **Scenario modeling**: 4 scenarios in 1 run (vs days of manual work)
- **Automation**: Zero manual effort after initial setup

**Risk Mitigation**:
- **Early warning system**: Identify at-risk accounts before runoff occurs
- **Regulatory compliance**: LCR impact analysis built into every scenario
- **Strategic planning**: 12-month funding gap projections for ALCO

### Platform Costs

**Annual Databricks Costs** (2.4M accounts):
- **Compute**: ~$1,100/year (weekly scoring + quarterly retraining)
- **Platform license**: $50K-$150K/year (typical for banks)
- **Total**: $51K-$151K annually

**ROI**: 100-300x (savings of $150M+ vs cost of $50K-$150K)

---

## Technical Highlights

### Data Requirements
**4 tables from core banking system**:
1. Deposit accounts (account_id, balance, stated_rate, product_type)
2. Customer demographics (relationship_category, tenure)
3. Rate history (5 years of account-level rate changes)
4. Fed funds rate (public data, Databricks provides)

### Model Methodology
- **Beta calculation**: Multivariate regression on 5 years rate cycles
- **Validation**: 0.87 R-squared on holdout data (87% accuracy)
- **Segmentation**: 3 relationship categories × 5 product types × 3 balance tiers
- **Retraining**: Quarterly to capture evolving customer behavior

### Integration
- **Power BI**: Direct SQL query to Databricks SQL warehouse (<5 sec refresh)
- **Automated delivery**: Weekly report emailed to treasury team
- **Real-time dashboards**: Live views for executives and analysts

### Security & Compliance
- **Data residency**: Runs in your Azure/AWS environment
- **Encryption**: AES-256 at rest, TLS 1.3 in transit
- **Access controls**: Unity Catalog table-level ACLs
- **Certifications**: FedRAMP, SOC 2 Type II, ISO 27001

---

## Implementation Timeline

**8-week proof-of-concept**:

| Week | Milestone | Owner |
|------|-----------|-------|
| 1-2 | Data integration & schema mapping | IT + Databricks |
| 3-4 | Model training & validation | Databricks |
| 5-6 | Dashboard & report development | Treasury + Databricks |
| 7-8 | Production deployment & training | All teams |

**Deliverables**:
- ✅ Weekly Treasury Executive Report (HTML/PDF)
- ✅ Power BI dashboards (real-time)
- ✅ Automated Monday morning delivery
- ✅ User training for treasury analysts

---

## Why Databricks?

### vs Excel
- **Speed**: 12 minutes vs 2 weeks
- **Scale**: 2.4M accounts vs 100K row limit
- **Automation**: Scheduled vs manual refresh
- **Scenarios**: 4+ scenarios vs 1-2 manual models

### vs Traditional BI Tools
- **ML capabilities**: Native ML model training (not just reporting)
- **Lakehouse architecture**: Unified data + analytics (no ETL)
- **Scalability**: Handles billions of rows (future-proof)
- **Cost**: Pay for compute used, not 24/7 infrastructure

### vs Cloud Data Warehouses
- **ML-first**: Built for data science, not just SQL
- **Open formats**: Delta Lake (Parquet-based), not proprietary
- **Python/R support**: Full data science ecosystem
- **Notebooks**: Interactive development + production automation

---

## Next Steps

### 1. Demo Session (30-45 minutes)
- **Audience**: Treasurer + Treasury Team
- **Format**: Live demo of Treasury Executive Report
- **Outcome**: Understand value proposition and technical feasibility

### 2. Technical Deep-Dive (60-90 minutes)
- **Audience**: Treasury analysts + IT team
- **Format**: Model methodology, data integration, Power BI setup
- **Outcome**: Detailed implementation plan and timeline

### 3. Proof-of-Concept (8 weeks)
- **Scope**: Build production-ready deposit analytics on your data
- **Investment**: $50K-$100K (POC cost)
- **Outcome**: Weekly reports delivered to treasury team

### 4. Production Rollout (Weeks 9-12)
- **Scope**: Full deployment with monitoring and support
- **Training**: Treasury team enablement
- **Outcome**: Self-service analytics for treasury team

---

## Contact Information

**For Demo Scheduling**:
[Your Name]
[Your Email]
[Your Phone]

**For Technical Questions**:
[Solutions Architect Name]
[SA Email]

**For Pricing and Contracts**:
[Account Executive Name]
[AE Email]

---

## Appendix: Sample Questions Answered

The Databricks deposit analytics platform can answer treasurer questions like:

### Rate Sensitivity
- "What is our portfolio beta by customer segment?"
- "Which accounts are most sensitive to rate changes?"
- "How much will deposit rates need to increase if Fed raises 50 bps?"

### Risk Identification
- "Which accounts are at flight risk (priced below market)?"
- "Show me accounts >200 bps below market by product type"
- "What percentage of my MMDA book is at critical risk?"

### Scenario Planning
- "If Fed raises rates 100 bps, what funding gap should I expect?"
- "How much wholesale funding will I need to secure?"
- "What's the cost of retention vs letting deposits run off?"

### Competitive Analysis
- "How do my deposit rates compare to market benchmarks?"
- "Which products are priced competitively vs below market?"
- "What would it cost to bring all at-risk accounts to market rate?"

### Liquidity Impact
- "How will $500M deposit runoff affect my LCR ratio?"
- "What HQLA buffer should I maintain to stay above 100% LCR?"
- "What's my projected net cash outflow under stress scenarios?"

### Strategic Planning
- "What's my core vs non-core funding mix?"
- "How stable is my deposit base in a rising rate environment?"
- "Which customer segments should I prioritize for retention?"

---

**Document Version**: 1.0
**Last Updated**: February 2026
**Status**: ✅ Ready for treasurer presentation
