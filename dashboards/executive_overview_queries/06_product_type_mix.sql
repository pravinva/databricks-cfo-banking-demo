-- Query 2B: Deposit mix by product_type (pie/donut)
SELECT
  product_type,
  SUM(current_balance) / 1e9 as balance_billions,
  COUNT(DISTINCT account_id) as account_count,
  ROUND(SUM(current_balance) / SUM(SUM(current_balance)) OVER () * 100, 1) as pct_of_total
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
WHERE is_current = TRUE
GROUP BY product_type
ORDER BY balance_billions DESC;

