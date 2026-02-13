-- Query 1 / Card 1: Total Deposits ($B)
WITH m AS (
  SELECT SUM(current_balance) / 1e9 AS value_billions
  FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
  WHERE is_current = TRUE
)
SELECT
  'Total Deposits' AS metric_name,
  value_billions AS value,
  '$B' AS unit,
  CONCAT('$', CAST(ROUND(value_billions, 1) AS STRING), 'B') AS value_display,
  '↑' AS trend_direction,
  '+2.3%' AS trend_change,
  'MoM Growth' AS trend_label,
  '#1E3A8A' AS color
FROM m;

