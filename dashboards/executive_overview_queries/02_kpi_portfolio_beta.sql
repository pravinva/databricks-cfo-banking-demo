-- Query 1 / Card 2: Portfolio Beta (balance-weighted; prefer predicted_beta)
WITH scored AS (
  SELECT
    d.account_id,
    d.current_balance,
    COALESCE(p.predicted_beta, d.beta) AS beta_used
  FROM cfo_banking_demo.bronze_core_banking.deposit_accounts d
  LEFT JOIN cfo_banking_demo.ml_models.deposit_beta_predictions p
    ON d.account_id = p.account_id
  WHERE d.is_current = TRUE
)
SELECT
  'Portfolio Beta' as metric_name,
  ROUND(
    SUM(current_balance * beta_used) / NULLIF(SUM(current_balance), 0),
    3
  ) as value,
  'beta' as unit,
  '↓' as trend_direction,
  '-0.02' as trend_change,
  'vs Last Month' as trend_label,
  '#0891B2' as color
FROM scored
WHERE beta_used IS NOT NULL;

