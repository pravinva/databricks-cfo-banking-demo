-- Query 5: Rate shock scenario comparison (NII impact + stressed beta)
SELECT
  scenario_name,
  rate_shock_bps,
  ROUND(delta_nii_millions, 1) as nii_impact_millions,
  ROUND(stressed_avg_beta, 3) as stressed_avg_beta,
  CASE
    WHEN scenario_name = 'Baseline' THEN '#64748B'
    WHEN scenario_name = 'Adverse' THEN '#D97706'
    WHEN scenario_name = 'Severely Adverse' THEN '#DC2626'
    WHEN scenario_name = 'Custom Stress' THEN '#991B1B'
  END as scenario_color
FROM cfo_banking_demo.ml_models.stress_test_results
ORDER BY rate_shock_bps;

