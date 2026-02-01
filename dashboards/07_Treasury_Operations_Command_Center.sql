-- ============================================================================
-- DASHBOARD 7: TREASURY OPERATIONS COMMAND CENTER
-- Audience: Treasury Operations, Funding Desk, Liquidity Management
-- ============================================================================

-- ============================================================================
-- QUERY 1: Real-Time Treasury Position KPIs (6 Cards)
-- ============================================================================

-- Card 1: Available Liquidity
SELECT
  'Available Liquidity' as metric_name,
  8.5 as amount_billions,
  '+$450M' as daily_change,
  '↑' as trend_direction,
  '#059669' as color
;

-- Card 2: Net Funding Position
SELECT
  'Net Funding Position' as metric_name,
  2.1 as amount_billions,
  'Positive' as position_status,
  '→' as trend_direction,
  '#0891B2' as color
;

-- Card 3: Wholesale Funding Ratio
SELECT
  'Wholesale Funding %' as metric_name,
  18.5 as ratio_pct,
  'Within Policy (<25%)' as status,
  '↓' as trend_direction,
  '#059669' as color
;

-- Card 4: Deposit Flow (Today)
SELECT
  'Net Deposit Flow (Today)' as metric_name,
  -125 as flow_millions,
  'Net Outflow' as flow_direction,
  '↓' as trend_direction,
  '#DC2626' as color
;

-- Card 5: Average Deposit Rate
SELECT
  'Avg Deposit Rate' as metric_name,
  2.85 as rate_pct,
  'vs Market: -15bps' as competitive_position,
  '↑' as trend_direction,
  '#D97706' as color
;

-- Card 6: Brokered Deposits
SELECT
  'Brokered Deposits' as metric_name,
  4.2 as amount_billions,
  '13.9% of Total' as pct_of_total,
  '→' as trend_direction,
  '#D97706' as color
;


-- ============================================================================
-- QUERY 2: Intraday Deposit Flows (Line Chart - Real-Time)
-- ============================================================================
WITH intraday_flows AS (
  SELECT hour, inflows, outflows, net_flow
  FROM (
    SELECT '08:00' as hour, 250 as inflows, 180 as outflows, 70 as net_flow
    UNION ALL SELECT '09:00', 420, 320, 100
    UNION ALL SELECT '10:00', 580, 450, 130
    UNION ALL SELECT '11:00', 720, 680, 40
    UNION ALL SELECT '12:00', 650, 720, -70
    UNION ALL SELECT '13:00', 520, 580, -60
    UNION ALL SELECT '14:00', 680, 720, -40
    UNION ALL SELECT '15:00', 890, 820, 70
    UNION ALL SELECT '16:00', 420, 520, -100
    UNION ALL SELECT '17:00', 180, 240, -60
  )
)
SELECT
  hour,
  inflows,
  outflows,
  net_flow,
  SUM(net_flow) OVER (ORDER BY hour) as cumulative_flow,
  CASE
    WHEN net_flow >= 0 THEN '#059669'
    ELSE '#DC2626'
  END as flow_color
FROM intraday_flows
ORDER BY hour;


-- ============================================================================
-- QUERY 3: Funding Composition (Donut Chart)
-- ============================================================================
SELECT
  funding_source,
  amount_billions,
  ROUND(amount_billions / SUM(amount_billions) OVER () * 100, 1) as pct_of_total,
  cost_bps,
  CASE funding_source
    WHEN 'Core Deposits' THEN '#059669'        -- Green (cheapest, most stable)
    WHEN 'Promotional CDs' THEN '#0891B2'      -- Teal
    WHEN 'Brokered Deposits' THEN '#D97706'    -- Amber (more expensive)
    WHEN 'FHLB Advances' THEN '#DC2626'        -- Red (most expensive)
    WHEN 'Fed Funds Purchased' THEN '#991B1B'  -- Dark red
    ELSE '#64748B'
  END as source_color
FROM (
  SELECT 'Core Deposits' as funding_source, 21.5 as amount_billions, 245 as cost_bps
  UNION ALL SELECT 'Promotional CDs', 4.4, 385
  UNION ALL SELECT 'Brokered Deposits', 4.2, 420
  UNION ALL SELECT 'FHLB Advances', 2.8, 485
  UNION ALL SELECT 'Fed Funds Purchased', 0.6, 525
)
ORDER BY amount_billions DESC;


-- ============================================================================
-- QUERY 4: Deposit Rate Positioning vs Competitors (Scatter Plot)
-- ============================================================================
WITH rate_comparison AS (
  SELECT
    'Checking' as product_type,
    0.50 as our_rate_pct,
    0.55 as market_avg_pct,
    0.75 as online_bank_avg_pct,
    8.5 as balance_billions
  UNION ALL SELECT 'Savings', 2.25, 2.45, 3.10, 9.2
  UNION ALL SELECT 'Money Market', 3.15, 3.35, 3.85, 8.8
  UNION ALL SELECT 'CD 6M', 3.85, 4.00, 4.25, 2.1
  UNION ALL SELECT 'CD 12M', 4.10, 4.25, 4.50, 1.5
)
SELECT
  product_type,
  our_rate_pct,
  market_avg_pct,
  online_bank_avg_pct,
  balance_billions,
  (our_rate_pct - market_avg_pct) * 100 as spread_vs_market_bps,
  CASE
    WHEN our_rate_pct >= market_avg_pct THEN '✓ Competitive'
    WHEN (market_avg_pct - our_rate_pct) <= 0.10 THEN '⚠ Below Market'
    ELSE '✗ Significantly Below'
  END as competitive_status,
  CASE
    WHEN our_rate_pct >= market_avg_pct THEN '#059669'
    WHEN (market_avg_pct - our_rate_pct) <= 0.10 THEN '#D97706'
    ELSE '#DC2626'
  END as status_color
FROM rate_comparison
ORDER BY balance_billions DESC;


-- ============================================================================
-- QUERY 5: Liquidity Buffer & LCR Trend (Area Chart)
-- ============================================================================
WITH daily_liquidity AS (
  SELECT date, hqla, net_outflows, lcr_pct
  FROM (
    SELECT '2026-01-17' as date, 8200 as hqla, 7100 as net_outflows, 115.5 as lcr_pct
    UNION ALL SELECT '2026-01-20', 8300, 7150, 116.1
    UNION ALL SELECT '2026-01-21', 8250, 7200, 114.6
    UNION ALL SELECT '2026-01-22', 8400, 7180, 117.0
    UNION ALL SELECT '2026-01-23', 8350, 7220, 115.7
    UNION ALL SELECT '2026-01-24', 8500, 7250, 117.2
    UNION ALL SELECT '2026-01-27', 8450, 7280, 116.1
    UNION ALL SELECT '2026-01-28', 8550, 7300, 117.1
    UNION ALL SELECT '2026-01-29', 8520, 7320, 116.4
    UNION ALL SELECT '2026-01-30', 8600, 7350, 117.0
    UNION ALL SELECT '2026-01-31', 8650, 7380, 117.2
  )
)
SELECT
  date,
  hqla,
  net_outflows,
  lcr_pct,
  (hqla - net_outflows) as liquidity_buffer,
  CASE
    WHEN lcr_pct >= 115 THEN '#059669'
    WHEN lcr_pct >= 100 THEN '#0891B2'
    WHEN lcr_pct >= 95 THEN '#D97706'
    ELSE '#DC2626'
  END as lcr_color
FROM daily_liquidity
ORDER BY date;


-- ============================================================================
-- QUERY 6: Wholesale Funding Maturity Profile (Bar Chart)
-- ============================================================================
WITH maturity_profile AS (
  SELECT
    '0-7D' as maturity_bucket,
    850 as amount_millions,
    5.25 as weighted_avg_rate_pct,
    1 as sort_order
  UNION ALL SELECT '8-30D', 1200, 5.15, 2
  UNION ALL SELECT '31-90D', 1850, 4.95, 3
  UNION ALL SELECT '91-180D', 2100, 4.75, 4
  UNION ALL SELECT '181-365D', 1650, 4.55, 5
  UNION ALL SELECT '1Y+', 980, 4.25, 6
)
SELECT
  maturity_bucket,
  amount_millions,
  weighted_avg_rate_pct,
  -- Calculate cumulative maturing amount
  SUM(amount_millions) OVER (ORDER BY sort_order) as cumulative_maturing_millions,
  CASE maturity_bucket
    WHEN '0-7D' THEN '#DC2626'   -- High rollover risk (red)
    WHEN '8-30D' THEN '#D97706'  -- Medium risk (amber)
    WHEN '31-90D' THEN '#0891B2' -- Lower risk (teal)
    ELSE '#059669'               -- Stable (green)
  END as maturity_color,
  sort_order
FROM maturity_profile
ORDER BY sort_order;


-- ============================================================================
-- QUERY 7: Deposit Flow Trends (Last 30 Days)
-- ============================================================================
WITH account_daily_changes AS (
  -- First, calculate balance changes per account per day
  SELECT
    account_id,
    DATE_TRUNC('day', effective_date) as flow_date,
    current_balance,
    LAG(current_balance) OVER (PARTITION BY account_id ORDER BY effective_date) as prev_balance
  FROM cfo_banking_demo.bronze_core_banking.deposit_accounts_historical
  WHERE effective_date >= DATE_ADD(CURRENT_DATE(), -31)
    AND effective_date < CURRENT_DATE()
),
account_flows AS (
  -- Calculate inflows and outflows per account
  SELECT
    flow_date,
    CASE
      WHEN current_balance > COALESCE(prev_balance, 0)
      THEN current_balance - COALESCE(prev_balance, 0)
      ELSE 0
    END as account_inflow,
    CASE
      WHEN current_balance < COALESCE(prev_balance, 0)
      THEN COALESCE(prev_balance, 0) - current_balance
      ELSE 0
    END as account_outflow
  FROM account_daily_changes
  WHERE prev_balance IS NOT NULL  -- Only compare when we have previous balance
),
daily_flows AS (
  -- Aggregate to daily totals
  SELECT
    flow_date,
    SUM(account_inflow) / 1e6 as inflows_millions,
    SUM(account_outflow) / 1e6 as outflows_millions
  FROM account_flows
  GROUP BY flow_date
)
SELECT
  flow_date,
  inflows_millions,
  outflows_millions,
  (inflows_millions - outflows_millions) as net_flow_millions,
  AVG(inflows_millions - outflows_millions) OVER (
    ORDER BY flow_date
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ) as net_flow_7d_avg,
  CASE
    WHEN (inflows_millions - outflows_millions) >= 0 THEN '#059669'
    ELSE '#DC2626'
  END as flow_color
FROM daily_flows
ORDER BY flow_date;


-- ============================================================================
-- QUERY 8: Brokered Deposits Tracker (Table with Maturity Schedule)
-- ============================================================================
WITH brokered_deposits AS (
  SELECT
    'CD-2024-Q1-001' as deal_id,
    '2024-03-15' as origination_date,
    '2025-03-15' as maturity_date,
    450 as amount_millions,
    4.25 as rate_pct,
    'Broker A' as broker_name,
    DATEDIFF('2025-03-15', CURRENT_DATE()) as days_to_maturity
  UNION ALL SELECT 'CD-2024-Q2-003', '2024-06-20', '2025-06-20', 580, 4.35, 'Broker B', DATEDIFF('2025-06-20', CURRENT_DATE())
  UNION ALL SELECT 'CD-2024-Q3-005', '2024-09-10', '2025-09-10', 720, 4.15, 'Broker A', DATEDIFF('2025-09-10', CURRENT_DATE())
  UNION ALL SELECT 'CD-2024-Q4-008', '2024-12-05', '2025-12-05', 650, 4.05, 'Broker C', DATEDIFF('2025-12-05', CURRENT_DATE())
  UNION ALL SELECT 'CD-2025-Q1-002', '2025-01-18', '2026-01-18', 820, 3.95, 'Broker B', DATEDIFF('2026-01-18', CURRENT_DATE())
)
SELECT
  deal_id,
  broker_name,
  amount_millions,
  rate_pct,
  origination_date,
  maturity_date,
  days_to_maturity,
  CASE
    WHEN days_to_maturity <= 30 THEN '🔴 Maturing Soon'
    WHEN days_to_maturity <= 90 THEN '🟡 Within 90 Days'
    ELSE '🟢 Stable'
  END as rollover_status,
  CASE
    WHEN days_to_maturity <= 30 THEN '#DC2626'
    WHEN days_to_maturity <= 90 THEN '#D97706'
    ELSE '#059669'
  END as status_color
FROM brokered_deposits
ORDER BY days_to_maturity;


-- ============================================================================
-- QUERY 9: Funding Cost Waterfall (Blended Rate Evolution)
-- ============================================================================
WITH cost_components AS (
  SELECT
    'Starting Blended Cost' as component,
    2.45 as rate_bps,
    1 as sort_order,
    '#64748B' as color
  UNION ALL SELECT 'Core Deposit Repricing', 0.15, 2, '#DC2626'
  UNION ALL SELECT 'CD Rollover Impact', 0.25, 3, '#DC2626'
  UNION ALL SELECT 'Brokered Deposit Increase', 0.18, 4, '#DC2626'
  UNION ALL SELECT 'FHLB Advance Change', -0.08, 5, '#059669'
  UNION ALL SELECT 'Mix Shift (Core Growth)', -0.12, 6, '#059669'
  UNION ALL SELECT 'Ending Blended Cost', 2.83, 7, '#1E3A8A'
)
SELECT
  component,
  rate_bps,
  -- Calculate cumulative for waterfall
  SUM(rate_bps) OVER (ORDER BY sort_order) as cumulative_rate_bps,
  sort_order,
  color
FROM cost_components
ORDER BY sort_order;


-- ============================================================================
-- QUERY 10: Real-Time Alert Feed (Streaming Updates)
-- ============================================================================
WITH treasury_alerts AS (
  SELECT
    CURRENT_TIMESTAMP() as alert_timestamp,
    'LCR below 105%' as alert_message,
    'Warning' as severity,
    'Liquidity' as category,
    '#D97706' as severity_color
  UNION ALL SELECT TIMESTAMP(CURRENT_DATE() || ' 14:30:00'), 'Large withdrawal: $25M from account 12345', 'Info', 'Operations', '#0891B2'
  UNION ALL SELECT TIMESTAMP(CURRENT_DATE() || ' 12:15:00'), 'Wholesale funding maturing in 5 days: $850M', 'Critical', 'Funding', '#DC2626'
  UNION ALL SELECT TIMESTAMP(CURRENT_DATE() || ' 10:45:00'), 'Deposit rate 20bps below market average', 'Warning', 'Pricing', '#D97706'
  UNION ALL SELECT TIMESTAMP(CURRENT_DATE() || ' 09:20:00'), 'Daily net outflow exceeds $200M', 'Warning', 'Liquidity', '#D97706'
)
SELECT
  alert_timestamp,
  alert_message,
  severity,
  category,
  TIMESTAMPDIFF(HOUR, alert_timestamp, CURRENT_TIMESTAMP()) as hours_ago,
  severity_color
FROM treasury_alerts
ORDER BY alert_timestamp DESC
LIMIT 10;


-- ============================================================================
-- DASHBOARD AGENT PROMPT FOR DASHBOARD 7
-- ============================================================================

/*
PASTE THIS INTO DATABRICKS AI/BI DASHBOARD AGENT:

Create "Treasury Operations Command Center Dashboard" with this layout:

TOP ROW (6 Real-Time KPI Cards - 2 rows of 3):
- Use Query 1 results (6 cards)
- Available Liquidity, Net Funding Position, Wholesale Funding %
- Deposit Flow, Avg Rate, Brokered Deposits
- Show daily change and trend arrows
- Apply color field to card accent

SECOND ROW (2 Visualizations):
LEFT (60% width):
- Multi-line chart from Query 2 (Intraday Flows)
- Title: "Intraday Deposit Flows (Real-Time)"
- X-axis: Hour of day
- Y-axis: Amount ($M)
- 3 lines: Inflows (green), Outflows (red), Net (blue)
- Show cumulative_flow as area overlay

RIGHT (40% width):
- Donut chart from Query 3 (Funding Composition)
- Title: "Funding Mix & Cost"
- Show amount_billions and cost_bps
- Color by source_color (green = cheapest)
- Center text: "Total: $XX.XB"

THIRD ROW (2 Visualizations):
LEFT (50% width):
- Scatter plot from Query 4 (Rate Positioning)
- Title: "Deposit Rate Positioning vs Market"
- X-axis: Product Type
- Y-axis: Rate %
- 3 markers per product: Our Rate, Market Avg, Online Banks
- Size bubbles by balance_billions
- Color by competitive_status

RIGHT (50% width):
- Area chart from Query 5 (Liquidity Buffer)
- Title: "10-Day LCR Trend & Liquidity Buffer"
- X-axis: Date
- Y-axis: Amount ($M) and LCR %
- 2 areas: HQLA (green), Net Outflows (red)
- LCR % as line overlay
- Add 100% reference line

FOURTH ROW (2 Visualizations):
LEFT (40% width):
- Stacked bar from Query 6 (Maturity Profile)
- Title: "Wholesale Funding Maturity Schedule"
- X-axis: Maturity buckets
- Y-axis: Amount ($M)
- Color by maturity_color (red = near-term)
- Show weighted_avg_rate_pct as annotation

RIGHT (60% width):
- Area chart from Query 7 (Deposit Flows)
- Title: "30-Day Deposit Flow Trends"
- X-axis: Date
- Y-axis: Amount ($M)
- 2 areas: Inflows (green), Outflows (red)
- Net flow as line
- Add 7-day moving average

FIFTH ROW (Full Width):
- Table from Query 8 (Brokered Deposits Tracker)
- Title: "Brokered Deposits Maturity Schedule"
- Columns: Deal ID, Broker, Amount, Rate, Origination, Maturity, Days to Maturity, Status
- Sort by days_to_maturity ascending
- Highlight rows maturing within 30 days in red

BOTTOM LEFT (50% width):
- Waterfall chart from Query 9 (Funding Cost)
- Title: "Blended Funding Cost Evolution"
- Show starting → ending blended cost
- Color positive/negative impacts

BOTTOM RIGHT (50% width):
- Live feed from Query 10 (Treasury Alerts)
- Title: "Real-Time Treasury Alerts"
- Show timestamp, message, severity, category
- Color-code by severity_color
- Auto-refresh every 30 seconds

DESIGN:
- Trading floor / command center aesthetic
- Dark mode option for 24/7 monitoring
- Real-time auto-refresh (1 minute)
- Large, readable fonts for distance viewing
- Navy/Teal/Emerald/Amber/Red palette
- Add "Last Updated" timestamp in header
*/
