-- ============================================================================
-- WS5: Enterprise Lakeview Dashboard Queries
-- Bank CFO Command Center - Executive Analytics
-- ============================================================================
-- Created: 2026-01-25
-- Purpose: Bloomberg Terminal-level sophisticated queries for Lakeview dashboards
-- Aesthetic: Professional navy/slate/white, data-dense but elegant
-- ============================================================================

-- ============================================================================
-- QUERY 1: KPI Scorecard with Sparklines
-- Executive summary metrics with 30-day trend data
-- ============================================================================
-- Main KPI Table (current snapshot)
WITH current_kpis AS (
  SELECT
    'Total Assets' as metric_name,
    SUM(current_balance)/1e9 as current_value_billions,
    'Loans + Securities' as composition,
    (SUM(current_balance) - LAG(SUM(current_balance), 30) OVER (ORDER BY CURRENT_DATE)) /
      LAG(SUM(current_balance), 30) OVER (ORDER BY CURRENT_DATE) * 100 as pct_change_30d
  FROM cfo_banking_demo.silver_finance.loan_portfolio
  WHERE is_current = true

  UNION ALL

  SELECT
    'Total Deposits',
    SUM(current_balance)/1e9,
    'MMDA + DDA + NOW + Savings',
    (SUM(current_balance) - LAG(SUM(current_balance), 30) OVER (ORDER BY CURRENT_DATE)) /
      LAG(SUM(current_balance), 30) OVER (ORDER BY CURRENT_DATE) * 100
  FROM cfo_banking_demo.silver_finance.deposit_portfolio
  WHERE is_current = true

  UNION ALL

  SELECT
    'Net Interest Margin',
    AVG(net_interest_margin) * 100,
    'Interest Income - Interest Expense',
    (AVG(net_interest_margin) - LAG(AVG(net_interest_margin), 30) OVER (ORDER BY CURRENT_DATE)) /
      LAG(AVG(net_interest_margin), 30) OVER (ORDER BY CURRENT_DATE) * 100
  FROM cfo_banking_demo.gold_finance.profitability_metrics
  WHERE calculation_date >= CURRENT_DATE - INTERVAL 30 DAYS

  UNION ALL

  SELECT
    'LCR',
    AVG(lcr_ratio) * 100,
    'HQLA / Net Cash Outflows (30d)',
    (AVG(lcr_ratio) - LAG(AVG(lcr_ratio), 30) OVER (ORDER BY CURRENT_DATE)) /
      LAG(AVG(lcr_ratio), 30) OVER (ORDER BY CURRENT_DATE) * 100
  FROM cfo_banking_demo.gold_finance.liquidity_coverage_ratio
  WHERE calculation_date >= CURRENT_DATE - INTERVAL 30 DAYS
)
SELECT * FROM current_kpis;

-- Sparkline Data (30-day trend for each KPI)
WITH daily_assets AS (
  SELECT
    DATE(load_timestamp) as metric_date,
    SUM(current_balance)/1e9 as value_billions
  FROM cfo_banking_demo.silver_finance.loan_portfolio
  WHERE load_timestamp >= CURRENT_DATE - INTERVAL 30 DAYS
  GROUP BY DATE(load_timestamp)
  ORDER BY metric_date
),
daily_deposits AS (
  SELECT
    DATE(load_timestamp) as metric_date,
    SUM(current_balance)/1e9 as value_billions
  FROM cfo_banking_demo.silver_finance.deposit_portfolio
  WHERE load_timestamp >= CURRENT_DATE - INTERVAL 30 DAYS
  GROUP BY DATE(load_timestamp)
  ORDER BY metric_date
),
daily_nim AS (
  SELECT
    calculation_date as metric_date,
    AVG(net_interest_margin) * 100 as value_pct
  FROM cfo_banking_demo.gold_finance.profitability_metrics
  WHERE calculation_date >= CURRENT_DATE - INTERVAL 30 DAYS
  GROUP BY calculation_date
  ORDER BY metric_date
),
daily_lcr AS (
  SELECT
    calculation_date as metric_date,
    AVG(lcr_ratio) * 100 as value_pct
  FROM cfo_banking_demo.gold_finance.liquidity_coverage_ratio
  WHERE calculation_date >= CURRENT_DATE - INTERVAL 30 DAYS
  GROUP BY calculation_date
  ORDER BY metric_date
)
SELECT 'Total Assets' as metric_name, metric_date, value_billions as value FROM daily_assets
UNION ALL
SELECT 'Total Deposits', metric_date, value_billions FROM daily_deposits
UNION ALL
SELECT 'Net Interest Margin', metric_date, value_pct FROM daily_nim
UNION ALL
SELECT 'LCR', metric_date, value_pct FROM daily_lcr
ORDER BY metric_name, metric_date;


-- ============================================================================
-- QUERY 2: Liquidity Waterfall Chart
-- LCR component breakdown showing HQLA sources and cash outflow drivers
-- ============================================================================
WITH lcr_components AS (
  SELECT
    'Level 1 HQLA' as component,
    'source' as flow_type,
    SUM(market_value)/1e9 as value_billions,
    1 as sort_order
  FROM cfo_banking_demo.silver_finance.securities
  WHERE security_type IN ('UST', 'Agency MBS')
    AND is_current = true

  UNION ALL

  SELECT
    'Level 2A HQLA',
    'source',
    SUM(market_value)/1e9,
    2
  FROM cfo_banking_demo.silver_finance.securities
  WHERE security_type IN ('Agency CMO', 'GSE Debt')
    AND is_current = true

  UNION ALL

  SELECT
    'Level 2B HQLA',
    'source',
    SUM(market_value)/1e9,
    3
  FROM cfo_banking_demo.silver_finance.securities
  WHERE security_type IN ('Corporate Bonds', 'Municipal Bonds')
    AND is_current = true

  UNION ALL

  SELECT
    'Retail Deposit Runoff',
    'outflow',
    SUM(current_balance * 0.03)/1e9, -- 3% runoff assumption for stable retail
    4
  FROM cfo_banking_demo.silver_finance.deposit_portfolio
  WHERE product_type IN ('MMDA', 'Savings')
    AND is_current = true

  UNION ALL

  SELECT
    'Wholesale Funding Runoff',
    'outflow',
    SUM(current_balance * 0.25)/1e9, -- 25% runoff for wholesale
    5
  FROM cfo_banking_demo.silver_finance.deposit_portfolio
  WHERE product_type IN ('DDA', 'NOW')
    AND is_current = true

  UNION ALL

  SELECT
    'Committed Credit Lines',
    'outflow',
    SUM(committed_amount * 0.05)/1e9, -- 5% drawdown assumption
    6
  FROM cfo_banking_demo.silver_finance.credit_facilities
  WHERE facility_status = 'active'

  UNION ALL

  SELECT
    'Derivative Collateral',
    'outflow',
    SUM(collateral_requirement)/1e9,
    7
  FROM cfo_banking_demo.silver_finance.derivative_positions
  WHERE valuation_date = CURRENT_DATE
)
SELECT
  component,
  flow_type,
  value_billions,
  CASE
    WHEN flow_type = 'source' THEN value_billions
    WHEN flow_type = 'outflow' THEN -value_billions
  END as signed_value_billions,
  sort_order
FROM lcr_components
ORDER BY sort_order;

-- LCR Ratio Calculation
WITH total_hqla AS (
  SELECT SUM(market_value) as hqla_total
  FROM cfo_banking_demo.silver_finance.securities
  WHERE security_type IN ('UST', 'Agency MBS', 'Agency CMO', 'GSE Debt')
    AND is_current = true
),
total_outflows AS (
  SELECT
    SUM(current_balance * 0.03) + -- Retail runoff
    SUM(current_balance * 0.25) + -- Wholesale runoff
    (SELECT SUM(committed_amount * 0.05) FROM cfo_banking_demo.silver_finance.credit_facilities WHERE facility_status = 'active') +
    (SELECT SUM(collateral_requirement) FROM cfo_banking_demo.silver_finance.derivative_positions WHERE valuation_date = CURRENT_DATE)
    as outflows_total
  FROM cfo_banking_demo.silver_finance.deposit_portfolio
  WHERE is_current = true
)
SELECT
  h.hqla_total/1e9 as hqla_billions,
  o.outflows_total/1e9 as outflows_billions,
  (h.hqla_total / o.outflows_total) * 100 as lcr_ratio_pct,
  CASE
    WHEN (h.hqla_total / o.outflows_total) >= 1.0 THEN 'Compliant (>100%)'
    ELSE 'Non-Compliant (<100%)'
  END as compliance_status
FROM total_hqla h
CROSS JOIN total_outflows o;


-- ============================================================================
-- QUERY 3: Yield Curve Surface (3D)
-- Treasury yield curve with historical term structure evolution
-- ============================================================================
WITH yield_curve_history AS (
  SELECT
    observation_date,
    tenor_years,
    yield_rate * 100 as yield_pct,
    DATEDIFF(DAY, MIN(observation_date) OVER (), observation_date) as days_from_start
  FROM cfo_banking_demo.bronze_market.treasury_yields
  WHERE observation_date >= CURRENT_DATE - INTERVAL 90 DAYS
    AND tenor_years IN (0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30)
  ORDER BY observation_date, tenor_years
),
curve_spreads AS (
  SELECT
    observation_date,
    MAX(CASE WHEN tenor_years = 10 THEN yield_pct END) -
    MAX(CASE WHEN tenor_years = 2 THEN yield_pct END) as spread_10y_2y,
    MAX(CASE WHEN tenor_years = 30 THEN yield_pct END) -
    MAX(CASE WHEN tenor_years = 10 THEN yield_pct END) as spread_30y_10y
  FROM yield_curve_history
  GROUP BY observation_date
)
SELECT
  yc.observation_date,
  yc.tenor_years,
  yc.yield_pct,
  yc.days_from_start,
  cs.spread_10y_2y,
  cs.spread_30y_10y,
  CASE
    WHEN cs.spread_10y_2y < 0 THEN 'Inverted'
    WHEN cs.spread_10y_2y < 0.5 THEN 'Flat'
    WHEN cs.spread_10y_2y < 1.5 THEN 'Normal'
    ELSE 'Steep'
  END as curve_shape
FROM yield_curve_history yc
JOIN curve_spreads cs ON yc.observation_date = cs.observation_date
ORDER BY yc.observation_date DESC, yc.tenor_years;

-- Latest Yield Curve Snapshot (for 2D overlay)
SELECT
  tenor_years,
  yield_rate * 100 as yield_pct,
  observation_date
FROM cfo_banking_demo.bronze_market.treasury_yields
WHERE observation_date = (SELECT MAX(observation_date) FROM cfo_banking_demo.bronze_market.treasury_yields)
  AND tenor_years IN (0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30)
ORDER BY tenor_years;


-- ============================================================================
-- QUERY 4: Portfolio Risk-Return Heatmap
-- Asset allocation matrix showing yield vs duration vs credit risk
-- ============================================================================
WITH portfolio_risk_metrics AS (
  SELECT
    security_type,
    COUNT(*) as position_count,
    SUM(market_value)/1e9 as market_value_billions,
    AVG(ytm) * 100 as avg_yield_pct,
    AVG(effective_duration) as avg_duration_years,
    AVG(oas_spread) * 10000 as avg_oas_bps,
    CASE
      WHEN security_type IN ('UST', 'Agency MBS') THEN 'AAA'
      WHEN security_type IN ('Agency CMO', 'GSE Debt') THEN 'AA'
      WHEN security_type IN ('Corporate Bonds') THEN 'A'
      WHEN security_type IN ('Municipal Bonds') THEN 'A-'
      ELSE 'BBB'
    END as credit_rating
  FROM cfo_banking_demo.silver_finance.securities
  WHERE is_current = true
  GROUP BY security_type
),
duration_buckets AS (
  SELECT
    security_type,
    market_value_billions,
    avg_yield_pct,
    avg_duration_years,
    avg_oas_bps,
    credit_rating,
    CASE
      WHEN avg_duration_years < 1 THEN 'Short (0-1Y)'
      WHEN avg_duration_years < 3 THEN 'Intermediate (1-3Y)'
      WHEN avg_duration_years < 5 THEN 'Medium (3-5Y)'
      WHEN avg_duration_years < 7 THEN 'Long (5-7Y)'
      ELSE 'Very Long (7Y+)'
    END as duration_bucket,
    CASE
      WHEN avg_yield_pct < 2.0 THEN 'Low (<2%)'
      WHEN avg_yield_pct < 3.0 THEN 'Medium (2-3%)'
      WHEN avg_yield_pct < 4.0 THEN 'Good (3-4%)'
      ELSE 'High (4%+)'
    END as yield_bucket
  FROM portfolio_risk_metrics
)
SELECT
  security_type,
  duration_bucket,
  yield_bucket,
  credit_rating,
  market_value_billions,
  avg_yield_pct,
  avg_duration_years,
  avg_oas_bps,
  (market_value_billions * avg_yield_pct / avg_duration_years) as sharpe_proxy,
  (market_value_billions / SUM(market_value_billions) OVER ()) * 100 as portfolio_weight_pct
FROM duration_buckets
ORDER BY avg_duration_years, avg_yield_pct DESC;

-- Credit Quality Distribution
SELECT
  credit_rating,
  COUNT(DISTINCT security_type) as asset_classes,
  SUM(market_value_billions) as total_value_billions,
  AVG(avg_yield_pct) as avg_yield_pct,
  AVG(avg_duration_years) as avg_duration_years,
  (SUM(market_value_billions) / (SELECT SUM(market_value_billions) FROM portfolio_risk_metrics)) * 100 as portfolio_pct
FROM duration_buckets
GROUP BY credit_rating
ORDER BY
  CASE credit_rating
    WHEN 'AAA' THEN 1
    WHEN 'AA' THEN 2
    WHEN 'A' THEN 3
    WHEN 'A-' THEN 4
    WHEN 'BBB' THEN 5
    ELSE 6
  END;


-- ============================================================================
-- QUERY 5: Deposit Beta Sensitivity Matrix
-- Rate shock scenarios across product types with deposit beta modeling
-- ============================================================================
WITH deposit_summary AS (
  SELECT
    product_type,
    COUNT(*) as account_count,
    SUM(current_balance)/1e9 as balance_billions,
    AVG(interest_rate) * 100 as current_rate_pct,
    -- Deposit beta coefficients (historical fit)
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
),
rate_shock_scenarios AS (
  SELECT
    product_type,
    balance_billions,
    current_rate_pct,
    deposit_beta,
    -- Scenario 1: +25 bps
    current_rate_pct + (25.0 * deposit_beta / 100.0) as rate_plus_25bps,
    balance_billions * (1 - 0.01 * deposit_beta) as balance_plus_25bps,
    balance_billions * 0.01 * deposit_beta as runoff_25bps,
    -- Scenario 2: +50 bps
    current_rate_pct + (50.0 * deposit_beta / 100.0) as rate_plus_50bps,
    balance_billions * (1 - 0.02 * deposit_beta) as balance_plus_50bps,
    balance_billions * 0.02 * deposit_beta as runoff_50bps,
    -- Scenario 3: +100 bps
    current_rate_pct + (100.0 * deposit_beta / 100.0) as rate_plus_100bps,
    balance_billions * (1 - 0.04 * deposit_beta) as balance_plus_100bps,
    balance_billions * 0.04 * deposit_beta as runoff_100bps,
    -- Scenario 4: -25 bps
    current_rate_pct + (-25.0 * deposit_beta / 100.0) as rate_minus_25bps,
    balance_billions * (1 + 0.005 * deposit_beta) as balance_minus_25bps,
    balance_billions * -0.005 * deposit_beta as runoff_minus_25bps
  FROM deposit_summary
)
SELECT
  product_type,
  balance_billions as current_balance_billions,
  current_rate_pct,
  deposit_beta,
  -- Scenarios
  rate_plus_25bps, balance_plus_25bps, runoff_25bps,
  rate_plus_50bps, balance_plus_50bps, runoff_50bps,
  rate_plus_100bps, balance_plus_100bps, runoff_100bps,
  rate_minus_25bps, balance_minus_25bps, runoff_minus_25bps
FROM rate_shock_scenarios
ORDER BY balance_billions DESC;

-- Total Impact Summary
WITH total_impact AS (
  SELECT
    SUM(balance_billions) as current_total_billions,
    SUM(runoff_25bps) as total_runoff_25bps,
    SUM(runoff_50bps) as total_runoff_50bps,
    SUM(runoff_100bps) as total_runoff_100bps,
    SUM(runoff_minus_25bps) as total_inflow_minus_25bps
  FROM rate_shock_scenarios
)
SELECT
  current_total_billions,
  total_runoff_25bps,
  (total_runoff_25bps / current_total_billions) * 100 as runoff_pct_25bps,
  total_runoff_50bps,
  (total_runoff_50bps / current_total_billions) * 100 as runoff_pct_50bps,
  total_runoff_100bps,
  (total_runoff_100bps / current_total_billions) * 100 as runoff_pct_100bps,
  total_inflow_minus_25bps,
  (total_inflow_minus_25bps / current_total_billions) * 100 as inflow_pct_minus_25bps
FROM total_impact;


-- ============================================================================
-- QUERY 6: Real-Time Activity Stream
-- Recent transactions, model predictions, and system events with drill-down
-- ============================================================================
WITH recent_loan_originations AS (
  SELECT
    'Loan Origination' as activity_type,
    loan_id as entity_id,
    borrower_name as entity_name,
    product_type,
    origination_date as activity_date,
    current_balance/1e6 as amount_millions,
    'New loan originated' as activity_description,
    origination_officer as responsible_party
  FROM cfo_banking_demo.silver_finance.loan_portfolio
  WHERE origination_date >= CURRENT_DATE - INTERVAL 7 DAYS
  ORDER BY origination_date DESC
  LIMIT 20
),
recent_deposits AS (
  SELECT
    'Deposit Account Opened',
    account_id,
    account_holder_name,
    product_type,
    open_date,
    current_balance/1e6,
    'New deposit account opened',
    relationship_manager
  FROM cfo_banking_demo.silver_finance.deposit_portfolio
  WHERE open_date >= CURRENT_DATE - INTERVAL 7 DAYS
  ORDER BY open_date DESC
  LIMIT 20
),
recent_securities_trades AS (
  SELECT
    CASE
      WHEN trade_type = 'buy' THEN 'Securities Purchase'
      ELSE 'Securities Sale'
    END,
    security_id,
    security_name,
    security_type,
    trade_date,
    trade_amount/1e6,
    CONCAT(trade_type, ' ', quantity, ' units at $', ROUND(price, 2)),
    trader_name
  FROM cfo_banking_demo.silver_finance.securities_trades
  WHERE trade_date >= CURRENT_DATE - INTERVAL 7 DAYS
  ORDER BY trade_date DESC
  LIMIT 20
),
model_predictions AS (
  SELECT
    'Churn Prediction',
    CAST(member_id AS STRING),
    member_name,
    'Analytics Model',
    prediction_timestamp,
    churn_probability * 100,
    CONCAT('Churn probability: ', ROUND(churn_probability * 100, 1), '%'),
    'ML Model: XGBoost v14'
  FROM cfo_banking_demo.gold_analytics.churn_predictions
  WHERE prediction_timestamp >= CURRENT_DATE - INTERVAL 7 DAYS
    AND churn_probability > 0.7
  ORDER BY prediction_timestamp DESC
  LIMIT 20
)
SELECT * FROM recent_loan_originations
UNION ALL
SELECT * FROM recent_deposits
UNION ALL
SELECT * FROM recent_securities_trades
UNION ALL
SELECT * FROM model_predictions
ORDER BY activity_date DESC
LIMIT 100;

-- Activity Summary Counts
SELECT
  activity_type,
  COUNT(*) as activity_count,
  SUM(amount_millions) as total_amount_millions,
  MIN(activity_date) as earliest_activity,
  MAX(activity_date) as latest_activity
FROM (
  SELECT * FROM recent_loan_originations
  UNION ALL
  SELECT * FROM recent_deposits
  UNION ALL
  SELECT * FROM recent_securities_trades
  UNION ALL
  SELECT * FROM model_predictions
) activities
GROUP BY activity_type
ORDER BY activity_count DESC;


-- ============================================================================
-- QUERY 7: Capital Adequacy Bullet Charts
-- Tier 1 Capital, CET1, Total Capital ratios with Basel III regulatory limits
-- ============================================================================
WITH capital_components AS (
  SELECT
    'Common Equity Tier 1 (CET1)' as capital_type,
    SUM(common_stock + retained_earnings - goodwill - intangibles)/1e9 as capital_billions,
    7.0 as regulatory_minimum_pct,
    8.5 as well_capitalized_pct,
    10.5 as target_pct,
    1 as sort_order
  FROM cfo_banking_demo.gold_finance.capital_structure
  WHERE calculation_date = CURRENT_DATE

  UNION ALL

  SELECT
    'Tier 1 Capital',
    SUM(common_stock + retained_earnings + preferred_stock - goodwill - intangibles)/1e9,
    8.5,
    10.0,
    12.0,
    2
  FROM cfo_banking_demo.gold_finance.capital_structure
  WHERE calculation_date = CURRENT_DATE

  UNION ALL

  SELECT
    'Total Capital',
    SUM(tier1_capital + tier2_capital)/1e9,
    10.5,
    13.0,
    16.0,
    3
  FROM cfo_banking_demo.gold_finance.capital_structure
  WHERE calculation_date = CURRENT_DATE
),
risk_weighted_assets AS (
  SELECT
    SUM(current_balance * risk_weight)/1e9 as rwa_billions
  FROM cfo_banking_demo.silver_finance.loan_portfolio
  WHERE is_current = true
),
capital_ratios AS (
  SELECT
    cc.capital_type,
    cc.capital_billions,
    rwa.rwa_billions,
    (cc.capital_billions / rwa.rwa_billions) * 100 as actual_ratio_pct,
    cc.regulatory_minimum_pct,
    cc.well_capitalized_pct,
    cc.target_pct,
    CASE
      WHEN (cc.capital_billions / rwa.rwa_billions) * 100 >= cc.target_pct THEN 'Excellent'
      WHEN (cc.capital_billions / rwa.rwa_billions) * 100 >= cc.well_capitalized_pct THEN 'Well Capitalized'
      WHEN (cc.capital_billions / rwa.rwa_billions) * 100 >= cc.regulatory_minimum_pct THEN 'Adequate'
      ELSE 'Undercapitalized'
    END as status,
    cc.sort_order
  FROM capital_components cc
  CROSS JOIN risk_weighted_assets rwa
)
SELECT
  capital_type,
  capital_billions,
  rwa_billions,
  actual_ratio_pct,
  regulatory_minimum_pct,
  well_capitalized_pct,
  target_pct,
  status,
  (actual_ratio_pct - regulatory_minimum_pct) as buffer_above_minimum_pct,
  (target_pct - actual_ratio_pct) as gap_to_target_pct
FROM capital_ratios
ORDER BY sort_order;

-- Historical Capital Ratio Trend
WITH daily_capital AS (
  SELECT
    calculation_date,
    (SUM(common_stock + retained_earnings - goodwill - intangibles) /
     (SELECT SUM(current_balance * risk_weight) FROM cfo_banking_demo.silver_finance.loan_portfolio WHERE is_current = true)) * 100
      as cet1_ratio_pct,
    (SUM(common_stock + retained_earnings + preferred_stock - goodwill - intangibles) /
     (SELECT SUM(current_balance * risk_weight) FROM cfo_banking_demo.silver_finance.loan_portfolio WHERE is_current = true)) * 100
      as tier1_ratio_pct,
    (SUM(tier1_capital + tier2_capital) /
     (SELECT SUM(current_balance * risk_weight) FROM cfo_banking_demo.silver_finance.loan_portfolio WHERE is_current = true)) * 100
      as total_capital_ratio_pct
  FROM cfo_banking_demo.gold_finance.capital_structure
  WHERE calculation_date >= CURRENT_DATE - INTERVAL 90 DAYS
  GROUP BY calculation_date
)
SELECT
  calculation_date,
  cet1_ratio_pct,
  tier1_ratio_pct,
  total_capital_ratio_pct
FROM daily_capital
ORDER BY calculation_date;


-- ============================================================================
-- QUERY 8: Net Interest Margin (NIM) Attribution Waterfall
-- Component-level NIM decomposition showing interest income and expense drivers
-- ============================================================================
WITH interest_income_components AS (
  SELECT
    'Loan Interest Income' as component,
    'income' as flow_type,
    SUM(current_balance * interest_rate / 100.0 / 12.0)/1e6 as monthly_amount_millions,
    1 as sort_order
  FROM cfo_banking_demo.silver_finance.loan_portfolio
  WHERE is_current = true

  UNION ALL

  SELECT
    'Securities Interest Income',
    'income',
    SUM(market_value * ytm / 100.0 / 12.0)/1e6,
    2
  FROM cfo_banking_demo.silver_finance.securities
  WHERE is_current = true

  UNION ALL

  SELECT
    'Fee Income',
    'income',
    SUM(fee_revenue)/1e6,
    3
  FROM cfo_banking_demo.gold_finance.profitability_metrics
  WHERE calculation_date >= CURRENT_DATE - INTERVAL 30 DAYS
),
interest_expense_components AS (
  SELECT
    'Deposit Interest Expense',
    'expense',
    SUM(current_balance * interest_rate / 100.0 / 12.0)/1e6,
    4
  FROM cfo_banking_demo.silver_finance.deposit_portfolio
  WHERE is_current = true

  UNION ALL

  SELECT
    'Wholesale Funding Cost',
    'expense',
    SUM(borrowing_amount * interest_rate / 100.0 / 12.0)/1e6,
    5
  FROM cfo_banking_demo.silver_finance.wholesale_funding
  WHERE is_current = true

  UNION ALL

  SELECT
    'Operating Expenses',
    'expense',
    SUM(operating_expenses)/1e6,
    6
  FROM cfo_banking_demo.gold_finance.profitability_metrics
  WHERE calculation_date >= CURRENT_DATE - INTERVAL 30 DAYS
),
all_components AS (
  SELECT * FROM interest_income_components
  UNION ALL
  SELECT * FROM interest_expense_components
)
SELECT
  component,
  flow_type,
  monthly_amount_millions,
  CASE
    WHEN flow_type = 'income' THEN monthly_amount_millions
    WHEN flow_type = 'expense' THEN -monthly_amount_millions
  END as signed_amount_millions,
  sort_order,
  SUM(CASE
    WHEN flow_type = 'income' THEN monthly_amount_millions
    WHEN flow_type = 'expense' THEN -monthly_amount_millions
  END) OVER (ORDER BY sort_order ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as cumulative_millions
FROM all_components
ORDER BY sort_order;

-- NIM Calculation Summary
WITH total_income AS (
  SELECT SUM(monthly_amount_millions) as income_total
  FROM interest_income_components
),
total_expense AS (
  SELECT SUM(monthly_amount_millions) as expense_total
  FROM interest_expense_components
),
total_assets AS (
  SELECT
    SUM(current_balance)/1e9 as assets_billions
  FROM cfo_banking_demo.silver_finance.loan_portfolio
  WHERE is_current = true
)
SELECT
  ti.income_total as total_income_millions,
  te.expense_total as total_expense_millions,
  (ti.income_total - te.expense_total) as net_interest_income_millions,
  ta.assets_billions,
  ((ti.income_total - te.expense_total) / (ta.assets_billions * 1000.0)) * 100 as nim_pct,
  CASE
    WHEN ((ti.income_total - te.expense_total) / (ta.assets_billions * 1000.0)) * 100 >= 3.5 THEN 'Excellent'
    WHEN ((ti.income_total - te.expense_total) / (ta.assets_billions * 1000.0)) * 100 >= 3.0 THEN 'Good'
    WHEN ((ti.income_total - te.expense_total) / (ta.assets_billions * 1000.0)) * 100 >= 2.5 THEN 'Fair'
    ELSE 'Poor'
  END as nim_rating
FROM total_income ti
CROSS JOIN total_expense te
CROSS JOIN total_assets ta;

-- ============================================================================
-- END OF DASHBOARD QUERIES
-- ============================================================================
