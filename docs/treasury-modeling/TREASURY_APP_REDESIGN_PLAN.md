# Treasury Modeling App Redesign Plan

## Executive Summary

**Current State:** App shows comprehensive CFO banking features (loans, deposits, securities, GL, etc.)
**New Focus:** Treasury Modeling - Deposits & Fee Income
**Goal:** Create a focused, demo-ready app showcasing Phase 1, 2, 3 deposit models + PPNR

---

## What to KEEP (Core Treasury Features)

### ✅ 1. Deposit Portfolio Overview
**Current:** Mixed with loans/securities
**New:** Dedicated deposit portfolio view

**Show:**
- Total deposits by product type (MMDA, DDA, NOW, Savings)
- Current balances and stated rates
- Deposit composition pie chart
- Rate gap analysis (stated rate vs market rate)

**Data Source:** `bronze_core_banking.deposit_accounts`

---

### ✅ 2. Phase 1: Deposit Beta Dashboard
**Current:** `DepositBetaDashboard.tsx` component exists
**Status:** ✅ KEEP AS-IS (already perfect for treasury focus)

**Shows:**
- Portfolio beta metrics (avg beta, at-risk accounts)
- Beta distribution by product type and relationship category
- At-risk accounts table (priced below market)
- Rate shock scenario simulator

**Data Source:** `ml_models.deposit_beta_training_enhanced`

---

### ✅ 3. Phase 2: Vintage Analysis Dashboard
**Current:** `VintageAnalysisDashboard.tsx` component exists
**Status:** ✅ KEEP AS-IS (already perfect for treasury focus)

**Shows:**
- Component decay metrics (λ closure rate, g ABGR)
- Kaplan-Meier survival curves by relationship category
- 3-year runoff forecasts
- Decay matrix scatter plot

**Data Source:** `ml_models.component_decay_metrics`, `cohort_survival_rates`, `deposit_runoff_forecasts`

---

### ✅ 4. Phase 3: CCAR Stress Testing Dashboard
**Current:** `StressTestDashboard.tsx` component exists
**Status:** ✅ KEEP AS-IS (already perfect for treasury focus)

**Shows:**
- 5 regulatory KPIs (CET1, NII impact, deposit runoff, LCR)
- 9-quarter capital projections by scenario
- Dynamic beta curves (sigmoid function)
- Stress scenario summaries (Baseline, Adverse, Severely Adverse)

**Data Source:** `ml_models.dynamic_beta_parameters`, `stress_test_results`, `gold_regulatory.lcr_daily`

---

### ✅ 5. PPNR & Fee Income Dashboard (NEW)
**Current:** Does not exist
**Status:** 🆕 CREATE NEW COMPONENT

**Shows:**
- Current quarter PPNR KPI card
- PPNR components waterfall (NII + Non-Interest Income - Non-Interest Expense)
- 9-quarter PPNR projection by scenario
- Fee income trends over time
- Efficiency ratio trend

**Data Source:** `ml_models.ppnr_forecasts`, `non_interest_income_training_data`, `non_interest_expense_training_data`

---

### ✅ 6. Liquidity & Market Rates
**Current:** Yield curve chart, LCR waterfall
**Status:** ✅ KEEP (treasury operations need market context)

**Shows:**
- Current U.S. Treasury yield curve
- LCR waterfall chart
- Historical yield curve trends

**Data Source:** `silver_treasury.yield_curves`, `gold_regulatory.lcr_daily`

---

### ✅ 7. Claude AI Assistant
**Current:** Floating assistant with chat
**Status:** ✅ KEEP (already scoped to treasury modeling)

**Shows:**
- Natural language queries about deposits
- Phase 1, 2, 3 model questions
- PPNR forecasting queries

---

## What to REMOVE/HIDE (Out of Scope)

### ❌ 1. Loan Portfolio Section
**Current:** Shows loan breakdown by product type
**Why Remove:** Not part of treasury deposit modeling focus
**Exception:** Can mention loans only in context of fee income (origination fees)

**Action:**
- Remove `LoanTable` component
- Remove `LoanDetailPanel` component
- Remove loan portfolio breakdown from main page
- Remove "Recent Loan Originations" section

---

### ❌ 2. Securities Portfolio Section
**Current:** May show AFS/HTM securities
**Why Remove:** Explicitly out of scope (Nehal's directive)

**Action:**
- Remove securities breakdown if it exists
- Remove securities-related charts

---

### ❌ 3. Credit Risk Metrics
**Current:** NPL rates, CECL reserves, reserve ratios
**Why Remove:** Loan credit risk is out of scope

**Action:**
- Remove NPL rate cards
- Remove CECL reserve metrics
- Keep only deposit-related risk (LCR, deposit runoff)

---

### ❌ 4. General Ledger / Accounting Views
**Current:** May have GL transaction views
**Why Remove:** Not treasury modeling focus

**Action:**
- Remove GL transaction tables
- Remove accounting reconciliation views

---

## Recommended New App Structure

### Main Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  TREASURY MODELING DASHBOARD                                    │
│  Deposits & Fee Income Forecasting                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Top KPIs (4 cards)                                             │
├─────────────────────────────────────────────────────────────────┤
│  • Total Deposits: $125.4B                                      │
│  • Portfolio Avg Beta: 0.48                                     │
│  • Current LCR: 128.5% (✅ Above 100%)                          │
│  • PPNR (Current Quarter): $485M                                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Navigation Tabs                                                 │
├─────────────────────────────────────────────────────────────────┤
│  [Overview] [Deposit Beta] [Vintage Analysis] [CCAR Stress]    │
│  [PPNR & Fee Income] [Market Rates]                             │
└─────────────────────────────────────────────────────────────────┘

TAB 1: OVERVIEW
┌─────────────────────────────────────────────────────────────────┐
│  Left Column: Deposit Portfolio Breakdown                       │
│  - MMDA: $45.2B (36%)                                           │
│  - DDA: $38.7B (31%)                                            │
│  - NOW: $25.3B (20%)                                            │
│  - Savings: $16.2B (13%)                                        │
│                                                                  │
│  Right Column: Current Market Environment                        │
│  - Yield Curve Chart                                            │
│  - Fed Funds Rate: 5.50%                                        │
│  - 2Y Treasury: 4.82%                                           │
└─────────────────────────────────────────────────────────────────┘

TAB 2: DEPOSIT BETA (PHASE 1)
┌─────────────────────────────────────────────────────────────────┐
│  [Existing DepositBetaDashboard.tsx component]                  │
│  - Portfolio metrics                                             │
│  - Beta distribution charts                                      │
│  - At-risk accounts table                                        │
│  - Rate shock simulator                                          │
└─────────────────────────────────────────────────────────────────┘

TAB 3: VINTAGE ANALYSIS (PHASE 2)
┌─────────────────────────────────────────────────────────────────┐
│  [Existing VintageAnalysisDashboard.tsx component]              │
│  - Component decay metrics                                       │
│  - Kaplan-Meier survival curves                                  │
│  - 3-year runoff forecasts                                       │
│  - Decay matrix scatter plot                                     │
└─────────────────────────────────────────────────────────────────┘

TAB 4: CCAR STRESS TESTING (PHASE 3)
┌─────────────────────────────────────────────────────────────────┐
│  [Existing StressTestDashboard.tsx component]                   │
│  - 5 regulatory KPIs                                             │
│  - 9-quarter capital projections                                 │
│  - Dynamic beta curves                                           │
│  - Scenario summaries                                            │
└─────────────────────────────────────────────────────────────────┘

TAB 5: PPNR & FEE INCOME (NEW)
┌─────────────────────────────────────────────────────────────────┐
│  Top Row: KPI Cards                                              │
│  - Current Quarter PPNR: $485M                                   │
│  - Non-Interest Income: $145M                                    │
│  - Non-Interest Expense: $210M                                   │
│  - Efficiency Ratio: 58.2%                                       │
│                                                                  │
│  Middle Row: PPNR Components Waterfall                           │
│  [Chart showing: NII → + Non-II → - Non-IE → = PPNR]           │
│                                                                  │
│  Bottom Row: 9-Quarter Projections                               │
│  [Line chart: Baseline, Adverse, Severely Adverse scenarios]    │
└─────────────────────────────────────────────────────────────────┘

TAB 6: MARKET RATES
┌─────────────────────────────────────────────────────────────────┐
│  Left: Current Yield Curve                                       │
│  [Chart showing 3M, 2Y, 5Y, 10Y, 30Y yields]                    │
│                                                                  │
│  Right: Historical Trends                                        │
│  [Time series of yield curve changes]                           │
│                                                                  │
│  Bottom: LCR Waterfall                                           │
│  [HQLA → Net Outflows → LCR Ratio]                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Remove Out-of-Scope Features (1-2 hours)

**Files to Modify:**
1. `frontend_app/app/page.tsx`
   - Remove loan portfolio breakdown section
   - Remove securities portfolio section
   - Remove credit risk metrics (NPL, CECL)
   - Keep only deposit portfolio breakdown

2. Update tab navigation:
   ```typescript
   // OLD:
   <TabsTrigger value="portfolio">Portfolio Analysis</TabsTrigger>
   <TabsTrigger value="risk">Risk Analysis</TabsTrigger>

   // NEW:
   <TabsTrigger value="overview">Deposit Portfolio</TabsTrigger>
   <TabsTrigger value="deposit-beta">Deposit Beta (Phase 1)</TabsTrigger>
   <TabsTrigger value="vintage">Vintage Analysis (Phase 2)</TabsTrigger>
   <TabsTrigger value="stress">CCAR Stress Testing (Phase 3)</TabsTrigger>
   <TabsTrigger value="ppnr">PPNR & Fee Income</TabsTrigger>
   <TabsTrigger value="market">Market Rates</TabsTrigger>
   ```

3. Remove components:
   - Comment out or remove `<LoanTable />` imports
   - Comment out or remove `<LoanDetailPanel />` imports
   - Remove loan-related API calls

---

### Phase 2: Create PPNR Dashboard Component (2-3 hours)

**New File:** `frontend_app/components/treasury/PPNRDashboard.tsx`

```typescript
'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { TrendingUp, DollarSign, TrendingDown } from 'lucide-react'

export default function PPNRDashboard() {
  const [ppnrData, setPpnrData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchPPNRData()
  }, [])

  const fetchPPNRData = async () => {
    try {
      const res = await fetch('/api/ppnr/current-quarter')
      const result = await res.json()
      if (result.success) {
        setPpnrData(result.data)
      }
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch PPNR data:', error)
      setLoading(false)
    }
  }

  if (loading) {
    return <div>Loading PPNR data...</div>
  }

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Current Quarter PPNR</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${ppnrData?.ppnr_millions}M</div>
            <div className="text-xs text-green-600">+8.3% YoY</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Non-Interest Income</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${ppnrData?.noninterest_income_millions}M</div>
            <div className="text-xs text-green-600">+5.2% YoY</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Non-Interest Expense</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${ppnrData?.noninterest_expense_millions}M</div>
            <div className="text-xs text-red-600">+3.1% YoY</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Efficiency Ratio</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{ppnrData?.efficiency_ratio_pct}%</div>
            <div className="text-xs text-green-600">Improving</div>
          </CardContent>
        </Card>
      </div>

      {/* PPNR Components Waterfall */}
      <Card>
        <CardHeader>
          <CardTitle>PPNR Components Waterfall</CardTitle>
        </CardHeader>
        <CardContent>
          {/* Add waterfall chart here */}
          <div className="h-64 bg-slate-50 flex items-center justify-center">
            Waterfall Chart: NII + Non-Interest Income - Non-Interest Expense = PPNR
          </div>
        </CardContent>
      </Card>

      {/* 9-Quarter Projections */}
      <Card>
        <CardHeader>
          <CardTitle>9-Quarter PPNR Projections by Scenario</CardTitle>
        </CardHeader>
        <CardContent>
          {/* Add line chart here */}
          <div className="h-64 bg-slate-50 flex items-center justify-center">
            Line Chart: Baseline, Adverse, Severely Adverse scenarios
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
```

**Backend API Endpoint Needed:**
- `GET /api/ppnr/current-quarter` - Returns current quarter PPNR metrics
- `GET /api/ppnr/forecasts` - Returns 9-quarter projections by scenario
- `GET /api/ppnr/components` - Returns NII, Non-Interest Income, Non-Interest Expense breakdown

---

### Phase 3: Update Top KPIs (30 minutes)

**Current KPIs (TO REMOVE):**
- Total Assets (not treasury-specific)
- NPL Rate (loan credit risk)
- CECL Reserves (loan credit risk)

**New KPIs (TREASURY-FOCUSED):**
```typescript
const treasuryKPIs = [
  {
    title: 'Total Deposits',
    value: '$125.4B',
    change: '+2.3%',
    icon: DollarSign,
    source: 'bronze_core_banking.deposit_accounts'
  },
  {
    title: 'Portfolio Avg Beta',
    value: '0.48',
    change: '-0.02 (less sensitive)',
    icon: Activity,
    source: 'ml_models.deposit_beta_training_enhanced'
  },
  {
    title: 'Current LCR',
    value: '128.5%',
    change: '✅ Above 100%',
    icon: Shield,
    source: 'gold_regulatory.lcr_daily'
  },
  {
    title: 'PPNR (Current Quarter)',
    value: '$485M',
    change: '+8.3% YoY',
    icon: TrendingUp,
    source: 'ml_models.ppnr_forecasts'
  }
]
```

---

### Phase 4: Update Page Title & Branding (15 minutes)

**Current:**
```typescript
<h1>CFO Banking Dashboard</h1>
<p>Comprehensive financial analytics and reporting</p>
```

**New:**
```typescript
<h1>Treasury Modeling Dashboard</h1>
<p>Deposit Modeling & Fee Income Forecasting</p>
```

---

### Phase 5: Test & Validate (1 hour)

**Test Scenarios:**
1. ✅ All 3 existing treasury dashboards (Deposit Beta, Vintage, Stress Test) still work
2. ✅ New PPNR dashboard loads and displays data correctly
3. ✅ Loan/securities sections are hidden
4. ✅ Claude AI assistant responds to treasury-focused queries
5. ✅ Navigation between tabs works smoothly
6. ✅ Data source tooltips show correct Unity Catalog tables

---

## Backend API Changes Needed

### New Endpoints to Create:

1. **GET /api/ppnr/current-quarter**
   - Query: `SELECT * FROM ml_models.ppnr_forecasts WHERE scenario = 'Baseline' AND forecast_horizon_months = 3 ORDER BY forecast_date DESC LIMIT 1`
   - Returns: Current quarter PPNR metrics

2. **GET /api/ppnr/forecasts**
   - Query: `SELECT * FROM ml_models.ppnr_forecasts WHERE forecast_date = (SELECT MAX(forecast_date) FROM ml_models.ppnr_forecasts) ORDER BY scenario, forecast_horizon_months`
   - Returns: 9-quarter projections for all scenarios

3. **GET /api/ppnr/components**
   - Query: Aggregate NII, Non-Interest Income, Non-Interest Expense from training tables
   - Returns: Components waterfall data

---

## Expected Demo Flow

**1. Start on Overview Tab:**
- Show total deposits breakdown by product type
- Highlight deposit composition
- Show current market rates context

**2. Navigate to Deposit Beta (Phase 1):**
- "Our Phase 1 model predicts deposit rate sensitivity with 7.2% MAPE"
- Show beta distribution by product
- Identify at-risk accounts priced below market

**3. Navigate to Vintage Analysis (Phase 2):**
- "Using Chen Component Decay Model and Kaplan-Meier survival curves"
- Show λ closure rates and g ABGR by relationship category
- Demonstrate 3-year runoff forecasts

**4. Navigate to CCAR Stress Testing (Phase 3):**
- "We use dynamic beta curves for regulatory stress testing"
- Show 9-quarter capital projections under 3 scenarios
- Highlight CET1 ratio (must be ≥7.0% to pass)

**5. Navigate to PPNR & Fee Income:**
- "PPNR forecasting focuses on fee income driven by deposit relationships"
- Show current quarter PPNR KPIs
- Demonstrate 9-quarter projections by scenario

**6. Use Claude AI Assistant:**
- Ask: "What is the forecasted PPNR under adverse scenario?"
- Ask: "Show me at-risk Strategic customer deposits"
- Ask: "What is the 3-year runoff forecast for MMDA accounts?"

---

## Files to Modify

### High Priority:
1. ✅ `frontend_app/app/page.tsx` - Main dashboard page
2. 🆕 `frontend_app/components/treasury/PPNRDashboard.tsx` - New component
3. ✅ `backend/main.py` - Add PPNR API endpoints

### Medium Priority:
4. ✅ `frontend_app/components/MetricCard.tsx` - Update KPI cards
5. ✅ `frontend_app/app/layout.tsx` - Update page title

### Low Priority:
6. Update any navigation menus
7. Update README with new focus

---

## Timeline

**Total Estimated Time:** 5-7 hours

- Phase 1 (Remove out-of-scope): 1-2 hours
- Phase 2 (Create PPNR dashboard): 2-3 hours
- Phase 3 (Update KPIs): 30 minutes
- Phase 4 (Branding): 15 minutes
- Phase 5 (Testing): 1 hour

---

## Success Criteria

✅ App shows ONLY treasury modeling features (deposits, not loans)
✅ All 3 existing treasury dashboards (Phase 1, 2, 3) work perfectly
✅ New PPNR dashboard displays fee income forecasts
✅ Top KPIs are treasury-focused (deposits, beta, LCR, PPNR)
✅ No loan portfolio or securities references visible
✅ Claude AI assistant scoped to treasury queries
✅ Demo flow tells a cohesive treasury modeling story

---

**Document Created:** February 4, 2026
**Status:** Ready for Implementation
