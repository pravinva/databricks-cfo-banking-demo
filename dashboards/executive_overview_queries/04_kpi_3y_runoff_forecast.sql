-- Query 1 / Card 4: 3Y Runoff Forecast ($B) at months_ahead=36
WITH m AS (
  SELECT
    SUM(current_balance_billions - projected_balance_billions) AS value_billions
  FROM cfo_banking_demo.ml_models.deposit_runoff_forecasts
  WHERE months_ahead = 36
)
SELECT
  '3Y Runoff Forecast' AS metric_name,
  value_billions AS value_billions,
  value_billions AS value,
  '$B' AS unit,
  CONCAT('$', CAST(ROUND(value_billions, 1) AS STRING), 'B') AS value_display,
  '↓' AS trend_direction,
  '-41.5%' AS trend_change,
  'Projected Decline' AS trend_label,
  '#DC2626' AS color
FROM m;

