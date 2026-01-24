# Bank CFO Command Center - Exact Dashboard Specifications

**Copy-paste ready guide for creating each visualization**

---

## Dashboard 1: KPI Scorecard

### Query 1: KPI Metrics

**SQL Query:**
```sql
SELECT
    'Total Assets' as metric_name,
    CONCAT('$', ROUND(SUM(current_balance)/1e9, 1), 'B') as value,
    '+1.8%' as change
FROM cfo_banking_demo.silver_finance.loan_portfolio
WHERE is_current = true

UNION ALL

SELECT
    'Total Deposits',
    CONCAT('$', ROUND(SUM(current_balance)/1e9, 1), 'B'),
    '-0.5%'
FROM cfo_banking_demo.silver_finance.deposit_portfolio
WHERE is_current = true

UNION ALL

SELECT
    'Net Interest Margin',
    CONCAT(ROUND(AVG(net_interest_margin) * 100, 2), '%'),
    '+3 bps'
FROM cfo_banking_demo.gold_finance.profitability_metrics

UNION ALL

SELECT
    'LCR Ratio',
    CONCAT(ROUND(AVG(lcr_ratio) * 100, 1), '%'),
    'Compliant'
FROM cfo_banking_demo.gold_finance.liquidity_coverage_ratio
```

**Visualization Type:** **COUNTER** (create 4 separate counters, one for each row)

**Configuration for each counter:**
- **Counter Label:** Use column `metric_name`
- **Counter Value:** Use column `value`
- **Target Value:** (leave empty)
- **Row to display:**
  - Counter 1: Row 1 (Total Assets)
  - Counter 2: Row 2 (Total Deposits)
  - Counter 3: Row 3 (Net Interest Margin)
  - Counter 4: Row 4 (LCR Ratio)

**Styling:**
- **Font size:** Large (24-32px for value)
- **Label color:** #475569 (slate)
- **Value color:** #1B3139 (navy)
- **Background:** White

**Layout:** Place in top row, 4 columns (3 units each)

---

## Dashboard 2: Treasury Yield Curve

### Query 2: Yield Curve

**SQL Query:**
```sql
SELECT
    tenor_years as maturity_years,
    ROUND(yield_rate * 100, 2) as yield_pct
FROM cfo_banking_demo.bronze_market.treasury_yields
WHERE observation_date = (
    SELECT MAX(observation_date)
    FROM cfo_banking_demo.bronze_market.treasury_yields
)
ORDER BY tenor_years
```

**Visualization Type:** **LINE CHART**

**Configuration:**
- **X-axis:** `maturity_years`
  - Label: "Maturity (Years)"
  - Type: Linear
- **Y-axis:** `yield_pct`
  - Label: "Yield (%)"
  - Type: Linear
  - Format: 2 decimal places

**Styling:**
- **Line color:** #00A8E1 (cyan)
- **Line width:** 3px
- **Fill:** Enable area fill with #00A8E133 (cyan 20% opacity)
- **Grid lines:** Light gray #E2E8F0
- **Background:** White

**Layout:** Top row, right side (6 columns)

---

## Dashboard 3: Securities Portfolio Breakdown

### Query 3: Portfolio Analysis

**SQL Query:**
```sql
SELECT
    security_type,
    ROUND(SUM(market_value)/1e9, 2) as value_billions,
    ROUND(AVG(ytm) * 100, 2) as avg_yield_pct,
    ROUND(AVG(effective_duration), 1) as duration_years
FROM cfo_banking_demo.silver_finance.securities
WHERE is_current = true
GROUP BY security_type
ORDER BY value_billions DESC
```

**Visualization Type:** **TABLE**

**Column Configuration:**
1. **Security Type**
   - Alignment: Left
   - Font weight: Semibold
   - Color: #1B3139 (navy)

2. **Value ($B)**
   - Alignment: Right
   - Format: Number with 2 decimals
   - Font weight: Bold
   - Color: #1B3139 (navy)

3. **Avg Yield (%)**
   - Alignment: Right
   - Format: Number with 2 decimals
   - Color: #0F766E (teal) if > 3%, #DC2626 (red) if < 2%

4. **Duration (Y)**
   - Alignment: Right
   - Format: Number with 1 decimal
   - Color: #475569 (slate)

**Styling:**
- **Header background:** #F8FAFC (light gray)
- **Header text:** #475569 (slate), uppercase, 11px
- **Row hover:** #F1F5F9 (light slate)
- **Borders:** #CBD5E1 (slate border)

**Layout:** Middle left (6 columns, 4 rows)

---

## Dashboard 4: Deposit Beta Sensitivity

### Query 4: Deposit Products

**SQL Query:**
```sql
SELECT
    product_type,
    ROUND(SUM(current_balance)/1e9, 1) as balance_billions,
    ROUND(AVG(interest_rate) * 100, 2) as rate_pct,
    CASE product_type
        WHEN 'MMDA' THEN 0.85
        WHEN 'DDA' THEN 0.20
        WHEN 'NOW' THEN 0.45
        WHEN 'Savings' THEN 0.60
        ELSE 0.50
    END as deposit_beta
FROM cfo_banking_demo.silver_finance.deposit_portfolio
WHERE is_current = true
GROUP BY product_type
ORDER BY balance_billions DESC
```

**Visualization Type:** **HORIZONTAL BAR CHART**

**Configuration:**
- **X-axis (bars):** `balance_billions`
  - Label: "Balance ($ Billions)"
- **Y-axis (categories):** `product_type`
  - Label: "Product Type"
- **Color by:** `deposit_beta`
  - Low beta (< 0.4): #10B981 (green) - stable deposits
  - Medium beta (0.4-0.7): #F59E0B (gold) - moderate sensitivity
  - High beta (> 0.7): #EF4444 (red) - rate sensitive

**Styling:**
- **Bar opacity:** 80%
- **Bar border:** 1px #1B3139
- **Value labels:** Show on bars, white text
- **Grid lines:** Vertical only, light gray

**Layout:** Middle right (6 columns, 4 rows)

---

## Dashboard 5: Capital Adequacy Ratios

### Query 5: Basel III Compliance

**SQL Query:**
```sql
WITH capital_calcs AS (
    SELECT
        'CET1' as capital_type,
        ROUND((SUM(common_stock + retained_earnings - goodwill - intangibles)/1e9) / 25.0 * 100, 1) as actual_pct,
        7.0 as minimum_pct,
        8.5 as well_capitalized_pct,
        10.5 as target_pct
    FROM cfo_banking_demo.gold_finance.capital_structure

    UNION ALL

    SELECT
        'Tier 1',
        ROUND((SUM(tier1_capital)/1e9) / 25.0 * 100, 1),
        8.5,
        10.0,
        12.0
    FROM cfo_banking_demo.gold_finance.capital_structure

    UNION ALL

    SELECT
        'Total Capital',
        ROUND((SUM(tier1_capital + tier2_capital)/1e9) / 25.0 * 100, 1),
        10.5,
        13.0,
        16.0
    FROM cfo_banking_demo.gold_finance.capital_structure
)
SELECT * FROM capital_calcs
```

**Visualization Type:** **BULLET CHART** (or horizontal bar with reference lines)

**Configuration:**
- **Measure:** `actual_pct` (main bar)
- **Minimum:** `minimum_pct` (red reference line)
- **Target:** `target_pct` (green reference line)
- **Categories:** `capital_type`

**Color Coding:**
- **Actual bar color:**
  - Green (#10B981) if actual > well_capitalized_pct
  - Gold (#F59E0B) if actual between minimum and well_capitalized
  - Red (#EF4444) if actual < minimum_pct

**Reference Lines:**
- Minimum (red dashed line): #EF4444
- Well Capitalized (gold dashed): #F59E0B
- Target (green dashed): #10B981

**Layout:** Bottom left (6 columns, 3 rows)

---

## Dashboard 6: Liquidity Waterfall

### Query 6: LCR Components

**SQL Query:**
```sql
SELECT
    'Level 1 HQLA' as component,
    ROUND(SUM(market_value)/1e9, 2) as value_billions,
    'source' as flow_type,
    1 as sort_order
FROM cfo_banking_demo.silver_finance.securities
WHERE security_type IN ('UST', 'Agency MBS')
    AND is_current = true

UNION ALL

SELECT
    'Level 2A HQLA',
    ROUND(SUM(market_value)/1e9, 2),
    'source',
    2
FROM cfo_banking_demo.silver_finance.securities
WHERE security_type IN ('Agency CMO', 'GSE Debt')
    AND is_current = true

UNION ALL

SELECT
    'Retail Deposit Runoff',
    ROUND(SUM(current_balance * 0.03)/1e9, 2),
    'outflow',
    3
FROM cfo_banking_demo.silver_finance.deposit_portfolio
WHERE product_type IN ('MMDA', 'Savings')
    AND is_current = true

UNION ALL

SELECT
    'Wholesale Funding Runoff',
    ROUND(SUM(current_balance * 0.25)/1e9, 2),
    'outflow',
    4
FROM cfo_banking_demo.silver_finance.deposit_portfolio
WHERE product_type IN ('DDA', 'NOW')
    AND is_current = true

ORDER BY sort_order
```

**Visualization Type:** **WATERFALL CHART** (or stacked bar)

**Configuration:**
- **X-axis:** `component` (categories)
- **Y-axis:** `value_billions` (values)
- **Color by:** `flow_type`
  - Sources (green): #10B981
  - Outflows (red): #EF4444

**Styling:**
- **Bar width:** Medium
- **Connector lines:** Dotted gray between bars
- **Value labels:** On top of each bar
- **Zero line:** Bold black line

**Layout:** Bottom middle (6 columns, 3 rows)

---

## Dashboard 7: Recent Loan Activity

### Query 7: Last 30 Days

**SQL Query:**
```sql
SELECT
    product_type,
    borrower_name,
    origination_date,
    ROUND(current_balance/1e6, 2) as amount_millions,
    ROUND(interest_rate, 2) as rate_pct
FROM cfo_banking_demo.silver_finance.loan_portfolio
WHERE origination_date >= CURRENT_DATE - INTERVAL 30 DAYS
ORDER BY origination_date DESC
LIMIT 50
```

**Visualization Type:** **TABLE**

**Column Configuration:**
1. **Product Type** - Left align, semibold
2. **Borrower Name** - Left align, regular
3. **Date** - Center align, format: MM/DD/YYYY
4. **Amount ($M)** - Right align, bold, 2 decimals
5. **Rate (%)** - Right align, 2 decimals

**Styling:**
- **Alternating rows:** White / #F8FAFC
- **Header:** #1B3139 background, white text
- **Font:** 12px regular, 11px for numbers
- **Max height:** 400px with scroll

**Layout:** Full width bottom (12 columns, 4 rows)

---

## Dashboard 8: Net Interest Margin Waterfall

### Query 8: NIM Components

**SQL Query:**
```sql
SELECT
    'Loan Interest Income' as component,
    ROUND(SUM(current_balance * interest_rate / 100.0 / 12.0)/1e6, 1) as monthly_millions,
    'income' as type,
    1 as sort_order
FROM cfo_banking_demo.silver_finance.loan_portfolio
WHERE is_current = true

UNION ALL

SELECT
    'Deposit Interest Expense',
    -ROUND(SUM(current_balance * interest_rate / 100.0 / 12.0)/1e6, 1),
    'expense',
    2
FROM cfo_banking_demo.silver_finance.deposit_portfolio
WHERE is_current = true

UNION ALL

SELECT
    'Fee Income',
    ROUND(SUM(fee_revenue)/1e6, 1),
    'income',
    3
FROM cfo_banking_demo.gold_finance.profitability_metrics

UNION ALL

SELECT
    'Operating Expenses',
    -ROUND(SUM(operating_expenses)/1e6, 1),
    'expense',
    4
FROM cfo_banking_demo.gold_finance.profitability_metrics

ORDER BY sort_order
```

**Visualization Type:** **WATERFALL CHART**

**Configuration:**
- **X-axis:** `component`
- **Y-axis:** `monthly_millions`
- **Color by:** `type`
  - Income (green): #10B981
  - Expense (red): #EF4444
- **Show total:** Yes, at the end in cyan #00A8E1

**Styling:**
- **Bar borders:** 1px navy
- **Connector lines:** Dotted
- **Total bar:** Bold outline, cyan fill
- **Value labels:** Currency format $XXM

**Layout:** Bottom right (6 columns, 3 rows)

---

## Complete Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Row 1: KPIs (Height: 2 units)                              │
├─────────┬─────────┬─────────┬─────────┬───────────────────┤
│ Assets  │ Deposits│   NIM   │   LCR   │  Yield Curve      │
│ Counter │ Counter │ Counter │ Counter │  Line Chart       │
│ 3 cols  │ 3 cols  │ 3 cols  │ 3 cols  │  6 cols           │
└─────────┴─────────┴─────────┴─────────┴───────────────────┘

┌─────────────────────────────┬─────────────────────────────┐
│  Row 2: Portfolio (4 units) │  Deposit Beta (4 units)     │
├─────────────────────────────┼─────────────────────────────┤
│ Securities Table            │ Horizontal Bar Chart        │
│ 6 cols                      │ 6 cols                      │
└─────────────────────────────┴─────────────────────────────┘

┌─────────────────────────────┬─────────────────────────────┐
│  Row 3: Capital (3 units)   │  Liquidity (3 units)        │
├─────────────────────────────┼─────────────────────────────┤
│ Bullet Chart                │ Waterfall Chart             │
│ 6 cols                      │ 6 cols                      │
└─────────────────────────────┴─────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Row 4: Recent Activity (4 units)                           │
├─────────────────────────────────────────────────────────────┤
│ Loan Activity Table - Full Width 12 cols                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────┬─────────────────────────────┐
│  Row 5: NIM Waterfall (3)   │  (Reserved for expansion)   │
├─────────────────────────────┼─────────────────────────────┤
│ Waterfall Chart             │                             │
│ 6 cols                      │ 6 cols                      │
└─────────────────────────────┴─────────────────────────────┘
```

---

## Color Palette Quick Reference

```
Primary Colors:
- Navy Dark:   #1B3139  (headers, text, borders)
- Cyan:        #00A8E1  (primary accent, data viz)
- Lava:        #FF3621  (alerts, critical)

Data Viz Colors:
- Green:       #10B981  (positive, income, compliant)
- Red:         #EF4444  (negative, expense, alerts)
- Gold:        #F59E0B  (warning, medium)

Neutral Colors:
- Slate Dark:  #475569  (secondary text)
- Slate Med:   #64748B  (tertiary text)
- Slate Light: #94A3B8  (disabled)
- Gray BG:     #F8FAFC  (backgrounds)
- White:       #FFFFFF  (cards, panels)
```

---

## Dashboard Settings

**General:**
- **Name:** Bank CFO Command Center
- **Tags:** cfo, treasury, risk, executive
- **Auto-refresh:** 5 minutes
- **Grid:** 12 columns
- **Theme:** Light

**Permissions:**
- Share with: CFO leadership group
- Can Edit: Data engineering team
- Can View: All finance users

---

## Step-by-Step Creation

1. **Open** https://e2-demo-field-eng.cloud.databricks.com/sql/dashboards
2. **Click** "Create Dashboard"
3. **Name** it "Bank CFO Command Center"
4. **For each query above:**
   - Click "Add" → "Visualization"
   - Paste SQL from this guide
   - Run to verify data
   - Click "Edit Visualization"
   - Select visualization type
   - Configure exactly as specified
   - Apply colors from palette
   - Save with descriptive name
5. **Drag visualizations** to match layout grid
6. **Set dashboard refresh** to 5 minutes
7. **Publish** and share

Done! You now have a Bloomberg Terminal-level CFO dashboard.
