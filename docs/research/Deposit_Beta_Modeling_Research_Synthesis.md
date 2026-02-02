# Deposit Beta Modeling: Research Synthesis for Practical Implementation

**Date:** January 31, 2026
**Purpose:** Synthesize industry best practices and academic frameworks for enhancing our deposit beta modeling approach

---

## Executive Summary

This document synthesizes research from Moody's, Abrigo, and academic literature (Chih Chen) to identify reusable components for our deposit beta modeling framework. The key insight: **static linear betas are insufficient** for modern IRRBB management, but **fully dynamic models face regulatory and governance challenges**. A **hybrid approach** using enriched features and conditional betas offers the most practical path forward.

---

## Part 1: From Static to Dynamic Beta Modeling

### 1.1 Traditional Linear Beta Model (Current Baseline)

**Formula:**
```
Rd = β * Rm + s
```

Where:
- `Rd` = Deposit rate offered by bank
- `β` = Beta coefficient (passthrough rate, e.g., 0.5 = 50% of rate changes passed through)
- `Rm` = Market reference rate (e.g., Fed Funds, 3-month SOFR)
- `s` = Spread/intercept (bank-specific premium/discount)

**Strengths:**
- ✅ Simple, interpretable, operationally efficient
- ✅ Easy to calibrate with OLS regression
- ✅ Regulatory-friendly (used in ALCO reporting)

**Weaknesses:**
- ❌ Assumes constant beta across all rate environments
- ❌ Fails to capture depositor behavior at rate inflection points
- ❌ Understates risk during rising rate regimes
- ❌ Ignores non-linear repricing dynamics

**Real-World Example (Abrigo):**
- **Early 2000s:** Rates rose 4%+ over 3 years → High customer rate sensitivity
- **2015-2018:** Rates rose only ~2% over 3 years → Banks kept rates flat, minimal deposit flight
- **Implication:** Beta is **not constant** — it depends on rate magnitude, speed, and starting level

---

### 1.2 Dynamic Beta Function (Chen Framework)

**Formula:**
```
β(Rm) = βmin + (βmax - βmin) * [1 / (1 + exp(-k * (Rm - R0)))]
```

Where:
- `βmin` = Minimum beta (e.g., 0.10 when rates near zero)
- `βmax` = Maximum beta (e.g., 0.85 during steep rate hikes)
- `k` = Steepness parameter (how fast beta transitions)
- `R0` = Inflection point (rate level where beta accelerates)

**Deposit Rate:**
```
Rd = β(Rm) * Rm + s
```

**Behavioral Intuition:**
- **Low rates (Rm < R0):** Customers tolerate low rates → βmin applies
- **Inflection point (Rm ≈ R0):** Customers become rate-sensitive → Beta rises sharply
- **High rates (Rm > R0):** Beta saturates at βmax (competitive pressure maxes out)

**Strengths:**
- ✅ Captures non-linear repricing behavior
- ✅ Realistic modeling of depositor psychology
- ✅ Better NII and EVE forecasts in stress scenarios

**Weaknesses:**
- ❌ Harder to calibrate (requires non-linear optimization)
- ❌ Increases EVE sensitivity (can breach -15% CET1 limits)
- ❌ No regulatory capital relief (unlike credit risk AIRB)
- ❌ Requires quarterly recalibration

**Regulatory Consideration:**
> *"Unlike credit risk modeling, where advanced internal models can reduce capital requirements, there is little incentive for banks to adopt more punitive dynamic deposit models for IRRBB."* — Chen (2025)

---

### 1.3 Hybrid Approach: Conditional Static Betas

**Pragmatic Solution:** Use **regime-dependent betas** instead of continuous functions.

**Model:**
```python
if market_rate < 1.0:
    beta = 0.15  # Low rate regime
elif 1.0 <= market_rate < 3.0:
    beta = 0.50  # Transition regime
else:
    beta = 0.75  # High rate regime
```

**Implementation in ML:**
```python
features = [
    'market_rate',
    'rate_regime',  # Categorical: low/medium/high
    'rate_change_3m',  # Speed of rate changes
    'yield_curve_slope',
    'customer_segment',
    'account_tenure',
    # ... other features
]
```

**Benefits:**
- ✅ Captures non-linearity without complex calibration
- ✅ Easier to explain to ALCO and regulators
- ✅ Can be validated with historical rate cycles
- ✅ XGBoost can learn thresholds automatically

---

## Part 2: Segmentation & Data Enrichment (Moody's Framework)

### 2.1 From Top-Down to Bottom-Up Modeling

**Traditional Approach (Static Segmentation):**
```
Segments:
  - Retail Checking (70% stable, β=0.20)
  - Retail Savings (50% stable, β=0.50)
  - Commercial DDA (40% stable, β=0.60)
```

**Moody's Recommendation: Bottom-Up with 6 Data Categories**

#### Category 1: Demographic Attributes
```python
features = [
    'customer_age',
    'household_income_bracket',
    'employment_status',
    'life_events',  # Marriage, home purchase, retirement
    'business_industry',  # For commercial
]
```

**Why it matters:** Retirees and high-income customers are **less rate-sensitive** (convenience > yield). Younger customers shop rates aggressively.

#### Category 2: Behavioral Patterns
```python
features = [
    'digital_banking_usage',  # % of transactions online/mobile
    'branch_visit_frequency',
    'atm_usage_count',
    'bill_pay_enrolled',
    'direct_deposit_active',
]
```

**Insight:** High digital engagement = **stickier deposits** (switching costs, inertia). Direct deposit = **core operational funds** (low beta).

#### Category 3: Customer Relationships
```python
features = [
    'relationship_length_years',  # Account tenure
    'product_count',  # Cross-sell depth (checking + savings + loan + credit card)
    'total_relationship_balance',
    'primary_bank_flag',  # Is this their main bank?
    'acquisition_channel',  # Branch, online, referral
]
```

**Moody's Categorization:**
- **Strategic customers:** Multi-product, long tenure, high balance → **Lowest beta**
- **Tactical customers:** 2-3 products, moderate tenure → **Medium beta**
- **Expendable customers:** Single product, rate-shopping → **Highest beta**

**Real-World Impact (Abrigo):**
> "Surge balances matter — rate-sensitive funds migrate to higher-paying products, carrying significantly higher costs during rate increases."

#### Category 4: Industry Concentration (Commercial Deposits)
```python
features = [
    'employer_industry_code',  # NAICS code
    'industry_concentration_risk',  # % of deposits from single industry
    'business_cycle_sensitivity',  # Cyclical vs. defensive
]
```

**Why it matters:** Tech startup deposits are **more volatile** than utility company deposits. Healthcare and government deposits are **sticky**.

#### Category 5: Competitive Landscape
```python
features = [
    'competitor_rate_spread',  # Our rate vs. local competitors
    'branch_density_5mi',  # Number of competitor branches nearby
    'online_bank_rate_spread',  # Our rate vs. Ally, Marcus, etc.
    'competitor_promotion_intensity',  # Tracking competitive offers
]
```

**Abrigo Insight:**
> "Beta measures rate sensitivity: if rates go up 200 basis points, you might pass 100 basis points on to your customer. That would be a beta of 50%."

**Competitive pressure** forces higher betas. If competitors raise rates 2%, but you only raise 1%, expect deposit outflows.

#### Category 6: Macroeconomic Factors
```python
features = [
    'fed_funds_rate',
    'sofr_3m',
    'yield_curve_slope',  # 10Y - 2Y
    'unemployment_rate',
    'gdp_growth',
    'inflation_rate',
    'vix_index',  # Market volatility
]
```

**Stress Testing:** Abrigo recommends validating models across **multiple rate environments**:
- Early 2000s: 4%+ rate increase → High sensitivity
- 2015-2018: 2% rate increase → Low sensitivity
- 2020-2023: Zero rates → Near-zero sensitivity
- 2022-2024: 5%+ rate increase → **Highest sensitivity in 20 years**

---

### 2.2 Implementation Strategy: Feature Engineering

**Existing Features (Current Model):**
```python
base_features = [
    'product_type',
    'customer_segment',
    'rate_gap',
    'churn_probability',
    'account_age_years',
    'balance_size',
    'rate_spread',
    'digital_user',
    'balance_trend_30d',
    'transaction_activity'
]
```

**Enhanced Features (Moody's + Abrigo):**
```python
enhanced_features = base_features + [
    # Behavioral depth
    'cross_sell_count',
    'primary_bank_flag',
    'direct_deposit_active',
    'bill_pay_enrolled',

    # Relationship value
    'relationship_length_years',
    'total_relationship_balance',
    'relationship_category',  # Strategic/Tactical/Expendable

    # Competitive context
    'competitor_rate_spread',
    'online_bank_rate_spread',
    'branch_density_5mi',

    # Market regime
    'rate_regime',  # Low/Medium/High
    'rate_change_velocity_3m',
    'yield_curve_inversion_flag',

    # Deposit stability
    'surge_balance_flag',  # Is this pandemic/QE-driven surge?
    'core_deposit_flag',  # Persistent through rate cycles
    'minimum_balance_24m',  # Floor balance (Abrigo methodology)
]
```

**Feature Importance Validation:**
Based on research, expected top features:
1. **Relationship length** (Moody's: Strategic customers have low beta)
2. **Product count** (Cross-sell = switching cost = low beta)
3. **Rate spread** (Abrigo: Competitive pressure drives beta)
4. **Market rate level** (Chen: Non-linear beta function)
5. **Direct deposit flag** (Operational funds = sticky = low beta)

---

## Part 3: Component-Based Decay Modeling (Chen Framework)

### 3.1 Beyond Simple Runoff: Closure + Balance Growth

**Traditional Approach:**
```
Runoff Rate = 5% annually (constant)
```

**Chen Component Model:**
```
D(t+1) = D(t) * (1 - λ) * (1 + g(Rt, St))
```

Where:
- `λ` = **Closure Rate** (% of accounts fully terminated)
- `g(Rt, St)` = **Average Balance Growth Rate (ABGR)** (among remaining accounts)
- `Rt` = Interest rate environment
- `St` = Credit spread environment

**ABGR Decomposition:**
```
g(Rt, St) = g_irrbb_stable + g_liquidity_stable + g_non_stable(Rt, St)
```

Components:
1. **IRRBB-Stable ABGR:** Structural balances (payroll, operating accounts) — **not rate-sensitive**
2. **Liquidity-Stable ABGR:** Operational deposits (treasury mgmt) — **not rate-sensitive**
3. **Non-Stable ABGR:** Rate-sensitive funds (CDs, MMDA) — **highly rate-sensitive**

**Example Calculation:**
```python
# Portfolio: $1B deposits
# λ = 3% annual closure rate
# g_irrbb_stable = +1% (operational growth)
# g_liquidity_stable = +2% (business expansion)
# g_non_stable = -5% (rate-driven outflows)

# If 70% is stable, 30% is non-stable:
g_total = 0.7 * (0.01 + 0.02) + 0.3 * (-0.05)
        = 0.021 - 0.015
        = +0.6% net growth

D(t+1) = $1B * (1 - 0.03) * (1 + 0.006)
       = $976M
```

**Why This Matters:**
- Separates **involuntary attrition** (λ) from **discretionary balance changes** (g)
- Links balance drift to **rate environment** and **liquidity conditions**
- Enables **scenario analysis** for CCAR/DFAST stress testing

---

### 3.2 Vintage Analysis (Abrigo Methodology)

**Concept:** Track cohorts of deposits over time to measure **decay curves**.

**Example:**
```
January 2020 cohort: $500M opening balance

Month 0:  $500M (100%)
Month 6:  $485M (97%)
Month 12: $470M (94%)
Month 24: $450M (90%)
Month 36: $440M (88%)
```

**Decay Rate:** 12% over 3 years = **4% annually**

**Segmented Vintage Analysis:**
```
Strategic customers:  2% annual decay
Tactical customers:   5% annual decay
Expendable customers: 15% annual decay
```

**Implementation in ML:**
```python
# Create vintage features
df['cohort'] = df['account_open_date'].dt.to_period('Q')  # Quarterly cohorts
df['months_since_open'] = (df['current_date'] - df['account_open_date']).dt.days / 30

# Track survival rate by cohort
survival_curves = df.groupby(['cohort', 'months_since_open'])['balance'].sum()

# Use as training feature
df['expected_survival_rate'] = df.merge(survival_curves, on=['cohort', 'months_since_open'])
```

**Abrigo Warning:**
> "Outdated studies create vulnerabilities — using old data is like trying to navigate the internet today using Windows Vista."

**Recommendation:** Recalibrate **quarterly**, especially post-pandemic (2020-2024 saw unprecedented deposit volatility).

---

## Part 4: Sensitivity Analysis & Taylor Series Approximation

### 4.1 Delta NII and Delta EVE Decomposition

**Chen's Taylor Series Approach:**
```
ΔNII ≈ (∂NII/∂Rm) * ΔRm + (∂NII/∂β) * Δβ + (∂NII/∂λ) * Δλ + ...

ΔEVE ≈ (∂EVE/∂Rm) * ΔRm + (∂EVE/∂β) * Δβ + (∂EVE/∂D) * ΔD + ...
```

**Interpretation:**
- **∂NII/∂Rm:** Direct rate impact on net interest margin
- **∂NII/∂β:** Indirect impact via deposit repricing
- **∂NII/∂λ:** Impact of deposit runoff on funding costs
- **∂EVE/∂Rm:** Duration/convexity effects
- **∂EVE/∂D:** Deposit volume changes

**Practical Use:**
```python
# Scenario: +200 bps rate shock
base_case = {
    'Rm': 2.0,
    'beta': 0.50,
    'deposit_balance': 1_000_000_000
}

stress_case = {
    'Rm': 4.0,  # +200 bps
    'beta': 0.65,  # Beta increases in rising rate environment
    'deposit_balance': 950_000_000  # -5% runoff
}

# Decompose NII impact
delta_nii_direct = nii_sensitivity_to_rate * (4.0 - 2.0)
delta_nii_beta = nii_sensitivity_to_beta * (0.65 - 0.50)
delta_nii_balance = nii_sensitivity_to_balance * (950M - 1B)

total_delta_nii = delta_nii_direct + delta_nii_beta + delta_nii_balance
```

**Governance Insight:**
> "EVE Sensitivity: Dynamic models often increase EVE sensitivity, especially for large upward rate shocks (e.g., +200bps), which can push institutions closer to or beyond the -15% of CET1 Standard Outlier Test."

**Implication:** If dynamic beta model pushes EVE/CET1 to -18%, bank **fails Standard Outlier Test** → Regulatory scrutiny.

---

### 4.2 Lag Factor Modeling

**Abrigo Definition:**
> "Lag represents timing: institutions typically delay passing rate changes to customers, sometimes taking six months to fully adjust offerings."

**Model Enhancement:**
```python
# Current model: Instantaneous repricing
Rd(t) = β * Rm(t) + s

# Lagged model: Distributed lag
Rd(t) = β0 * Rm(t) + β1 * Rm(t-1) + β2 * Rm(t-2) + ... + s

# Or exponential smoothing
Rd(t) = α * β * Rm(t) + (1 - α) * Rd(t-1)
```

**α (Speed of Adjustment):**
- α = 1.0 → Immediate repricing (rare)
- α = 0.5 → 50% adjustment each period (common)
- α = 0.2 → Slow adjustment over 6+ months

**Implementation:**
```python
features = [
    'market_rate_current',
    'market_rate_lag_1m',
    'market_rate_lag_3m',
    'market_rate_lag_6m',
    'deposit_rate_lag_1m',  # Bank's own rate history
]
```

**XGBoost Advantage:** Automatically learns optimal lag structure through feature importance.

---

## Part 5: Gap Analysis Integration

### 5.1 Three Types of Gaps (Chen Framework)

#### Gap 1: Liquidity Gaps
**Definition:** Mismatch between cash inflows and outflows by time bucket.

```
Time Bucket  | Assets  | Liabilities | Gap      | Cumulative Gap
-------------|---------|-------------|----------|----------------
0-30 days    | $500M   | $600M       | -$100M   | -$100M
31-90 days   | $300M   | $200M       | +$100M   | $0M
91-180 days  | $200M   | $150M       | +$50M    | +$50M
```

**Negative Gap:** Funding shortfall → Need to borrow or raise rates.

**Deposit Beta Impact:**
- High beta = More rate-sensitive liabilities = **Larger negative gap** in rising rates
- Low beta = Stable funding = **Smaller liquidity risk**

#### Gap 2: Repricing Gaps
**Definition:** When assets vs. liabilities reset their rates.

```
Next 12 Months:
  Rate-Sensitive Assets:      $2B (repricing loans, floating rate)
  Rate-Sensitive Liabilities: $3B (deposits with β > 0.5)

Repricing Gap = $2B - $3B = -$1B (negative)
```

**NII Sensitivity:**
```
ΔNII = Repricing Gap * ΔRm * (1 - β_avg)

If rates rise 1% (+100 bps):
ΔNII = -$1B * 0.01 * (1 - 0.50) = -$5M annually
```

**Interpretation:** Bank is **liability-sensitive** — rising rates hurt NII if beta > asset repricing speed.

#### Gap 3: Fixed Rate Gaps
**Definition:** Non-repricing balances exposed to duration risk (EVE).

```
Fixed Rate Assets:       $5B (5-year mortgages, 10-year bonds)
Fixed Rate Liabilities:  $3B (stable core deposits, term CDs)

Fixed Rate Gap = $5B - $3B = +$2B
```

**EVE Sensitivity:**
```
ΔEVE = -Duration * Fixed Rate Gap * (ΔRm / (1 + Rm))

If rates rise 2% (+200 bps):
ΔEVE = -7.5 * $2B * (0.02 / 1.02) = -$294M

If CET1 = $2B, EVE/CET1 = -14.7% ✅ (just under -15% threshold)
```

**Deposit Modeling Impact:**
- **Static beta models:** Overestimate stable NMD portion → Understate fixed rate gap → Understate EVE risk
- **Dynamic beta models:** More realistic stable portion → Larger fixed rate gap → Higher EVE sensitivity

---

### 5.2 Stable vs. Non-Stable Segmentation

**Traditional Static Approach:**
```python
# Assume 70% of all NMDs are stable (non-rate-sensitive)
stable_deposits = total_nmds * 0.70
non_stable_deposits = total_nmds * 0.30

# Apply fixed beta
stable_beta = 0.10
non_stable_beta = 0.70
```

**Enhanced Component-Based Approach:**
```python
# Segment by actual behavior
stable_deposits = (
    strategic_customers * 0.90 +  # 90% of strategic is stable
    tactical_customers * 0.60 +   # 60% of tactical is stable
    expendable_customers * 0.20   # Only 20% of expendable is stable
)

# Apply dynamic beta
stable_beta = max(0.10, 0.15 if rate_regime == 'high' else 0.10)
non_stable_beta = 0.50 if rate_regime == 'low' else 0.75
```

**Why This Matters:**
- **Regulatory capital:** -15% EVE/CET1 threshold
- **Liquidity risk:** LCR, NSFR ratios
- **Pricing strategy:** FTP rates for loans/deposits

---

## Part 6: Practical Implementation Roadmap

### Phase 1: Quick Wins (1-3 Months)
**Goal:** Enhance existing XGBoost model with high-impact features.

**Actions:**
1. ✅ **Add relationship features:**
   ```python
   new_features = [
       'relationship_length_years',
       'product_count',
       'primary_bank_flag',
       'direct_deposit_active'
   ]
   ```

2. ✅ **Add market regime features:**
   ```python
   df['rate_regime'] = pd.cut(
       df['fed_funds_rate'],
       bins=[0, 1.0, 3.0, 10.0],
       labels=['low', 'medium', 'high']
   )
   ```

3. ✅ **Add competitive context:**
   ```python
   df['competitor_rate_spread'] = df['our_rate'] - df['market_benchmark']
   ```

**Expected Impact:** +5-10% improvement in beta prediction accuracy (MAPE).

---

### Phase 2: Segmentation Overhaul (3-6 Months)
**Goal:** Move from product-based to relationship-based segmentation.

**Actions:**
1. 📊 **Implement Moody's 3-tier classification:**
   ```python
   def classify_customer(row):
       score = 0
       score += min(row['product_count'], 5) * 2  # Max 10 points
       score += min(row['tenure_years'], 10)      # Max 10 points
       score += min(row['balance'] / 100000, 5)   # Max 5 points (per $100k)

       if score >= 15:
           return 'Strategic'
       elif score >= 8:
           return 'Tactical'
       else:
           return 'Expendable'

   df['customer_category'] = df.apply(classify_customer, axis=1)
   ```

2. 📊 **Implement Abrigo vintage analysis:**
   ```python
   # Track cohort survival rates
   cohort_analysis = df.groupby(['cohort', 'months_since_open']).agg({
       'balance': 'sum',
       'account_id': 'count'
   })

   cohort_analysis['survival_rate'] = (
       cohort_analysis['balance'] /
       cohort_analysis.groupby('cohort')['balance'].transform('first')
   )
   ```

3. 📊 **Build component decay model:**
   ```python
   # Closure rate (λ)
   closure_rate = (
       df.groupby('customer_category')['account_closed']
       .mean()
   )

   # ABGR (g)
   abgr = (
       df[df['account_closed'] == False]
       .groupby('customer_category')['balance_growth_pct']
       .mean()
   )

   # Combined model
   df['expected_balance_next_period'] = (
       df['balance'] *
       (1 - df['closure_rate']) *
       (1 + df['abgr'])
   )
   ```

**Expected Impact:** +10-15% improvement in beta prediction, **25%+ improvement in runoff forecasting**.

---

### Phase 3: Dynamic Beta Integration (6-12 Months)
**Goal:** Implement Chen's dynamic beta framework for stress testing.

**Actions:**
1. 🔬 **Calibrate dynamic beta parameters:**
   ```python
   from scipy.optimize import curve_fit

   def dynamic_beta(Rm, beta_min, beta_max, k, R0):
       return beta_min + (beta_max - beta_min) / (1 + np.exp(-k * (Rm - R0)))

   # Fit to historical data
   params, _ = curve_fit(
       dynamic_beta,
       historical_rates,
       historical_betas,
       p0=[0.10, 0.85, 2.0, 2.5]  # Initial guesses
   )

   beta_min, beta_max, k, R0 = params
   ```

2. 🔬 **Implement regime-conditional models:**
   ```python
   # Train separate XGBoost models for each regime
   model_low = xgb.XGBRegressor().fit(X_low_rate, y_low_rate)
   model_med = xgb.XGBRegressor().fit(X_med_rate, y_med_rate)
   model_high = xgb.XGBRegressor().fit(X_high_rate, y_high_rate)

   # Ensemble prediction
   def predict_beta(X):
       current_rate = X['market_rate'].iloc[0]
       if current_rate < 1.0:
           return model_low.predict(X)
       elif current_rate < 3.0:
           return model_med.predict(X)
       else:
           return model_high.predict(X)
   ```

3. 🔬 **Taylor series sensitivity analysis:**
   ```python
   # Compute partial derivatives
   def nii_sensitivity(base_case, shock):
       # ∂NII/∂Rm
       d_nii_d_rate = compute_repricing_gap_impact(base_case, shock)

       # ∂NII/∂β
       d_nii_d_beta = compute_deposit_repricing_impact(base_case, shock)

       # ∂NII/∂λ
       d_nii_d_lambda = compute_runoff_impact(base_case, shock)

       return {
           'direct_rate_impact': d_nii_d_rate,
           'beta_impact': d_nii_d_beta,
           'runoff_impact': d_nii_d_lambda,
           'total_impact': d_nii_d_rate + d_nii_d_beta + d_nii_d_lambda
       }
   ```

**Expected Impact:** **20-30% improvement in stress test accuracy**, better EVE forecasting.

---

### Phase 4: Governance & Monitoring (Ongoing)
**Goal:** Establish quarterly recalibration process.

**Actions:**
1. 📈 **Quarterly model validation:**
   ```python
   # Backtest predictions vs. actuals
   validation_report = {
       'period': 'Q4 2024',
       'predicted_avg_beta': 0.52,
       'actual_avg_beta': 0.49,
       'mape': 0.06,  # 6% error
       'segments_outperforming': ['Strategic', 'Tactical'],
       'segments_underperforming': ['Expendable'],
       'recalibration_needed': False  # MAPE < 10%
   }
   ```

2. 📈 **Competitive intelligence tracking:**
   ```python
   # Scrape competitor rates weekly
   competitor_rates = {
       'Chase': 2.50,
       'BofA': 2.25,
       'Marcus': 4.50,
       'Ally': 4.25
   }

   our_spread = our_rate - np.mean(list(competitor_rates.values()))
   ```

3. 📈 **Regulatory compliance:**
   ```python
   # EVE/CET1 monitoring
   stress_scenarios = {
       '+200bps': compute_eve_impact(rate_shock=2.0),
       '-200bps': compute_eve_impact(rate_shock=-2.0),
       '+300bps_slow': compute_eve_impact(rate_shock=3.0, speed='slow'),
       '+300bps_fast': compute_eve_impact(rate_shock=3.0, speed='fast')
   }

   for scenario, eve_change in stress_scenarios.items():
       eve_cet1_ratio = eve_change / cet1_capital
       if eve_cet1_ratio < -0.15:
           print(f"⚠️ WARNING: {scenario} breaches -15% SOT threshold")
   ```

**Expected Impact:** Maintain model accuracy > 90%, avoid regulatory violations.

---

## Part 7: Key Formulas Reference

### Beta Modeling

**Static Linear Beta:**
```
Rd = β * Rm + s
```

**Dynamic Sigmoid Beta:**
```
β(Rm) = βmin + (βmax - βmin) / [1 + exp(-k * (Rm - R0))]
Rd = β(Rm) * Rm + s
```

**Lagged Beta:**
```
Rd(t) = β0 * Rm(t) + β1 * Rm(t-1) + β2 * Rm(t-2) + s
```

**Exponential Smoothing Beta:**
```
Rd(t) = α * β * Rm(t) + (1 - α) * Rd(t-1)
```

---

### Decay Modeling

**Component Decay:**
```
D(t+1) = D(t) * (1 - λ) * (1 + g)

Where:
  λ = Closure rate
  g = Average Balance Growth Rate (ABGR)
```

**ABGR Decomposition:**
```
g = g_irrbb_stable + g_liquidity_stable + g_non_stable(Rm, Sm)
```

---

### Gap Analysis

**Repricing Gap NII Sensitivity:**
```
ΔNII = Repricing_Gap * ΔRm * (1 - β_avg)
```

**Fixed Rate Gap EVE Sensitivity:**
```
ΔEVE = -Duration * Fixed_Rate_Gap * [ΔRm / (1 + Rm)]
```

**EVE/CET1 Standard Outlier Test:**
```
EVE_CET1_Ratio = ΔEVE / CET1_Capital

Regulatory Threshold: -15%
Warning Level: -12%
```

---

### Taylor Series Approximation

**NII Sensitivity Decomposition:**
```
ΔNII ≈ (∂NII/∂Rm) * ΔRm + (∂NII/∂β) * Δβ + (∂NII/∂λ) * Δλ
```

**EVE Sensitivity Decomposition:**
```
ΔEVE ≈ (∂EVE/∂Rm) * ΔRm + (∂EVE/∂β) * Δβ + (∂EVE/∂D) * ΔD
```

---

## Part 8: Real-World Validation Checklist

### Model Validation Questions (Abrigo Framework)

✅ **Historical Validation:**
- [ ] Does the model accurately predict the 2015-2018 low-sensitivity period?
- [ ] Does the model capture the 2022-2024 high-sensitivity period?
- [ ] Are pandemic-era surge balances correctly flagged as non-core?

✅ **Segmentation Validation:**
- [ ] Do "Strategic" customers have materially lower betas than "Expendable"?
- [ ] Do customers with direct deposit have lower runoff rates?
- [ ] Do multi-product households show higher retention?

✅ **Competitive Validation:**
- [ ] When competitors raise rates 2%, does the model predict outflows if we don't follow?
- [ ] Does beta increase when our rate falls below online bank benchmarks?

✅ **Regime Validation:**
- [ ] Is beta higher when rates are above 3% vs. below 1%?
- [ ] Does beta accelerate when rates rise quickly (>1% in 3 months)?

✅ **Regulatory Validation:**
- [ ] Does the +200bps stress test keep EVE/CET1 above -15%?
- [ ] Are stable deposit assumptions consistent with LCR/NSFR calculations?

---

## Part 9: Pitfalls to Avoid

### Common Mistakes (Research Synthesis)

❌ **Mistake 1: Using Outdated Data**
> "Using old data is like trying to navigate the internet today using Windows Vista." — Abrigo

**Solution:** Recalibrate **quarterly**, especially after major rate moves.

---

❌ **Mistake 2: Ignoring Surge Balances**
**Problem:** 2020-2022 saw $5T+ in pandemic-driven deposit inflows. Banks that treated these as "core" got burned in 2022-2023 rate hikes.

**Solution:**
```python
df['surge_balance_flag'] = (
    (df['account_open_date'] >= '2020-03-01') &
    (df['account_open_date'] <= '2022-06-30')
)

# Assign higher runoff rate to surge balances
df.loc[df['surge_balance_flag'], 'expected_closure_rate'] *= 2.0
```

---

❌ **Mistake 3: Overfitting to Low-Rate Regimes**
**Problem:** Models trained on 2010-2021 data (zero rate era) fail spectacularly in 2022+.

**Solution:** **Stratified train/test split** by rate regime:
```python
from sklearn.model_selection import StratifiedShuffleSplit

splitter = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
for train_idx, test_idx in splitter.split(X, y_rate_regime):
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
```

---

❌ **Mistake 4: Ignoring Lag Effects**
**Problem:** Assuming instant repricing. In reality, banks delay 3-6 months.

**Solution:** Add lagged features + exponential smoothing.

---

❌ **Mistake 5: Static Segmentation**
**Problem:** "Retail Savings" segment includes both $500 balance rate-shoppers and $250k balance relationship customers.

**Solution:** Use **bottom-up** relationship-based segmentation (Moody's framework).

---

## Part 10: Summary & Next Steps

### What We Can Reuse in Our Model

#### Immediate (Next Model Iteration)
1. ✅ **Enhanced features:**
   - Relationship length, product count, primary bank flag
   - Direct deposit active, bill pay enrolled
   - Competitor rate spreads
   - Market rate regime (low/medium/high)

2. ✅ **Conditional betas:**
   - Train separate models or use `rate_regime` as categorical feature
   - XGBoost will learn non-linear thresholds automatically

3. ✅ **Vintage analysis:**
   - Track cohort survival rates
   - Flag surge balances (2020-2022 cohorts)

#### Medium-Term (3-6 Months)
4. 📊 **Relationship-based segmentation:**
   - Implement Strategic/Tactical/Expendable classification
   - Use as primary segmentation axis (replace product-type)

5. 📊 **Component decay model:**
   - Separate closure rate (λ) from ABGR (g)
   - Link ABGR to rate environment

6. 📊 **Gap analysis integration:**
   - Use beta predictions to compute repricing gaps
   - Validate EVE sensitivity for regulatory compliance

#### Long-Term (6-12 Months)
7. 🔬 **Dynamic beta functions:**
   - Calibrate Chen sigmoid model for stress testing
   - Use for CCAR/DFAST submissions (not day-to-day ALM)

8. 🔬 **Taylor series sensitivity:**
   - Decompose NII/EVE impacts by driver
   - Build ALCO reporting dashboards

9. 🔬 **Quarterly recalibration:**
   - Establish governance process
   - Track model drift and competitive landscape

---

### Success Metrics

**Model Accuracy:**
- Current MAPE: ~8-10% (baseline)
- Target MAPE: <5% (with enhancements)

**Business Impact:**
- **Pricing optimization:** +10-20 bps on NII margin (better rate decisions)
- **Liquidity risk:** -25% on unexpected runoff (better decay forecasting)
- **Regulatory capital:** Maintain EVE/CET1 > -15% (avoid SOT breach)

**Governance:**
- Quarterly recalibration (maintain accuracy)
- Competitive intelligence tracking (avoid deposit flight)
- Stress testing validation (regulatory compliance)

---

## References

1. **Moody's Analytics (2024).** *How Small and Medium-Sized Banks Can Enhance Deposits Modelling Frameworks.*
   https://www.moodys.com/web/en/us/insights/banking/how-small-and-medium-sized-banks-can-enhance-deposits-modelling-frameworks.html

2. **Abrigo (2024).** *Core Deposit Analysis Advisory Services.*
   https://www.abrigo.com/advisory-services/core-deposit-analysis/

3. **Abrigo (2024).** *Core Deposit Analytics Results.*
   https://www.abrigo.com/blog/core-deposit-analytics-results/

4. **Chen, Chih (2025).** *Deposit Modeling: A Practical Synthesis for ALM Practitioners.*
   LinkedIn Article. Key articles cited:
   - *Introduction to Gap Analysis in Bank ALM – Part 1 & 2*
   - *Non-Maturity Deposits as a Structural Hedge for Interest Rate Risk in the Banking Book*
   - *Deposit Repricing Models for IRRBB: Evolving from Static to Dynamic Betas*
   - *A Component-Based Model for Non-Maturity Deposit Decay Incorporating Interest Rate and Credit Spread Sensitivity*
   - *Dynamic Deposit Behaviours in IRRBB: Enhancing Risk Management through Sensitivity Analysis*

---

## Appendix: Feature Engineering Code Examples

### A1: Relationship-Based Segmentation
```python
def classify_customer_relationship(df):
    """
    Implement Moody's Strategic/Tactical/Expendable framework
    """
    df['relationship_score'] = (
        np.minimum(df['product_count'], 5) * 2 +  # Max 10 pts
        np.minimum(df['tenure_years'], 10) +      # Max 10 pts
        np.minimum(df['balance'] / 100000, 5)     # Max 5 pts per $100k
    )

    df['relationship_category'] = pd.cut(
        df['relationship_score'],
        bins=[-np.inf, 8, 15, np.inf],
        labels=['Expendable', 'Tactical', 'Strategic']
    )

    return df
```

### A2: Competitive Context Features
```python
def add_competitive_features(df, market_data):
    """
    Add Moody's competitive landscape features
    """
    # Our rate vs. peer banks
    df['peer_rate_spread'] = df['our_rate'] - market_data['peer_avg_rate']

    # Our rate vs. online banks (Ally, Marcus, etc.)
    df['online_rate_spread'] = df['our_rate'] - market_data['online_avg_rate']

    # Branch density (competitor branches within 5 miles)
    df['competitor_branch_density'] = df['zip_code'].map(
        market_data['branch_counts_by_zip']
    )

    return df
```

### A3: Rate Regime Features
```python
def add_rate_regime_features(df):
    """
    Capture non-linear beta dynamics via regime classification
    """
    # Regime classification
    df['rate_regime'] = pd.cut(
        df['fed_funds_rate'],
        bins=[0, 1.0, 3.0, 10.0],
        labels=['low', 'medium', 'high']
    )

    # Rate velocity (speed of change)
    df['rate_change_velocity_3m'] = (
        df['fed_funds_rate'] -
        df['fed_funds_rate'].shift(3)
    )

    # Yield curve shape
    df['yield_curve_slope'] = df['rate_10y'] - df['rate_2y']
    df['yield_curve_inverted'] = (df['yield_curve_slope'] < 0).astype(int)

    return df
```

### A4: Vintage Analysis
```python
def compute_vintage_survival_rates(df):
    """
    Implement Abrigo vintage analysis methodology
    """
    # Assign cohorts (quarterly)
    df['cohort'] = pd.to_datetime(df['account_open_date']).dt.to_period('Q')

    # Months since open
    df['months_since_open'] = (
        (pd.to_datetime(df['current_date']) -
         pd.to_datetime(df['account_open_date'])).dt.days / 30
    ).astype(int)

    # Compute survival rates by cohort
    cohort_survival = (
        df.groupby(['cohort', 'months_since_open'])
        .agg({'balance': 'sum', 'account_id': 'count'})
        .reset_index()
    )

    # Initial balance for each cohort
    initial_balances = (
        cohort_survival[cohort_survival['months_since_open'] == 0]
        .set_index('cohort')['balance']
    )

    cohort_survival['survival_rate'] = (
        cohort_survival['balance'] /
        cohort_survival['cohort'].map(initial_balances)
    )

    # Merge back to main df
    df = df.merge(
        cohort_survival[['cohort', 'months_since_open', 'survival_rate']],
        on=['cohort', 'months_since_open'],
        how='left'
    )

    return df
```

### A5: Component Decay Model
```python
def compute_component_decay(df, rate_environment):
    """
    Implement Chen's component-based decay model
    """
    # Closure rate (λ) by customer category
    closure_rates = {
        'Strategic': 0.02,    # 2% annual
        'Tactical': 0.05,     # 5% annual
        'Expendable': 0.15    # 15% annual
    }

    df['closure_rate'] = df['relationship_category'].map(closure_rates)

    # ABGR components
    df['abgr_irrbb_stable'] = 0.01   # 1% structural growth
    df['abgr_liquidity_stable'] = 0.02  # 2% operational growth

    # Non-stable ABGR (rate-sensitive)
    df['abgr_non_stable'] = -0.05 * (
        (rate_environment['market_rate'] - df['our_rate']) /
        rate_environment['market_rate']
    )

    # Weight by stability
    df['abgr_total'] = (
        df['stability_pct'] * (df['abgr_irrbb_stable'] + df['abgr_liquidity_stable']) +
        (1 - df['stability_pct']) * df['abgr_non_stable']
    )

    # Expected balance next period
    df['expected_balance_next_period'] = (
        df['balance'] *
        (1 - df['closure_rate'] / 12) *  # Monthly closure rate
        (1 + df['abgr_total'] / 12)      # Monthly ABGR
    )

    return df
```

---

**End of Document**

---

**Document Metadata:**
- **Version:** 1.0
- **Date:** January 31, 2026
- **Author:** Research synthesis from Moody's, Abrigo, Chen (2025)
- **Purpose:** Inform deposit beta model enhancements for cfo_banking_demo
- **Next Review:** Quarterly (April 30, 2026)
