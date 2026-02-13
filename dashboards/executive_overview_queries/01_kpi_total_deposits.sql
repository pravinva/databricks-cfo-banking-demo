-- Query 1 / Card 1: Total Deposits ($B)
SELECT
  'Total Deposits' as metric_name,
  SUM(current_balance) / 1e9 as value_billions,
  '$B' as unit,
  '↑' as trend_direction,
  '+2.3%' as trend_change,
  'MoM Growth' as trend_label,
  '#1E3A8A' as color
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
WHERE is_current = TRUE;

