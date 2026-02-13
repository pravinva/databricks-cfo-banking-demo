-- Query 2C: Total balance trend (last 6 months) ($B)
SELECT
  effective_date,
  SUM(current_balance) / 1e9 AS total_balance_billions
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts_historical
WHERE effective_date >= add_months(date_trunc('month', current_date()), -6)
GROUP BY effective_date
ORDER BY effective_date;

