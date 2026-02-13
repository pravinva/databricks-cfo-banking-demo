-- Query 2C: Total balance trend (last 6 months) ($B)
-- NOTE: anchor to latest available effective_date (demo data may not be current-date aligned)
WITH bounds AS (
  SELECT MAX(effective_date) AS max_effective_date
  FROM cfo_banking_demo.bronze_core_banking.deposit_accounts_historical
),
monthly AS (
  SELECT
    date_trunc('month', h.effective_date) AS month,
    SUM(h.current_balance) / 1e9 AS total_balance_billions
  FROM cfo_banking_demo.bronze_core_banking.deposit_accounts_historical h
  CROSS JOIN bounds b
  WHERE h.effective_date >= add_months(date_trunc('month', b.max_effective_date), -6)
  GROUP BY date_trunc('month', h.effective_date)
)
SELECT
  month,
  total_balance_billions
FROM monthly
ORDER BY month;

