# Final Setup Steps - Genie Space

## ✅ Tables Added! (12/12 Complete)

Great! You've successfully added all 12 tables through the Databricks UI. Now complete the setup with SQL expressions and sample questions.

---

## 🎯 Remaining Setup (30 minutes total)

### Step 1: Add SQL Expressions (~20 minutes)

**Purpose:** Teach Genie business concepts like "average deposit beta", "at-risk percentage", "risk level category"

**File to use:** `SQL_EXPRESSIONS_QUICK_ADD.md`

**How to add:**
1. Open Databricks → Genie → "Treasury Modeling - Deposits & Fee Income"
2. Click **"Configure"** → **"Instructions"** tab
3. Scroll to **"SQL Expressions"** section
4. Click **"Add"** and select type (Measure/Dimension/Filter)
5. Copy-paste from `SQL_EXPRESSIONS_QUICK_ADD.md`:
   - Name
   - Code (⚠️ **uses full table names** like `cfo_banking_demo.ml_models.deposit_beta_training_enhanced.target_beta`)
   - Instructions
   - Synonyms
6. Repeat for all 23 expressions

**What you're adding:**
- **11 Measures** - Aggregations (Total Account Count, Average Beta, At-Risk %, etc.)
- **6 Dimensions** - Categories (Risk Level, Balance Tier, Beta Sensitivity, etc.)
- **6 Filters** - WHERE conditions (Latest Data, Active Accounts, Strategic Customers, etc.)

**Estimated time:** 20 minutes

---

### Step 2: Add Sample Questions (~10 minutes)

**Purpose:** Guide users on what they can ask Genie

**File to use:** `SAMPLE_QUESTIONS_TO_ADD.md`

**How to add:**
1. Open Databricks → Genie → "Treasury Modeling - Deposits & Fee Income"
2. Click **"Configure"** → **"Sample questions"** tab
3. Click **"Add sample question"**
4. Copy-paste each question from `SAMPLE_QUESTIONS_TO_ADD.md`
5. Repeat for all 26 questions

**What you're adding:**
- **6 questions** on Deposit Beta Modeling
- **5 questions** on Vintage Analysis
- **7 questions** on CCAR Stress Testing
- **5 questions** on PPNR Modeling
- **3 questions** on Cross-Domain Analysis

**Estimated time:** 10 minutes

---

## 📋 Progress Checklist

### Tables (DONE ✅)
- [x] All 12 tables added through GUI
- [x] Tables visible in Genie Space

### SQL Expressions (TODO)
- [ ] 11 Measures added
- [ ] 6 Dimensions added
- [ ] 6 Filters added

### Sample Questions (TODO)
- [ ] 26 sample questions added

### Testing (TODO)
- [ ] Test basic queries
- [ ] Test SQL expressions
- [ ] Test sample questions
- [ ] Train users

---

## 🧪 Test Queries (After Adding SQL Expressions)

Once SQL expressions are added, test these:

### Test Measures
```
What is the average deposit beta?
Show me the at-risk percentage
What is the total account count?
```

### Test Dimensions
```
Show me accounts by risk level category
Group accounts by balance tier
What is the capital adequacy status?
```

### Test Filters
```
Show me at-risk accounts only
Filter to strategic customers
Use latest data only
```

### Test Combined
```
Show me at-risk Strategic customers by risk level category
What is the average beta for high balance accounts?
Show me efficiency ratio for latest data only
```

---

## 📚 Documentation Files Reference

### Core Setup Files (Use These)
1. **`SQL_EXPRESSIONS_QUICK_ADD.md`** ⭐ - 23 SQL expressions (copy-paste format)
2. **`SAMPLE_QUESTIONS_TO_ADD.md`** ⭐ - 26 sample questions (copy-paste format)

### Reference Files (For Context)
3. **`SQL_EXPRESSIONS_TO_ADD.md`** - Detailed explanations of each expression
4. **`SQL_EXPRESSIONS_README.md`** - Overview and instructions
5. **`VERIFIED_QUERIES.md`** - Tested SQL queries with results
6. **`GENIE_SPACE_CONFIGURATION.md`** - Complete configuration guide

### Troubleshooting
7. **`ADD_TABLES_TO_GENIE.md`** - Table setup guide (already done)

---

## 🔧 Important Notes

### About SQL Expressions

**✅ All expressions use full table names:**
- GOOD: `cfo_banking_demo.ml_models.deposit_beta_training_enhanced.target_beta`
- BAD: `target_beta` (won't work)

**Example from `SQL_EXPRESSIONS_QUICK_ADD.md`:**
```sql
Name: Average Deposit Beta
Code: ROUND(AVG(cfo_banking_demo.ml_models.deposit_beta_training_enhanced.target_beta), 3)
Instructions: Average deposit beta coefficient (0-1 scale). Higher beta = more rate sensitive.
Synonyms: avg beta, mean beta, portfolio beta, average rate sensitivity
```

### About Sample Questions

**Sample questions appear when users open the Genie Space**, helping them understand what they can ask.

**Example questions:**
- "What is the average deposit beta by relationship category?"
- "Show me at-risk accounts for Strategic customers"
- "What is the CET1 ratio under severely adverse scenario?"

---

## 🎯 Your Next Steps

### Immediate (Today)
1. Open `SQL_EXPRESSIONS_QUICK_ADD.md`
2. Add all 23 SQL expressions (20 minutes)
3. Open `SAMPLE_QUESTIONS_TO_ADD.md`
4. Add all 26 sample questions (10 minutes)

### Testing (After Setup)
5. Test queries listed above
6. Verify SQL expressions work correctly
7. Check sample questions generate correct SQL

### Rollout (This Week)
8. Train team members on how to use Genie
9. Share sample questions as examples
10. Gather feedback and iterate

---

## 💡 Tips for Success

### When Adding SQL Expressions
- ✅ Copy-paste exactly from `SQL_EXPRESSIONS_QUICK_ADD.md`
- ✅ Include all synonyms (helps natural language matching)
- ✅ Double-check full table names are present
- ✅ Test each expression after adding

### When Adding Sample Questions
- ✅ Add questions from all 4 domains (Beta, Vintage, Stress, PPNR)
- ✅ Include simple and complex examples
- ✅ Test that clicking questions generates correct SQL

### When Training Users
- ✅ Show them the sample questions
- ✅ Explain the SQL expressions (measures, dimensions, filters)
- ✅ Encourage them to try variations
- ✅ Collect feedback for future improvements

---

## 🚀 After Complete Setup

Once you've added SQL expressions and sample questions, your Genie Space will:

### Enable Natural Language Queries
- "What is the average deposit beta?" → Uses "Average Deposit Beta" measure
- "Show me at-risk Strategic customers" → Uses "At-Risk Accounts" and "Strategic Customers" filters
- "Group by risk level" → Uses "Risk Level Category" dimension

### Guide Users
- Sample questions visible when opening space
- Click sample question → generates SQL automatically
- Users learn what types of questions work

### Improve Accuracy
- SQL expressions provide business context
- Genie understands banking terminology
- Synonyms match various ways users ask questions

---

## ✅ Summary

**Status:**
- ✅ Tables: 12/12 added (DONE)
- ⏳ SQL Expressions: 0/23 added (TODO - 20 minutes)
- ⏳ Sample Questions: 0/26 added (TODO - 10 minutes)

**Files to use:**
1. `SQL_EXPRESSIONS_QUICK_ADD.md` (expressions)
2. `SAMPLE_QUESTIONS_TO_ADD.md` (questions)

**Total remaining time:** ~30 minutes

**Once complete, your Genie Space will be production-ready! 🎉**
