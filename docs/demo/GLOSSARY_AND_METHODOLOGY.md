# Glossary & Methodology Guide
## Treasury Deposit Modeling Demo

---

## Acronyms & Terms Glossary

### General Banking & Treasury

| Acronym | Full Name | Definition |
|---------|-----------|------------|
| **ALCO** | Asset Liability Committee | Executive committee that manages interest rate risk, liquidity, and capital. Meets monthly/quarterly to review treasury models and approve strategies. |
| **ALM** | Asset Liability Management | The practice of managing financial risks that arise from mismatches between assets and liabilities (deposits vs loans). |
| **CFO** | Chief Financial Officer | Executive responsible for financial planning, treasury, accounting, and investor relations. |
| **CRM** | Customer Relationship Management | System that tracks customer interactions, product holdings, and relationship history. |
| **EVE** | Economic Value of Equity | The present value of assets minus present value of liabilities. Measures long-term interest rate risk. |
| **NII** | Net Interest Income | Interest earned on loans minus interest paid on deposits. Primary revenue source for banks. |
| **PPNR** | Pre-Provision Net Revenue | Revenue before accounting for loan losses. Used in stress testing (PPNR = NII + Non-Interest Income - Non-Interest Expense). |

### Regulatory & Compliance

| Acronym | Full Name | Definition |
|---------|-----------|------------|
| **CCAR** | Comprehensive Capital Analysis and Review | Annual Federal Reserve stress test for large banks (>$100B assets). Tests capital adequacy under adverse scenarios. |
| **DFAST** | Dodd-Frank Act Stress Testing | Mid-tier bank stress test ($10-100B assets). Less stringent than CCAR but similar methodology. |
| **LCR** | Liquidity Coverage Ratio | Ratio of high-quality liquid assets to net cash outflows over 30 days. Must be >100% per Basel III. |
| **Basel III** | Third Basel Accord | International regulatory framework for bank capital adequacy, stress testing, and liquidity. |
| **CET1** | Common Equity Tier 1 | Highest quality capital (common stock + retained earnings). Must be >7% under stress, >10.5% for "well-capitalized". |
| **RWA** | Risk-Weighted Assets | Assets weighted by credit risk. Used in capital ratio denominator (CET1 / RWA). |
| **HQLA** | High-Quality Liquid Assets | Cash and top-quality liquid assets. Numerator in LCR calculation. |
| **SOC 2 Type II** | Service Organization Control 2 Type II | Audit standard for security, availability, confidentiality of customer data. |

### Modeling & Analytics

| Acronym | Full Name | Definition |
|---------|-----------|------------|
| **Beta (β)** | Deposit Beta Coefficient | Sensitivity of deposit rates to market rate changes. β = 0.50 means a 100bps Fed hike → 50bps deposit rate increase. |
| **MAPE** | Mean Absolute Percentage Error | Average prediction error as %. Lower is better. Target <8% for beta models. |
| **MAE** | Mean Absolute Error | Average absolute difference between predicted and actual values. |
| **RMSE** | Root Mean Squared Error | Square root of average squared errors. Penalizes large errors more than MAE. |
| **PSI** | Population Stability Index | Measures feature drift. PSI < 0.10 = stable, 0.10-0.25 = moderate drift, >0.25 = high drift (recalibrate). |
| **ABGR (g)** | Average Balance Growth Rate | Rate at which deposit balances grow/shrink for accounts that remain open. Used in Chen component decay model. |
| **Lambda (λ)** | Closure Rate | Probability that an account closes in a given period. Used in Chen component decay model. |
| **SHAP** | SHapley Additive exPlanations | Method to explain individual ML predictions. Shows feature contributions to each prediction. |

### Technical & Data

| Acronym | Full Name | Definition |
|---------|-----------|------------|
| **ETL** | Extract, Transform, Load | Traditional data integration process. Replaced by ELT (Extract, Load, Transform) in modern lakehouses. |
| **ACID** | Atomicity, Consistency, Isolation, Durability | Database transaction properties. Delta Lake provides ACID guarantees for data lakes. |
| **JDBC** | Java Database Connectivity | Standard API for connecting to relational databases. |
| **API** | Application Programming Interface | Software interface for system integration. REST APIs are most common. |
| **DBU** | Databricks Unit | Billing unit for compute. 1 DBU ≈ $0.40/hour for standard tier. Medium warehouse = 16 DBUs. |
| **MLflow** | Machine Learning Flow | Open-source platform for ML lifecycle management (tracking, registry, deployment). |

### Research Frameworks (Used in Model Development)

| Term | Source | Definition |
|------|--------|------------|
| **Moody's Relationship Framework** | Moody's Analytics | Classification of deposits as Strategic (sticky), Tactical (medium), or Expendable (hot money) based on customer relationship depth. |
| **Chen Component Decay Model** | Chen (2025) | D(t+1) = D(t) × (1-λ) × (1+g). Separates runoff into closure rate and balance growth components. |
| **Abrigo Vintage Analysis** | Abrigo Software | Cohort-based survival analysis. Tracks deposit retention by origination quarter (e.g., Q1 2020 cohort). |
| **Kaplan-Meier Survival Curves** | Statistical Method | Non-parametric estimator of survival probability over time. Used to visualize cohort retention. |
| **Sigmoid Function** | Chen Dynamic Beta | β(Rm) = βmin + (βmax - βmin) / [1 + exp(-k*(Rm-R0))]. Models non-linear beta response to rate changes. |
| **Taylor Series Attribution** | Mathematical Method | Decomposes EVE changes into duration effect, convexity effect, and beta effect. |

---

## Why 3 Phases in Deposit Modeling?

### The Strategic Rationale

**Problem:** Traditional deposit modeling tries to do everything at once:
- Predict beta coefficients
- Forecast deposit runoff
- Run stress tests
- Build dashboards

**Result:**
- 3-4 month projects that are hard to debug
- Monolithic models that can't be updated independently
- Stakeholders wait months to see any value

**Solution:** Incremental value delivery in 3 distinct phases

---

## Phase 1: Enhanced Deposit Beta Model

### **Goal:** Predict interest rate sensitivity with research-backed features

**Why This First?**
1. **Immediate CFO Value:** "What happens to my $30B deposit portfolio if the Fed moves rates?"
2. **Foundational:** Beta is used in all downstream models (runoff, stress testing, ALM)
3. **Quick Win:** 2 weeks to build, 41% accuracy improvement vs baseline
4. **Standalone Value:** Even without Phase 2/3, CFO can make better pricing decisions

**What We Build:**
- XGBoost model with canonical feature set (19 features)
- Moody's Relationship Framework (Strategic/Tactical/Expendable)
- Chen Market Regime Classification (Low/Medium/High rate environments)
- Abrigo Competitive Pressure indicators (below-market pricing flags)

**Key Output:**
```
Account #12345:
  Product: Money Market
  Balance: $2.5M
  Predicted Beta: 0.62
  Relationship: Expendable
  Risk: $2.5M at-risk (rate 25bps below market)
```

**Business Decision:**
> "We need to raise Money Market rates by 25bps to defend $8.5B in at-risk deposits."

---

## Phase 2: Vintage Analysis & Component Decay Modeling

### **Goal:** Forecast deposit runoff using cohort survival and component separation

**Why This Second?**
1. **Builds on Phase 1:** Uses beta predictions from Phase 1 as inputs
2. **ALCO Requirement:** Treasury committees need 3-year runoff forecasts for liquidity planning
3. **More Complex:** Requires historical time-series data (Phase 1 only needs point-in-time)
4. **Regulatory Need:** LCR calculations require runoff assumptions by segment

**What We Build:**
- Abrigo Vintage Analysis: Cohort survival rates by origination quarter
- Chen Component Decay: D(t+1) = D(t) × (1-λ) × (1+g)
  - λ (lambda) = Closure rate (accounts that leave)
  - g (ABGR) = Balance growth rate (accounts that stay)
- Moody's Segmented Runoff: Different decay curves for Strategic/Tactical/Expendable

**Why Separate λ and g?**
Traditional models lump everything into one "runoff rate". But these are different behaviors:

**Example: Expendable Deposits**
- **λ = 6.68% annually:** 6,680 out of 100,000 accounts close each year
- **g = -5.0% annually:** Remaining 93,320 accounts shrink balances by 5%
- **Combined Effect:** $10.41B → $2.94B over 3 years (-71.7%)

**Business Decision:**
> "We're losing 72% of Expendable deposits. Focus retention on Strategic segment instead (only -47% runoff)."

**Why Not Combined with Phase 1?**
- Phase 1 answers: "What's the beta TODAY?"
- Phase 2 answers: "How many deposits will we have in 3 YEARS?"
- Different questions → different models → different stakeholders

---

## Phase 3: Dynamic Beta & Stress Testing

### **Goal:** Model non-linear beta response and generate regulatory stress test submissions

**Why This Third?**
1. **Most Advanced:** Requires outputs from Phase 1 (beta) and Phase 2 (runoff)
2. **Regulatory Cadence:** CCAR/DFAST are annual/semi-annual, not daily decisions
3. **Specialized Audience:** Board Risk Committee, regulators (vs operational use in Phase 1/2)
4. **Controversial:** Dynamic betas show 30-40% MORE risk than static models (management may resist)

**What We Build:**
- Chen Sigmoid Function: β(Rm) = βmin + (βmax - βmin) / [1 + exp(-k*(Rm-R0))]
  - Shows beta evolves non-linearly as rates change
  - Example: Strategic customers' beta goes from 0.06 (0% rates) → 0.55 (6% rates)
- CCAR/DFAST Scenarios: Baseline, Adverse (+100bps), Severely Adverse (+200bps)
- EVE Sensitivity: Taylor series decomposition (duration + convexity + beta effects)
- Capital Projections: 9-quarter forecasts of CET1, Tier 1, Total Capital ratios

**Why Dynamic vs Static Beta?**

**Static Model (Phase 1):**
- Assumes β = 0.42 at all rate levels
- Good for current environment
- Used for day-to-day ALM decisions

**Dynamic Model (Phase 3):**
- β increases as rates rise (rate fatigue, competition intensifies)
- Example: At 6% rates, β = 0.78 (not 0.42!)
- Shows TRUE risk under extreme stress
- Required for regulatory stress testing

**Key Output:**
```
Severely Adverse Scenario (+200bps shock):
  CET1 Minimum: 8.2% (Pass ✓ - above 7% threshold)
  NII Impact:   -$285M over 2 years
  Deposit Runoff: -$8.5B (-28.2%)
  LCR @ Stress:  105% (Compliant ✓)
```

**Business Decision:**
> "We pass CCAR stress tests. Submit to Fed Reserve by April 5th deadline."

**Why Not Combined with Phase 1/2?**
- Phase 1/2 are used MONTHLY for operational decisions
- Phase 3 is used ANNUALLY for regulatory submissions
- Mixing them confuses operational risk (use static beta) vs stress risk (use dynamic beta)

---

## The Incremental Value Story

### Week 2 (Phase 1 Complete):
**Deliver to CFO:**
> "Here's your $30B portfolio beta: 0.42. Here's $8.5B at-risk. Raise rates on Money Market by 25bps."

**Value:** Immediate pricing decision
**Stakeholder:** CFO, Treasurer
**Use Case:** Monthly pricing committee

---

### Week 4 (Phase 2 Complete):
**Deliver to ALCO:**
> "3-year runoff forecast: Expendable -72%, Strategic -47%. Focus retention budget on Strategic segment."

**Value:** Multi-year liquidity planning
**Stakeholder:** ALCO Committee, Treasury
**Use Case:** Annual budget planning, LCR calculations

---

### Week 6 (Phase 3 Complete):
**Deliver to Board Risk Committee:**
> "CCAR stress test results: CET1 minimum 8.2% (pass). Severely Adverse scenario shows -$285M NII impact."

**Value:** Regulatory compliance
**Stakeholder:** Board Risk Committee, Regulators
**Use Case:** Annual CCAR submission (due April 5)

---

## Why Not Build Everything at Once?

### **Option A: Monolithic Model (Traditional Approach)**
```
Months 1-3: Build mega-model that does everything
Month 4: Debug why it doesn't work
Month 5: Realize you need more data
Month 6: Start over
```

**Problems:**
- ❌ No value until month 6
- ❌ Hard to debug (which part is broken?)
- ❌ Stakeholders lose confidence
- ❌ Can't update beta model without re-running stress tests

### **Option B: Three-Phase Model (Databricks Approach)**
```
Week 2: Phase 1 working → CFO gets beta predictions
Week 4: Phase 2 working → ALCO gets runoff forecasts
Week 6: Phase 3 working → Board gets stress tests
```

**Benefits:**
- ✅ Value every 2 weeks (incremental delivery)
- ✅ Easy to debug (isolate phase-specific issues)
- ✅ Stakeholders see progress
- ✅ Independent updates (recalibrate Phase 1 without touching Phase 3)

---

## How the Phases Integrate

### **Data Flow:**

```
Phase 1 Output: deposit_beta_training_enhanced
  ↓ (contains predicted beta for each account)

Phase 2 Input: Uses Phase 1 betas + historical time-series
Phase 2 Output: deposit_cohort_analysis, component_decay_metrics
  ↓ (contains runoff forecasts by segment)

Phase 3 Input: Uses Phase 1 betas + Phase 2 runoff rates
Phase 3 Output: dynamic_beta_parameters, stress_test_results
```

### **Example Integration:**

**Phase 1 Predicts:**
> Account #12345 (Expendable) has β = 0.78

**Phase 2 Uses That:**
> Expendable segment has λ = 6.68% closure rate
> If rates rise 100bps, Expendable accounts with β > 0.70 close at 2x rate
> Forecasted runoff: -72% over 3 years

**Phase 3 Uses Both:**
> Under Severely Adverse (+200bps):
> - Expendable beta increases to 0.88 (dynamic function)
> - Closure rate accelerates to 12% (stress multiplier)
> - Total deposit loss: $8.5B

---

## Comparison to Other Industries

### **Similar to Software Development:**

**Waterfall (Old Way):**
- Spend 6 months building entire app
- Ship version 1.0
- Realize users wanted something different

**Agile (New Way - 3 Phases):**
- Sprint 1 (Phase 1): Ship login + core features
- Sprint 2 (Phase 2): Ship analytics
- Sprint 3 (Phase 3): Ship advanced features
- Users get value after Sprint 1, not after 6 months

### **Similar to Manufacturing:**

**Build Entire Car at Once (Old Way):**
- Design engine, transmission, body, interior simultaneously
- Integrate at end
- Find problems late

**Modular Assembly (New Way - 3 Phases):**
- Build engine first → test it works
- Build transmission → test it works
- Integrate → final testing
- Catch problems early

---

## When to Combine Phases?

### **Scenario 1: Mature Treasury Team**
If your team already has:
- ✅ Working beta models in production
- ✅ Historical data pipelines
- ✅ Quarterly recalibration process

**Then:** Build all 3 phases in parallel (3 weeks instead of 6)

### **Scenario 2: Regulatory Deadline**
If CCAR submission is due in 4 weeks:
- ✅ Skip Phase 1 enhancements (use existing beta)
- ✅ Focus on Phase 3 stress testing
- ✅ Come back to Phase 1/2 after submission

### **Scenario 3: New to Databricks**
If this is your first lakehouse project:
- ✅ Do Phase 1 only (2 weeks)
- ✅ Prove value to stakeholders
- ✅ Get budget approval for Phase 2/3

---

## Key Takeaway

**3 Phases = 3 Business Questions:**

1. **Phase 1:** "What's my interest rate risk TODAY?" (Beta prediction)
2. **Phase 2:** "How much money will I have in 3 YEARS?" (Runoff forecasting)
3. **Phase 3:** "Will I pass regulatory stress tests?" (CCAR/DFAST compliance)

**Different questions require different models.**
**Building them separately = faster time-to-value + easier maintenance.**

---

## Appendix: Phase Comparison Table

| Aspect | Phase 1 | Phase 2 | Phase 3 |
|--------|---------|---------|---------|
| **Primary Output** | Beta predictions | Runoff forecasts | Stress test results |
| **Time Horizon** | Current period | 1-3 years | 9 quarters (CCAR) |
| **Update Frequency** | Monthly | Quarterly | Annually |
| **Primary User** | CFO, Treasurer | ALCO, Treasury | Board, Regulators |
| **Model Type** | XGBoost (ML) | Component decay | Sigmoid + scenarios |
| **Data Requirement** | Point-in-time | Time-series | Historical + scenarios |
| **Accuracy Metric** | MAPE (beta) | MAE (runoff) | RMSE (stress) |
| **Business Decision** | Pricing | Liquidity planning | Capital adequacy |
| **Regulatory Use** | Optional | LCR calculations | CCAR/DFAST mandatory |
| **Build Time** | 2 weeks | 2 weeks | 2 weeks |
| **Can Run Standalone?** | ✅ Yes | ⚠️ Needs Phase 1 | ⚠️ Needs Phase 1+2 |

---

## Further Reading

### Research Papers:
- Chen, A. (2025). "Dynamic Beta Functions for Deposit Modeling"
- Moody's Analytics. (2023). "Deposit Segmentation Framework"
- Abrigo Software. (2024). "Vintage Analysis Best Practices"

### Regulatory Guidance:
- Federal Reserve SR 11-7: "Guidance on Model Risk Management"
- Basel Committee BCBS 368: "Interest Rate Risk in the Banking Book"
- OCC Bulletin 2011-12: "Sound Practices for Model Risk Management"

### Databricks Resources:
- Unity Catalog Documentation
- MLflow Model Registry Guide
- Delta Lake Performance Tuning

---

## License

This glossary is part of the Databricks CFO Banking Demo project.
See main repository for details.
