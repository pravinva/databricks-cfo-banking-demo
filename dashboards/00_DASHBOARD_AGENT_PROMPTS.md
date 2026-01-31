# AI/BI Dashboard Agent Prompts for CFO Banking Demo

## Design Guidelines - USE THESE FOR ALL DASHBOARDS

**Color Palette (Professional Banking):**
- Primary Blue: #1E3A8A (Deep Navy - trust, stability)
- Accent Teal: #0891B2 (Cyan - growth, technology)
- Warning Amber: #D97706 (Gold - caution, attention)
- Danger Red: #DC2626 (Red - risk, alerts)
- Success Green: #059669 (Emerald - positive metrics)
- Neutral Gray: #64748B (Slate - supporting data)

**Typography:**
- Headers: Bold, 18-20pt
- Metrics: Bold, 24-32pt for KPIs
- Labels: Regular, 12-14pt

**Layout Principles:**
- Clean white background with subtle grid lines
- Card-based design with shadows for depth
- Left-to-right reading flow for key metrics
- Strategic use of color for emphasis (not decoration)
- Professional banking aesthetic (think Bloomberg Terminal meets modern SaaS)

---

## Master Prompt: Overall Dashboard Structure

**Dashboard Name:** CFO Deposit Portfolio Command Center

**Dashboard Organization:** Create **3 separate dashboards** (not 1):

### Dashboard 1: Executive Overview (CEO/CFO Focus)
- Use this for high-level metrics and strategic decisions
- Large KPI cards at top, trend charts below
- 3-column layout for key metrics
- Include: Executive Risk Overview, Stress Testing, Competitive Positioning

### Dashboard 2: ALM & Treasury Operations (Treasury/ALM Team)
- Use this for operational analytics and risk management
- Detailed charts with drill-down capabilities
- Include: Component Decay, Vintage Analysis, Dynamic Beta Functions

### Dashboard 3: Product & Customer Analytics (Retail Banking/Marketing)
- Use this for customer insights and product performance
- Segmentation analysis and cohort tracking
- Include: Relationship Depth, Customer Value, Product Performance

---

## Prompt for Dashboard Agent - Copy/Paste This

```
I need you to create a professional CFO banking dashboard with the following specifications:

DESIGN STYLE:
- Professional banking aesthetic (Bloomberg Terminal meets modern SaaS)
- Color palette: Deep Navy (#1E3A8A), Teal (#0891B2), Gold (#D97706), Red (#DC2626), Emerald (#059669)
- Clean white background with card-based layout
- Large, bold KPI numbers (24-32pt) with trend indicators
- Subtle shadows for depth
- Use color strategically for emphasis, not decoration

LAYOUT:
- Top row: 4 large KPI cards with key metrics
- Middle section: 2-3 primary visualizations (full width or 2-column)
- Bottom section: Supporting charts and tables

VISUALIZATION PREFERENCES:
- Use area charts for trends (with gradient fills)
- Use horizontal bar charts for rankings/comparisons
- Use donut charts for composition (not pie charts)
- Use line charts for time-series with multiple series
- Include trend arrows (↑↓) and percentage changes
- Add conditional formatting for risk indicators

SQL QUERIES: [Insert specific SQL from sections below]

Make it look professional, actionable, and suitable for C-level executives.
```

---

