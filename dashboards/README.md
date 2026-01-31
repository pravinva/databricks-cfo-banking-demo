# CFO Banking Demo - AI/BI Dashboard Suite

## Overview

This folder contains **3 professional executive dashboards** designed for CFO banking operations, built using Databricks AI/BI Dashboard Agent.

**Total Value:** 8 analytical capabilities across executive, operational, and customer insights.

---

## Dashboard Architecture

### **Dashboard 1: Executive Deposit Portfolio Overview**
**File:** `01_Executive_Overview_Dashboard.sql`
**Audience:** CFO, Treasurer, ALCO Committee
**Purpose:** Strategic decision-making and risk monitoring

**Key Features:**
- 4 KPI cards: Total Deposits, Portfolio Beta, At-Risk Deposits, 3Y Runoff
- Portfolio composition donut chart (Strategic/Tactical/Expendable)
- Beta distribution by product type
- 3-year runoff projection waterfall
- Rate shock scenario comparison
- Top 10 at-risk accounts table

**Refresh Frequency:** Daily (8am)

---

### **Dashboard 2: ALM & Treasury Operations**
**File:** `02_ALM_Treasury_Operations_Dashboard.sql`
**Audience:** Treasury Team, ALM Committee, Risk Management
**Purpose:** Operational analytics and component decay monitoring

**Key Features:**
- Component decay metrics (λ closure rate, g ABGR, compound factor)
- Cohort survival curves (Kaplan-Meier analysis)
- Closure vs Growth scatter plot (decay matrix)
- Vintage performance heatmap by opening regime
- Product-specific runoff rates
- Dynamic beta curves (0-6% rate scenarios)
- Core vs Non-Core classification
- Surge balance detection (2020-2022 pandemic era)

**Refresh Frequency:** Weekly (Monday 9am)

---

### **Dashboard 3: Product & Customer Analytics**
**File:** `03_Product_Customer_Analytics_Dashboard.sql`
**Audience:** Retail Banking, Product Managers, Marketing
**Purpose:** Customer insights and product performance

**Key Features:**
- Relationship value KPIs (Strategic/Tactical/Expendable + cross-sell)
- Customer journey Sankey diagram
- Product penetration heatmap
- Tenure vs Beta correlation scatter
- Digital engagement impact analysis
- Top 20 strategic relationships table
- Cross-sell opportunity matrix (bubble chart)
- Autopay & direct deposit stickiness
- Balance tier distribution

**Refresh Frequency:** Daily (6am)

---

## Design Specifications

### Color Palette (Professional Banking)
```
Primary Blue:   #1E3A8A  (Deep Navy - trust, stability)
Accent Teal:    #0891B2  (Cyan - growth, technology)
Warning Amber:  #D97706  (Gold - caution, attention)
Danger Red:     #DC2626  (Red - risk, alerts)
Success Green:  #059669  (Emerald - positive metrics)
Neutral Gray:   #64748B  (Slate - supporting data)
```

### Typography
- **Headers:** Bold, 18-20pt
- **KPI Metrics:** Bold, 24-32pt
- **Labels:** Regular, 12-14pt

### Layout Principles
- Clean white background with card-based design
- Left-to-right reading flow for key metrics
- Strategic use of color for emphasis (not decoration)
- Professional banking aesthetic (Bloomberg Terminal meets modern SaaS)

---

## How to Build Dashboards

### Method 1: Using Databricks AI/BI Dashboard Agent (Recommended)

1. **Open Databricks Workspace**
   - Navigate to **Dashboards** → **Create Dashboard**
   - Select **AI/BI Dashboard** option

2. **For Dashboard 1 (Executive Overview):**
   - Copy the prompt from bottom of `01_Executive_Overview_Dashboard.sql`
   - Paste into AI/BI Dashboard Agent
   - Copy/paste SQL queries one by one when prompted
   - Agent will automatically create visualizations with proper colors

3. **Repeat for Dashboard 2 & 3:**
   - Use prompts from `02_ALM_Treasury_Operations_Dashboard.sql`
   - Use prompts from `03_Product_Customer_Analytics_Dashboard.sql`

### Method 2: Manual SQL Dashboard Creation

1. **Create New SQL Dashboard**
   - Databricks → Dashboards → Create → SQL Dashboard

2. **Add Queries:**
   - Click "Add Query"
   - Copy SQL from respective `.sql` files
   - Assign to appropriate warehouse (use `4b9b953939869799`)

3. **Create Visualizations:**
   - Select query → "Add Visualization"
   - Choose chart type as specified in SQL comments
   - Apply color mappings from color fields in queries
   - Adjust formatting per specifications

4. **Arrange Layout:**
   - Drag/drop visualizations to match layout in prompts
   - Set card sizes as specified (e.g., 50% width, full width)

---

## Data Dependencies

### Required Tables (from Phase 1-3 Notebooks)

**Phase 1 Outputs:**
- `cfo_banking_demo.ml_models.deposit_beta_training_enhanced`
- `cfo_banking_demo.bronze_core_banking.deposit_accounts`

**Phase 2 Outputs:**
- `cfo_banking_demo.ml_models.deposit_cohort_analysis`
- `cfo_banking_demo.ml_models.cohort_survival_rates`
- `cfo_banking_demo.ml_models.component_decay_metrics`
- `cfo_banking_demo.ml_models.deposit_beta_training_phase2`
- `cfo_banking_demo.ml_models.deposit_runoff_forecasts`

**Phase 3 Outputs:**
- Dynamic beta parameters (stored in variables, not tables)
- Stress scenario results (computed on-demand)

### Prerequisites

Before building dashboards, ensure:
1. ✅ Phase 1 notebook has been run (deposit beta model)
2. ✅ Phase 2 notebook has been run (vintage analysis & decay)
3. ✅ Historical data generated (`generate_deposit_history.py`)
4. ✅ All tables exist and have current data

**Validation Query:**
```sql
-- Check all required tables exist
SHOW TABLES IN cfo_banking_demo.ml_models LIKE 'deposit%';
```

---

## Dashboard Filters

### Recommended Global Filters

**All Dashboards:**
- Date Range Picker (default: Last 90 days)
- Relationship Category (Strategic/Tactical/Expendable/All)
- Product Type (Checking/Savings/Money Market/CD/All)

**Dashboard 1 Additional:**
- Balance Tier ($10K, $50K, $100K, $250K, $1M+)
- Risk Level (High/Medium/Low)

**Dashboard 2 Additional:**
- Cohort Quarter (last 8 quarters)
- Opening Regime (Low/Medium/High)

**Dashboard 3 Additional:**
- Digital Engagement (Full/Partial/None)
- Convenience Features (DD + Autopay / DD Only / Autopay Only / Neither)

---

## Scheduled Refresh

Configure automatic refresh for real-time insights:

```sql
-- Dashboard 1: Daily 8am
-- Dashboard 2: Weekly Monday 9am
-- Dashboard 3: Daily 6am
```

**Setup in Databricks:**
1. Open dashboard → **Schedule** tab
2. Set frequency (daily/weekly)
3. Set time zone (default: UTC, adjust to local)
4. Enable email notifications on failure

---

## Performance Optimization

### Query Performance Tips

1. **Use Warehouse Caching:**
   - Assign all dashboards to same warehouse
   - Enable auto-stop after 10 minutes
   - Use Serverless SQL if available

2. **Add Indexes (if using Delta tables):**
   ```sql
   OPTIMIZE cfo_banking_demo.ml_models.deposit_cohort_analysis
   ZORDER BY (cohort_quarter, relationship_category, is_current);
   ```

3. **Sample Large Queries:**
   - Query 4 in Dashboard 3 uses `LIMIT 1000` for scatter plots
   - Adjust based on performance needs

4. **Materialized Views (Optional):**
   - For complex aggregations, create materialized views
   - Refresh nightly via scheduled job

---

## Customization Guide

### Changing Colors

All colors are embedded in SQL queries as hex codes. To customize:

```sql
-- Find lines like:
CASE
  WHEN relationship_category = 'Strategic' THEN '#059669'  -- Change this
  ...
```

### Adding New Metrics

1. Modify SQL query to add column
2. Update visualization in dashboard
3. Adjust layout if needed

### Exporting for Power BI

If you need to use these in Power BI instead:

1. **Extract Data:**
   ```python
   from databricks import sql

   connection = sql.connect(
       server_hostname="your-workspace.cloud.databricks.com",
       http_path="/sql/1.0/warehouses/4b9b953939869799"
   )

   df = pd.read_sql("SELECT * FROM query_result", connection)
   df.to_csv("export.csv")
   ```

2. **Import to Power BI:**
   - Use "Get Data" → CSV
   - Apply same color palette in Power BI theme
   - Recreate visualizations

---

## Troubleshooting

### Common Issues

**1. "Table not found" error:**
- Run Phase 1, 2, 3 notebooks first
- Verify catalog/schema names: `cfo_banking_demo.ml_models`

**2. Query timeout:**
- Increase warehouse size (Medium → Large)
- Add filters to reduce data volume
- Check for missing indexes

**3. Colors not showing:**
- Ensure color fields are mapped in visualization settings
- Check hex codes are valid (#RRGGBB format)

**4. Missing relationship_category:**
- Join with `deposit_cohort_analysis` table (see Phase 3 fix)
- Filter `WHERE relationship_category IS NOT NULL`

---

## Support & Feedback

For questions or improvements:
- GitHub Issues: [databricks-cfo-banking-demo/issues](https://github.com/pravinva/databricks-cfo-banking-demo/issues)
- Internal: Contact Data Science Team

---

## Next Steps

1. ✅ Build Dashboard 1 (Executive Overview) - Start here for quick wins
2. ✅ Build Dashboard 2 (ALM Operations) - For treasury team
3. ✅ Build Dashboard 3 (Customer Analytics) - For product team
4. 📊 Share with stakeholders for feedback
5. 🔄 Schedule automated refresh
6. 📈 Monitor usage analytics in Databricks workspace

**Estimated Build Time:**
- Dashboard 1: 30-45 minutes
- Dashboard 2: 45-60 minutes
- Dashboard 3: 45-60 minutes
- **Total: ~2-3 hours for all 3 dashboards**

---

## License

MIT License - See main repository for details.
