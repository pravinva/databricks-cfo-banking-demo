-- ============================================================================
-- DASHBOARD 6: MODEL PERFORMANCE & RECALIBRATION MONITORING
-- Audience: Data Science Team, Model Risk Management, Model Validation
-- ============================================================================

-- ============================================================================
-- QUERY 1: Model Performance KPIs (5 Cards)
-- ============================================================================

-- Card 1: Phase 1 Current MAPE
SELECT
  'Phase 1 Beta MAPE' as metric_name,
  7.2 as current_mape_pct,
  8.5 as baseline_mape_pct,
  '+15.3%' as improvement_vs_baseline,
  CASE
    WHEN 7.2 <= 8.0 THEN '#059669'  -- Meeting target
    WHEN 7.2 <= 10.0 THEN '#D97706' -- Acceptable
    ELSE '#DC2626'                   -- Needs recalibration
  END as color
;

-- Card 2: Phase 2 Runoff Accuracy
SELECT
  'Phase 2 Runoff MAE' as metric_name,
  4.8 as current_mae_pct,
  6.2 as baseline_mae_pct,
  '+22.6%' as improvement_vs_baseline,
  CASE
    WHEN 4.8 <= 5.0 THEN '#059669'
    WHEN 4.8 <= 7.0 THEN '#D97706'
    ELSE '#DC2626'
  END as color
;

-- Card 3: Phase 3 Stress Test RMSE
SELECT
  'Phase 3 Stress RMSE' as metric_name,
  12.5 as current_rmse_bps,
  18.3 as baseline_rmse_bps,
  '+31.7%' as improvement_vs_baseline,
  '#059669' as color
;

-- Card 4: Days Since Last Recalibration
SELECT
  'Days Since Recalibration' as metric_name,
  45 as days,
  90 as recal_threshold_days,
  ROUND(45.0 / 90 * 100, 0) as pct_of_threshold,
  CASE
    WHEN 45 < 75 THEN '#059669'
    WHEN 45 < 90 THEN '#D97706'
    ELSE '#DC2626'
  END as color
;

-- Card 5: PSI (Population Stability Index)
SELECT
  'Feature Drift (PSI)' as metric_name,
  0.08 as psi_value,
  0.10 as alert_threshold,
  CASE
    WHEN 0.08 < 0.10 THEN 'Stable'
    WHEN 0.08 < 0.25 THEN 'Moderate Drift'
    ELSE 'High Drift - Recalibrate'
  END as drift_status,
  CASE
    WHEN 0.08 < 0.10 THEN '#059669'
    WHEN 0.08 < 0.25 THEN '#D97706'
    ELSE '#DC2626'
  END as color
;


-- ============================================================================
-- QUERY 2: Model MAPE Over Time (Time Series)
-- ============================================================================
WITH monthly_performance AS (
  SELECT
    '2025-07' as month,
    'Phase 1' as model_phase,
    8.5 as mape_pct,
    1 as sort_order
  UNION ALL SELECT '2025-08', 'Phase 1', 8.2, 2
  UNION ALL SELECT '2025-09', 'Phase 1', 7.9, 3
  UNION ALL SELECT '2025-10', 'Phase 1', 7.6, 4
  UNION ALL SELECT '2025-11', 'Phase 1', 7.4, 5
  UNION ALL SELECT '2025-12', 'Phase 1', 7.2, 6
  UNION ALL SELECT '2026-01', 'Phase 1', 7.2, 7

  UNION ALL SELECT '2025-07', 'Phase 2', 6.8, 8
  UNION ALL SELECT '2025-08', 'Phase 2', 6.5, 9
  UNION ALL SELECT '2025-09', 'Phase 2', 6.1, 10
  UNION ALL SELECT '2025-10', 'Phase 2', 5.8, 11
  UNION ALL SELECT '2025-11', 'Phase 2', 5.3, 12
  UNION ALL SELECT '2025-12', 'Phase 2', 4.9, 13
  UNION ALL SELECT '2026-01', 'Phase 2', 4.8, 14

  UNION ALL SELECT '2025-07', 'Phase 3', 18.3, 15
  UNION ALL SELECT '2025-08', 'Phase 3', 17.1, 16
  UNION ALL SELECT '2025-09', 'Phase 3', 15.8, 17
  UNION ALL SELECT '2025-10', 'Phase 3', 14.5, 18
  UNION ALL SELECT '2025-11', 'Phase 3', 13.2, 19
  UNION ALL SELECT '2025-12', 'Phase 3', 12.8, 20
  UNION ALL SELECT '2026-01', 'Phase 3', 12.5, 21
)
SELECT
  month,
  model_phase,
  mape_pct,
  -- Calculate 3-month moving average
  AVG(mape_pct) OVER (
    PARTITION BY model_phase
    ORDER BY sort_order
    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
  ) as mape_3m_avg,
  CASE model_phase
    WHEN 'Phase 1' THEN '#1E3A8A'  -- Navy
    WHEN 'Phase 2' THEN '#0891B2'  -- Teal
    WHEN 'Phase 3' THEN '#059669'  -- Emerald
  END as phase_color,
  sort_order
FROM monthly_performance
ORDER BY model_phase, sort_order;


-- ============================================================================
-- QUERY 3: Actual vs Predicted Beta (Scatter Plot with Residuals)
-- ============================================================================
SELECT
  target_beta as actual_beta,
  -- Simulated prediction (add small random noise)
  target_beta * (1 + (RAND() - 0.5) * 0.15) as predicted_beta,
  ABS(target_beta - (target_beta * (1 + (RAND() - 0.5) * 0.15))) as absolute_error,
  relationship_category,
  product_type,
  CASE relationship_category
    WHEN 'Strategic' THEN '#059669'
    WHEN 'Tactical' THEN '#0891B2'
    WHEN 'Expendable' THEN '#DC2626'
  END as category_color
FROM cfo_banking_demo.ml_models.deposit_beta_training_phase2
WHERE target_beta IS NOT NULL
ORDER BY RAND()
LIMIT 500;


-- ============================================================================
-- QUERY 4: Feature Importance Rankings (Bar Chart)
-- ============================================================================
WITH feature_importance AS (
  SELECT
    'market_fed_funds_rate' as feature_name,
    0.285 as importance_score,
    1 as rank
  UNION ALL SELECT 'relationship_tenure_years', 0.182, 2
  UNION ALL SELECT 'product_count', 0.145, 3
  UNION ALL SELECT 'current_balance', 0.128, 4
  UNION ALL SELECT 'yield_curve_slope', 0.092, 5
  UNION ALL SELECT 'competitor_rate_spread', 0.078, 6
  UNION ALL SELECT 'has_direct_deposit', 0.045, 7
  UNION ALL SELECT 'transaction_count_30d', 0.032, 8
  UNION ALL SELECT 'account_age_years', 0.021, 9
  UNION ALL SELECT 'has_mobile_banking', 0.012, 10
)
SELECT
  feature_name,
  ROUND(importance_score * 100, 1) as importance_pct,
  rank,
  CASE
    WHEN importance_score >= 0.20 THEN '#DC2626'  -- Critical feature
    WHEN importance_score >= 0.10 THEN '#D97706'  -- Important feature
    WHEN importance_score >= 0.05 THEN '#0891B2'  -- Moderate feature
    ELSE '#059669'                                 -- Minor feature
  END as importance_color
FROM feature_importance
ORDER BY rank
LIMIT 10;


-- ============================================================================
-- QUERY 5: PSI by Feature (Population Stability Index)
-- ============================================================================
WITH feature_psi AS (
  SELECT
    'market_fed_funds_rate' as feature_name,
    0.12 as psi_score,
    'Moderate Drift' as drift_status,
    1 as sort_order
  UNION ALL SELECT 'relationship_tenure_years', 0.05, 'Stable', 2
  UNION ALL SELECT 'product_count', 0.08, 'Stable', 3
  UNION ALL SELECT 'current_balance', 0.18, 'Moderate Drift', 4
  UNION ALL SELECT 'yield_curve_slope', 0.28, 'High Drift', 5
  UNION ALL SELECT 'competitor_rate_spread', 0.15, 'Moderate Drift', 6
  UNION ALL SELECT 'has_direct_deposit', 0.03, 'Stable', 7
  UNION ALL SELECT 'transaction_count_30d', 0.09, 'Stable', 8
  UNION ALL SELECT 'account_age_years', 0.04, 'Stable', 9
  UNION ALL SELECT 'has_mobile_banking', 0.02, 'Stable', 10
)
SELECT
  feature_name,
  psi_score,
  drift_status,
  CASE
    WHEN psi_score < 0.10 THEN '#059669'  -- Stable
    WHEN psi_score < 0.25 THEN '#D97706'  -- Moderate drift
    ELSE '#DC2626'                         -- High drift (recalibrate)
  END as drift_color,
  sort_order
FROM feature_psi
ORDER BY psi_score DESC;


-- ============================================================================
-- QUERY 6: Residual Distribution (Histogram)
-- ============================================================================
WITH residuals AS (
  SELECT
    (target_beta - (target_beta * (1 + (RAND() - 0.5) * 0.15))) as residual,
    CASE
      WHEN (target_beta - (target_beta * (1 + (RAND() - 0.5) * 0.15))) < -0.10 THEN '< -0.10'
      WHEN (target_beta - (target_beta * (1 + (RAND() - 0.5) * 0.15))) < -0.05 THEN '-0.10 to -0.05'
      WHEN (target_beta - (target_beta * (1 + (RAND() - 0.5) * 0.15))) < 0.0 THEN '-0.05 to 0.00'
      WHEN (target_beta - (target_beta * (1 + (RAND() - 0.5) * 0.15))) < 0.05 THEN '0.00 to 0.05'
      WHEN (target_beta - (target_beta * (1 + (RAND() - 0.5) * 0.15))) < 0.10 THEN '0.05 to 0.10'
      ELSE '> 0.10'
    END as residual_bucket
  FROM cfo_banking_demo.ml_models.deposit_beta_training_phase2
  WHERE target_beta IS NOT NULL
  LIMIT 1000
)
SELECT
  residual_bucket,
  COUNT(*) as frequency,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as pct_of_total,
  CASE residual_bucket
    WHEN '-0.05 to 0.00' THEN '#059669'
    WHEN '0.00 to 0.05' THEN '#059669'
    WHEN '-0.10 to -0.05' THEN '#0891B2'
    WHEN '0.05 to 0.10' THEN '#0891B2'
    ELSE '#DC2626'
  END as bucket_color
FROM residuals
GROUP BY residual_bucket
ORDER BY CASE residual_bucket
  WHEN '< -0.10' THEN 1
  WHEN '-0.10 to -0.05' THEN 2
  WHEN '-0.05 to 0.00' THEN 3
  WHEN '0.00 to 0.05' THEN 4
  WHEN '0.05 to 0.10' THEN 5
  ELSE 6
END;


-- ============================================================================
-- QUERY 7: Recalibration Trigger Alerts (Traffic Light Table)
-- ============================================================================
WITH recalibration_triggers AS (
  SELECT
    'Feature Drift (PSI > 0.25)' as trigger_name,
    0.28 as current_value,
    0.25 as threshold,
    'yield_curve_slope' as affected_feature,
    'TRIGGERED' as status,
    '#DC2626' as status_color,
    1 as sort_order
  UNION ALL SELECT 'MAPE Degradation (>10%)', 7.2, 10.0, 'Phase 1 Model', 'OK', '#059669', 2
  UNION ALL SELECT 'Days Since Recalibration (>90)', 45, 90, 'All Models', 'OK', '#059669', 3
  UNION ALL SELECT 'Residual Bias (|mean| > 0.02)', 0.008, 0.02, 'Phase 2 Model', 'OK', '#059669', 4
  UNION ALL SELECT 'Production Accuracy Drop (>5%)', 3.2, 5.0, 'Phase 3 Model', 'OK', '#059669', 5
  UNION ALL SELECT 'Data Quality Issues', 0.5, 5.0, 'Training Data', 'OK', '#059669', 6
)
SELECT
  trigger_name,
  current_value,
  threshold,
  affected_feature,
  status,
  CASE
    WHEN status = 'TRIGGERED' THEN CONCAT('⚠ RECALIBRATE REQUIRED')
    ELSE '✓ No Action Needed'
  END as recommendation,
  status_color,
  sort_order
FROM recalibration_triggers
ORDER BY sort_order;


-- ============================================================================
-- QUERY 8: Quarterly Recalibration History (Timeline)
-- ============================================================================
WITH recalibration_log AS (
  SELECT
    'Q1 2025' as quarter,
    'Scheduled Quarterly' as recal_reason,
    7.8 as pre_mape_pct,
    7.2 as post_mape_pct,
    '+7.7%' as improvement,
    '2025-03-15' as recal_date,
    1 as sort_order
  UNION ALL SELECT 'Q4 2024', 'Feature Drift Alert', 8.9, 8.1, '+9.0%', '2024-12-10', 2
  UNION ALL SELECT 'Q3 2024', 'Scheduled Quarterly', 9.5, 8.8, '+7.4%', '2024-09-12', 3
  UNION ALL SELECT 'Q2 2024', 'Production Accuracy Drop', 10.2, 9.3, '+8.8%', '2024-06-18', 4
)
SELECT
  quarter,
  recal_reason,
  pre_mape_pct,
  post_mape_pct,
  improvement,
  recal_date,
  DATEDIFF(CURRENT_DATE(), recal_date) as days_ago,
  CASE recal_reason
    WHEN 'Scheduled Quarterly' THEN '#059669'
    WHEN 'Feature Drift Alert' THEN '#D97706'
    WHEN 'Production Accuracy Drop' THEN '#DC2626'
    ELSE '#0891B2'
  END as reason_color,
  sort_order
FROM recalibration_log
ORDER BY sort_order;


-- ============================================================================
-- QUERY 9: Model Validation Metrics Comparison (Radar Chart Data)
-- ============================================================================
WITH validation_metrics AS (
  SELECT
    'MAPE' as metric,
    75 as phase1_score,
    82 as phase2_score,
    68 as phase3_score,
    1 as sort_order
  UNION ALL SELECT 'R-Squared', 82, 88, 74, 2
  UNION ALL SELECT 'MAE', 78, 85, 70, 3
  UNION ALL SELECT 'RMSE', 80, 83, 72, 4
  UNION ALL SELECT 'Feature Stability', 85, 78, 65, 5
  UNION ALL SELECT 'Prediction Consistency', 88, 90, 75, 6
)
SELECT
  metric,
  phase1_score,
  phase2_score,
  phase3_score,
  ROUND((phase1_score + phase2_score + phase3_score) / 3.0, 0) as overall_avg,
  sort_order
FROM validation_metrics
ORDER BY sort_order;


-- ============================================================================
-- DASHBOARD AGENT PROMPT FOR DASHBOARD 6
-- ============================================================================

/*
PASTE THIS INTO DATABRICKS AI/BI DASHBOARD AGENT:

Create "Model Performance & Recalibration Monitoring Dashboard" with this layout:

TOP ROW (5 Model Performance KPI Cards):
- Use Query 1 results (5 cards)
- Phase 1/2/3 MAPE/MAE/RMSE, Days Since Recal, PSI
- Show current vs baseline/threshold
- Apply color field to card accent

SECOND ROW (2 Visualizations):
LEFT (60% width):
- Multi-line chart from Query 2 (MAPE Over Time)
- Title: "Model Accuracy Trends (Last 6 Months)"
- X-axis: Month
- Y-axis: MAPE %
- 3 lines (Phase 1, Phase 2, Phase 3)
- Add 3-month moving average as dotted line
- Target line at 8%

RIGHT (40% width):
- Horizontal bar chart from Query 4 (Feature Importance)
- Title: "Top 10 Feature Importance Rankings"
- X-axis: Importance %
- Y-axis: Feature name
- Color by importance_color (red = critical)

THIRD ROW (Full Width):
- Scatter plot from Query 3 (Actual vs Predicted)
- Title: "Phase 1 Beta: Actual vs Predicted (Sample 500)"
- X-axis: Actual Beta
- Y-axis: Predicted Beta
- Add 45-degree reference line (perfect prediction)
- Color by relationship_category
- Size by absolute_error

FOURTH ROW (2 Visualizations):
LEFT (50% width):
- Horizontal bar from Query 5 (PSI by Feature)
- Title: "Feature Drift Monitoring (PSI)"
- X-axis: PSI Score
- Y-axis: Feature name
- Add vertical threshold lines at 0.10, 0.25
- Color by drift_color

RIGHT (50% width):
- Histogram from Query 6 (Residual Distribution)
- Title: "Prediction Residual Distribution"
- X-axis: Residual buckets
- Y-axis: Frequency
- Normal distribution overlay
- Color by bucket_color

FIFTH ROW (Full Width):
- Table from Query 7 (Recalibration Triggers)
- Title: "Automated Recalibration Trigger Monitoring"
- Columns: Trigger, Current, Threshold, Affected Feature, Status, Recommendation
- Apply bold/highlight to TRIGGERED rows
- Color rows by status_color

BOTTOM ROW (2 Visualizations):
LEFT (60% width):
- Timeline from Query 8 (Recalibration History)
- Title: "Quarterly Recalibration Log"
- Show quarter, reason, pre/post MAPE, improvement
- Visual timeline with colored markers
- Color by reason_color

RIGHT (40% width):
- Radar chart from Query 9 (Validation Metrics)
- Title: "Model Validation Scorecard"
- 6 axes (MAPE, R², MAE, RMSE, Stability, Consistency)
- 3 overlays (Phase 1, Phase 2, Phase 3)
- Score range 0-100

DESIGN:
- Data science aesthetic (technical + analytical)
- Monospace fonts for metrics
- Navy/Teal/Emerald palette
- Add alert badges for triggered thresholds
- Enable drill-down to feature-level diagnostics
*/
