-- Query 2D: Total balance trend (monthly vs prior year) ($B + YoY %)
WITH bounds AS (
  SELECT MAX(effective_date) AS max_effective_date
  FROM cfo_banking_demo.bronze_core_banking.deposit_accounts_historical
),
monthly AS (
  SELECT
    date_trunc('month', effective_date) AS month,
    SUM(current_balance) / 1e9 AS total_balance_b
  FROM cfo_banking_demo.bronze_core_banking.deposit_accounts_historical
  CROSS JOIN bounds b
  WHERE effective_date >= add_months(date_trunc('month', b.max_effective_date), -24)
  GROUP BY date_trunc('month', effective_date)
),
with_yoy AS (
  SELECT
    month,
    total_balance_b,
    LAG(total_balance_b, 12) OVER (ORDER BY month) AS prior_year_balance_b
  FROM monthly
)
SELECT
  month,
  total_balance_b,
  prior_year_balance_b,
  (total_balance_b - prior_year_balance_b) AS yoy_delta_b,
  ROUND((total_balance_b - prior_year_balance_b) / NULLIF(prior_year_balance_b, 0) * 100, 2) AS yoy_pct
FROM with_yoy
WHERE month >= add_months(
  date_trunc('month', (SELECT max_effective_date FROM bounds)),
  -12
)
ORDER BY month;

