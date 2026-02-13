-- Query 6: Top 10 at-risk accounts table (rate gap vs benchmark + beta)
WITH yc AS (
  SELECT rate_2y AS market_benchmark_rate
  FROM cfo_banking_demo.silver_treasury.yield_curves
  WHERE date = (SELECT MAX(date) FROM cfo_banking_demo.silver_treasury.yield_curves)
),
scored AS (
  SELECT
    d.account_id,
    d.product_type,
    d.account_open_date,
    d.current_balance,
    d.stated_rate,
    (d.stated_rate - yc.market_benchmark_rate) AS rate_gap,
    yc.market_benchmark_rate,
    COALESCE(p.predicted_beta, d.beta) AS beta_used
  FROM cfo_banking_demo.bronze_core_banking.deposit_accounts d
  CROSS JOIN yc
  LEFT JOIN cfo_banking_demo.ml_models.deposit_beta_predictions p
    ON d.account_id = p.account_id
  WHERE d.is_current = TRUE
)
SELECT
  account_id,
  product_type,
  current_balance / 1e6 as balance_millions,
  ROUND(beta_used, 3) as beta,
  ROUND(stated_rate * 100, 2) as our_rate_pct,
  ROUND(market_benchmark_rate * 100, 2) as market_rate_pct,
  ROUND((stated_rate - market_benchmark_rate) * 100, 2) as rate_gap_bps,
  CASE
    WHEN (stated_rate - market_benchmark_rate) < -0.005 THEN '🔴 High Risk'
    WHEN (stated_rate - market_benchmark_rate) < -0.002 THEN '🟡 Medium Risk'
    ELSE '🟢 Low Risk'
  END as risk_level,
  DATEDIFF(CURRENT_DATE(), account_open_date) / 365.25 as account_age_years
FROM scored
WHERE rate_gap < -0.002
ORDER BY current_balance DESC
LIMIT 10;

