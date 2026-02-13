-- Query 4: 3-year runoff waterfall by relationship_category
WITH forecast_detail AS (
  SELECT
    months_ahead,
    relationship_category,
    SUM(projected_balance_billions) as balance_billions,
    SUM(current_balance_billions - projected_balance_billions) as runoff_billions
  FROM cfo_banking_demo.ml_models.deposit_runoff_forecasts
  WHERE months_ahead IN (0, 6, 12, 18, 24, 30, 36)
  GROUP BY months_ahead, relationship_category
)
SELECT
  months_ahead,
  ROUND(months_ahead / 12.0, 1) as years_ahead,
  relationship_category,
  balance_billions,
  runoff_billions,
  CASE
    WHEN relationship_category = 'Strategic' THEN '#059669'
    WHEN relationship_category = 'Tactical' THEN '#0891B2'
    WHEN relationship_category = 'Expendable' THEN '#DC2626'
  END as category_color
FROM forecast_detail
ORDER BY months_ahead, relationship_category;

