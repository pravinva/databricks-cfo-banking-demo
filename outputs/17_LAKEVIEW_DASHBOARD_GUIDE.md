# WS5: Enterprise Lakeview Dashboard Creation Guide

**Bank CFO Command Center - Executive Analytics**

Created: 2026-01-25
Purpose: Step-by-step guide to create Bloomberg Terminal-level Lakeview dashboards
Aesthetic: Professional navy/slate/white, enterprise banking quality

---

## 📋 Overview

This guide provides instructions for creating sophisticated Lakeview dashboards using the SQL queries, Plotly configurations, and design system generated in WS5.

### Deliverables

✅ **17_dashboard_queries.sql** - 8 sophisticated SQL queries
✅ **17_plotly_chart_configs.py** - Professional chart configurations
✅ **17_design_system.py** - Color palette & typography system
✅ **17_test_dashboard_queries.py** - Query validation script
✅ **17_LAKEVIEW_DASHBOARD_GUIDE.md** (this file)

---

## 🎯 Dashboard Architecture

### Executive Command Center Dashboard

**Purpose**: Single-pane-of-glass executive view for Bank CFO
**Update Frequency**: Real-time (query on load) with 5-minute refresh
**Target Audience**: C-suite executives, treasury leadership, risk management

### 8 Core Visualizations

1. **KPI Scorecard with Sparklines** - Executive summary metrics (Total Assets, Deposits, NIM, LCR)
2. **Liquidity Waterfall Chart** - LCR component breakdown (HQLA sources & cash outflows)
3. **Yield Curve Surface (3D)** - Treasury term structure evolution (90-day history)
4. **Portfolio Risk-Return Heatmap** - Asset allocation by security type with risk metrics
5. **Deposit Beta Sensitivity Matrix** - Rate shock scenarios across product types
6. **Real-Time Activity Stream** - Recent transactions & model predictions
7. **Capital Adequacy Bullet Charts** - Basel III compliance (CET1, Tier 1, Total Capital)
8. **Net Interest Margin Waterfall** - NIM component attribution

---

## 🚀 Step-by-Step Implementation

### Prerequisites

1. **Databricks Workspace** with Lakeview enabled
2. **Unity Catalog** with database `cfo_banking_demo` created
3. **SQL Warehouse** running (any size, recommend Medium or Large)
4. **Permissions**: CREATE DASHBOARD, USE CATALOG, USE SCHEMA

### Step 1: Prepare Data Tables

Some queries reference tables that need to be created from existing data:

#### Missing Tables (need to be created):

- `cfo_banking_demo.silver_finance.securities`
- `cfo_banking_demo.silver_finance.deposit_portfolio`
- `cfo_banking_demo.bronze_market.treasury_yields`
- `cfo_banking_demo.gold_finance.capital_structure`
- `cfo_banking_demo.silver_finance.securities_trades`
- `cfo_banking_demo.gold_analytics.churn_predictions`
- `cfo_banking_demo.silver_finance.wholesale_funding`

#### Existing Tables (verified working):

✅ `cfo_banking_demo.silver_finance.loan_portfolio`

**Action Items**:

1. Run WS1-04 scripts to populate missing tables
2. Or modify queries to work with existing `loan_portfolio` table only
3. Or create mock data for demonstration purposes

### Step 2: Create Lakeview Dashboard

#### 2.1 Navigate to Databricks SQL

1. Go to **SQL** in left sidebar
2. Click **Dashboards**
3. Click **Create Dashboard**
4. Name: `Bank CFO Command Center`

#### 2.2 Configure Dashboard Settings

- **Layout**: Grid layout, 12 columns
- **Theme**: Dark mode off (use light professional theme)
- **Auto-refresh**: 5 minutes
- **Permissions**: Share with CFO leadership group

### Step 3: Add Visualizations

For each of the 8 visualizations:

#### 3.1 Create Query

1. Click **Add** → **Visualization from query**
2. Click **New Query**
3. Copy SQL from `outputs/17_dashboard_queries.sql` (corresponding section)
4. Name query appropriately (e.g., "KPI Scorecard - Current Metrics")
5. Click **Run** to test
6. **Save Query**

#### 3.2 Configure Visualization

Use the Plotly configurations from `outputs/17_plotly_chart_configs.py` as reference:

##### Chart 1: KPI Scorecard

- **Visualization Type**: Counter (for each KPI)
- **Layout**: 2x2 grid (4 KPIs)
- **Counter Value Column**: `current_value_billions`
- **Counter Label**: `metric_name`
- **Trend Column**: `pct_change_30d`
- **Color Scheme**: Green (up), Red (down)

For sparklines, create separate **Line Chart** visualizations:
- **X-axis**: `metric_date`
- **Y-axis**: `value`
- **Group by**: `metric_name`
- **Line color**: Cyan (#00A8E1)
- **Fill area**: Light cyan (#00A8E133)

##### Chart 2: Liquidity Waterfall

- **Visualization Type**: Bar Chart (waterfall mode)
- **X-axis (Categories)**: `component`
- **Y-axis (Values)**: `signed_value_billions`
- **Colors**: Green (sources), Red (outflows)
- **Sort**: By `sort_order`
- **Format Y-axis**: Currency, billions

##### Chart 3: Yield Curve Surface

- **Visualization Type**: 3D Surface (if available) OR multiple line charts
- **X-axis**: `tenor_years`
- **Y-axis**: `observation_date` (for 3D) OR just latest date (for 2D)
- **Z-axis / Value**: `yield_pct`
- **Color scale**: Green → Gold → Red

##### Chart 4: Portfolio Risk-Return Heatmap

- **Visualization Type**: Treemap OR Bubble Chart
- **Categories**: `security_type`
- **Size**: `market_value_billions`
- **Color**: `avg_yield_pct`
- **Tooltip**: Show duration, yield, credit rating

##### Chart 5: Deposit Beta Sensitivity

- **Visualization Type**: Heatmap
- **X-axis**: Product types (MMDA, DDA, NOW, Savings)
- **Y-axis**: Rate scenarios (-25, +25, +50, +100 bps)
- **Cell values**: Runoff amounts
- **Color scale**: Green (low) → Red (high)

##### Chart 6: Activity Stream

- **Visualization Type**: Table with sparklines OR Timeline
- **Columns**:
  - `activity_type`
  - `entity_name`
  - `activity_date`
  - `amount_millions`
  - `activity_description`
- **Sort**: By `activity_date` DESC
- **Limit**: 50 rows

##### Chart 7: Capital Adequacy Bullets

- **Visualization Type**: Horizontal Bar Chart (bullet chart style)
- **Categories**: CET1, Tier 1, Total Capital
- **Actual Value**: `actual_ratio_pct`
- **Reference Lines**:
  - `regulatory_minimum_pct` (red line)
  - `well_capitalized_pct` (yellow line)
  - `target_pct` (green line)

##### Chart 8: NIM Waterfall

- **Visualization Type**: Bar Chart (waterfall mode)
- **X-axis**: `component`
- **Y-axis**: `signed_amount_millions`
- **Colors**: Green (income), Red (expenses)
- **Show cumulative**: Yes

### Step 4: Apply Design System

Reference `outputs/17_design_system.py` for colors and styling:

#### Color Palette

Use these hex codes in visualization settings:

- **Navy Dark**: `#1B3139` (headers, critical text)
- **Cyan**: `#00A8E1` (primary data viz, actions)
- **Lava**: `#FF3621` (alerts, critical metrics)
- **Green**: `#10B981` (positive trends, success)
- **Red**: `#EF4444` (negative trends, errors)
- **Gold**: `#F59E0B` (warnings, medium priority)
- **Background**: `#F8FAFC` (light gray)

#### Typography

- **Font Family**: Inter (or system sans-serif fallback)
- **Title Size**: 24px, weight 700
- **Subtitle**: 18px, weight 600
- **Body**: 14px, weight 400
- **Labels**: 12px, weight 500, uppercase

#### Spacing

- **Card padding**: 24px
- **Section gap**: 32px
- **Chart margins**: 16px

### Step 5: Layout Dashboard

#### Recommended Grid Layout (12-column)

```
┌─────────────────────────────────────────────────────────────┐
│  BANK CFO COMMAND CENTER                     [Refresh: 5m]  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  [KPI 1]  [KPI 2]  [KPI 3]  [KPI 4]      (4 cols each)      │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  [Liquidity Waterfall Chart]      [Yield Curve Surface]     │
│       (6 cols)                          (6 cols)             │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  [Portfolio Risk Heatmap]         [Deposit Beta Matrix]     │
│       (6 cols)                          (6 cols)             │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  [Activity Stream Table]                (12 cols)            │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  [Capital Bullet Charts]          [NIM Waterfall]           │
│       (6 cols)                          (6 cols)             │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

#### Positioning Tips

1. **Most critical metrics at top** (KPIs)
2. **Liquidity & yield curve** (regulatory focus)
3. **Portfolio analytics** (investment decisions)
4. **Activity stream** (operational awareness)
5. **Capital & profitability** (bottom line)

### Step 6: Add Filters & Parameters

#### Recommended Dashboard Parameters

1. **Date Range Selector**
   - Type: Date Range
   - Default: Last 90 days
   - Used in: Yield Curve, Activity Stream

2. **Product Type Filter**
   - Type: Multi-select
   - Options: MMDA, DDA, NOW, Savings, All
   - Used in: Deposit Beta, Portfolio Breakdown

3. **Security Type Filter**
   - Type: Multi-select
   - Options: UST, Agency MBS, Corporate Bonds, All
   - Used in: Portfolio Risk, Securities queries

4. **Rate Shock Scenario**
   - Type: Dropdown
   - Options: -25 bps, +25 bps, +50 bps, +100 bps
   - Used in: Deposit Beta Sensitivity

#### Add Parameters to Queries

Edit each query to reference parameters:

```sql
-- Example: Add date range parameter
WHERE observation_date >= {{ date_range.start }}
  AND observation_date <= {{ date_range.end }}

-- Example: Add product filter
WHERE product_type IN ({{ product_filter }})
```

### Step 7: Testing & Validation

#### Pre-Launch Checklist

- [ ] All 8 visualizations render without errors
- [ ] Data refreshes correctly (test refresh button)
- [ ] Filters work across relevant charts
- [ ] Numbers match expected values
- [ ] Color scheme is consistent
- [ ] Typography is readable at 100% zoom
- [ ] Dashboard loads in < 5 seconds
- [ ] Mobile/tablet view is acceptable
- [ ] Permissions are set correctly

#### Test Scenarios

1. **Stress Test**: Rapid refresh (10 times)
2. **Filter Test**: Apply all filters simultaneously
3. **Date Range Test**: Select YTD, Last Quarter, Custom ranges
4. **Zoom Test**: 75%, 100%, 125%, 150%
5. **Browser Test**: Chrome, Safari, Firefox, Edge

---

## 📊 Query Validation Results

Test results from `outputs/17_test_dashboard_queries.py`:

```
Total Queries Tested: 8
✅ Successful: 3
❌ Failed: 5 (tables not yet created)
```

### Working Queries

✅ Query 1: KPI Scorecard - Loan portfolio data
✅ Query 6: Recent Activity - Loans
✅ Query 8: NIM Components - Loan interest income

### Queries Requiring Additional Tables

❌ Query 2: Liquidity Waterfall (needs `securities` table)
❌ Query 3: Yield Curve (needs `treasury_yields` table)
❌ Query 4: Portfolio Risk (needs `securities` table)
❌ Query 5: Deposit Beta (needs `deposit_portfolio` table)
❌ Query 7: Capital Adequacy (needs `capital_structure` table)

**Next Steps**: Run WS1-04 data generation scripts or create mock tables.

---

## 🎨 Design Philosophy

### Bloomberg Terminal Meets Modern SaaS

**Inspiration**: Professional trading terminals, enterprise BI tools
**Goal**: Data-dense but not cluttered, sophisticated without being overwhelming

### Key Design Principles

1. **Clarity First**: Every pixel serves a purpose
2. **Hierarchy**: Most important metrics are largest and highest
3. **Consistency**: Same colors/fonts/spacing throughout
4. **Actionability**: Insights lead to decisions
5. **Trust**: Show data sources, calculation methods, refresh times

### Color Usage Guidelines

- **Navy**: Authority, trust, financial stability
- **Cyan**: Data highlights, clickable elements, active states
- **Lava**: Urgent attention, alerts, critical thresholds
- **Green/Red**: Trend indicators (up/down, good/bad)
- **White/Gray**: Canvas, neutral backgrounds, disabled states

### Typography Hierarchy

1. **Dashboard Title** (32px, bold): Bank CFO Command Center
2. **Section Headers** (20px, semibold): Liquidity, Risk, Capital
3. **Chart Titles** (16px, medium): 10Y Treasury Yield Curve
4. **Body/Labels** (14px, regular): Axis labels, table headers
5. **Fine Print** (12px, regular): Data sources, timestamps

---

## 🔧 Advanced Features

### Custom SQL Functions

Create reusable functions in Unity Catalog:

```sql
-- Calculate LCR ratio
CREATE OR REPLACE FUNCTION cfo_banking_demo.calculate_lcr(
  hqla DECIMAL(18,2),
  net_outflows DECIMAL(18,2)
)
RETURNS DECIMAL(5,2)
RETURN (hqla / net_outflows) * 100;

-- Format currency billions
CREATE OR REPLACE FUNCTION cfo_banking_demo.format_billions(
  amount DECIMAL(18,2)
)
RETURNS STRING
RETURN CONCAT('$', ROUND(amount/1e9, 1), 'B');
```

### Alerts & Notifications

Set up dashboard alerts for critical thresholds:

1. **LCR < 100%** → Email to CFO, Treasurer
2. **Capital Ratio < Regulatory Minimum** → Slack #risk-alerts
3. **Deposit Runoff > $500M/day** → SMS to Treasury team
4. **Yield Curve Inversion** → Email to Investment Committee

### Scheduled PDF Reports

Export dashboard as PDF every Monday 6am:

- **Recipients**: CFO, Treasurer, Risk Manager
- **Format**: PDF landscape, A4 size
- **Include**: All 8 visualizations + summary commentary

---

## 📚 Reference Materials

### Files Generated in WS5

1. **outputs/17_dashboard_queries.sql** (26KB)
   - 8 production-ready SQL queries
   - Comments explaining each query
   - Sample data structures

2. **outputs/17_plotly_chart_configs.py** (19KB)
   - 10 chart configuration functions
   - Professional styling presets
   - Color palette constants

3. **outputs/17_design_system.py** (18KB)
   - ColorPalette class with full spectrum
   - Typography scale and presets
   - Component styles (cards, buttons, badges)
   - CSS export functions

4. **outputs/17_test_dashboard_queries.py** (8KB)
   - Automated query validation
   - Execution time tracking
   - Sample data verification

### External Documentation

- [Databricks Lakeview Docs](https://docs.databricks.com/dashboards/lakeview.html)
- [Unity Catalog SQL Reference](https://docs.databricks.com/sql/language-manual/index.html)
- [Plotly Python Graphing](https://plotly.com/python/)

---

## 🚨 Troubleshooting

### Common Issues

#### Issue: "Table or view not found"

**Solution**: Check that all required tables exist in Unity Catalog. Run:

```sql
SHOW TABLES IN cfo_banking_demo.silver_finance;
SHOW TABLES IN cfo_banking_demo.bronze_market;
SHOW TABLES IN cfo_banking_demo.gold_finance;
```

#### Issue: "Query timeout"

**Solution**: Optimize query with:
- Add appropriate indexes
- Use partitioning (by date)
- Filter early in WHERE clause
- Increase SQL Warehouse size

#### Issue: "Visualization not rendering"

**Solution**: Check:
- Data types match expected (numeric for charts)
- No NULL values in key columns
- Column names match visualization config
- Query returns < 10,000 rows

#### Issue: "Colors don't match design system"

**Solution**: Manually set colors in visualization editor:
1. Click visualization → Edit
2. Go to **Color** tab
3. Select **Custom colors**
4. Paste hex codes from design system

---

## ✅ Success Criteria

Dashboard is ready for production when:

- ✅ All 8 visualizations display data
- ✅ Refresh completes in < 10 seconds
- ✅ No SQL errors in any query
- ✅ Colors match design system
- ✅ Mobile view is usable
- ✅ Filters work correctly
- ✅ Stakeholders can interpret metrics
- ✅ Data sources are documented
- ✅ Auto-refresh is enabled
- ✅ Permissions are configured

---

## 📞 Support

For questions or issues:

1. Check this guide first
2. Review SQL query comments in `17_dashboard_queries.sql`
3. Test queries individually using `17_test_dashboard_queries.py`
4. Consult Databricks documentation
5. Contact data engineering team

---

**Created**: 2026-01-25
**Version**: 1.0
**Author**: WS5 Automated Workflow
**Project**: Bank CFO Command Center - Databricks CFO Banking Demo
