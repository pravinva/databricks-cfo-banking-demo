-- Query 2: Portfolio composition by relationship_category (donut)
SELECT
  c.relationship_category,
  SUM(d.current_balance) / 1e9 as balance_billions,
  COUNT(DISTINCT d.account_id) as account_count,
  ROUND(SUM(d.current_balance) / SUM(SUM(d.current_balance)) OVER () * 100, 1) as pct_of_total,
  CASE
    WHEN c.relationship_category = 'Strategic' THEN '#059669'
    WHEN c.relationship_category = 'Tactical' THEN '#0891B2'
    WHEN c.relationship_category = 'Expendable' THEN '#DC2626'
  END as segment_color
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts d
LEFT JOIN (
  SELECT DISTINCT account_id, relationship_category
  FROM cfo_banking_demo.ml_models.deposit_cohort_analysis
  WHERE is_current = TRUE
) c ON d.account_id = c.account_id
WHERE d.is_current = TRUE
  AND c.relationship_category IS NOT NULL
GROUP BY c.relationship_category
ORDER BY balance_billions DESC;

