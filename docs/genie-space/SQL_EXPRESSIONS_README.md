# SQL Expressions for Genie Space - README

## 📁 Files Created

This folder contains complete documentation for adding SQL expressions and sample questions to your Genie Space:

### 1. **SQL_EXPRESSIONS_TO_ADD.md** (MAIN GUIDE)
- **Purpose:** Complete detailed guide with full explanations
- **Use When:** You need detailed context and understanding
- **Contains:**
  - Full instructions for each expression
  - Detailed business logic explanations
  - Testing guidance
  - 23 total expressions (11 measures, 6 dimensions, 6 filters)

### 2. **SQL_EXPRESSIONS_QUICK_ADD.md** (QUICK REFERENCE)
- **Purpose:** Fast copy-paste guide for adding expressions
- **Use When:** You're actively adding expressions in the UI
- **Contains:**
  - Condensed format optimized for copy-paste
  - Checklist to track progress
  - All 23 expressions in compact format
  - **Estimated time:** 15-20 minutes

### 3. **SAMPLE_QUESTIONS_TO_ADD.md** (SAMPLE QUESTIONS)
- **Purpose:** 26 sample questions to guide users
- **Use When:** Setting up Genie Space for the first time
- **Contains:**
  - 26 curated questions across all 4 domains
  - Organized by: Deposit Beta, Vintage, Stress Testing, PPNR
  - Copy-paste format for quick data entry
  - **Estimated time:** 10 minutes

### 4. **VERIFIED_QUERIES.md** (TESTING REFERENCE)
- **Purpose:** SQL query examples with actual test results
- **Use When:** You want to verify expressions work correctly
- **Contains:**
  - Verified queries tested against production data (Jan 2026)
  - Sample results
  - Common patterns and formulas

---

## 🎯 Quick Start

**To complete your Genie Space setup:**

### Step 1: Add SQL Expressions (~20 minutes)
1. **Open** `SQL_EXPRESSIONS_QUICK_ADD.md`
2. **Navigate** to Databricks → Genie → "Treasury Modeling - Deposits & Fee Income"
3. **Click** "Configure" → "Instructions" tab → "SQL Expressions" section
4. **Add** all 23 expressions using copy-paste from the quick guide

### Step 2: Add Sample Questions (~10 minutes)
1. **Open** `SAMPLE_QUESTIONS_TO_ADD.md`
2. **Navigate** to Databricks → Genie → "Treasury Modeling - Deposits & Fee Income"
3. **Click** "Configure" → "Sample questions" tab
4. **Add** all 26 questions using copy-paste from the guide

**Total time:** ~30 minutes

---

## 📊 What's Included

### Measures (11)
Aggregations and calculations for metrics:
- Total Account Count
- Total Balance (Millions)
- Average Deposit Beta ⭐
- Average Interest Rate
- At-Risk Account Count ⭐
- At-Risk Percentage ⭐
- Critical Risk Count
- Balance in Billions
- Runoff Percentage
- Efficiency Ratio
- LCR Ratio ⭐

⭐ = Most frequently used

### Dimensions (6)
Categorizations for grouping and analysis:
- Risk Level Category ⭐
- Balance Tier
- Beta Sensitivity Category ⭐
- Capital Adequacy Status
- LCR Compliance Status
- Balance in Millions

### Filters (6)
Common WHERE clause conditions:
- Latest Data Only ⭐
- Active Accounts Only ⭐
- Strategic Customers
- At-Risk Accounts ⭐
- High Balance Accounts
- Below Market Rate

---

## ✅ Verification Status

**All 23 expressions have been:**
- ✅ Tested against actual production data (January 2026)
- ✅ Verified to return correct results
- ✅ Documented with sample queries in VERIFIED_QUERIES.md
- ✅ Aligned with business requirements in GENIE_SPACE_CONFIGURATION.md

**Data source:** `cfo_banking_demo` catalog
**Test date:** January 2026
**Total accounts tested:** 402,000
**Status:** Production-ready

---

## 🔧 Technical Details

### Expression Structure

Each expression requires 4 fields in Databricks UI:

1. **Name** - Display name (e.g., "Average Deposit Beta")
2. **Code** - SQL expression (e.g., `ROUND(AVG(target_beta), 3)`)
3. **Instructions** - Business context and usage guidance
4. **Synonyms** - Alternative names for natural language matching

### Expression Types

| Type | Databricks UI | Purpose | Example |
|------|---------------|---------|---------|
| **Measure** | "Measure" | Aggregations across rows | `SUM(balance_millions)` |
| **Dimension** | "Dimension" | Derived columns for grouping | `CASE WHEN ... END` |
| **Filter** | "Filter" | WHERE clause conditions | `is_current = TRUE` |

---

## 🚀 Testing Your Expressions

After adding all expressions, test with these queries in Genie:

### Basic Tests
```
"What is the average deposit beta?"
"Show me total account count"
"What is the at-risk percentage?"
```

### Dimension Tests
```
"Show me accounts by risk level category"
"Group accounts by balance tier"
"What is the capital adequacy status?"
```

### Filter Tests
```
"Show me at-risk accounts only"
"Filter to strategic customers"
"Use latest data only"
```

### Combined Tests
```
"Show me at-risk Strategic customers by risk level category"
"What is the average beta for high balance accounts?"
"Show efficiency ratio for latest data only"
```

---

## 📚 Related Documentation

### In This Folder
- `GENIE_SPACE_CONFIGURATION.md` - Complete Genie Space setup guide
- `GENIE_INSTRUCTIONS_SHORT.md` - Shortened instructions for space
- `SAMPLE_QUERIES.md` - Sample queries across all tables
- `VERIFIED_QUERIES.md` - Tested queries with results
- `QUICK_START_GENIE.md` - 5-minute setup guide

### In Root Folder
- `../scripts/genie_table_comments.sql` - All table and column comments (217 SQL statements)
- `../scripts/update_genie_table_comments.py` - Script to generate table comments

---

## 🤝 Support

**For questions or issues:**
1. Check `VERIFIED_QUERIES.md` for working query examples
2. Review `GENIE_SPACE_CONFIGURATION.md` for full context
3. Test expressions individually before combining

**Common Issues:**
- **Expression not recognized:** Check synonyms match user's natural language
- **SQL error:** Verify column names match actual table schema
- **No results:** Ensure correct table is referenced in query

---

## 📈 Next Steps After Adding

1. ✅ **Test all expressions** with sample queries
2. ✅ **Train users** on new natural language capabilities
3. ✅ **Monitor usage** to identify most valuable expressions
4. ✅ **Iterate** - Add more expressions based on user needs
5. ✅ **Document** - Keep VERIFIED_QUERIES.md updated with new patterns

---

## 🎓 Best Practices

### When to Add More Expressions

Add new SQL expressions when you notice:
- Users repeatedly asking similar questions
- Complex SQL patterns being generated incorrectly
- Business terms not being understood by Genie

### Expression Design Guidelines

1. **Name:** Clear, concise, matches business terminology
2. **Code:** Efficient SQL, handles NULLs gracefully
3. **Instructions:** Explain when/how to use, include context
4. **Synonyms:** Add all variations users might say

### Maintenance

- **Review quarterly:** Are expressions still relevant?
- **Update synonyms:** Based on actual user queries
- **Deprecate unused:** Remove expressions with <1% usage
- **Add new:** Based on user feedback and query patterns

---

**Last Updated:** January 2026
**Status:** ✅ Production-ready - All expressions tested and verified
**Genie Space:** Treasury Modeling - Deposits & Fee Income
**Space ID:** 01f101adda151c09835a99254d4c308c

---

## 🏁 Summary

You now have **23 production-ready SQL expressions** to add to your Genie Space:

- **11 Measures** for aggregations and calculations
- **6 Dimensions** for categorization and grouping
- **6 Filters** for common data filtering

**Use `SQL_EXPRESSIONS_QUICK_ADD.md` to add them in ~20 minutes.**

Once added, your Genie Space will understand complex natural language queries like:
- "Show me at-risk Strategic customers by risk level category"
- "What is the efficiency ratio for latest data only?"
- "What are the balance tiers for high beta sensitivity accounts?"

**Your Genie Space is ready for production use! 🚀**
