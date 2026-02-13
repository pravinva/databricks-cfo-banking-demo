-- Query 1 / Card 3: At-Risk Deposits ($B) priced below market benchmark
WITH yc AS (
  SELECT rate_2y
  FROM cfo_banking_demo.silver_treasury.yield_curves
  WHERE date = (SELECT MAX(date) FROM cfo_banking_demo.silver_treasury.yield_curves)
),
base AS (
  SELECT
    d.account_id,
    d.current_balance,
    d.stated_rate,
    (d.stated_rate - yc.rate_2y) AS rate_gap
  FROM cfo_banking_demo.bronze_core_banking.deposit_accounts d
  CROSS JOIN yc
  WHERE d.is_current = TRUE
)
SELECT
  'At-Risk Deposits' as metric_name,
  SUM(CASE WHEN rate_gap < -0.002 THEN current_balance ELSE 0 END) / 1e9 as value,
  '$B' as unit,
  CONCAT(
    '$',
    CAST(ROUND(SUM(CASE WHEN rate_gap < -0.002 THEN current_balance ELSE 0 END) / 1e9, 1) AS STRING),
    'B'
  ) as value_display,
  '⚠' as trend_direction,
  '+12.5%' as trend_change,
  'QoQ Increase' as trend_label,
  '#D97706' as color
FROM base;

