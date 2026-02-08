# Stress Testing Terminology - Important Clarifications

## Overview

This document clarifies terminology used in the CFO Banking Demo related to regulatory stress testing, CCAR, and DFAST.

---

## Key Terms

### Stress Testing (Broad Term)
**Definition:** A broader risk management practice where banks test their balance sheets against adverse scenarios.

**Scope:**
- Internal stress tests (bank-defined scenarios)
- Regulatory stress tests (supervisor-defined scenarios)
- IRRBB (Interest Rate Risk in the Banking Book) stress testing
- Liquidity stress testing
- Credit stress testing

**Use in this demo:** We use "stress testing" as a general term for testing deposits, capital, and PPNR under adverse rate scenarios.

---

### CCAR (Comprehensive Capital Analysis and Review)
**Definition:** The Federal Reserve's regulatory framework for evaluating large banks' capital adequacy and planning processes.

**Key Details:**
- **Regulated by:** Federal Reserve
- **Applies to:** Bank holding companies with $100B+ in assets
- **Frequency:** Annual
- **Requirements:**
  - 9-quarter capital projections under multiple scenarios
  - Baseline, Adverse, and Severely Adverse scenarios
  - Capital actions (dividends, buybacks) must be approved
  - CET1 ratio must remain ≥ 7.0% under stress

**Scenarios:**
- **Baseline:** Most likely economic path
- **Adverse:** Moderate recession (+200 bps rate shock)
- **Severely Adverse:** Severe recession (+300 bps rate shock)

**Components tested:**
- **Capital ratios:** CET1, Tier 1, Total Capital
- **PPNR:** Pre-Provision Net Revenue projections
- **Credit losses:** Loan loss provisions
- **RWA:** Risk-Weighted Assets
- **Trading/Counterparty losses:** For large trading banks

**Use in this demo:** Our stress test tables (`stress_test_results`) follow CCAR framework with 9-quarter projections.

---

### DFAST (Dodd-Frank Act Stress Testing)
**Status:** ⚠️ **DEPRECATED** - Regulation has been sunset

**Historical Context:**
- **Enacted:** 2010 (Dodd-Frank Wall Street Reform Act)
- **Purpose:** Required banks to conduct annual stress tests
- **Applied to:** Banks with $10B-$100B in assets (mid-tier banks)
- **Sunset:** Economic Growth, Regulatory Relief, and Consumer Protection Act (2018) raised threshold to $100B, effectively ending DFAST for most banks

**Why mentioned historically:**
- DFAST was the underlying regulation that mandated stress testing
- CCAR was the Fed's implementation of DFAST requirements for large banks
- The terms were often used interchangeably (incorrectly)

**Correct usage today:**
- ✅ "CCAR stress testing"
- ✅ "Regulatory stress testing per CCAR framework"
- ❌ "DFAST" (regulation no longer applies)
- ❌ "CCAR/DFAST" (DFAST is deprecated)

---

## Usage in This Demo

### Approach 3: Dynamic Beta and Stress Testing
**Notebook:** `Approach3_Dynamic_Beta_and_Stress_Testing.py`

**What it does:**
- Tests deposit beta sensitivity under rate shocks
- Projects CET1 ratios over 9 quarters
- Calculates Economic Value of Equity (EVE) impact
- Follows CCAR scenario structure (Baseline, Adverse, Severely Adverse)

**Regulatory alignment:**
- ✅ Scenarios match CCAR framework
- ✅ 9-quarter projection horizon (CCAR requirement)
- ✅ CET1 ratio pass/fail threshold (7.0%)
- ⚠️ Note: Full CCAR includes credit losses, trading losses, and operational risk (not all modeled in this demo)

### PPNR Modeling
**Notebook:** `Train_PPNR_Models.py`

**What it does:**
- Forecasts Net Interest Income (NII)
- Forecasts Non-Interest Income (fee income)
- Forecasts Non-Interest Expense (operating costs)
- Calculates PPNR = NII + Non-Interest Income - Non-Interest Expense

**Regulatory context:**
- PPNR is a **component** of CCAR stress testing
- Banks must project PPNR under each scenario
- PPNR projections feed into capital ratio calculations
- PPNR = revenue available to absorb credit losses before impacting capital

**Use in stress testing:**
```
Capital Ratio = Capital / Risk-Weighted Assets

Where Capital is impacted by:
+ Beginning Capital
+ PPNR (revenue generation)
- Credit Losses (loan loss provisions)
- Operational Losses
± Trading/Counterparty Gains or Losses
- Capital Actions (dividends, buybacks)
```

---

## Correct Terminology Guide

### ✅ Correct Usage

| Scenario | Say This |
|----------|----------|
| Referring to regulatory stress testing | "CCAR stress testing" or "regulatory stress testing" |
| Describing PPNR role | "PPNR is a key component of CCAR stress testing" |
| Mentioning scenarios | "Baseline, Adverse, and Severely Adverse scenarios (per CCAR)" |
| Historical context | "DFAST regulation (now deprecated) established stress testing requirements" |
| General stress testing | "Stress testing" or "scenario analysis" |

### ❌ Incorrect Usage

| Don't Say | Problem | Say Instead |
|-----------|---------|-------------|
| "CCAR/DFAST stress testing" | DFAST is deprecated | "CCAR stress testing" |
| "DFAST scenarios" | DFAST no longer applies | "CCAR scenarios" |
| "PPNR stress testing" | PPNR is an input, not the test itself | "CCAR stress testing (includes PPNR projections)" |
| "CCAR and PPNR are separate" | They're related, not separate | "PPNR is a component of CCAR" |

---

## Relationship Diagram

```
┌────────────────────────────────────────────────────────────┐
│                  CCAR STRESS TESTING                       │
│          (Comprehensive Regulatory Framework)              │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────┐  ┌───────────────────────────┐ │
│  │   PPNR PROJECTIONS   │  │  CREDIT LOSS PROJECTIONS  │ │
│  │  (9 quarters ahead)  │  │   (Loan loss provisions)  │ │
│  └──────────────────────┘  └───────────────────────────┘ │
│            ↓                            ↓                 │
│  ┌────────────────────────────────────────────────────┐  │
│  │        CAPITAL RATIO PROJECTIONS                   │  │
│  │  (CET1, Tier 1, Total Capital under stress)      │  │
│  └────────────────────────────────────────────────────┘  │
│            ↓                                              │
│  ┌────────────────────────────────────────────────────┐  │
│  │    PASS/FAIL DETERMINATION                         │  │
│  │    (CET1 must remain ≥ 7.0% to pass)              │  │
│  └────────────────────────────────────────────────────┘  │
│                                                            │
│  Applied to 3 scenarios:                                  │
│  - Baseline                                               │
│  - Adverse                                                │
│  - Severely Adverse                                       │
└────────────────────────────────────────────────────────────┘
```

---

## Demo Scope vs Full CCAR

### What This Demo Includes ✅
- PPNR projections (NII, Non-Interest Income, Expenses)
- Deposit beta stress testing (rate shock scenarios)
- CET1 ratio tracking under stress
- 9-quarter projection horizon
- Baseline, Adverse, Severely Adverse scenarios

### What Full CCAR Additionally Requires (Not in Demo) ⚠️
- Credit loss provisioning (CECL methodology)
- Trading book losses (for banks with significant trading)
- Operational risk losses
- Counterparty credit risk
- Capital action planning (dividends, buybacks)
- Qualitative assessment (governance, risk management)

---

## Summary

**Key Takeaways:**
1. **CCAR** is the current regulatory framework for stress testing large banks
2. **DFAST** was the underlying regulation, now deprecated (threshold raised to $100B+)
3. **PPNR** is a **component** of CCAR stress testing, not a separate stress test
4. **Stress testing** (broad term) encompasses CCAR and other internal/regulatory tests
5. Use **"CCAR stress testing"** or **"regulatory stress testing"** in documentation

**When discussing this demo:**
- ✅ "This demo shows PPNR modeling for CCAR stress testing"
- ✅ "Approach 3 demonstrates deposit beta sensitivity under CCAR scenarios"
- ✅ "We project CET1 ratios following CCAR framework"
- ❌ "This is a CCAR/DFAST demo" (DFAST is deprecated)
- ❌ "PPNR stress testing" (PPNR is an input, not the test itself)

---

**Last Updated:** February 2026
**Status:** ✅ All documentation updated with correct terminology
