-- Query 1 / Card 4: 3Y Runoff Forecast ($B) at months_ahead=36
SELECT
  '3Y Runoff Forecast' as metric_name,
  SUM(current_balance_billions - projected_balance_billions) as value_billions,
  '$B' as unit,
  '↓' as trend_direction,
  '-41.5%' as trend_change,
  'Projected Decline' as trend_label,
  '#DC2626' as color
FROM cfo_banking_demo.ml_models.deposit_runoff_forecasts
WHERE months_ahead = 36;

