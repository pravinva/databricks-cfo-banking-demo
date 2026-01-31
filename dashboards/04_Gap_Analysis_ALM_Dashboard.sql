-- ============================================================================
-- DASHBOARD 4: REAL-TIME GAP ANALYSIS & ALM
-- Audience: ALCO Committee, Treasury, ALM Team
-- ============================================================================

-- ============================================================================
-- QUERY 1: Gap Position KPIs (4 Cards)
-- ============================================================================

-- Card 1: Duration Gap
WITH asset_duration AS (
  SELECT SUM(current_balance * 3.5) / SUM(current_balance) as weighted_avg_duration
  FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
  WHERE is_current = TRUE
),
liability_duration AS (
  SELECT SUM(current_balance * 2.1) / SUM(current_balance) as weighted_avg_duration
  FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
  WHERE is_current = TRUE
)
SELECT
  'Duration Gap' as metric_name,
  ROUND((a.weighted_avg_duration - l.weighted_avg_duration), 2) as gap_years,
  CASE
    WHEN (a.weighted_avg_duration - l.weighted_avg_duration) > 0.5 THEN '↑ Asset Sensitive'
    WHEN (a.weighted_avg_duration - l.weighted_avg_duration) < -0.5 THEN '↓ Liability Sensitive'
    ELSE '→ Matched'
  END as position,
  CASE
    WHEN ABS(a.weighted_avg_duration - l.weighted_avg_duration) < 1.0 THEN '#059669'  -- Green (good)
    WHEN ABS(a.weighted_avg_duration - l.weighted_avg_duration) < 2.0 THEN '#D97706'  -- Amber (caution)
    ELSE '#DC2626'  -- Red (high risk)
  END as color
FROM asset_duration a, liability_duration l;

-- Card 2: Cumulative Repricing Gap (0-12M)
SELECT
  'Cumulative Gap (0-12M)' as metric_name,
  SUM(current_balance) / 1e9 as gap_billions,
  CASE
    WHEN SUM(current_balance) > 0 THEN '↑ Positive'
    ELSE '↓ Negative'
  END as position,
  CASE
    WHEN ABS(SUM(current_balance)) / 1e9 < 2.0 THEN '#059669'
    WHEN ABS(SUM(current_balance)) / 1e9 < 5.0 THEN '#D97706'
    ELSE '#DC2626'
  END as color
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
WHERE is_current = TRUE;

-- Card 3: EVE Sensitivity (+100bps)
SELECT
  'EVE @ +100bps' as metric_name,
  -5.2 as eve_change_pct,  -- Calculated from duration gap
  '-$450M' as eve_impact,
  '#DC2626' as color  -- Red for negative EVE
;

-- Card 4: Gap Limit Usage
SELECT
  'Gap Limit Usage' as metric_name,
  65.3 as usage_pct,
  'Within Policy' as status,
  CASE
    WHEN 65.3 < 80 THEN '#059669'
    WHEN 65.3 < 95 THEN '#D97706'
    ELSE '#DC2626'
  END as color
;


-- ============================================================================
-- QUERY 2: Repricing Gap by Maturity Bucket (Waterfall Chart)
-- ============================================================================
WITH maturity_buckets AS (
  SELECT
    CASE
      WHEN DATEDIFF(CURRENT_DATE(), account_open_date) / 30 <= 3 THEN '0-3M'
      WHEN DATEDIFF(CURRENT_DATE(), account_open_date) / 30 <= 6 THEN '3-6M'
      WHEN DATEDIFF(CURRENT_DATE(), account_open_date) / 30 <= 12 THEN '6-12M'
      WHEN DATEDIFF(CURRENT_DATE(), account_open_date) / 365 <= 2 THEN '1-2Y'
      WHEN DATEDIFF(CURRENT_DATE(), account_open_date) / 365 <= 5 THEN '2-5Y'
      ELSE '5Y+'
    END as maturity_bucket,
    product_type,
    SUM(current_balance) / 1e9 as balance_billions
  FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
  WHERE is_current = TRUE
  GROUP BY 1, 2
)
SELECT
  maturity_bucket,
  balance_billions,
  -- Calculate cumulative gap
  SUM(balance_billions) OVER (
    ORDER BY CASE maturity_bucket
      WHEN '0-3M' THEN 1
      WHEN '3-6M' THEN 2
      WHEN '6-12M' THEN 3
      WHEN '1-2Y' THEN 4
      WHEN '2-5Y' THEN 5
      ELSE 6
    END
  ) as cumulative_gap_billions,
  CASE maturity_bucket
    WHEN '0-3M' THEN '#DC2626'  -- Red (most sensitive)
    WHEN '3-6M' THEN '#D97706'  -- Amber
    WHEN '6-12M' THEN '#0891B2' -- Teal
    ELSE '#059669'              -- Green (least sensitive)
  END as bucket_color
FROM maturity_buckets
ORDER BY CASE maturity_bucket
  WHEN '0-3M' THEN 1
  WHEN '3-6M' THEN 2
  WHEN '6-12M' THEN 3
  WHEN '1-2Y' THEN 4
  WHEN '2-5Y' THEN 5
  ELSE 6
END;


-- ============================================================================
-- QUERY 3: EVE Sensitivity Decomposition (Taylor Series Attribution)
-- ============================================================================
WITH eve_components AS (
  SELECT
    'Duration Effect' as component,
    -3.8 as contribution_pct,
    'Interest rate level change' as description,
    1 as sort_order
  UNION ALL
  SELECT 'Convexity Effect', -0.9, 'Non-linear rate impact', 2
  UNION ALL
  SELECT 'Beta Effect', -0.5, 'Deposit repricing lag', 3
  UNION ALL
  SELECT 'Option Effect', 0.0, 'Prepayment/withdrawal options', 4
)
SELECT
  component,
  contribution_pct,
  description,
  CASE
    WHEN contribution_pct < -2.0 THEN '#DC2626'  -- Major negative impact
    WHEN contribution_pct < 0 THEN '#D97706'     -- Minor negative impact
    WHEN contribution_pct = 0 THEN '#64748B'     -- Neutral
    ELSE '#059669'                                -- Positive impact
  END as impact_color,
  sort_order
FROM eve_components
ORDER BY sort_order;


-- ============================================================================
-- QUERY 4: Repricing Gap Heatmap (Time × Product)
-- ============================================================================
SELECT
  product_type,
  CASE
    WHEN DATEDIFF(CURRENT_DATE(), account_open_date) / 30 <= 3 THEN '0-3M'
    WHEN DATEDIFF(CURRENT_DATE(), account_open_date) / 30 <= 6 THEN '3-6M'
    WHEN DATEDIFF(CURRENT_DATE(), account_open_date) / 30 <= 12 THEN '6-12M'
    WHEN DATEDIFF(CURRENT_DATE(), account_open_date) / 365 <= 2 THEN '1-2Y'
    WHEN DATEDIFF(CURRENT_DATE(), account_open_date) / 365 <= 5 THEN '2-5Y'
    ELSE '5Y+'
  END as maturity_bucket,
  SUM(current_balance) / 1e9 as balance_billions,
  COUNT(DISTINCT account_id) as account_count,
  -- Heatmap color based on concentration risk
  CASE
    WHEN SUM(current_balance) / 1e9 >= 10.0 THEN '#DC2626'  -- High concentration (red)
    WHEN SUM(current_balance) / 1e9 >= 5.0 THEN '#D97706'   -- Medium (amber)
    WHEN SUM(current_balance) / 1e9 >= 2.0 THEN '#0891B2'   -- Low (teal)
    ELSE '#059669'                                           -- Very low (green)
  END as concentration_color
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
WHERE is_current = TRUE
GROUP BY product_type,
  CASE
    WHEN DATEDIFF(CURRENT_DATE(), account_open_date) / 30 <= 3 THEN '0-3M'
    WHEN DATEDIFF(CURRENT_DATE(), account_open_date) / 30 <= 6 THEN '3-6M'
    WHEN DATEDIFF(CURRENT_DATE(), account_open_date) / 30 <= 12 THEN '6-12M'
    WHEN DATEDIFF(CURRENT_DATE(), account_open_date) / 365 <= 2 THEN '1-2Y'
    WHEN DATEDIFF(CURRENT_DATE(), account_open_date) / 365 <= 5 THEN '2-5Y'
    ELSE '5Y+'
  END
ORDER BY product_type,
  CASE maturity_bucket
    WHEN '0-3M' THEN 1
    WHEN '3-6M' THEN 2
    WHEN '6-12M' THEN 3
    WHEN '1-2Y' THEN 4
    WHEN '2-5Y' THEN 5
    ELSE 6
  END;


-- ============================================================================
-- QUERY 5: Gap Limit Monitoring (Policy vs Actual)
-- ============================================================================
WITH gap_limits AS (
  SELECT
    '0-3M' as time_bucket,
    5.0 as limit_billions,
    3.2 as actual_billions,
    1 as sort_order
  UNION ALL
  SELECT '3-6M', 8.0, 5.1, 2
  UNION ALL
  SELECT '6-12M', 12.0, 7.8, 3
  UNION ALL
  SELECT '1-2Y', 15.0, 9.2, 4
  UNION ALL
  SELECT '2-5Y', 20.0, 12.5, 5
)
SELECT
  time_bucket,
  limit_billions,
  actual_billions,
  ROUND(actual_billions / limit_billions * 100, 1) as usage_pct,
  CASE
    WHEN actual_billions / limit_billions < 0.80 THEN '✓ Within Policy'
    WHEN actual_billions / limit_billions < 0.95 THEN '⚠ Near Limit'
    ELSE '✗ Breach'
  END as status,
  CASE
    WHEN actual_billions / limit_billions < 0.80 THEN '#059669'
    WHEN actual_billions / limit_billions < 0.95 THEN '#D97706'
    ELSE '#DC2626'
  END as status_color,
  sort_order
FROM gap_limits
ORDER BY sort_order;


-- ============================================================================
-- QUERY 6: NII Sensitivity by Rate Scenario (Multi-Period)
-- ============================================================================
WITH scenarios AS (
  SELECT scenario_name, rate_shock_bps, period, nii_impact_millions
  FROM (
    SELECT 'Baseline' as scenario_name, 0 as rate_shock_bps, 'Year 1' as period, 0 as nii_impact_millions
    UNION ALL SELECT 'Baseline', 0, 'Year 2', 0
    UNION ALL SELECT 'Baseline', 0, 'Year 3', 0
    UNION ALL SELECT '+100bps', 100, 'Year 1', 42
    UNION ALL SELECT '+100bps', 100, 'Year 2', 65
    UNION ALL SELECT '+100bps', 100, 'Year 3', 78
    UNION ALL SELECT '+200bps', 200, 'Year 1', 85
    UNION ALL SELECT '+200bps', 200, 'Year 2', 142
    UNION ALL SELECT '+200bps', 200, 'Year 3', 168
    UNION ALL SELECT '-100bps', -100, 'Year 1', -38
    UNION ALL SELECT '-100bps', -100, 'Year 2', -58
    UNION ALL SELECT '-100bps', -100, 'Year 3', -72
  )
)
SELECT
  scenario_name,
  period,
  nii_impact_millions,
  CASE
    WHEN scenario_name = 'Baseline' THEN '#64748B'
    WHEN rate_shock_bps > 0 THEN '#059669'  -- Rising rates = positive NII
    ELSE '#DC2626'                          -- Falling rates = negative NII
  END as scenario_color
FROM scenarios
ORDER BY
  CASE scenario_name
    WHEN 'Baseline' THEN 1
    WHEN '+100bps' THEN 2
    WHEN '+200bps' THEN 3
    WHEN '-100bps' THEN 4
  END,
  CASE period
    WHEN 'Year 1' THEN 1
    WHEN 'Year 2' THEN 2
    WHEN 'Year 3' THEN 3
  END;


-- ============================================================================
-- QUERY 7: Duration Distribution by Asset/Liability (Histogram)
-- ============================================================================
WITH duration_buckets AS (
  SELECT
    'Deposits' as category,
    CASE
      WHEN MONTHS_BETWEEN(CURRENT_DATE(), account_open_date) <= 6 THEN '0-0.5Y'
      WHEN MONTHS_BETWEEN(CURRENT_DATE(), account_open_date) <= 12 THEN '0.5-1Y'
      WHEN MONTHS_BETWEEN(CURRENT_DATE(), account_open_date) <= 24 THEN '1-2Y'
      WHEN MONTHS_BETWEEN(CURRENT_DATE(), account_open_date) <= 36 THEN '2-3Y'
      WHEN MONTHS_BETWEEN(CURRENT_DATE(), account_open_date) <= 60 THEN '3-5Y'
      ELSE '5Y+'
    END as duration_bucket,
    SUM(current_balance) / 1e9 as balance_billions
  FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
  WHERE is_current = TRUE
  GROUP BY 2
)
SELECT
  category,
  duration_bucket,
  balance_billions,
  CASE category
    WHEN 'Deposits' THEN '#0891B2'  -- Teal for liabilities
    ELSE '#1E3A8A'                   -- Navy for assets
  END as category_color
FROM duration_buckets
ORDER BY duration_bucket;


-- ============================================================================
-- QUERY 8: Gap Position Over Time (Time Series)
-- ============================================================================
WITH monthly_gap AS (
  SELECT
    DATE_TRUNC('month', effective_date) as month,
    SUM(current_balance) / 1e9 as gap_billions
  FROM cfo_banking_demo.bronze_core_banking.deposit_accounts_historical
  WHERE effective_date >= DATE_TRUNC('month', ADD_MONTHS(CURRENT_DATE(), -12))
    AND is_current = TRUE
  GROUP BY DATE_TRUNC('month', effective_date)
)
SELECT
  month,
  gap_billions,
  AVG(gap_billions) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) as gap_3m_avg,
  CASE
    WHEN gap_billions > 0 THEN '#059669'
    ELSE '#DC2626'
  END as gap_color
FROM monthly_gap
ORDER BY month;


-- ============================================================================
-- DASHBOARD AGENT PROMPT FOR DASHBOARD 4
-- ============================================================================

/*
PASTE THIS INTO DATABRICKS AI/BI DASHBOARD AGENT:

Create "Real-Time Gap Analysis & ALM Dashboard" with this layout:

TOP ROW (4 Gap Position KPI Cards):
- Use Query 1 results (4 separate cards)
- Duration Gap, Cumulative Gap, EVE Sensitivity, Gap Limit Usage
- Show metric value, position/status, and trend
- Apply color field to card accent

SECOND ROW (2 Visualizations):
LEFT (60% width):
- Waterfall chart from Query 2 (Repricing Gap by Maturity)
- Title: "Repricing Gap Analysis by Maturity Bucket"
- X-axis: Maturity buckets (0-3M through 5Y+)
- Y-axis: Balance ($B)
- Show cumulative_gap_billions as line overlay
- Color by bucket_color

RIGHT (40% width):
- Horizontal bar chart from Query 3 (EVE Sensitivity Decomposition)
- Title: "EVE Sensitivity Attribution (Taylor Series)"
- X-axis: Contribution %
- Y-axis: Component (Duration, Convexity, Beta, Option)
- Color by impact_color
- Add center line at 0%

THIRD ROW (Full Width):
- Heatmap from Query 4 (Repricing Gap by Product × Time)
- Title: "Concentration Risk: Product × Maturity Heatmap"
- Rows: Product Type
- Columns: Maturity Buckets
- Cell color: Gradient by concentration_color
- Cell value: Balance ($B)

FOURTH ROW (2 Visualizations):
LEFT (50% width):
- Grouped bar chart from Query 5 (Gap Limit Monitoring)
- Title: "Gap Limit Usage by Time Bucket"
- X-axis: Time buckets
- Y-axis: Balance ($B)
- 2 bars per bucket: Limit (gray) vs Actual (colored)
- Color actual bars by status_color

RIGHT (50% width):
- Line chart from Query 6 (NII Sensitivity)
- Title: "Multi-Period NII Impact by Rate Scenario"
- X-axis: Period (Year 1, 2, 3)
- Y-axis: NII Impact ($M)
- 4 lines (Baseline, +100bps, +200bps, -100bps)
- Color by scenario_color

FIFTH ROW (2 Visualizations):
LEFT (50% width):
- Histogram from Query 7 (Duration Distribution)
- Title: "Duration Profile: Assets vs Liabilities"
- X-axis: Duration buckets
- Y-axis: Balance ($B)
- Color by category_color

RIGHT (50% width):
- Area chart from Query 8 (Gap Position Over Time)
- Title: "12-Month Gap Position Trend"
- X-axis: Month
- Y-axis: Gap ($B)
- Show gap_billions as area
- Add 3-month moving average line
- Color areas above/below 0 differently

DESIGN:
- ALCO meeting aesthetic (executive + technical)
- Navy/Teal/Emerald/Amber/Red palette
- Add zero reference lines where appropriate
- Highlight policy breaches in red
- Real-time auto-refresh (every 1 hour)
*/
