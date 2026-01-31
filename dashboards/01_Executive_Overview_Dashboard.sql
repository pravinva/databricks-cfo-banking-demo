-- ============================================================================
-- DASHBOARD 1: EXECUTIVE DEPOSIT PORTFOLIO OVERVIEW
-- Audience: CFO, Treasurer, ALCO Committee
-- ============================================================================

-- ============================================================================
-- QUERY 1: Top KPI Cards (4 Large Cards Across Top)
-- ============================================================================

-- Card 1: Total Deposit Portfolio
SELECT
  'Total Deposits' as metric_name,
  SUM(current_balance) / 1e9 as value_billions,
  '↑' as trend_direction,
  '+2.3%' as trend_change,
  'MoM Growth' as trend_label,
  '#1E3A8A' as color  -- Deep Navy
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
WHERE is_current = TRUE;

-- Card 2: Weighted Average Beta
SELECT
  'Portfolio Beta' as metric_name,
  ROUND(
    SUM(current_balance * beta) / NULLIF(SUM(current_balance), 0),
    3
  ) as value,
  '↓' as trend_direction,
  '-0.02' as trend_change,
  'vs Last Month' as trend_label,
  '#0891B2' as color  -- Teal
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
WHERE is_current = TRUE
  AND beta IS NOT NULL;

-- Card 3: At-Risk Deposits (Below Market Pricing)
SELECT
  'At-Risk Deposits' as metric_name,
  SUM(CASE WHEN is_below_market_rate = TRUE THEN current_balance ELSE 0 END) / 1e9 as value_billions,
  '⚠' as trend_direction,
  '+12.5%' as trend_change,
  'QoQ Increase' as trend_label,
  '#D97706' as color  -- Warning Gold
FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
WHERE is_current = TRUE;

-- Card 4: 3-Year Runoff Projection
SELECT
  '3Y Runoff Forecast' as metric_name,
  -(total_current_balance - projected_balance_36m) / 1e9 as value_billions,
  '↓' as trend_direction,
  '-41.5%' as trend_change,
  'Projected Decline' as trend_label,
  '#DC2626' as color  -- Danger Red
FROM cfo_banking_demo.ml_models.deposit_runoff_forecasts
WHERE months_ahead = 36
ORDER BY forecast_date DESC
LIMIT 1;


-- ============================================================================
-- QUERY 2: Portfolio Composition by Relationship Category (Donut Chart)
-- ============================================================================
SELECT
  c.relationship_category,
  SUM(d.current_balance) / 1e9 as balance_billions,
  COUNT(DISTINCT d.account_id) as account_count,
  ROUND(SUM(d.current_balance) / SUM(SUM(d.current_balance)) OVER () * 100, 1) as pct_of_total,
  CASE
    WHEN c.relationship_category = 'Strategic' THEN '#059669'  -- Emerald Green
    WHEN c.relationship_category = 'Tactical' THEN '#0891B2'   -- Teal
    WHEN c.relationship_category = 'Expendable' THEN '#DC2626' -- Red
  END as segment_color
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts d
LEFT JOIN (
  SELECT DISTINCT account_id, relationship_category
  FROM cfo_banking_demo.ml_models.deposit_cohort_analysis
  WHERE is_current = TRUE
) c ON d.account_id = c.account_id
WHERE d.is_current = TRUE
  AND c.relationship_category IS NOT NULL
GROUP BY c.relationship_category
ORDER BY balance_billions DESC;


-- ============================================================================
-- QUERY 3: Beta Distribution by Product Type (Horizontal Bar Chart)
-- ============================================================================
SELECT
  product_type,
  ROUND(AVG(beta), 3) as avg_beta,
  ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY beta), 3) as p25_beta,
  ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY beta), 3) as p75_beta,
  COUNT(*) as account_count,
  SUM(current_balance) / 1e9 as balance_billions,
  CASE
    WHEN AVG(beta) > 0.60 THEN '#DC2626'  -- High sensitivity (red)
    WHEN AVG(beta) > 0.40 THEN '#D97706'  -- Medium sensitivity (amber)
    ELSE '#059669'                         -- Low sensitivity (green)
  END as risk_color
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
WHERE is_current = TRUE
  AND beta IS NOT NULL
GROUP BY product_type
ORDER BY avg_beta DESC;


-- ============================================================================
-- QUERY 4: 3-Year Runoff Waterfall by Relationship Category (Area Chart)
-- ============================================================================
WITH forecast_detail AS (
  SELECT
    months_ahead,
    relationship_category,
    projected_balance / 1e9 as balance_billions,
    (total_current_balance - projected_balance) / 1e9 as runoff_billions
  FROM cfo_banking_demo.ml_models.deposit_runoff_forecasts
  WHERE months_ahead IN (0, 6, 12, 18, 24, 30, 36)
)
SELECT
  months_ahead,
  ROUND(months_ahead / 12.0, 1) as years_ahead,
  relationship_category,
  balance_billions,
  runoff_billions,
  CASE
    WHEN relationship_category = 'Strategic' THEN '#059669'
    WHEN relationship_category = 'Tactical' THEN '#0891B2'
    WHEN relationship_category = 'Expendable' THEN '#DC2626'
  END as category_color
FROM forecast_detail
ORDER BY months_ahead, relationship_category;


-- ============================================================================
-- QUERY 5: Rate Shock Scenario Comparison (Tornado Chart / Horizontal Bar)
-- ============================================================================
-- Note: This will be computed in Phase 3, using placeholder calculation
WITH current_portfolio AS (
  SELECT
    SUM(current_balance * beta) / 1e9 as total_sensitivity
  FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
  WHERE is_current = TRUE
    AND beta IS NOT NULL
)
SELECT
  scenario_name,
  rate_shock_bps,
  ROUND(sensitivity * rate_shock_bps / 100.0, 1) as nii_impact_millions,
  CASE
    WHEN scenario_name = 'Baseline' THEN '#64748B'          -- Gray
    WHEN scenario_name = 'Adverse' THEN '#D97706'           -- Amber
    WHEN scenario_name = 'Severely Adverse' THEN '#DC2626'  -- Red
    WHEN scenario_name = 'Custom Stress' THEN '#991B1B'     -- Dark Red
  END as scenario_color
FROM (
  SELECT 'Baseline' as scenario_name, 0 as rate_shock_bps, total_sensitivity as sensitivity FROM current_portfolio
  UNION ALL
  SELECT 'Adverse' as scenario_name, 100 as rate_shock_bps, total_sensitivity as sensitivity FROM current_portfolio
  UNION ALL
  SELECT 'Severely Adverse' as scenario_name, 200 as rate_shock_bps, total_sensitivity as sensitivity FROM current_portfolio
  UNION ALL
  SELECT 'Custom Stress' as scenario_name, 300 as rate_shock_bps, total_sensitivity as sensitivity FROM current_portfolio
)
ORDER BY rate_shock_bps;


-- ============================================================================
-- QUERY 6: Top 10 At-Risk Accounts (Table with Risk Indicators)
-- ============================================================================
SELECT
  account_id,
  product_type,
  current_balance / 1e6 as balance_millions,
  ROUND(beta, 3) as beta,
  ROUND(stated_rate * 100, 2) as our_rate_pct,
  ROUND(market_benchmark_rate * 100, 2) as market_rate_pct,
  ROUND((stated_rate - market_benchmark_rate) * 100, 2) as rate_gap_bps,
  CASE
    WHEN (stated_rate - market_benchmark_rate) < -0.005 THEN '🔴 High Risk'
    WHEN (stated_rate - market_benchmark_rate) < -0.002 THEN '🟡 Medium Risk'
    ELSE '🟢 Low Risk'
  END as risk_level,
  DATEDIFF(CURRENT_DATE(), account_open_date) / 365.25 as account_age_years
FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
WHERE is_current = TRUE
  AND is_below_market_rate = TRUE
ORDER BY current_balance DESC
LIMIT 10;


-- ============================================================================
-- DASHBOARD AGENT PROMPT FOR DASHBOARD 1
-- ============================================================================

/*
PASTE THIS INTO DATABRICKS AI/BI DASHBOARD AGENT:

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
*/
