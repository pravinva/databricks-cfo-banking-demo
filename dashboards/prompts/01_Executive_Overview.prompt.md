# Dashboard 1 Prompt (Copy/Paste): Executive Deposit Portfolio Overview

Paste this into the **Databricks AI/BI Dashboard Agent**.

```
Create "Executive Deposit Portfolio Overview" dashboard with this layout:

TOP ROW (4 Large KPI Cards):
- Use Query 1 results (4 separate cards)
- Card layout: Large number (32pt), metric name (18pt), trend arrow + change below
- Apply the color field to each card's accent color
- Add subtle gradient background to each card

SECOND ROW (2 Visualizations):
LEFT (50% width):
- Donut chart from Query 2 (Portfolio Composition)
- Title: "Portfolio by Relationship Category"
- Use segment_color field for slice colors
- Show percentage labels on slices
- Center text: "$XX.XB Total"

RIGHT (50% width):
- Horizontal bar chart from Query 3 (Beta by Product)
- Title: "Rate Sensitivity by Product Type"
- Use risk_color field for bar colors
- X-axis: Beta (0.0 to 1.0)
- Show balance_billions as secondary value

ADD (below second row or as a third-row 2-column section):
- Line chart from Query 2C: "Total Deposit Balance (Last 6 Months)" (Y = $B)
- Line chart from Query 2D: "Total Deposit Balance (Monthly vs Prior Year)" (two-series seasonality)
- Donut chart from Query 2B: "Deposit Mix by Product Type" (show % labels)

THIRD ROW (Full Width):
- Stacked area chart from Query 4 (Runoff Forecast)
- Title: "3-Year Deposit Runoff Projection"
- X-axis: Years Ahead (0-3)
- Y-axis: Balance ($B)
- Use category_color for area fills
- Add opacity gradient for depth

FOURTH ROW (2 Visualizations):
LEFT (40% width):
- Tornado chart from Query 5 (Rate Shock Scenarios)
- Title: "NII Impact by Stress Scenario"
- Use scenario_color for bars
- Show positive/negative divergence from baseline
- Include stressed_avg_beta as a label/tooltip (macro-cycle sensitivity)

RIGHT (60% width):
- Table from Query 6 (Top At-Risk Accounts)
- Title: "Top 10 At-Risk Deposits"
- Apply conditional formatting to risk_level column
- Highlight rows with High Risk in light red background

DESIGN:
- White background, card-based layout with shadows
- Professional banking colors (Navy, Teal, Gold, Red, Emerald)
- Bold headers, large KPI numbers
- Add filters: Date Range, Relationship Category, Product Type
```

