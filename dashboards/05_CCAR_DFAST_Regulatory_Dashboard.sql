-- ============================================================================
-- DASHBOARD 5: CCAR/DFAST REGULATORY REPORTING
-- Audience: CFO, Chief Risk Officer, Board Risk Committee, Regulators
-- ============================================================================

-- ============================================================================
-- QUERY 1: Regulatory Stress Test Summary KPIs (5 Cards)
-- ============================================================================

-- Card 1: Baseline CET1 Ratio
SELECT
  'CET1 Ratio (Baseline)' as metric_name,
  12.8 as ratio_pct,
  '✓ Well-Capitalized' as status,
  '#059669' as color  -- Green (>10.5%)
;

-- Card 2: Severely Adverse CET1 (Minimum)
SELECT
  'CET1 @ Severely Adverse' as metric_name,
  8.2 as ratio_pct,
  '⚠ Above Minimum' as status,
  CASE
    WHEN 8.2 >= 9.0 THEN '#059669'   -- Well above minimum
    WHEN 8.2 >= 7.0 THEN '#D97706'   -- Above minimum (caution)
    ELSE '#DC2626'                    -- Below minimum (fail)
  END as color
;

-- Card 3: NII Impact (Severely Adverse)
SELECT
  'NII Impact (2Y Cumulative)' as metric_name,
  -285 as impact_millions,
  '-12.3%' as pct_change,
  '#DC2626' as color  -- Red (negative impact)
;

-- Card 4: Deposit Runoff (Severely Adverse)
SELECT
  'Deposit Runoff (2Y)' as metric_name,
  -8.5 as runoff_billions,
  '-28.2%' as pct_of_total,
  '#DC2626' as color
;

-- Card 5: LCR Ratio (Stress)
SELECT
  'LCR @ Stress' as metric_name,
  105 as lcr_pct,
  '✓ Above 100%' as status,
  CASE
    WHEN 105 >= 100 THEN '#059669'
    WHEN 105 >= 90 THEN '#D97706'
    ELSE '#DC2626'
  END as color
;


-- ============================================================================
-- QUERY 2: Multi-Period Capital Ratios by Scenario (Line Chart)
-- ============================================================================
WITH capital_projections AS (
  SELECT
    'Baseline' as scenario,
    'Q0' as quarter,
    12.8 as cet1_pct,
    14.2 as tier1_pct,
    16.5 as total_capital_pct,
    0 as sort_order
  UNION ALL SELECT 'Baseline', 'Q1', 12.9, 14.3, 16.6, 1
  UNION ALL SELECT 'Baseline', 'Q2', 13.0, 14.4, 16.7, 2
  UNION ALL SELECT 'Baseline', 'Q3', 13.1, 14.5, 16.8, 3
  UNION ALL SELECT 'Baseline', 'Q4', 13.2, 14.6, 16.9, 4
  UNION ALL SELECT 'Baseline', 'Q5', 13.3, 14.7, 17.0, 5
  UNION ALL SELECT 'Baseline', 'Q6', 13.4, 14.8, 17.1, 6
  UNION ALL SELECT 'Baseline', 'Q7', 13.5, 14.9, 17.2, 7
  UNION ALL SELECT 'Baseline', 'Q8', 13.6, 15.0, 17.3, 8

  UNION ALL SELECT 'Adverse', 'Q0', 12.8, 14.2, 16.5, 0
  UNION ALL SELECT 'Adverse', 'Q1', 12.3, 13.7, 16.0, 1
  UNION ALL SELECT 'Adverse', 'Q2', 11.8, 13.2, 15.5, 2
  UNION ALL SELECT 'Adverse', 'Q3', 11.4, 12.8, 15.1, 3
  UNION ALL SELECT 'Adverse', 'Q4', 11.0, 12.4, 14.7, 4
  UNION ALL SELECT 'Adverse', 'Q5', 10.8, 12.2, 14.5, 5
  UNION ALL SELECT 'Adverse', 'Q6', 10.6, 12.0, 14.3, 6
  UNION ALL SELECT 'Adverse', 'Q7', 10.5, 11.9, 14.2, 7
  UNION ALL SELECT 'Adverse', 'Q8', 10.4, 11.8, 14.1, 8

  UNION ALL SELECT 'Severely Adverse', 'Q0', 12.8, 14.2, 16.5, 0
  UNION ALL SELECT 'Severely Adverse', 'Q1', 11.5, 12.9, 15.2, 1
  UNION ALL SELECT 'Severely Adverse', 'Q2', 10.2, 11.6, 13.9, 2
  UNION ALL SELECT 'Severely Adverse', 'Q3', 9.3, 10.7, 13.0, 3
  UNION ALL SELECT 'Severely Adverse', 'Q4', 8.8, 10.2, 12.5, 4
  UNION ALL SELECT 'Severely Adverse', 'Q5', 8.5, 9.9, 12.2, 5
  UNION ALL SELECT 'Severely Adverse', 'Q6', 8.3, 9.7, 12.0, 6
  UNION ALL SELECT 'Severely Adverse', 'Q7', 8.2, 9.6, 11.9, 7
  UNION ALL SELECT 'Severely Adverse', 'Q8', 8.2, 9.6, 11.9, 8
)
SELECT
  scenario,
  quarter,
  cet1_pct,
  tier1_pct,
  total_capital_pct,
  CASE scenario
    WHEN 'Baseline' THEN '#059669'          -- Green
    WHEN 'Adverse' THEN '#D97706'           -- Amber
    WHEN 'Severely Adverse' THEN '#DC2626'  -- Red
  END as scenario_color,
  sort_order
FROM capital_projections
ORDER BY scenario, sort_order;


-- ============================================================================
-- QUERY 3: Balance Sheet Projections Under Stress (Stacked Area)
-- ============================================================================
WITH balance_sheet_stress AS (
  SELECT
    'Q0' as quarter,
    30.1 as deposits_billions,
    35.2 as loans_billions,
    5.8 as securities_billions,
    0 as sort_order
  UNION ALL SELECT 'Q1', 29.5, 35.0, 5.9, 1
  UNION ALL SELECT 'Q2', 28.8, 34.7, 6.0, 2
  UNION ALL SELECT 'Q3', 27.9, 34.3, 6.1, 3
  UNION ALL SELECT 'Q4', 27.2, 33.9, 6.2, 4
  UNION ALL SELECT 'Q5', 26.5, 33.5, 6.3, 5
  UNION ALL SELECT 'Q6', 25.8, 33.1, 6.4, 6
  UNION ALL SELECT 'Q7', 25.2, 32.7, 6.5, 7
  UNION ALL SELECT 'Q8', 24.7, 32.3, 6.6, 8
)
SELECT
  quarter,
  deposits_billions,
  loans_billions,
  securities_billions,
  (deposits_billions + loans_billions + securities_billions) as total_assets_billions,
  sort_order
FROM balance_sheet_stress
ORDER BY sort_order;


-- ============================================================================
-- QUERY 4: NII Waterfall (Pre-Tax Pre-Provision)
-- ============================================================================
WITH nii_components AS (
  SELECT
    'Starting NII' as component,
    2320 as amount_millions,
    1 as sort_order,
    '#64748B' as color
  UNION ALL SELECT 'Asset Repricing Impact', -285, 2, '#DC2626'
  UNION ALL SELECT 'Liability Repricing Impact', 142, 3, '#059669'
  UNION ALL SELECT 'Volume Impact (Runoff)', -165, 4, '#DC2626'
  UNION ALL SELECT 'Mix Impact', -38, 5, '#D97706'
  UNION ALL SELECT 'Fee Income Change', -52, 6, '#DC2626'
  UNION ALL SELECT 'Ending NII', 1922, 7, '#1E3A8A'
)
SELECT
  component,
  amount_millions,
  -- Calculate cumulative for waterfall
  SUM(amount_millions) OVER (ORDER BY sort_order) as cumulative_millions,
  sort_order,
  color
FROM nii_components
ORDER BY sort_order;


-- ============================================================================
-- QUERY 5: Deposit Runoff by Segment (Severely Adverse Scenario)
-- ============================================================================
SELECT
  c.relationship_category,
  SUM(d.current_balance) / 1e9 as current_balance_billions,
  -- Apply stress runoff rates
  CASE
    WHEN c.relationship_category = 'Strategic' THEN 0.12    -- 12% runoff
    WHEN c.relationship_category = 'Tactical' THEN 0.28     -- 28% runoff
    WHEN c.relationship_category = 'Expendable' THEN 0.45   -- 45% runoff
  END as stress_runoff_rate,
  SUM(d.current_balance) *
    CASE
      WHEN c.relationship_category = 'Strategic' THEN 0.88
      WHEN c.relationship_category = 'Tactical' THEN 0.72
      WHEN c.relationship_category = 'Expendable' THEN 0.55
    END / 1e9 as stressed_balance_billions,
  SUM(d.current_balance) *
    CASE
      WHEN c.relationship_category = 'Strategic' THEN 0.12
      WHEN c.relationship_category = 'Tactical' THEN 0.28
      WHEN c.relationship_category = 'Expendable' THEN 0.45
    END / 1e9 as runoff_billions,
  CASE c.relationship_category
    WHEN 'Strategic' THEN '#059669'
    WHEN 'Tactical' THEN '#0891B2'
    WHEN 'Expendable' THEN '#DC2626'
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
ORDER BY runoff_billions DESC;


-- ============================================================================
-- QUERY 6: LCR Components (High-Quality Liquid Assets vs Net Outflows)
-- ============================================================================
WITH lcr_components AS (
  SELECT
    'Baseline' as scenario,
    8500 as hqla_millions,
    7200 as net_outflows_millions,
    ROUND(8500.0 / 7200 * 100, 0) as lcr_pct,
    1 as sort_order
  UNION ALL SELECT 'Adverse', 8200, 8100, ROUND(8200.0 / 8100 * 100, 0), 2
  UNION ALL SELECT 'Severely Adverse', 7800, 7400, ROUND(7800.0 / 7400 * 100, 0), 3
)
SELECT
  scenario,
  hqla_millions,
  net_outflows_millions,
  lcr_pct,
  CASE
    WHEN lcr_pct >= 100 THEN '✓ Compliant'
    WHEN lcr_pct >= 90 THEN '⚠ Near Breach'
    ELSE '✗ Non-Compliant'
  END as compliance_status,
  CASE
    WHEN lcr_pct >= 100 THEN '#059669'
    WHEN lcr_pct >= 90 THEN '#D97706'
    ELSE '#DC2626'
  END as lcr_color,
  sort_order
FROM lcr_components
ORDER BY sort_order;


-- ============================================================================
-- QUERY 7: Standardized CCAR Template (PP&R Schedule A)
-- ============================================================================
WITH ccar_schedule AS (
  SELECT
    'Net Interest Income' as line_item,
    2320 as baseline_millions,
    2145 as adverse_millions,
    1922 as severely_adverse_millions,
    1 as sort_order,
    'Revenue' as category
  UNION ALL SELECT 'Non-Interest Income', 485, 425, 368, 2, 'Revenue'
  UNION ALL SELECT 'Pre-Provision Net Revenue', 2805, 2570, 2290, 3, 'Revenue'
  UNION ALL SELECT 'Provision for Credit Losses', -320, -580, -925, 4, 'Expense'
  UNION ALL SELECT 'Non-Interest Expense', -1825, -1825, -1825, 5, 'Expense'
  UNION ALL SELECT 'Net Income Before Taxes', 660, 165, -460, 6, 'Income'
  UNION ALL SELECT 'Taxes', -165, -41, 115, 7, 'Taxes'
  UNION ALL SELECT 'Net Income', 495, 124, -345, 8, 'Income'
  UNION ALL SELECT 'Dividends & Distributions', -180, -180, -180, 9, 'Capital'
  UNION ALL SELECT 'Retained Earnings', 315, -56, -525, 10, 'Capital'
)
SELECT
  line_item,
  baseline_millions,
  adverse_millions,
  severely_adverse_millions,
  (severely_adverse_millions - baseline_millions) as stress_impact_millions,
  ROUND((severely_adverse_millions - baseline_millions) * 100.0 / NULLIF(baseline_millions, 0), 1) as stress_impact_pct,
  category,
  sort_order
FROM ccar_schedule
ORDER BY sort_order;


-- ============================================================================
-- QUERY 8: Risk-Weighted Assets (RWA) by Scenario
-- ============================================================================
WITH rwa_projections AS (
  SELECT
    'Q0' as quarter,
    'Baseline' as scenario,
    42500 as rwa_millions,
    12.8 as cet1_ratio,
    0 as sort_order
  UNION ALL SELECT 'Q4', 'Baseline', 43200, 13.2, 1
  UNION ALL SELECT 'Q8', 'Baseline', 43800, 13.6, 2
  UNION ALL SELECT 'Q0', 'Adverse', 42500, 12.8, 3
  UNION ALL SELECT 'Q4', 'Adverse', 44100, 11.0, 4
  UNION ALL SELECT 'Q8', 'Adverse', 45200, 10.4, 5
  UNION ALL SELECT 'Q0', 'Severely Adverse', 42500, 12.8, 6
  UNION ALL SELECT 'Q4', 'Severely Adverse', 46800, 8.8, 7
  UNION ALL SELECT 'Q8', 'Severely Adverse', 48500, 8.2, 8
)
SELECT
  quarter,
  scenario,
  rwa_millions,
  cet1_ratio,
  CASE scenario
    WHEN 'Baseline' THEN '#059669'
    WHEN 'Adverse' THEN '#D97706'
    WHEN 'Severely Adverse' THEN '#DC2626'
  END as scenario_color,
  sort_order
FROM rwa_projections
ORDER BY sort_order;


-- ============================================================================
-- QUERY 9: Stress Test Pass/Fail Summary (Traffic Light Dashboard)
-- ============================================================================
WITH stress_tests AS (
  SELECT
    'CET1 Minimum > 7.0%' as test_name,
    7.0 as threshold,
    8.2 as result,
    'Pass' as status,
    '#059669' as status_color,
    1 as sort_order
  UNION ALL SELECT 'CET1 Minimum > 9.0%', 9.0, 8.2, 'Fail', '#DC2626', 2
  UNION ALL SELECT 'Tier 1 Minimum > 8.5%', 8.5, 9.6, 'Pass', '#059669', 3
  UNION ALL SELECT 'Total Capital > 10.5%', 10.5, 11.9, 'Pass', '#059669', 4
  UNION ALL SELECT 'LCR > 100%', 100, 105, 'Pass', '#059669', 5
  UNION ALL SELECT 'Leverage Ratio > 4.0%', 4.0, 4.8, 'Pass', '#059669', 6
)
SELECT
  test_name,
  threshold,
  result,
  status,
  ROUND((result - threshold), 2) as buffer,
  status_color,
  sort_order
FROM stress_tests
ORDER BY sort_order;


-- ============================================================================
-- DASHBOARD AGENT PROMPT FOR DASHBOARD 5
-- ============================================================================

/*
PASTE THIS INTO DATABRICKS AI/BI DASHBOARD AGENT:

Create "CCAR/DFAST Regulatory Reporting Dashboard" with this layout:

TOP ROW (5 Regulatory KPI Cards):
- Use Query 1 results (5 cards)
- CET1 Baseline, CET1 Stress, NII Impact, Deposit Runoff, LCR
- Large numbers with status indicators
- Apply color field to card accent

SECOND ROW (Full Width):
- Multi-line chart from Query 2 (Capital Ratios by Scenario)
- Title: "Capital Adequacy Projections (9-Quarter Horizon)"
- X-axis: Quarters (Q0-Q8)
- Y-axis: Ratio (%)
- 3 lines per scenario × 3 ratios (CET1, Tier 1, Total)
- Add horizontal reference lines at 7%, 9%, 10.5%
- Color by scenario_color

THIRD ROW (2 Visualizations):
LEFT (60% width):
- Waterfall chart from Query 4 (NII Waterfall)
- Title: "Pre-Tax Pre-Provision Net Revenue Bridge"
- Show cumulative impact from starting to ending NII
- Color positive/negative impacts differently

RIGHT (40% width):
- Stacked area from Query 3 (Balance Sheet)
- Title: "Balance Sheet Under Severely Adverse"
- X-axis: Quarters
- Y-axis: Assets ($B)
- 3 layers: Deposits, Loans, Securities

FOURTH ROW (2 Visualizations):
LEFT (50% width):
- Grouped bar chart from Query 5 (Deposit Runoff)
- Title: "Deposit Runoff by Segment (Severely Adverse)"
- X-axis: Relationship category
- Y-axis: Balance ($B)
- 2 bars: Current vs Stressed
- Show runoff_billions as annotation

RIGHT (50% width):
- Grouped bar from Query 6 (LCR Components)
- Title: "Liquidity Coverage Ratio by Scenario"
- X-axis: Scenario
- Y-axis: Amount ($M)
- 2 bars per scenario: HQLA vs Net Outflows
- Show LCR % as line overlay
- Add 100% reference line

FIFTH ROW (Full Width):
- Table from Query 7 (CCAR Schedule A)
- Title: "Standardized CCAR Reporting Template (PP&R Schedule A)"
- Columns: Line Item, Baseline, Adverse, Severely Adverse, Impact ($M), Impact (%)
- Apply conditional formatting:
  - Green for positive impact
  - Red for negative impact
- Bold key rows (PPNR, Net Income, Retained Earnings)

BOTTOM ROW (2 Visualizations):
LEFT (60% width):
- Dual-axis chart from Query 8 (RWA)
- Title: "Risk-Weighted Assets & CET1 Ratio Evolution"
- X-axis: Quarters
- Left Y-axis: RWA ($M)
- Right Y-axis: CET1 Ratio (%)
- Bar for RWA, line for CET1

RIGHT (40% width):
- Traffic light dashboard from Query 9 (Pass/Fail)
- Title: "Stress Test Results Summary"
- Show test_name, threshold, result, buffer
- Color entire row by status_color
- Large visual pass/fail indicators

DESIGN:
- Regulatory reporting aesthetic (formal, official)
- Use official Fed/OCC color schemes
- Add Fed logo placeholder area
- Include "Confidential Supervisory Information" footer
- Export-ready for PDF submission
- Print-optimized layout
*/
