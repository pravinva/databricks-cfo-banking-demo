# Report Generator Analysis

## File: `../../notebooks/Generate_Deposit_Analytics_Report.py`

**Status:** ✅ **PERFECTLY ALIGNED** - No changes needed!

---

## Current Scope

The report generator notebook is **already 100% focused on deposits and treasury modeling**. It generates comprehensive reports covering:

### Report Sections:
1. **Executive Summary** - Key deposit metrics and findings
2. **Portfolio Composition** - Current deposit mix and characteristics
3. **Deposit Beta Analysis** - Rate sensitivity by product type (Approach 1)
4. **Rate Shock Scenarios** - Impact of +100bps, +200bps, +300bps shocks
5. **Deposit Runoff Projections** - Expected outflows under stress
6. **Vintage Analysis** - Cohort retention and decay patterns (Approach 2)
7. **Recommendations** - Strategic insights and action items

### Data Sources Used:
✅ `silver_treasury.deposit_portfolio` - Deposit portfolio data
✅ `ml_models.deposit_beta_predictions` - Approach 1 deposit beta predictions
✅ `ml_models.cohort_survival_rates` - Approach 2 vintage analysis
✅ `ml_models.stress_test_results` - Approach 3 stress testing

---

## What's Great About This Notebook

### ✅ 1. Deposit-Focused
- **No loan references** - Exclusively focused on deposits
- **No investment portfolio** - Out of scope
- **Treasury operations** - Rate sensitivity, runoff, stress testing

### ✅ 2. Covers All 3 Approaches
- **Approach 1: Deposit Beta** - Rate sensitivity analysis
- **Approach 2: Vintage Analysis** - Cohort survival and decay
- **Approach 3: Stress Testing** - CCAR scenarios (if data available)

### ✅ 3. Use Cases Perfectly Aligned
From the notebook (lines 20-24):
```
Use Cases:
- ALCO presentations
- Regulatory reporting (CCAR-style stress testing)
- Executive briefings
- Board presentations
```

These are **exactly** the use cases for Treasury Modeling!

### ✅ 4. Output Formats
- HTML report (saved to DBFS)
- Delta table (for dashboard integration)
- PDF export (optional)

Perfect for treasury teams to share with stakeholders.

### ✅ 5. Key Metrics Calculated
```python
# Lines 115-149
report_date = datetime.now()
total_deposits = deposits_pdf['current_balance'].sum()
weighted_avg_rate = (deposits_pdf['current_balance'] * deposits_pdf['stated_rate']).sum() / total_deposits
portfolio_beta = (beta_predictions_pdf['current_balance'] * beta_predictions_pdf['predicted_beta']).sum() / total_deposits
```

All deposit-centric, treasury-focused metrics.

---

## Minor Enhancement Opportunity (Optional)

### Could Add: PPNR Section

**Current Sections:** 7 sections covering deposit beta, vintage, stress testing
**Missing:** PPNR & Fee Income analysis

**Potential Enhancement:**
Add an 8th section: "PPNR & Fee Income Projections"

**What It Would Show:**
- Current quarter PPNR
- Non-interest income trends
- Non-interest expense trends
- 9-quarter PPNR forecasts by scenario
- Efficiency ratio analysis

**Data Source:**
- `ml_models.ppnr_forecasts`
- `ml_models.non_interest_income_training_data`
- `ml_models.non_interest_expense_training_data`

**Code to Add (Lines 300+):**
```python
# MAGIC %md
# MAGIC ## Section 8: PPNR & Fee Income Analysis

# Load PPNR forecasts
try:
    ppnr_df = spark.table("cfo_banking_demo.ml_models.ppnr_forecasts")
    ppnr_pdf = ppnr_df.toPandas()
    has_ppnr = True

    # Current quarter PPNR
    current_ppnr = ppnr_pdf[
        (ppnr_pdf['scenario'] == 'Baseline') &
        (ppnr_pdf['forecast_horizon_months'] == 3)
    ].iloc[0]

    print(f"Current Quarter PPNR: ${current_ppnr['forecasted_ppnr']/1e6:.1f}M")
    print(f"  - Net Interest Income: ${current_ppnr['forecasted_nii']/1e6:.1f}M")
    print(f"  - Non-Interest Income: ${current_ppnr['forecasted_noninterest_income']/1e6:.1f}M")
    print(f"  - Non-Interest Expense: ${current_ppnr['forecasted_noninterest_expense']/1e6:.1f}M")

    # Calculate efficiency ratio
    efficiency_ratio = (
        current_ppnr['forecasted_noninterest_expense'] /
        (current_ppnr['forecasted_nii'] + current_ppnr['forecasted_noninterest_income'])
    ) * 100
    print(f"Efficiency Ratio: {efficiency_ratio:.1f}%")

except Exception as e:
    print(f"⚠️ Warning: Could not load PPNR data: {e}")
    has_ppnr = False
```

---

## Terminology Update Needed

### Minor Fix: CCAR/DFAST Reference

**Line 22:**
```python
# Current:
- Regulatory reporting (CCAR-style stress testing)

# Should be:
- Regulatory reporting (CCAR Stress Testing)
```

**Why:** DFAST is legacy terminology. Prefer "CCAR stress testing" or "Stress Testing"

**Impact:** Very minor - just a comment update

---

## Recommendation

### ✅ KEEP AS-IS (with optional enhancements)

**Current State:** 9.5/10 - Excellent alignment with Treasury Modeling focus

**Required Changes:** None (it's already perfect for the scope)

**Optional Enhancements:**
1. Add PPNR section (Section 8) - if you want comprehensive treasury reporting
2. Update CCAR/DFAST terminology in comments (lines 22) - minor fix

**Effort Required:**
- No changes: 0 hours
- Add PPNR section: 1-2 hours
- Fix terminology: 5 minutes

---

## How It Fits in Treasury Modeling Demo

### Perfect for Demo Scenarios:

**Scenario 1: ALCO Presentation**
"Let me generate a comprehensive deposit analytics report for this month's ALCO meeting..."
- Run notebook
- Generate HTML report with all 7 sections
- Show executive summary, beta analysis, vintage forecasts

**Scenario 2: Board Presentation**
"The board wants to understand our deposit portfolio's rate sensitivity..."
- Run notebook
- Focus on Section 3: Deposit Beta Analysis
- Show rate shock scenarios (+100, +200, +300 bps)

**Scenario 3: CCAR Submission**
"We need to document our stress testing methodology for regulators..."
- Run notebook
- Include all sections
- Export to PDF for regulatory submission

**Scenario 4: Executive Briefing**
"CFO wants a quick update on deposit runoff risk..."
- Run notebook
- Focus on Section 6: Vintage Analysis
- Show 3-year runoff projections

---

## Integration with Other Components

### Works Perfectly With:

1. **Batch Inference Notebook** (`Batch_Inference_Deposit_Beta_Model.py`)
   - Batch inference creates `ml_models.deposit_beta_predictions`
   - Report generator reads those predictions
   - Perfect pipeline: Inference → Report

2. **Approach 2 Vintage Analysis**
   - Report reads `ml_models.cohort_survival_rates`
   - Displays Kaplan-Meier curves and decay metrics

3. **Approach 3 Stress Testing**
   - Report reads `ml_models.stress_test_results`
   - Shows CCAR scenario outcomes

4. **Frontend Dashboard**
   - Report can save outputs to Delta tables
   - Dashboard can display report metrics

---

## Sample Output Structure

```
DEPOSIT ANALYTICS REPORT
Generated: February 4, 2026

═══════════════════════════════════════════════════════════════
EXECUTIVE SUMMARY
═══════════════════════════════════════════════════════════════
Total Deposits: $125.4B
Weighted Average Rate: 3.85%
Portfolio Beta: 0.48
Top Product: MMDA ($45.2B, 36%)

═══════════════════════════════════════════════════════════════
PORTFOLIO COMPOSITION
═══════════════════════════════════════════════════════════════
[Pie Chart: Product Mix]
- MMDA: 36%
- DDA: 31%
- NOW: 20%
- Savings: 13%

═══════════════════════════════════════════════════════════════
DEPOSIT BETA ANALYSIS (APPROACH 1)
═══════════════════════════════════════════════════════════════
[Chart: Beta Distribution by Product Type]
MMDA: 0.35 (least sensitive)
NOW: 0.48
Savings: 0.62
DDA: 0.72 (most sensitive)

Model Accuracy: MAPE 7.2%

═══════════════════════════════════════════════════════════════
RATE SHOCK SCENARIOS
═══════════════════════════════════════════════════════════════
+100 bps shock: $6.2B runoff (4.9% of portfolio)
+200 bps shock: $11.8B runoff (9.4% of portfolio)
+300 bps shock: $16.3B runoff (13.0% of portfolio)

═══════════════════════════════════════════════════════════════
DEPOSIT RUNOFF PROJECTIONS
═══════════════════════════════════════════════════════════════
[Chart: Expected Runoff by Rate Scenario]

═══════════════════════════════════════════════════════════════
VINTAGE ANALYSIS (APPROACH 2)
═══════════════════════════════════════════════════════════════
[Chart: Kaplan-Meier Survival Curves]
Strategic customers: λ=0.05 (5% closure rate)
Tactical customers: λ=0.12 (12% closure rate)
Expendable customers: λ=0.25 (25% closure rate)

3-Year Runoff Forecast:
- Strategic: -8% balance erosion
- Tactical: -18% balance erosion
- Expendable: -35% balance erosion

═══════════════════════════════════════════════════════════════
RECOMMENDATIONS
═══════════════════════════════════════════════════════════════
1. Focus retention efforts on Strategic customers (sticky deposits)
2. Consider rate increases for at-risk Expendable deposits
3. Monitor beta changes as Fed raises rates
4. Implement deposit runoff contingency funding plan
```

---

## Conclusion

**Status:** ✅ **PERFECTLY ALIGNED**

The `Generate_Deposit_Analytics_Report.py` notebook is:
- 100% deposit-focused (no loan portfolio, no investment portfolio)
- Covers all 3 phases (Beta, Vintage, Stress Testing)
- Uses correct data sources (ml_models tables)
- Perfect for treasury team use cases (ALCO, Board, CCAR)
- Already produces comprehensive reports

**No changes required** - this notebook is a showcase example of Treasury Modeling reporting!

**Optional Enhancement:** Add PPNR section (Section 8) to make it even more comprehensive, but it's already excellent as-is.

---

**Analysis Date:** February 4, 2026
**Status:** Ready for Treasury Modeling Demos
