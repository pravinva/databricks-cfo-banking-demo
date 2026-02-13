# Executive Overview Dashboard Agent Prompt (SQL pack)

Use this prompt when building **Dashboard 1: Executive Deposit Portfolio Overview** using the SQL files in this folder.

## How to use
- Open the Databricks **AI/BI Dashboard Agent**
- Paste the prompt below
- When the agent asks for SQL, use the files in this folder in order:
  - KPI cards: `01_kpi_total_deposits.sql`, `02_kpi_portfolio_beta.sql`, `03_kpi_at_risk_deposits.sql`, `04_kpi_3y_runoff_forecast.sql`
  - Composition: `05_relationship_category_composition.sql`, `06_product_type_mix.sql`
  - Trends: `07_total_balance_trend_last_6_months.sql`, `08_total_balance_trend_monthly_yoy.sql`
  - Breakdowns: `09_beta_by_product_type.sql`, `10_runoff_waterfall_by_category.sql`
  - Stress / competitive: `11_rate_shock_scenario_comparison.sql`, `12_top_10_at_risk_accounts.sql`

## Prompt (copy/paste)

```
Create "Executive Deposit Portfolio Overview" dashboard with this layout:

TOP ROW (4 Large KPI Cards):
- Use KPI queries (4 separate cards)
- Large number (32pt), metric name (18pt), trend arrow + change below
- Use the provided color field (if present) for card accent
- Add subtle gradient background to each card

SECOND ROW (2 Visualizations):
LEFT (50% width):
- Donut chart: "Portfolio by Relationship Category"
- Show % labels; center text "$XX.XB Total"

RIGHT (50% width):
- Horizontal bar chart: "Rate Sensitivity by Product Type"
- X-axis Beta (0.0–1.0); show balance as secondary value

THIRD SECTION (Trends & Mix):
- Line chart: "Total Deposit Balance (Last 6 Months)" (Y = $B)
- Two-series line chart: "Total Deposit Balance (Monthly vs Prior Year)" (seasonality)
- Donut chart: "Deposit Mix by Product Type" (show % labels)

FOURTH ROW (Full Width):
- Stacked area chart: "3-Year Deposit Runoff Projection" (Y = $B)

FIFTH ROW (2 Visualizations):
LEFT (40% width):
- Tornado chart: "NII Impact by Stress Scenario"
- Include stressed_avg_beta in tooltip/label

RIGHT (60% width):
- Table: "Top 10 At-Risk Deposits"
- Conditional formatting for risk level; highlight High Risk rows light red

DESIGN:
- Executive banking aesthetic (clean, card-based)
- Use Navy/Teal/Gold/Red/Emerald palette
- Add global filters: Date Range, Relationship Category, Product Type
```

