# Treasury Deposit Modeling Demo Script
## 15-Minute Executive Demonstration

**Audience:** Treasury Modeling Team, ALM Committee, CFO
**Duration:** 15 minutes + 5 minutes Q&A
**Objective:** Show how Databricks accelerates deposit beta modeling from 3 months to 2 weeks

---

## Point of View (POV)

### The Treasury Modeling Challenge

**Traditional Approach (3-4 months):**
- Week 1-2: Extract data from 5+ siloed systems (core banking, market data, CRM)
- Week 3-4: Manual data cleaning and reconciliation in Excel
- Week 5-8: Build beta models in SAS/R with limited features
- Week 9-10: Run vintage analysis separately in Excel
- Week 11-12: Stress testing in yet another tool
- Week 13+: Consolidate results, build PowerPoint for ALCO

**Problems:**
- ❌ Data silos prevent holistic view
- ❌ Excel breaks at 402K accounts
- ❌ No integration between beta model, vintage analysis, and stress testing
- ❌ Static models miss regime changes (low → high rates)
- ❌ Quarterly recalibration takes weeks

### The Databricks Advantage

**Modern Approach (2 weeks):**
- Day 1-2: Unified lakehouse ingests all data automatically
- Day 3-5: Static deposit beta model with canonical feature set (19 features)
- Day 6-8: Vintage analysis with component decay (integrated)
- Day 9-10: Dynamic beta + stress testing (CCAR/DFAST ready)
- Day 11-12: AI/BI dashboards auto-generate insights
- Day 13-14: Present to ALCO with live, drill-down dashboards

**Benefits:**
- ✅ **8x faster:** 2 weeks vs 3 months
- ✅ **10-15% more accurate:** MAPE improvement through advanced features
- ✅ **Integrated:** One platform for beta, vintage, stress testing
- ✅ **Real-time:** Dashboards update automatically
- ✅ **Regulatory ready:** CCAR/DFAST templates built-in

---

## Demo Flow (15 Minutes)

### **PART 1: The Problem (2 minutes)**
**Slide 1: Current State Pain Points**

**Talk Track:**
> "Let me show you what we're hearing from treasury teams across the industry. You're spending 3-4 months building deposit beta models for ALCO, and by the time you present, the Fed has moved rates twice. Sound familiar?"

**Show:**
- Timeline graphic: Traditional 3-4 month process
- Pain points: Data silos, Excel limitations, disconnected tools

**Key Message:**
> "The problem isn't your team—it's the tools. Excel wasn't built for 402,000 accounts. SAS wasn't built for real-time integration. And PowerPoint wasn't built for interactive drill-downs."

---

### **PART 2: The Databricks Approach (3 minutes)**
**Slide 2: Unified Lakehouse Architecture**

**Talk Track:**
> "Here's how Databricks changes the game. Everything lives in one lakehouse—your core banking data, market rates, customer relationships, transaction history. No more ETL hell."

**Show:**
- Architecture diagram: Bronze (raw) → Silver (cleansed) → Gold (analytics)
- Unity Catalog with 3 schemas: `bronze_core_banking`, `silver_finance`, `ml_models`

**Live Demo (30 seconds):**
```python
# Show one line of code
df = spark.table("cfo_banking_demo.bronze_core_banking.deposit_accounts")
print(f"402,000 accounts loaded in {time_taken} seconds")
```

**Key Message:**
> "What used to take 2 weeks of data wrangling now takes 2 seconds. That's the lakehouse advantage."

---

### **PART 3: Enhanced Beta Model (3 minutes)**
**Slide 3: Approach 1 - Static deposit beta model**

**Talk Track:**
> "Your current model probably has 15 features—product type, balance, maybe account age. We've added 25 research-backed features from Moody's, Chen (2025), and Abrigo frameworks."

**Show Phase 1 Notebook Results:**
```
Baseline Model MAPE: 12.3%
Enhanced Model MAPE: 7.2%
Improvement: +41.5% accuracy
```

**Key Features Added:**
1. **Moody's Relationship Framework:**
   - Strategic customers: β = 0.25 (sticky, low sensitivity)
   - Expendable customers: β = 0.78 (hot money, high sensitivity)

2. **Market Regime Classification:**
   - Low rates (<1%): β increases 15-20%
   - High rates (>3%): β plateaus (rate fatigue)

3. **Competitive Pressure:**
   - Below-market pricing: +$8.5B at-risk deposits flagged

**Live Demo (1 minute):**
- Show Dashboard 1: Executive Overview
- Highlight "At-Risk Deposits" card: $8.5B
- Drill into Top 10 At-Risk Accounts table

**Key Message:**
> "You're not just predicting beta—you're predicting which $8.5 billion is about to walk out the door."

---

### **PART 4: Vintage Analysis & Runoff Forecasting (3 minutes)**
**Slide 4: Phase 2 - Component Decay Model**

**Talk Track:**
> "Traditional vintage analysis tracks cohort survival. We go further with Chen's component decay model: D(t+1) = D(t) × (1-λ) × (1+g). Lambda is closure rate, g is balance growth rate. This matters because..."

**Show Phase 2 Results:**
```
3-YEAR DEPOSIT RUNOFF OUTLOOK
================================
Strategic Deposits:
  $1.82B → $0.97B (-46.8%)
  Closure Rate (λ): 0.85% annually
  ABGR (g): +3.0% annually

Expendable Deposits:
  $10.41B → $2.94B (-71.7%)
  Closure Rate (λ): 6.68% annually
  ABGR (g): -5.0% annually
```

**Live Demo (1 minute):**
- Show Dashboard 2: ALM & Treasury Operations
- Component Decay Metrics cards (λ, g, compound factor)
- Cohort Survival Curves chart (Kaplan-Meier)

**Key Message:**
> "You're losing 71% of your Expendable deposits over 3 years. That's not a bug—that's the model telling you where to focus retention efforts."

---

### **PART 5: Dynamic Beta & Stress Testing (2 minutes)**
**Slide 5: Phase 3 - Regulatory Stress Testing**

**Talk Track:**
> "Static betas miss regime changes. When the Fed raised rates 500bps in 18 months, did your beta stay constant? Ours doesn't. We use Chen's sigmoid function to show beta evolves with rate environment."

**Show Phase 3 Dynamic Beta Function:**
```
DYNAMIC BETA PREDICTIONS BY RATE SCENARIO
==========================================
Rate     Strategic   Tactical   Expendable
0.0%       0.0582      0.1243      0.2156
3.0%       0.2845      0.4521      0.7234
6.0%       0.5523      0.7012      0.8856

(Beta increases non-linearly as rates rise)
```

**Show CCAR/DFAST Results:**
```
SEVERELY ADVERSE SCENARIO (+200bps shock)
========================================
CET1 Minimum:        8.2% (above 7% threshold ✓)
NII Impact:          -$285M over 2 years
Deposit Runoff:      -$8.5B (-28.2%)
LCR @ Stress:        105% (compliant ✓)
```

**Live Demo (30 seconds):**
- Show Dashboard 5: CCAR/DFAST Regulatory
- Capital ratio projections chart (9 quarters)
- Stress test pass/fail summary (traffic lights)

**Key Message:**
> "You're not just running a model—you're generating your CCAR submission. This is board-ready, regulator-ready, ALCO-ready."

---

### **PART 6: Real-Time Dashboards (2 minutes)**
**Slide 6: From PowerPoint to Interactive Insights**

**Talk Track:**
> "Remember that PowerPoint you spent 2 weeks building? It's obsolete the moment you present it. Here's the alternative."

**Live Demo (90 seconds - rapid fire):**

1. **Dashboard 1 (Executive Overview):**
   - "CFO sees $30.1B portfolio, 0.42 beta, $8.5B at-risk"
   - Click on "At-Risk Deposits" → drill into accounts

2. **Dashboard 2 (ALM Operations):**
   - "Treasury sees component decay by segment"
   - Cohort survival curves update automatically

3. **Dashboard 4 (Gap Analysis):**
   - "ALCO sees duration gap: 1.4 years"
   - "EVE @ +100bps: -$450M"

4. **Dashboard 7 (Treasury Command Center):**
   - "Real-time: Net deposit outflow today: -$125M"
   - "Liquidity buffer: $8.5B"
   - "Brokered deposits maturing in 30 days: $850M"

**Key Message:**
> "These dashboards update every hour. Your ALCO deck is never out of date. Your CFO can drill into any number. Your examiners can see live compliance."

---

## Closing (2 minutes)

### The Business Case

**Time to Value:**
| Metric | Traditional | Databricks | Improvement |
|--------|-------------|------------|-------------|
| Model Build Time | 12 weeks | 2 weeks | **6x faster** |
| Beta Model MAPE | 12.3% | 7.2% | **+41% accuracy** |
| Runoff Forecast MAE | 6.2% | 4.8% | **+23% accuracy** |
| Dashboard Build | 2 weeks manual | 6 hours automated | **14x faster** |
| Quarterly Recalibration | 4 weeks | 3 days | **9x faster** |

**ROI Calculation (Conservative):**
- Treasury Modeler salary: $150K/year
- Time saved per quarter: 8 weeks → 2 weeks = **6 weeks saved**
- Annual savings: (6 weeks × 4 quarters) / 52 weeks × $150K = **$69K/year per modeler**
- Improved accuracy prevents deposit runoff: **1% retention = $300M × 1% × 2.5% cost of funds = $75K/year**
- **Total ROI: $144K/year** (payback in ~8 months)

### Call to Action

**Talk Track:**
> "Here's what I'm proposing:"
>
> **Week 1-2:** Pilot with your Q1 2026 deposit beta model
> - We'll run Phase 1-3 notebooks on your actual data
> - Build 3 core dashboards (Executive, ALM, Treasury)
> - Present results to ALCO alongside your existing model
>
> **Week 3-4:** Expand to full production
> - Add 4 advanced dashboards (Gap Analysis, CCAR, Model Governance, Command Center)
> - Integrate with your existing treasury systems
> - Train your team on quarterly recalibration workflow
>
> **Month 2+:** Scale across ALM use cases
> - Loan portfolio modeling
> - Liquidity stress testing
> - Capital planning automation

---

## Demo Environment Checklist

### Before Demo:

**Data Preparation:**
- ✅ Run Phase 1 notebook (deposit_beta_training_enhanced table exists)
- ✅ Run Phase 2 notebook (component_decay_metrics, cohort_survival_rates exist)
- ✅ Run Phase 3 notebook (dynamic_beta_parameters exist)
- ✅ Verify historical data: 12.7M rows in deposit_accounts_historical

**Dashboards Built:**
- ✅ Dashboard 1: Executive Overview (for KPI drill-down)
- ✅ Dashboard 2: ALM Operations (for component decay)
- ✅ Dashboard 7: Treasury Command Center (for real-time wow factor)

**Backup Slides:**
- Architecture diagram (Bronze → Silver → Gold)
- Feature importance rankings (top 10)
- Customer testimonials (if available)
- Competitive comparison (Databricks vs SAS/Excel)

### During Demo:

**Timing Control:**
- Part 1 (Problem): 2 min ⏱️
- Part 2 (Approach): 3 min ⏱️
- Part 3 (Phase 1): 3 min ⏱️
- Part 4 (Phase 2): 3 min ⏱️
- Part 5 (Phase 3): 2 min ⏱️
- Part 6 (Dashboards): 2 min ⏱️
- **Total: 15 minutes**

**Key Moments:**
1. **"Wow" moment 1:** Phase 1 MAPE improvement (7.2% vs 12.3%)
2. **"Wow" moment 2:** Phase 2 runoff forecast (-71.7% for Expendable)
3. **"Wow" moment 3:** Dashboard 7 real-time treasury alerts

### After Demo:

**Follow-Up Materials:**
- Email PDF: "Databricks for Treasury Modeling - Executive Summary"
- Share GitHub repo: https://github.com/pravinva/databricks-cfo-banking-demo
- Schedule follow-up: "Pilot planning session"

---

## Q&A Preparation

### Expected Questions:

**Q1: "How does this integrate with our existing systems?"**
**A:** "Databricks connects to any system via REST APIs, JDBC, or file-based ingestion. Your core banking system, market data feeds, CRM—everything flows into the lakehouse. We've done this with Fiserv, FIS, Jack Henry, and Temenos."

**Q2: "What about data governance and security?"**
**A:** "Unity Catalog provides row-level, column-level, and attribute-based access control. Your PII stays encrypted. Your auditors can see who accessed what data when. We're SOC 2 Type II certified."

**Q3: "Can we still use our existing models while we transition?"**
**A:** "Absolutely. We recommend a parallel run for 1-2 quarters. You present both models to ALCO, compare results, build confidence. Many customers keep legacy models for regulatory continuity."

**Q4: "What if our data science team doesn't know Python/Spark?"**
**A:** "We provide 2 weeks of training, pre-built notebooks, and AI assistants that write code for you. Your treasury analysts can use SQL and point-click dashboards. No PhD required."

**Q5: "How much does this cost?"**
**A:** "Typical treasury team runs on a Medium warehouse (16 DBUs/hour) for ~100 hours/quarter. That's $40/hour × 100 hours = $4,000/quarter. Compare that to $37,500/quarter in modeler time savings. 9:1 ROI."

**Q6: "What about model validation and documentation?"**
**A:** "Dashboard 6 (Model Governance) tracks MAPE, PSI, recalibration triggers, and validation metrics automatically. MLflow logs every model version, hyperparameter, and training dataset. Your model validators will love it."

---

## Key Talking Points (Cheat Sheet)

### When They Say... You Say...

**"We already have SAS models working."**
> "SAS is great for static models. But when rates moved 500bps in 18 months, did your beta models keep up? Dynamic betas + real-time dashboards are the difference."

**"Our data is too messy."**
> "That's exactly why lakehouse architecture matters. Bronze layer takes data as-is, Silver cleanses it with Delta Lake ACID transactions, Gold serves analytics. Your data gets better over time."

**"We don't have data scientists."**
> "You don't need them. We're treasury modelers who learned to use better tools. If you can write SQL, you can use Databricks. Plus, AI assistants write the complex code for you."

**"Excel is free, Databricks costs money."**
> "Excel is 'free' like a free puppy is free. You're paying treasury modelers $150K/year to wrangle data for 8 weeks per quarter. That's $75K/year in labor costs. Databricks costs $16K/year."

**"What if we want to customize?"**
> "Every notebook is open source Python. Every SQL query is yours to modify. No vendor lock-in. Export to CSV, Parquet, Delta, or push to your data warehouse. You own the code."

---

## Success Metrics (What "Good" Looks Like)

### After 30 Days:
- ✅ Pilot model built on real data
- ✅ 3 core dashboards deployed
- ✅ ALCO presentation delivered
- ✅ Accuracy improvement quantified

### After 60 Days:
- ✅ Production models in quarterly cycle
- ✅ 7 dashboards fully operational
- ✅ Integration with treasury systems
- ✅ Team trained on recalibration workflow

### After 90 Days:
- ✅ Time-to-ALCO reduced from 12 weeks → 2 weeks
- ✅ Model accuracy improved by 10-15%
- ✅ CFO/Treasurer using dashboards weekly
- ✅ Regulatory examiners impressed with transparency

---

## Appendix: Demo Backup Materials

### If Demo Fails:

**Have ready:**
1. **Screenshots:** Pre-captured images of all dashboards
2. **Video recording:** 3-minute walkthrough of live system
3. **PDF exports:** Static versions of Phase 1/2/3 results

### If They Want Deeper Dive:

**Technical Deep Dive (30 minutes):**
1. Show Unity Catalog schema structure
2. Walk through Phase 1 notebook cell-by-cell
3. Explain XGBoost hyperparameter tuning
4. Demo MLflow experiment tracking
5. Show AI/BI Dashboard Agent creating visuals

### If They Want ROI Calculator:

**Spreadsheet Template:**
```
Current State:
- Modeler salary: $________
- Weeks per model: ________
- Models per year: ________
- Total annual cost: $________

Future State:
- Databricks cost: $16,000/year
- Time saved: ________ weeks/quarter
- Accuracy improvement: ________%
- Deposit runoff prevented: $________
- ROI: $________ (payback: ________ months)
```

---

## Post-Demo Email Template

**Subject:** Databricks Treasury Modeling Demo Follow-Up

**Body:**
> Hi [Name],
>
> Thank you for attending today's demo on modernizing deposit beta modeling with Databricks.
>
> **Key Takeaways:**
> - 6x faster model development (12 weeks → 2 weeks)
> - 41% accuracy improvement (MAPE: 12.3% → 7.2%)
> - Real-time dashboards for ALCO, CFO, and Treasury
> - CCAR/DFAST regulatory templates built-in
>
> **Next Steps:**
> 1. Schedule pilot planning session (30 minutes)
> 2. Get access to demo environment
> 3. Review GitHub repository: [link]
>
> **Resources Shared:**
> - Demo recording: [link]
> - ROI calculator: [attached]
> - Technical architecture: [attached]
> - Customer case studies: [link]
>
> Looking forward to discussing how we can accelerate your Q1 2026 model cycle.
>
> Best regards,
> [Your Name]

---

## License

This demo script is part of the Databricks CFO Banking Demo project.
See main repository for details.
