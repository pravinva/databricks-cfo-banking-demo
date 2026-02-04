# Sample Questions for Genie Space

## Overview

Add these **26 sample questions** to your Genie Space to guide users on what they can ask.

**Space:** Treasury Modeling - Deposits & Fee Income
**Space ID:** 01f101adda151c09835a99254d4c308c

---

## How to Add Sample Questions

### Via Databricks UI (Recommended)

1. Open Databricks → **Genie** → "Treasury Modeling - Deposits & Fee Income"
2. Click **"Configure"** (top right)
3. Go to **"Sample questions"** tab
4. Click **"Add sample question"**
5. Copy-paste each question below
6. Click **"Save"**

---

## 📊 DEPOSIT BETA MODELING (6 questions)

These questions help users explore deposit rate sensitivity, at-risk accounts, and beta analysis.

```
What is the average deposit beta by relationship category?

Show me at-risk accounts for Strategic customers

What is the average rate gap by product type?

How many accounts are priced below market rate?

Show me the top 10 accounts by balance with high flight risk

What percentage of MMDA accounts are at-risk?
```

---

## 📈 VINTAGE ANALYSIS & RUNOFF FORECASTING (5 questions)

These questions demonstrate cohort survival rates and deposit runoff projections.

```
What is the 12-month survival rate for Tactical customers?

Show me the 3-year deposit runoff forecast by segment

What is the closure rate for Expendable customers?

Compare account survival rates across all relationship categories at 24 months

What is the projected balance for Strategic deposits in 36 months?
```

---

## ⚠️ CCAR STRESS TESTING (7 questions)

These questions cover regulatory stress testing, capital adequacy, and liquidity ratios.

```
What is the CET1 ratio under severely adverse scenario?

Show me NII impact across all stress test scenarios

Does the bank pass the CCAR stress test?

What is today's LCR ratio?

Show me HQLA composition by level

What is the stressed beta under adverse scenario?

Compare delta EVE across baseline, adverse, and severely adverse scenarios
```

---

## 💰 PPNR MODELING (5 questions)

These questions demonstrate PPNR forecasting, efficiency ratios, and fee income analysis.

```
What is the forecasted PPNR for next quarter?

Show me 9-quarter PPNR projections

What is the efficiency ratio trend over the next 2 years?

Compare net interest income vs non-interest income

What is the expected non-interest expense growth rate?
```

---

## 🔄 CROSS-DOMAIN COMPLEX QUERIES (3 questions)

These questions demonstrate how to combine data across multiple domains.

```
Show me the complete risk dashboard: at-risk deposits, runoff forecast, and CET1 ratio

What is the relationship between deposit beta and account survival rates?

How does PPNR vary across different stress scenarios?
```

---

## ✅ Complete List (Copy-Paste Format)

For quick copy-paste, here's all 26 questions in a single list:

```
What is the average deposit beta by relationship category?
Show me at-risk accounts for Strategic customers
What is the average rate gap by product type?
How many accounts are priced below market rate?
Show me the top 10 accounts by balance with high flight risk
What percentage of MMDA accounts are at-risk?
What is the 12-month survival rate for Tactical customers?
Show me the 3-year deposit runoff forecast by segment
What is the closure rate for Expendable customers?
Compare account survival rates across all relationship categories at 24 months
What is the projected balance for Strategic deposits in 36 months?
What is the CET1 ratio under severely adverse scenario?
Show me NII impact across all stress test scenarios
Does the bank pass the CCAR stress test?
What is today's LCR ratio?
Show me HQLA composition by level
What is the stressed beta under adverse scenario?
Compare delta EVE across baseline, adverse, and severely adverse scenarios
What is the forecasted PPNR for next quarter?
Show me 9-quarter PPNR projections
What is the efficiency ratio trend over the next 2 years?
Compare net interest income vs non-interest income
What is the expected non-interest expense growth rate?
Show me the complete risk dashboard: at-risk deposits, runoff forecast, and CET1 ratio
What is the relationship between deposit beta and account survival rates?
How does PPNR vary across different stress scenarios?
```

---

## 📋 Checklist

Track your progress as you add questions:

### Deposit Beta (6)
- [ ] What is the average deposit beta by relationship category?
- [ ] Show me at-risk accounts for Strategic customers
- [ ] What is the average rate gap by product type?
- [ ] How many accounts are priced below market rate?
- [ ] Show me the top 10 accounts by balance with high flight risk
- [ ] What percentage of MMDA accounts are at-risk?

### Vintage Analysis (5)
- [ ] What is the 12-month survival rate for Tactical customers?
- [ ] Show me the 3-year deposit runoff forecast by segment
- [ ] What is the closure rate for Expendable customers?
- [ ] Compare account survival rates across all relationship categories at 24 months
- [ ] What is the projected balance for Strategic deposits in 36 months?

### Stress Testing (7)
- [ ] What is the CET1 ratio under severely adverse scenario?
- [ ] Show me NII impact across all stress test scenarios
- [ ] Does the bank pass the CCAR stress test?
- [ ] What is today's LCR ratio?
- [ ] Show me HQLA composition by level
- [ ] What is the stressed beta under adverse scenario?
- [ ] Compare delta EVE across baseline, adverse, and severely adverse scenarios

### PPNR Forecasting (5)
- [ ] What is the forecasted PPNR for next quarter?
- [ ] Show me 9-quarter PPNR projections
- [ ] What is the efficiency ratio trend over the next 2 years?
- [ ] Compare net interest income vs non-interest income
- [ ] What is the expected non-interest expense growth rate?

### Cross-Domain (3)
- [ ] Show me the complete risk dashboard: at-risk deposits, runoff forecast, and CET1 ratio
- [ ] What is the relationship between deposit beta and account survival rates?
- [ ] How does PPNR vary across different stress scenarios?

**Progress: 0/26 complete**

---

## 🎯 Why These Questions?

### User Guidance
- Sample questions teach users what types of queries the space can handle
- Demonstrates natural language patterns that work well
- Covers all 4 modeling domains (Beta, Vintage, Stress, PPNR)

### Business Value
- **Deposit Beta:** Rate sensitivity and at-risk account identification
- **Vintage:** Long-term deposit stability and runoff projections
- **Stress Testing:** Regulatory compliance (CCAR)
- **PPNR:** Profitability forecasting and efficiency analysis

### Technical Coverage
- Simple aggregations ("What is the average...")
- Filtered queries ("Show me... for Strategic customers")
- Comparisons ("Compare... across...")
- Complex multi-table queries ("Show me the complete risk dashboard...")

---

## 🚀 After Adding

Once all sample questions are added:

1. **Test them** - Click each question to verify it generates correct SQL
2. **Train users** - Show team members where to find sample questions
3. **Monitor usage** - Track which questions users click most often
4. **Iterate** - Add more questions based on actual user needs

---

## 📚 Related Documentation

- **SQL Expressions:** See `SQL_EXPRESSIONS_TO_ADD.md` for measures, dimensions, and filters
- **Verified Queries:** See `VERIFIED_QUERIES.md` for tested SQL examples
- **Full Configuration:** See `GENIE_SPACE_CONFIGURATION.md` for complete setup

---

**Estimated Time to Add All 26:** ~10 minutes
**Source:** Curated from SAMPLE_QUERIES.md and VERIFIED_QUERIES.md
**Status:** ✅ Production-ready - Covers all 4 modeling domains

---

## 🏁 Summary

You have **26 sample questions** ready to add to your Genie Space:

- **6 questions** on Deposit Beta Modeling
- **5 questions** on Vintage Analysis & Runoff Forecasting
- **7 questions** on CCAR Stress Testing
- **5 questions** on PPNR Modeling
- **3 questions** on Cross-Domain Analysis

**These questions will help users discover what they can ask Genie! 🚀**
