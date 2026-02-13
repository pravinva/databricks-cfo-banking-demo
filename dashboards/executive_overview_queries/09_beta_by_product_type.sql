-- Query 3: Beta distribution / sensitivity by product_type
WITH scored AS (
  SELECT
    d.product_type,
    d.current_balance,
    COALESCE(p.predicted_beta, d.beta) AS beta_used
  FROM cfo_banking_demo.bronze_core_banking.deposit_accounts d
  LEFT JOIN cfo_banking_demo.ml_models.deposit_beta_predictions p
    ON d.account_id = p.account_id
  WHERE d.is_current = TRUE
)
SELECT
  product_type,
  ROUND(AVG(beta_used), 3) as avg_beta,
  ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY beta_used), 3) as p25_beta,
  ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY beta_used), 3) as p75_beta,
  COUNT(*) as account_count,
  SUM(current_balance) / 1e9 as balance_billions,
  CASE
    WHEN AVG(beta_used) > 0.60 THEN '#DC2626'
    WHEN AVG(beta_used) > 0.40 THEN '#D97706'
    ELSE '#059669'
  END as risk_color
FROM scored
WHERE beta_used IS NOT NULL
GROUP BY product_type
ORDER BY avg_beta DESC;

