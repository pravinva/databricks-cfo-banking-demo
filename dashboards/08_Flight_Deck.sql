-- ============================================================================
-- Bank CFO Flight Deck
-- ============================================================================
-- Dashboard ID: 01f0f97c007f1364a78d06fbfd74303a
-- Exported: 2026-01-25T05:45:34.109Z
-- Warehouse: 4b9b953939869799
-- Source: https://e2-demo-field-eng.cloud.databricks.com/dashboardsv3/01f0f97c007f1364a78d06fbfd74303a
-- ============================================================================


-- ============================================================================
-- QUERY 1: KPI Metrics
-- Dataset Name: 398f6bec
-- ============================================================================

SELECT
    'Total Assets' as metric_name,
    CONCAT('$', ROUND(SUM(current_balance)/1e9, 1), 'B') as value,
    '+1.8%' as change
FROM cfo_banking_demo.bronze_core_banking.loan_portfolio

UNION ALL

SELECT
    'Total Deposits',
    CONCAT('$', ROUND(SUM(current_balance)/1e9, 1), 'B'),
    '-0.5%'
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts

UNION ALL

SELECT
    'Net Interest Margin',
    CONCAT(ROUND(AVG(net_interest_margin) * 100, 2), '%'),
    '+3 bps'
FROM cfo_banking_demo.gold_finance.profitability_metrics

UNION ALL

SELECT
    'LCR Ratio',
    CONCAT(ROUND(AVG(lcr_ratio), 1), '%'),
    CASE
        WHEN AVG(lcr_ratio) >= 100 THEN 'Pass'
        ELSE 'Fail'
    END
FROM cfo_banking_demo.gold_regulatory.lcr_daily
WHERE calculation_date = (SELECT MAX(calculation_date) FROM cfo_banking_demo.gold_regulatory.lcr_daily)


-- ============================================================================
-- QUERY 2: Treasury Yield Curve
-- Dataset Name: 5ce78fcc
-- ============================================================================

SELECT
    tenor_years as maturity_years,
    ROUND(yield_rate * 100, 2) as yield_pct
FROM cfo_banking_demo.bronze_market.treasury_yields
WHERE observation_date = (
    SELECT MAX(observation_date)
    FROM cfo_banking_demo.bronze_market.treasury_yields
)
ORDER BY tenor_years


-- ============================================================================
-- QUERY 3: Securities Portfolio
-- Dataset Name: 17caa0dd
-- ============================================================================

SELECT
    security_type,
    ROUND(SUM(market_value)/1e9, 2) as value_billions,
    ROUND(AVG(ytm), 2) as avg_yield_pct,
    ROUND(AVG(effective_duration), 1) as duration_years
FROM cfo_banking_demo.silver_finance.securities
WHERE is_current = true
GROUP BY security_type
ORDER BY value_billions DESC


-- ============================================================================
-- QUERY 4: Deposit Beta Analysis
-- Dataset Name: 04224f06
-- ============================================================================

SELECT
    product_type,
    ROUND(SUM(current_balance)/1e9, 1) as balance_billions,
    ROUND(AVG(interest_rate), 2) as rate_pct,
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
ORDER BY balance_billions DESC


-- ============================================================================
-- QUERY 5: Liquidity Waterfall
-- Dataset Name: 8c5d8154
-- ============================================================================

SELECT
    'L1 HQLA' as component,
    ROUND(SUM(market_value)/1e9, 2) as value_billions,
    'source' as flow_type,
    1 as sort_order
FROM cfo_banking_demo.silver_finance.securities
WHERE security_type IN ('UST', 'Agency MBS')
    AND is_current = true

UNION ALL

SELECT
    'L2A HQLA',
    ROUND(SUM(market_value)/1e9, 2),
    'source',
    2
FROM cfo_banking_demo.silver_finance.securities
WHERE security_type IN ('Agency')
    AND is_current = true

UNION ALL

SELECT
    'Retail Runoff',
    ROUND(SUM(current_balance * 0.03)/1e9, 2),
    'outflow',
    3
FROM cfo_banking_demo.silver_finance.deposit_portfolio
WHERE product_type IN ('MMDA', 'Savings')
    AND is_current = true

UNION ALL

SELECT
    'Wholesale Runoff',
    ROUND(SUM(current_balance * 0.25)/1e9, 2),
    'outflow',
    4
FROM cfo_banking_demo.silver_finance.deposit_portfolio
WHERE product_type IN ('DDA', 'NOW')
    AND is_current = true

ORDER BY sort_order


-- ============================================================================
-- QUERY 6: Loan Activity
-- Dataset Name: a6062388
-- ============================================================================

SELECT
    product_type,
    borrower_name,
    origination_date,
    ROUND(original_amount/1e6, 1) as amount_millions,
    ROUND(interest_rate, 2) as rate_pct
FROM cfo_banking_demo.silver_finance.loan_portfolio
WHERE origination_date >= CURRENT_DATE - INTERVAL 30 DAYS
    AND is_current = true
ORDER BY origination_date DESC
LIMIT 50


-- ============================================================================
-- QUERY 7: Profitability Scorecard
-- Dataset Name: 8baf08dd
-- ============================================================================

SELECT
    'Current Month' as period,
    CONCAT(ROUND(net_interest_margin * 100, 2), '%') as nim,
    CONCAT('$', ROUND(fee_revenue/1e6, 1), 'M') as fee_revenue,
    CONCAT('$', ROUND(operating_expenses/1e6, 1), 'M') as operating_expenses,
    CONCAT('$', ROUND((fee_revenue - operating_expenses)/1e6, 1), 'M') as net_income
FROM cfo_banking_demo.gold_finance.profitability_metrics


-- ============================================================================
-- QUERY 8: Capital Adequacy Ratios
-- Dataset Name: c10c3fb3
-- ============================================================================

SELECT
    'CET1' as capital_type,
    16.3 as actual_pct,
    7.0 as minimum_pct,
    8.5 as well_capitalized_pct,
    10.5 as target_pct

UNION ALL

SELECT
    'Tier 1',
    18.3,
    8.5,
    10.0,
    12.0

UNION ALL

SELECT
    'Total Capital',
    21.7,
    10.5,
    13.0,
    16.0

