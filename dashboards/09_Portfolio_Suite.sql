-- ============================================================================
-- CFO Deposit Portfolio Suite
-- ============================================================================
-- Dashboard ID: 01f0fea1adbb1e97a3142da3a87f7cb8
-- Exported: 2026-02-01T01:18:28.416Z
-- Warehouse: 4b9b953939869799
-- Source: https://e2-demo-field-eng.cloud.databricks.com/dashboardsv3/01f0fea1adbb1e97a3142da3a87f7cb8
-- ============================================================================


-- ============================================================================
-- QUERY 1: KPI - Total Deposits
-- Dataset Name: f2b1215f
-- ============================================================================

SELECT
  'Total Deposits' as metric_name,
  SUM(current_balance) / 1e9 as value_billions,
  '↑' as trend_direction,
  '+2.3%' as trend_change,
  'MoM Growth' as trend_label,
  '#1E3A8A' as color
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
WHERE is_current = TRUE


-- ============================================================================
-- QUERY 2: KPI - Portfolio Beta
-- Dataset Name: 6e354394
-- ============================================================================

SELECT
  'Portfolio Beta' as metric_name,
  ROUND(
    SUM(current_balance * beta) / NULLIF(SUM(current_balance), 0),
    3
  ) as value,
  '↓' as trend_direction,
  '-0.02' as trend_change,
  'vs Last Month' as trend_label,
  '#0891B2' as color
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
WHERE is_current = TRUE
  AND beta IS NOT NULL


-- ============================================================================
-- QUERY 3: KPI - At-Risk Deposits
-- Dataset Name: 2d835e04
-- ============================================================================

SELECT
  'At-Risk Deposits' as metric_name,
  SUM(CASE WHEN below_competitor_rate = TRUE THEN balance_millions ELSE 0 END) / 1000 as value_billions,
  '⚠' as trend_direction,
  '+12.5%' as trend_change,
  'QoQ Increase' as trend_label,
  '#D97706' as color
FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced


-- ============================================================================
-- QUERY 4: KPI - 3Y Runoff Forecast
-- Dataset Name: fd0dc4dc
-- ============================================================================

SELECT
  '3Y Runoff Forecast' as metric_name,
  SUM(current_balance_billions - projected_balance_billions) as value_billions,
  '↓' as trend_direction,
  CONCAT(ROUND((SUM(projected_balance_billions) / SUM(current_balance_billions) - 1) * 100, 1), '%') as trend_change,
  'Projected Decline' as trend_label,
  '#DC2626' as color
FROM cfo_banking_demo.ml_models.deposit_runoff_forecasts
WHERE months_ahead = 36


-- ============================================================================
-- QUERY 5: Portfolio Composition by Relationship
-- Dataset Name: 646ffcc4
-- ============================================================================

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
ORDER BY balance_billions DESC


-- ============================================================================
-- QUERY 6: Beta Distribution by Product Type
-- Dataset Name: 5e761e86
-- ============================================================================

SELECT
  product_type,
  ROUND(AVG(beta), 3) as avg_beta,
  COUNT(*) as account_count,
  SUM(current_balance) / 1e9 as balance_billions,
  CASE
    WHEN AVG(beta) > 0.60 THEN '#DC2626'
    WHEN AVG(beta) > 0.40 THEN '#D97706'
    ELSE '#059669'
  END as risk_color
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
WHERE is_current = TRUE
  AND beta IS NOT NULL
GROUP BY product_type
ORDER BY avg_beta DESC


-- ============================================================================
-- QUERY 7: 3-Year Runoff by Relationship
-- Dataset Name: 0466fb39
-- ============================================================================

SELECT
  months_ahead,
  ROUND(months_ahead / 12.0, 1) as years_ahead,
  relationship_category,
  projected_balance_billions as balance_billions,
  (current_balance_billions - projected_balance_billions) as runoff_billions,
  CASE
    WHEN relationship_category = 'Strategic' THEN '#059669'
    WHEN relationship_category = 'Tactical' THEN '#0891B2'
    WHEN relationship_category = 'Expendable' THEN '#DC2626'
  END as category_color
FROM cfo_banking_demo.ml_models.deposit_runoff_forecasts
WHERE months_ahead IN (0, 6, 12, 18, 24, 30, 36)
ORDER BY months_ahead, relationship_category


-- ============================================================================
-- QUERY 8: Component Decay - Strategic
-- Dataset Name: fba99733
-- ============================================================================

SELECT
  'Strategic Deposits' as segment,
  lambda_closure_rate * 100 as closure_rate_pct,
  g_abgr * 100 as abgr_pct,
  ROUND((1 - lambda_closure_rate) * (1 + g_abgr), 4) as compound_factor,
  '#059669' as color
FROM cfo_banking_demo.ml_models.component_decay_metrics
WHERE relationship_category = 'Strategic'
LIMIT 1


-- ============================================================================
-- QUERY 9: Component Decay - Tactical
-- Dataset Name: bdf9b3d5
-- ============================================================================

SELECT
  'Tactical Deposits' as segment,
  lambda_closure_rate * 100 as closure_rate_pct,
  g_abgr * 100 as abgr_pct,
  ROUND((1 - lambda_closure_rate) * (1 + g_abgr), 4) as compound_factor,
  '#0891B2' as color
FROM cfo_banking_demo.ml_models.component_decay_metrics
WHERE relationship_category = 'Tactical'
LIMIT 1


-- ============================================================================
-- QUERY 10: Component Decay - Expendable
-- Dataset Name: c18a140a
-- ============================================================================

SELECT
  'Expendable Deposits' as segment,
  lambda_closure_rate * 100 as closure_rate_pct,
  g_abgr * 100 as abgr_pct,
  ROUND((1 - lambda_closure_rate) * (1 + g_abgr), 4) as compound_factor,
  '#DC2626' as color
FROM cfo_banking_demo.ml_models.component_decay_metrics
WHERE relationship_category = 'Expendable'
LIMIT 1


-- ============================================================================
-- QUERY 11: Cohort Survival Curves
-- Dataset Name: 638e1ccc
-- ============================================================================

SELECT
  cohort_quarter,
  months_since_open,
  relationship_category,
  balance_survival_rate as survival_rate,
  total_balance / 1e9 as remaining_balance_billions,
  CASE
    WHEN relationship_category = 'Strategic' THEN '#059669'
    WHEN relationship_category = 'Tactical' THEN '#0891B2'
    WHEN relationship_category = 'Expendable' THEN '#DC2626'
  END as line_color
FROM cfo_banking_demo.ml_models.cohort_survival_rates
WHERE cohort_quarter >= DATE_TRUNC('quarter', ADD_MONTHS(CURRENT_DATE(), -24))
  AND months_since_open <= 36
ORDER BY cohort_quarter, months_since_open, relationship_category


-- ============================================================================
-- QUERY 12: Decay Matrix - Closure vs Growth
-- Dataset Name: f8204817
-- ============================================================================

SELECT
  relationship_category,
  product_type,
  ROUND(lambda_closure_rate * 100, 2) as closure_rate_pct,
  ROUND(g_abgr * 100, 2) as abgr_pct,
  total_accounts,
  CASE
    WHEN relationship_category = 'Strategic' THEN '#059669'
    WHEN relationship_category = 'Tactical' THEN '#0891B2'
    WHEN relationship_category = 'Expendable' THEN '#DC2626'
  END as dot_color,
  CASE
    WHEN lambda_closure_rate < 0.05 AND g_abgr > 0 THEN 'Core Growth'
    WHEN lambda_closure_rate < 0.05 AND g_abgr <= 0 THEN 'Core Stable'
    WHEN lambda_closure_rate >= 0.05 AND g_abgr > 0 THEN 'Non-Core Growth'
    ELSE 'High Risk Runoff'
  END as quadrant
FROM cfo_banking_demo.ml_models.component_decay_metrics
ORDER BY total_accounts DESC


-- ============================================================================
-- QUERY 13: Product Decay Rates
-- Dataset Name: 56d06c34
-- ============================================================================

SELECT
  product_type,
  ROUND(AVG(lambda_closure_rate) * 100, 2) as avg_closure_rate_pct,
  ROUND(AVG(g_abgr) * 100, 2) as avg_abgr_pct,
  SUM(total_accounts) as account_count,
  CASE
    WHEN product_type = 'Checking' THEN '#059669'
    WHEN product_type = 'Savings' THEN '#0891B2'
    WHEN product_type = 'Money Market' THEN '#D97706'
    WHEN product_type = 'CD' THEN '#DC2626'
    ELSE '#64748B'
  END as product_color,
  CASE
    WHEN AVG(lambda_closure_rate) < 0.03 THEN 'Very Sticky'
    WHEN AVG(lambda_closure_rate) < 0.08 THEN 'Moderately Sticky'
    ELSE 'Rate Sensitive'
  END as stickiness_label
FROM cfo_banking_demo.ml_models.component_decay_metrics
GROUP BY product_type
ORDER BY avg_closure_rate_pct


-- ============================================================================
-- QUERY 14: Surge Balance Detection
-- Dataset Name: 1f3e9887
-- ============================================================================

SELECT
  DATE_TRUNC('quarter', cohort_quarter) as cohort_quarter,
  SUM(CASE WHEN is_surge_balance = 1 THEN current_balance ELSE 0 END) / 1e9 as surge_balance_billions,
  SUM(CASE WHEN is_surge_balance = 0 THEN current_balance ELSE 0 END) / 1e9 as normal_balance_billions,
  SUM(CASE WHEN is_surge_balance = 1 THEN current_balance ELSE 0 END) /
    NULLIF(SUM(current_balance), 0) * 100 as surge_pct
FROM cfo_banking_demo.ml_models.deposit_cohort_analysis
WHERE is_current = TRUE
  AND cohort_quarter >= '2019-01-01'
GROUP BY DATE_TRUNC('quarter', cohort_quarter)
ORDER BY cohort_quarter


-- ============================================================================
-- QUERY 15: Component Decay Metrics - All Segments
-- Dataset Name: 8567fee7
-- ============================================================================

SELECT
  relationship_category,
  ROUND(AVG(lambda_closure_rate) * 100, 2) as closure_rate_pct,
  ROUND(AVG(g_abgr) * 100, 2) as abgr_pct,
  ROUND(AVG((1 - lambda_closure_rate) * (1 + g_abgr)), 4) as compound_factor,
  SUM(total_accounts) as total_accounts,
  CASE
    WHEN relationship_category = 'Strategic' THEN '#059669'
    WHEN relationship_category = 'Tactical' THEN '#0891B2'
    WHEN relationship_category = 'Expendable' THEN '#DC2626'
  END as color
FROM cfo_banking_demo.ml_models.component_decay_metrics
GROUP BY relationship_category
ORDER BY relationship_category


-- ============================================================================
-- QUERY 16: Core vs Non-Core Classification
-- Dataset Name: 92f5c2a4
-- ============================================================================

SELECT
  CASE
    WHEN lambda_closure_rate < 0.05 THEN 'Core Deposits'
    ELSE 'Non-Core Deposits'
  END as deposit_class,
  SUM(total_accounts) as account_count,
  ROUND(AVG(lambda_closure_rate) * 100, 2) as avg_closure_rate_pct,
  CASE
    WHEN AVG(lambda_closure_rate) < 0.05 THEN '#059669'
    ELSE '#D97706'
  END as class_color
FROM cfo_banking_demo.ml_models.component_decay_metrics
GROUP BY CASE WHEN lambda_closure_rate < 0.05 THEN 'Core Deposits' ELSE 'Non-Core Deposits' END


-- ============================================================================
-- QUERY 17: Customer Relationship KPIs
-- Dataset Name: a765754a
-- ============================================================================

SELECT
  relationship_category as segment,
  COUNT(DISTINCT customer_id) as customer_count,
  SUM(total_relationship_balance_millions) / 1000 as total_balance_billions,
  ROUND(AVG(total_relationship_balance_millions), 1) as avg_balance_millions,
  ROUND(AVG(product_count), 2) as avg_products_per_customer,
  CASE
    WHEN relationship_category = 'Strategic' THEN '#059669'
    WHEN relationship_category = 'Tactical' THEN '#0891B2'
    WHEN relationship_category = 'Expendable' THEN '#DC2626'
  END as color
FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
GROUP BY relationship_category
ORDER BY total_balance_billions DESC


-- ============================================================================
-- QUERY 18: Digital Engagement Impact
-- Dataset Name: 6bb0a6d5
-- ============================================================================

SELECT
  CASE
    WHEN cross_sell_online = true AND cross_sell_mobile = true THEN 'Full Digital'
    WHEN cross_sell_online = true OR cross_sell_mobile = true THEN 'Partial Digital'
    ELSE 'No Digital'
  END as digital_engagement,
  COUNT(DISTINCT account_id) as account_count,
  SUM(balance_millions) / 1000 as balance_billions,
  ROUND(AVG(target_beta), 3) as avg_beta,
  CASE
    WHEN cross_sell_online = true AND cross_sell_mobile = true THEN '#059669'
    WHEN cross_sell_online = true OR cross_sell_mobile = true THEN '#0891B2'
    ELSE '#64748B'
  END as engagement_color
FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
GROUP BY 
  CASE
    WHEN cross_sell_online = true AND cross_sell_mobile = true THEN 'Full Digital'
    WHEN cross_sell_online = true OR cross_sell_mobile = true THEN 'Partial Digital'
    ELSE 'No Digital'
  END,
  CASE
    WHEN cross_sell_online = true AND cross_sell_mobile = true THEN '#059669'
    WHEN cross_sell_online = true OR cross_sell_mobile = true THEN '#0891B2'
    ELSE '#64748B'
  END
ORDER BY balance_billions DESC


-- ============================================================================
-- QUERY 19: Product Penetration Matrix
-- Dataset Name: bd7b2335
-- ============================================================================

SELECT
  relationship_category,
  product_type,
  COUNT(DISTINCT account_id) as account_count,
  SUM(balance_millions) / 1000 as balance_billions,
  ROUND(AVG(target_beta), 3) as avg_beta
FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
GROUP BY relationship_category, product_type
ORDER BY relationship_category, balance_billions DESC


-- ============================================================================
-- QUERY 20: Tenure vs Beta Correlation
-- Dataset Name: 9a06aefb
-- ============================================================================

SELECT
  relationship_category,
  product_type,
  ROUND(relationship_length_years, 1) as tenure_years,
  ROUND(target_beta, 3) as beta,
  balance_millions,
  CASE
    WHEN direct_deposit_flag = 1 THEN 'Direct Deposit'
    ELSE 'No Direct Deposit'
  END as direct_deposit_flag,
  CASE
    WHEN relationship_category = 'Strategic' THEN '#059669'
    WHEN relationship_category = 'Tactical' THEN '#0891B2'
    WHEN relationship_category = 'Expendable' THEN '#DC2626'
  END as dot_color
FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
WHERE target_beta IS NOT NULL
  AND relationship_length_years IS NOT NULL
  AND relationship_length_years <= 20
ORDER BY RAND()
LIMIT 1000


-- ============================================================================
-- QUERY 21: Top 20 Strategic Customers
-- Dataset Name: 6efcce31
-- ============================================================================

SELECT
  customer_id,
  product_count as products,
  ROUND(relationship_length_years, 1) as tenure_years,
  total_relationship_balance_millions as balance_millions,
  ROUND(AVG(target_beta), 3) as avg_beta,
  CASE WHEN direct_deposit_flag = 1 THEN '✓' ELSE '✗' END as direct_deposit,
  CASE WHEN cross_sell_online = true THEN '✓' ELSE '✗' END as online,
  CASE WHEN cross_sell_mobile = true THEN '✓' ELSE '✗' END as mobile,
  CASE WHEN cross_sell_autopay = true THEN '✓' ELSE '✗' END as autopay,
  CASE
    WHEN AVG(target_beta) < 0.35 AND relationship_length_years > 5 AND direct_deposit_flag = 1 THEN '🟢 Low Risk'
    WHEN AVG(target_beta) < 0.50 THEN '🟡 Medium Risk'
    ELSE '🔴 High Risk'
  END as retention_risk
FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
WHERE relationship_category = 'Strategic'
GROUP BY customer_id, product_count, relationship_length_years, total_relationship_balance_millions,
         direct_deposit_flag, cross_sell_online, cross_sell_mobile, cross_sell_autopay
ORDER BY total_relationship_balance_millions DESC
LIMIT 20


-- ============================================================================
-- QUERY 22: Cross-Sell Opportunity Matrix
-- Dataset Name: 66379044
-- ============================================================================

SELECT
  relationship_category,
  CASE
    WHEN product_count = 1 THEN 'Single Product'
    WHEN product_count = 2 THEN 'Two Products'
    WHEN product_count >= 3 THEN 'Multi-Product'
  END as product_tier,
  COUNT(DISTINCT customer_id) as customer_count,
  ROUND(AVG(total_relationship_balance_millions), 2) as avg_balance_millions,
  ROUND(SUM(total_relationship_balance_millions), 2) as total_balance_millions
FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
GROUP BY relationship_category, product_count
ORDER BY relationship_category, product_count


-- ============================================================================
-- QUERY 23: Convenience Features Impact
-- Dataset Name: cd85f6a8
-- ============================================================================

SELECT
  relationship_category,
  CASE
    WHEN direct_deposit_flag = 1 AND cross_sell_autopay = true THEN 'DD + Autopay'
    WHEN direct_deposit_flag = 1 THEN 'Direct Deposit Only'
    WHEN cross_sell_autopay = true THEN 'Autopay Only'
    ELSE 'Neither'
  END as convenience_tier,
  COUNT(DISTINCT account_id) as account_count,
  SUM(balance_millions) / 1000 as balance_billions,
  ROUND(AVG(target_beta), 3) as avg_beta,
  CASE
    WHEN direct_deposit_flag = 1 AND cross_sell_autopay = true THEN '#059669'
    WHEN direct_deposit_flag = 1 OR cross_sell_autopay = true THEN '#0891B2'
    ELSE '#DC2626'
  END as tier_color
FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
GROUP BY relationship_category,
  CASE
    WHEN direct_deposit_flag = 1 AND cross_sell_autopay = true THEN 'DD + Autopay'
    WHEN direct_deposit_flag = 1 THEN 'Direct Deposit Only'
    WHEN cross_sell_autopay = true THEN 'Autopay Only'
    ELSE 'Neither'
  END,
  CASE
    WHEN direct_deposit_flag = 1 AND cross_sell_autopay = true THEN '#059669'
    WHEN direct_deposit_flag = 1 OR cross_sell_autopay = true THEN '#0891B2'
    ELSE '#DC2626'
  END
ORDER BY relationship_category, balance_billions DESC


-- ============================================================================
-- QUERY 24: Cross-Sell Opportunity Matrix
-- Dataset Name: bae0553f
-- ============================================================================

SELECT
  relationship_category,
  CASE
    WHEN product_count = 1 THEN 'Single Product'
    WHEN product_count = 2 THEN 'Two Products'
    WHEN product_count >= 3 THEN 'Multi-Product'
  END as product_tier,
  COUNT(DISTINCT customer_id) as customer_count,
  ROUND(AVG(total_relationship_balance_millions), 2) as avg_balance_millions,
  ROUND(SUM(total_relationship_balance_millions), 2) as total_balance_millions
FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
GROUP BY relationship_category, product_count
ORDER BY relationship_category, product_count


-- ============================================================================
-- QUERY 25: Gap Position KPIs
-- Dataset Name: c8fc8388
-- ============================================================================

SELECT 'Duration Gap' as metric_name, 1.4 as gap_years, '↑ Asset Sensitive' as position, '#D97706' as color
UNION ALL
SELECT 'Cumulative Gap (0-12M)', 31.02 as gap_years, '↑ Positive' as position, '#DC2626' as color
UNION ALL
SELECT 'EVE @ +100bps', -5.2 as gap_years, '-$450M' as position, '#DC2626' as color
UNION ALL
SELECT 'Gap Limit Usage', 65.3 as gap_years, 'Within Policy' as position, '#059669' as color


-- ============================================================================
-- QUERY 26: Repricing Gap by Maturity
-- Dataset Name: e6d16ecd
-- ============================================================================

SELECT
  CASE
    WHEN DATEDIFF(CURRENT_DATE(), account_open_date) / 30 <= 3 THEN '0-3M'
    WHEN DATEDIFF(CURRENT_DATE(), account_open_date) / 30 <= 6 THEN '3-6M'
    WHEN DATEDIFF(CURRENT_DATE(), account_open_date) / 30 <= 12 THEN '6-12M'
    WHEN DATEDIFF(CURRENT_DATE(), account_open_date) / 365 <= 2 THEN '1-2Y'
    WHEN DATEDIFF(CURRENT_DATE(), account_open_date) / 365 <= 5 THEN '2-5Y'
    ELSE '5Y+'
  END as maturity_bucket,
  SUM(current_balance) / 1e9 as balance_billions
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
WHERE is_current = TRUE
GROUP BY 1
ORDER BY CASE maturity_bucket
  WHEN '0-3M' THEN 1
  WHEN '3-6M' THEN 2
  WHEN '6-12M' THEN 3
  WHEN '1-2Y' THEN 4
  WHEN '2-5Y' THEN 5
  ELSE 6
END


-- ============================================================================
-- QUERY 27: EVE Sensitivity Decomposition
-- Dataset Name: 3c1799b2
-- ============================================================================

SELECT 'Duration Effect' as component, -3.8 as contribution_pct, 'Interest rate level change' as description, 1 as sort_order
UNION ALL SELECT 'Convexity Effect', -0.9, 'Non-linear rate impact', 2
UNION ALL SELECT 'Beta Effect', -0.5, 'Deposit repricing lag', 3
UNION ALL SELECT 'Option Effect', 0.0, 'Prepayment/withdrawal options', 4
ORDER BY sort_order


-- ============================================================================
-- QUERY 28: Repricing Gap Heatmap
-- Dataset Name: 744f74b1
-- ============================================================================

SELECT
  product_type,
  CASE
    WHEN DATEDIFF(CURRENT_DATE(), account_open_date) / 30 <= 3 THEN '0-3M'
    WHEN DATEDIFF(CURRENT_DATE(), account_open_date) / 30 <= 6 THEN '3-6M'
    WHEN DATEDIFF(CURRENT_DATE(), account_open_date) / 30 <= 12 THEN '6-12M'
    WHEN DATEDIFF(CURRENT_DATE(), account_open_date) / 365 <= 2 THEN '1-2Y'
    WHEN DATEDIFF(CURRENT_DATE(), account_open_date) / 365 <= 5 THEN '2-5Y'
    ELSE '5Y+'
  END as maturity_bucket,
  SUM(current_balance) / 1e9 as balance_billions,
  COUNT(DISTINCT account_id) as account_count
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
WHERE is_current = TRUE
GROUP BY product_type, 2
ORDER BY product_type, 2


-- ============================================================================
-- QUERY 29: Gap Limit Monitoring
-- Dataset Name: 82ba627b
-- ============================================================================

SELECT '0-3M' as time_bucket, 5.0 as limit_billions, 3.2 as actual_billions, 1 as sort_order
UNION ALL SELECT '3-6M', 8.0, 5.1, 2
UNION ALL SELECT '6-12M', 12.0, 7.8, 3
UNION ALL SELECT '1-2Y', 15.0, 9.2, 4
UNION ALL SELECT '2-5Y', 20.0, 12.5, 5
ORDER BY sort_order


-- ============================================================================
-- QUERY 30: NII Sensitivity Scenarios
-- Dataset Name: a2e425a4
-- ============================================================================

SELECT 'Baseline' as scenario_name, 0 as rate_shock_bps, 'Year 1' as period, 0 as nii_impact_millions, 1 as scenario_order, 1 as period_order
UNION ALL SELECT 'Baseline', 0, 'Year 2', 0, 1, 2
UNION ALL SELECT 'Baseline', 0, 'Year 3', 0, 1, 3
UNION ALL SELECT '+100bps', 100, 'Year 1', 42, 2, 1
UNION ALL SELECT '+100bps', 100, 'Year 2', 65, 2, 2
UNION ALL SELECT '+100bps', 100, 'Year 3', 78, 2, 3
UNION ALL SELECT '+200bps', 200, 'Year 1', 85, 3, 1
UNION ALL SELECT '+200bps', 200, 'Year 2', 142, 3, 2
UNION ALL SELECT '+200bps', 200, 'Year 3', 168, 3, 3
UNION ALL SELECT '-100bps', -100, 'Year 1', -38, 4, 1
UNION ALL SELECT '-100bps', -100, 'Year 2', -58, 4, 2
UNION ALL SELECT '-100bps', -100, 'Year 3', -72, 4, 3
ORDER BY scenario_order, period_order


-- ============================================================================
-- QUERY 31: Duration Distribution
-- Dataset Name: 43bdc354
-- ============================================================================

SELECT
  'Deposits' as category,
  CASE
    WHEN MONTHS_BETWEEN(CURRENT_DATE(), account_open_date) <= 6 THEN '0-0.5Y'
    WHEN MONTHS_BETWEEN(CURRENT_DATE(), account_open_date) <= 12 THEN '0.5-1Y'
    WHEN MONTHS_BETWEEN(CURRENT_DATE(), account_open_date) <= 24 THEN '1-2Y'
    WHEN MONTHS_BETWEEN(CURRENT_DATE(), account_open_date) <= 36 THEN '2-3Y'
    WHEN MONTHS_BETWEEN(CURRENT_DATE(), account_open_date) <= 60 THEN '3-5Y'
    ELSE '5Y+'
  END as duration_bucket,
  SUM(current_balance) / 1e9 as balance_billions
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
WHERE is_current = TRUE
GROUP BY 2
ORDER BY duration_bucket


-- ============================================================================
-- QUERY 32: Regulatory Stress Test KPIs
-- Dataset Name: 325820c6
-- ============================================================================

SELECT 'CET1 Ratio (Baseline)' as metric_name, 12.8 as ratio_pct, '✓ Well-Capitalized' as status, '#059669' as color
UNION ALL SELECT 'CET1 @ Severely Adverse', 8.2, '⚠ Above Minimum', '#D97706'
UNION ALL SELECT 'NII Impact (2Y Cumulative)', -285, '-12.3%', '#DC2626'
UNION ALL SELECT 'Deposit Runoff (2Y)', -8.5, '-28.2%', '#DC2626'
UNION ALL SELECT 'LCR @ Stress', 105, '✓ Above 100%', '#059669'


-- ============================================================================
-- QUERY 33: Capital Ratios by Scenario
-- Dataset Name: 074fd4b0
-- ============================================================================

SELECT 'Baseline' as scenario, 'Q0' as quarter, 12.8 as cet1_pct, 14.2 as tier1_pct, 16.5 as total_capital_pct, 0 as sort_order
UNION ALL SELECT 'Baseline', 'Q1', 12.9, 14.3, 16.6, 1
UNION ALL SELECT 'Baseline', 'Q2', 13.0, 14.4, 16.7, 2
UNION ALL SELECT 'Baseline', 'Q3', 13.1, 14.5, 16.8, 3
UNION ALL SELECT 'Baseline', 'Q4', 13.2, 14.6, 16.9, 4
UNION ALL SELECT 'Baseline', 'Q5', 13.3, 14.7, 17.0, 5
UNION ALL SELECT 'Baseline', 'Q6', 13.4, 14.8, 17.1, 6
UNION ALL SELECT 'Baseline', 'Q7', 13.5, 14.9, 17.2, 7
UNION ALL SELECT 'Baseline', 'Q8', 13.6, 15.0, 17.3, 8
UNION ALL SELECT 'Adverse', 'Q0', 12.8, 14.2, 16.5, 9
UNION ALL SELECT 'Adverse', 'Q1', 12.3, 13.7, 16.0, 10
UNION ALL SELECT 'Adverse', 'Q2', 11.8, 13.2, 15.5, 11
UNION ALL SELECT 'Adverse', 'Q3', 11.4, 12.8, 15.1, 12
UNION ALL SELECT 'Adverse', 'Q4', 11.0, 12.4, 14.7, 13
UNION ALL SELECT 'Adverse', 'Q5', 10.8, 12.2, 14.5, 14
UNION ALL SELECT 'Adverse', 'Q6', 10.6, 12.0, 14.3, 15
UNION ALL SELECT 'Adverse', 'Q7', 10.5, 11.9, 14.2, 16
UNION ALL SELECT 'Adverse', 'Q8', 10.4, 11.8, 14.1, 17
UNION ALL SELECT 'Severely Adverse', 'Q0', 12.8, 14.2, 16.5, 18
UNION ALL SELECT 'Severely Adverse', 'Q1', 11.5, 12.9, 15.2, 19
UNION ALL SELECT 'Severely Adverse', 'Q2', 10.2, 11.6, 13.9, 20
UNION ALL SELECT 'Severely Adverse', 'Q3', 9.3, 10.7, 13.0, 21
UNION ALL SELECT 'Severely Adverse', 'Q4', 8.8, 10.2, 12.5, 22
UNION ALL SELECT 'Severely Adverse', 'Q5', 8.5, 9.9, 12.2, 23
UNION ALL SELECT 'Severely Adverse', 'Q6', 8.3, 9.7, 12.0, 24
UNION ALL SELECT 'Severely Adverse', 'Q7', 8.2, 9.6, 11.9, 25
UNION ALL SELECT 'Severely Adverse', 'Q8', 8.2, 9.6, 11.9, 26
ORDER BY sort_order


-- ============================================================================
-- QUERY 34: Balance Sheet Stress Projections
-- Dataset Name: 0ac84955
-- ============================================================================

SELECT 'Q0' as quarter, 30.1 as deposits_billions, 35.2 as loans_billions, 5.8 as securities_billions, 0 as sort_order
UNION ALL SELECT 'Q1', 29.5, 35.0, 5.9, 1
UNION ALL SELECT 'Q2', 28.8, 34.7, 6.0, 2
UNION ALL SELECT 'Q3', 27.9, 34.3, 6.1, 3
UNION ALL SELECT 'Q4', 27.2, 33.9, 6.2, 4
UNION ALL SELECT 'Q5', 26.5, 33.5, 6.3, 5
UNION ALL SELECT 'Q6', 25.8, 33.1, 6.4, 6
UNION ALL SELECT 'Q7', 25.2, 32.7, 6.5, 7
UNION ALL SELECT 'Q8', 24.7, 32.3, 6.6, 8
ORDER BY sort_order


-- ============================================================================
-- QUERY 35: NII Waterfall Components
-- Dataset Name: b3c0135a
-- ============================================================================

SELECT 'Starting NII' as component, 2320 as amount_millions, 1 as sort_order, '#64748B' as color
UNION ALL SELECT 'Asset Repricing Impact', -285, 2, '#DC2626'
UNION ALL SELECT 'Liability Repricing Impact', 142, 3, '#059669'
UNION ALL SELECT 'Volume Impact (Runoff)', -165, 4, '#DC2626'
UNION ALL SELECT 'Mix Impact', -38, 5, '#D97706'
UNION ALL SELECT 'Fee Income Change', -52, 6, '#DC2626'
UNION ALL SELECT 'Ending NII', 1922, 7, '#1E3A8A'
ORDER BY sort_order


-- ============================================================================
-- QUERY 36: Deposit Runoff by Segment (Stress)
-- Dataset Name: f1b97b69
-- ============================================================================

SELECT
  c.relationship_category,
  SUM(d.current_balance) / 1e9 as current_balance_billions,
  CASE
    WHEN c.relationship_category = 'Strategic' THEN 0.12
    WHEN c.relationship_category = 'Tactical' THEN 0.28
    WHEN c.relationship_category = 'Expendable' THEN 0.45
  END as stress_runoff_rate,
  SUM(d.current_balance) *
    CASE
      WHEN c.relationship_category = 'Strategic' THEN 0.88
      WHEN c.relationship_category = 'Tactical' THEN 0.72
      WHEN c.relationship_category = 'Expendable' THEN 0.55
    END / 1e9 as stressed_balance_billions,
  SUM(d.current_balance) *
    CASE
      WHEN c.relationship_category = 'Strategic' THEN 0.12
      WHEN c.relationship_category = 'Tactical' THEN 0.28
      WHEN c.relationship_category = 'Expendable' THEN 0.45
    END / 1e9 as runoff_billions
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts d
LEFT JOIN (
  SELECT DISTINCT account_id, relationship_category
  FROM cfo_banking_demo.ml_models.deposit_cohort_analysis
  WHERE is_current = TRUE
) c ON d.account_id = c.account_id
WHERE d.is_current = TRUE
  AND c.relationship_category IS NOT NULL
GROUP BY c.relationship_category
ORDER BY runoff_billions DESC


-- ============================================================================
-- QUERY 37: LCR Components by Scenario
-- Dataset Name: ed1084c8
-- ============================================================================

SELECT 'Baseline' as scenario, 8500 as hqla_millions, 7200 as net_outflows_millions, ROUND(8500.0 / 7200 * 100, 0) as lcr_pct, 1 as sort_order
UNION ALL SELECT 'Adverse', 8200, 8100, ROUND(8200.0 / 8100 * 100, 0), 2
UNION ALL SELECT 'Severely Adverse', 7800, 7400, ROUND(7800.0 / 7400 * 100, 0), 3
ORDER BY sort_order


-- ============================================================================
-- QUERY 38: CCAR Schedule A (PP&R)
-- Dataset Name: 16b585e9
-- ============================================================================

SELECT 'Net Interest Income' as line_item, 2320 as baseline_millions, 2145 as adverse_millions, 1922 as severely_adverse_millions, 1 as sort_order, 'Revenue' as category
UNION ALL SELECT 'Non-Interest Income', 485, 425, 368, 2, 'Revenue'
UNION ALL SELECT 'Pre-Provision Net Revenue', 2805, 2570, 2290, 3, 'Revenue'
UNION ALL SELECT 'Provision for Credit Losses', -320, -580, -925, 4, 'Expense'
UNION ALL SELECT 'Non-Interest Expense', -1825, -1825, -1825, 5, 'Expense'
UNION ALL SELECT 'Net Income Before Taxes', 660, 165, -460, 6, 'Income'
UNION ALL SELECT 'Taxes', -165, -41, 115, 7, 'Taxes'
UNION ALL SELECT 'Net Income', 495, 124, -345, 8, 'Income'
UNION ALL SELECT 'Dividends & Distributions', -180, -180, -180, 9, 'Capital'
UNION ALL SELECT 'Retained Earnings', 315, -56, -525, 10, 'Capital'
ORDER BY sort_order


-- ============================================================================
-- QUERY 39: RWA and CET1 Projections
-- Dataset Name: de26c641
-- ============================================================================

SELECT 'Q0' as quarter, 'Baseline' as scenario, 42500 as rwa_millions, 12.8 as cet1_ratio, 0 as sort_order
UNION ALL SELECT 'Q4', 'Baseline', 43200, 13.2, 1
UNION ALL SELECT 'Q8', 'Baseline', 43800, 13.6, 2
UNION ALL SELECT 'Q0', 'Adverse', 42500, 12.8, 3
UNION ALL SELECT 'Q4', 'Adverse', 44100, 11.0, 4
UNION ALL SELECT 'Q8', 'Adverse', 45200, 10.4, 5
UNION ALL SELECT 'Q0', 'Severely Adverse', 42500, 12.8, 6
UNION ALL SELECT 'Q4', 'Severely Adverse', 46800, 8.8, 7
UNION ALL SELECT 'Q8', 'Severely Adverse', 48500, 8.2, 8
ORDER BY sort_order


-- ============================================================================
-- QUERY 40: Stress Test Pass/Fail Summary
-- Dataset Name: 515cb6c0
-- ============================================================================

SELECT 'CET1 Minimum > 7.0%' as test_name, 7.0 as threshold, 8.2 as result, 'Pass' as status, '#059669' as status_color, 1 as sort_order
UNION ALL SELECT 'CET1 Minimum > 9.0%', 9.0, 8.2, 'Fail', '#DC2626', 2
UNION ALL SELECT 'Tier 1 Minimum > 8.5%', 8.5, 9.6, 'Pass', '#059669', 3
UNION ALL SELECT 'Total Capital > 10.5%', 10.5, 11.9, 'Pass', '#059669', 4
UNION ALL SELECT 'LCR > 100%', 100, 105, 'Pass', '#059669', 5
UNION ALL SELECT 'Leverage Ratio > 4.0%', 4.0, 4.8, 'Pass', '#059669', 6
ORDER BY sort_order


-- ============================================================================
-- QUERY 41: Model Performance KPIs
-- Dataset Name: 2c3153b5
-- ============================================================================

SELECT 'Phase 1 Beta MAPE' as metric_name, 7.2 as current_value, 8.5 as baseline_value, '+15.3%' as improvement, '#059669' as color, 1 as sort_order
UNION ALL SELECT 'Phase 2 Runoff MAE', 4.8, 6.2, '+22.6%', '#059669', 2
UNION ALL SELECT 'Phase 3 Stress RMSE', 12.5, 18.3, '+31.7%', '#059669', 3
UNION ALL SELECT 'Days Since Recalibration', 45, 90, CONCAT(ROUND(45.0 / 90 * 100, 0), '%'), CASE WHEN 45 < 75 THEN '#059669' WHEN 45 < 90 THEN '#D97706' ELSE '#DC2626' END, 4
UNION ALL SELECT 'Feature Drift (PSI)', 0.08, 0.10, 'Stable', CASE WHEN 0.08 < 0.10 THEN '#059669' WHEN 0.08 < 0.25 THEN '#D97706' ELSE '#DC2626' END, 5
ORDER BY sort_order


-- ============================================================================
-- QUERY 42: MAPE Time Series by Phase
-- Dataset Name: f18f7d84
-- ============================================================================

WITH monthly_performance AS (
  SELECT '2025-07' as month, 'Phase 1' as model_phase, 8.5 as mape_pct, 1 as sort_order
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
  AVG(mape_pct) OVER (PARTITION BY model_phase ORDER BY sort_order ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) as mape_3m_avg,
  CASE model_phase
    WHEN 'Phase 1' THEN '#1E3A8A'
    WHEN 'Phase 2' THEN '#0891B2'
    WHEN 'Phase 3' THEN '#059669'
  END as phase_color,
  sort_order
FROM monthly_performance
ORDER BY model_phase, sort_order


-- ============================================================================
-- QUERY 43: Actual vs Predicted Beta Scatter
-- Dataset Name: 240a9ae6
-- ============================================================================

SELECT
  target_beta as actual_beta,
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
LIMIT 500


-- ============================================================================
-- QUERY 44: Feature Importance Rankings
-- Dataset Name: c1e92b8f
-- ============================================================================

SELECT 'market_fed_funds_rate' as feature_name, 0.285 as importance_score, 1 as rank, ROUND(0.285 * 100, 1) as importance_pct, '#DC2626' as importance_color
UNION ALL SELECT 'relationship_tenure_years', 0.182, 2, ROUND(0.182 * 100, 1), '#DC2626'
UNION ALL SELECT 'product_count', 0.145, 3, ROUND(0.145 * 100, 1), '#D97706'
UNION ALL SELECT 'current_balance', 0.128, 4, ROUND(0.128 * 100, 1), '#D97706'
UNION ALL SELECT 'yield_curve_slope', 0.092, 5, ROUND(0.092 * 100, 1), '#0891B2'
UNION ALL SELECT 'competitor_rate_spread', 0.078, 6, ROUND(0.078 * 100, 1), '#0891B2'
UNION ALL SELECT 'has_direct_deposit', 0.045, 7, ROUND(0.045 * 100, 1), '#059669'
UNION ALL SELECT 'transaction_count_30d', 0.032, 8, ROUND(0.032 * 100, 1), '#059669'
UNION ALL SELECT 'account_age_years', 0.021, 9, ROUND(0.021 * 100, 1), '#059669'
UNION ALL SELECT 'has_mobile_banking', 0.012, 10, ROUND(0.012 * 100, 1), '#059669'
ORDER BY rank


-- ============================================================================
-- QUERY 45: PSI by Feature (Population Stability)
-- Dataset Name: 69a1de64
-- ============================================================================

SELECT 'market_fed_funds_rate' as feature_name, 0.12 as psi_score, 'Moderate Drift' as drift_status, '#D97706' as drift_color, 1 as sort_order
UNION ALL SELECT 'relationship_tenure_years', 0.05, 'Stable', '#059669', 2
UNION ALL SELECT 'product_count', 0.08, 'Stable', '#059669', 3
UNION ALL SELECT 'current_balance', 0.18, 'Moderate Drift', '#D97706', 4
UNION ALL SELECT 'yield_curve_slope', 0.28, 'High Drift', '#DC2626', 5
UNION ALL SELECT 'competitor_rate_spread', 0.15, 'Moderate Drift', '#D97706', 6
UNION ALL SELECT 'has_direct_deposit', 0.03, 'Stable', '#059669', 7
UNION ALL SELECT 'transaction_count_30d', 0.09, 'Stable', '#059669', 8
UNION ALL SELECT 'account_age_years', 0.04, 'Stable', '#059669', 9
UNION ALL SELECT 'has_mobile_banking', 0.02, 'Stable', '#059669', 10
ORDER BY psi_score DESC


-- ============================================================================
-- QUERY 46: Residual Distribution Histogram
-- Dataset Name: c0a15a3e
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
END


-- ============================================================================
-- QUERY 47: Recalibration Trigger Alerts
-- Dataset Name: a415cf91
-- ============================================================================

SELECT 'Feature Drift (PSI > 0.25)' as trigger_name, 0.28 as current_value, 0.25 as threshold, 'yield_curve_slope' as affected_feature, 'TRIGGERED' as status, '⚠ RECALIBRATE REQUIRED' as recommendation, '#DC2626' as status_color, 1 as sort_order
UNION ALL SELECT 'MAPE Degradation (>10%)', 7.2, 10.0, 'Phase 1 Model', 'OK', '✓ No Action Needed', '#059669', 2
UNION ALL SELECT 'Days Since Recalibration (>90)', 45, 90, 'All Models', 'OK', '✓ No Action Needed', '#059669', 3
UNION ALL SELECT 'Residual Bias (|mean| > 0.02)', 0.008, 0.02, 'Phase 2 Model', 'OK', '✓ No Action Needed', '#059669', 4
UNION ALL SELECT 'Production Accuracy Drop (>5%)', 3.2, 5.0, 'Phase 3 Model', 'OK', '✓ No Action Needed', '#059669', 5
UNION ALL SELECT 'Data Quality Issues', 0.5, 5.0, 'Training Data', 'OK', '✓ No Action Needed', '#059669', 6
ORDER BY sort_order


-- ============================================================================
-- QUERY 48: Quarterly Recalibration History
-- Dataset Name: a1169ebd
-- ============================================================================

SELECT 'Q1 2025' as quarter, 'Scheduled Quarterly' as recal_reason, 7.8 as pre_mape_pct, 7.2 as post_mape_pct, '+7.7%' as improvement, '2025-03-15' as recal_date, DATEDIFF(CURRENT_DATE(), '2025-03-15') as days_ago, '#059669' as reason_color, 1 as sort_order
UNION ALL SELECT 'Q4 2024', 'Feature Drift Alert', 8.9, 8.1, '+9.0%', '2024-12-10', DATEDIFF(CURRENT_DATE(), '2024-12-10'), '#D97706', 2
UNION ALL SELECT 'Q3 2024', 'Scheduled Quarterly', 9.5, 8.8, '+7.4%', '2024-09-12', DATEDIFF(CURRENT_DATE(), '2024-09-12'), '#059669', 3
UNION ALL SELECT 'Q2 2024', 'Production Accuracy Drop', 10.2, 9.3, '+8.8%', '2024-06-18', DATEDIFF(CURRENT_DATE(), '2024-06-18'), '#DC2626', 4
ORDER BY sort_order


-- ============================================================================
-- QUERY 49: Model Validation Scorecard
-- Dataset Name: d4aa3a30
-- ============================================================================

SELECT 'MAPE' as metric, 75 as phase1_score, 82 as phase2_score, 68 as phase3_score, ROUND((75 + 82 + 68) / 3.0, 0) as overall_avg, 1 as sort_order
UNION ALL SELECT 'R-Squared', 82, 88, 74, ROUND((82 + 88 + 74) / 3.0, 0), 2
UNION ALL SELECT 'MAE', 78, 85, 70, ROUND((78 + 85 + 70) / 3.0, 0), 3
UNION ALL SELECT 'RMSE', 80, 83, 72, ROUND((80 + 83 + 72) / 3.0, 0), 4
UNION ALL SELECT 'Feature Stability', 85, 78, 65, ROUND((85 + 78 + 65) / 3.0, 0), 5
UNION ALL SELECT 'Prediction Consistency', 88, 90, 75, ROUND((88 + 90 + 75) / 3.0, 0), 6
ORDER BY sort_order


-- ============================================================================
-- QUERY 50: Treasury Position KPIs
-- Dataset Name: a1381421
-- ============================================================================

SELECT 'Available Liquidity' as metric_name, 8.5 as amount_billions, '+$450M' as daily_change, '↑' as trend_direction, '#059669' as color, 1 as sort_order
UNION ALL SELECT 'Net Funding Position', 2.1, 'Positive', '→', '#0891B2', 2
UNION ALL SELECT 'Wholesale Funding %', 18.5, 'Within Policy (<25%)', '↓', '#059669', 3
UNION ALL SELECT 'Net Deposit Flow (Today)', -0.125, 'Net Outflow', '↓', '#DC2626', 4
UNION ALL SELECT 'Avg Deposit Rate', 2.85, 'vs Market: -15bps', '↑', '#D97706', 5
UNION ALL SELECT 'Brokered Deposits', 4.2, '13.9% of Total', '→', '#D97706', 6
ORDER BY sort_order


-- ============================================================================
-- QUERY 51: Intraday Deposit Flows
-- Dataset Name: 312d080a
-- ============================================================================

WITH intraday_flows AS (
  SELECT '08:00' as hour, 250 as inflows, 180 as outflows, 70 as net_flow, 1 as sort_order
  UNION ALL SELECT '09:00', 420, 320, 100, 2
  UNION ALL SELECT '10:00', 580, 450, 130, 3
  UNION ALL SELECT '11:00', 720, 680, 40, 4
  UNION ALL SELECT '12:00', 650, 720, -70, 5
  UNION ALL SELECT '13:00', 520, 580, -60, 6
  UNION ALL SELECT '14:00', 680, 720, -40, 7
  UNION ALL SELECT '15:00', 890, 820, 70, 8
  UNION ALL SELECT '16:00', 420, 520, -100, 9
  UNION ALL SELECT '17:00', 180, 240, -60, 10
)
SELECT
  hour,
  inflows,
  outflows,
  net_flow,
  SUM(net_flow) OVER (ORDER BY sort_order) as cumulative_flow,
  CASE WHEN net_flow >= 0 THEN '#059669' ELSE '#DC2626' END as flow_color,
  sort_order
FROM intraday_flows
ORDER BY sort_order


-- ============================================================================
-- QUERY 52: Funding Composition Mix
-- Dataset Name: abe46dd5
-- ============================================================================

SELECT
  funding_source,
  amount_billions,
  ROUND(amount_billions / SUM(amount_billions) OVER () * 100, 1) as pct_of_total,
  cost_bps,
  CASE funding_source
    WHEN 'Core Deposits' THEN '#059669'
    WHEN 'Promotional CDs' THEN '#0891B2'
    WHEN 'Brokered Deposits' THEN '#D97706'
    WHEN 'FHLB Advances' THEN '#DC2626'
    WHEN 'Fed Funds Purchased' THEN '#991B1B'
    ELSE '#64748B'
  END as source_color
FROM (
  SELECT 'Core Deposits' as funding_source, 21.5 as amount_billions, 245 as cost_bps
  UNION ALL SELECT 'Promotional CDs', 4.4, 385
  UNION ALL SELECT 'Brokered Deposits', 4.2, 420
  UNION ALL SELECT 'FHLB Advances', 2.8, 485
  UNION ALL SELECT 'Fed Funds Purchased', 0.6, 525
)
ORDER BY amount_billions DESC


-- ============================================================================
-- QUERY 53: Deposit Rate Positioning vs Market
-- Dataset Name: 22250f07
-- ============================================================================

WITH rate_comparison AS (
  SELECT 'Checking' as product_type, 0.50 as our_rate_pct, 0.55 as market_avg_pct, 0.75 as online_bank_avg_pct, 8.5 as balance_billions
  UNION ALL SELECT 'Savings', 2.25, 2.45, 3.10, 9.2
  UNION ALL SELECT 'Money Market', 3.15, 3.35, 3.85, 8.8
  UNION ALL SELECT 'CD 6M', 3.85, 4.00, 4.25, 2.1
  UNION ALL SELECT 'CD 12M', 4.10, 4.25, 4.50, 1.5
)
SELECT
  product_type,
  our_rate_pct,
  market_avg_pct,
  online_bank_avg_pct,
  balance_billions,
  (our_rate_pct - market_avg_pct) * 100 as spread_vs_market_bps,
  CASE
    WHEN our_rate_pct >= market_avg_pct THEN '✓ Competitive'
    WHEN (market_avg_pct - our_rate_pct) <= 0.10 THEN '⚠ Below Market'
    ELSE '✗ Significantly Below'
  END as competitive_status,
  CASE
    WHEN our_rate_pct >= market_avg_pct THEN '#059669'
    WHEN (market_avg_pct - our_rate_pct) <= 0.10 THEN '#D97706'
    ELSE '#DC2626'
  END as status_color
FROM rate_comparison
ORDER BY balance_billions DESC


-- ============================================================================
-- QUERY 54: LCR Trend and Liquidity Buffer
-- Dataset Name: c122c980
-- ============================================================================

WITH daily_liquidity AS (
  SELECT '2026-01-17' as date, 8200 as hqla, 7100 as net_outflows, 115.5 as lcr_pct, 1 as sort_order
  UNION ALL SELECT '2026-01-20', 8300, 7150, 116.1, 2
  UNION ALL SELECT '2026-01-21', 8250, 7200, 114.6, 3
  UNION ALL SELECT '2026-01-22', 8400, 7180, 117.0, 4
  UNION ALL SELECT '2026-01-23', 8350, 7220, 115.7, 5
  UNION ALL SELECT '2026-01-24', 8500, 7250, 117.2, 6
  UNION ALL SELECT '2026-01-27', 8450, 7280, 116.1, 7
  UNION ALL SELECT '2026-01-28', 8550, 7300, 117.1, 8
  UNION ALL SELECT '2026-01-29', 8520, 7320, 116.4, 9
  UNION ALL SELECT '2026-01-30', 8600, 7350, 117.0, 10
  UNION ALL SELECT '2026-01-31', 8650, 7380, 117.2, 11
)
SELECT
  date,
  hqla,
  net_outflows,
  lcr_pct,
  (hqla - net_outflows) as liquidity_buffer,
  CASE
    WHEN lcr_pct >= 115 THEN '#059669'
    WHEN lcr_pct >= 100 THEN '#0891B2'
    WHEN lcr_pct >= 95 THEN '#D97706'
    ELSE '#DC2626'
  END as lcr_color,
  sort_order
FROM daily_liquidity
ORDER BY sort_order


-- ============================================================================
-- QUERY 55: Wholesale Funding Maturity Profile
-- Dataset Name: d7ab7d8c
-- ============================================================================

WITH maturity_profile AS (
  SELECT '0-7D' as maturity_bucket, 850 as amount_millions, 5.25 as weighted_avg_rate_pct, 1 as sort_order
  UNION ALL SELECT '8-30D', 1200, 5.15, 2
  UNION ALL SELECT '31-90D', 1850, 4.95, 3
  UNION ALL SELECT '91-180D', 2100, 4.75, 4
  UNION ALL SELECT '181-365D', 1650, 4.55, 5
  UNION ALL SELECT '1Y+', 980, 4.25, 6
)
SELECT
  maturity_bucket,
  amount_millions,
  weighted_avg_rate_pct,
  SUM(amount_millions) OVER (ORDER BY sort_order) as cumulative_maturing_millions,
  CASE maturity_bucket
    WHEN '0-7D' THEN '#DC2626'
    WHEN '8-30D' THEN '#D97706'
    WHEN '31-90D' THEN '#0891B2'
    ELSE '#059669'
  END as maturity_color,
  sort_order
FROM maturity_profile
ORDER BY sort_order


-- ============================================================================
-- QUERY 56: 30-Day Deposit Flow Trends
-- Dataset Name: 59688aa7
-- ============================================================================

WITH account_monthly_changes AS (
  SELECT
    account_id,
    effective_date as snapshot_date,
    current_balance,
    LAG(current_balance) OVER (PARTITION BY account_id ORDER BY effective_date) as prev_balance
  FROM cfo_banking_demo.bronze_core_banking.deposit_accounts_historical
  WHERE effective_date >= '2023-01-01'
    AND effective_date <= '2026-01-01'
),
account_flows AS (
  SELECT
    snapshot_date,
    CASE
      WHEN current_balance > COALESCE(prev_balance, 0)
      THEN current_balance - COALESCE(prev_balance, 0)
      ELSE 0
    END as account_inflow,
    CASE
      WHEN current_balance < COALESCE(prev_balance, 0)
      THEN COALESCE(prev_balance, 0) - current_balance
      ELSE 0
    END as account_outflow
  FROM account_monthly_changes
  WHERE prev_balance IS NOT NULL
),
monthly_flows AS (
  SELECT
    snapshot_date,
    SUM(account_inflow) / 1e6 as inflows_millions,
    SUM(account_outflow) / 1e6 as outflows_millions
  FROM account_flows
  GROUP BY snapshot_date
)
SELECT
  snapshot_date as flow_date,
  inflows_millions,
  outflows_millions,
  (inflows_millions - outflows_millions) as net_flow_millions,
  AVG(inflows_millions - outflows_millions) OVER (
    ORDER BY snapshot_date
    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
  ) as net_flow_3m_avg,
  CASE
    WHEN (inflows_millions - outflows_millions) >= 0 THEN '#059669'
    ELSE '#DC2626'
  END as flow_color
FROM monthly_flows
ORDER BY snapshot_date


-- ============================================================================
-- QUERY 57: Brokered Deposits Maturity Tracker
-- Dataset Name: 4952a16f
-- ============================================================================

WITH brokered_deposits AS (
  SELECT 'CD-2024-Q1-001' as deal_id, '2024-03-15' as origination_date, '2025-03-15' as maturity_date, 450 as amount_millions, 4.25 as rate_pct, 'Broker A' as broker_name, DATEDIFF('2025-03-15', CURRENT_DATE()) as days_to_maturity
  UNION ALL SELECT 'CD-2024-Q2-003', '2024-06-20', '2025-06-20', 580, 4.35, 'Broker B', DATEDIFF('2025-06-20', CURRENT_DATE())
  UNION ALL SELECT 'CD-2024-Q3-005', '2024-09-10', '2025-09-10', 720, 4.15, 'Broker A', DATEDIFF('2025-09-10', CURRENT_DATE())
  UNION ALL SELECT 'CD-2024-Q4-008', '2024-12-05', '2025-12-05', 650, 4.05, 'Broker C', DATEDIFF('2025-12-05', CURRENT_DATE())
  UNION ALL SELECT 'CD-2025-Q1-002', '2025-01-18', '2026-01-18', 820, 3.95, 'Broker B', DATEDIFF('2026-01-18', CURRENT_DATE())
)
SELECT
  deal_id,
  broker_name,
  amount_millions,
  rate_pct,
  origination_date,
  maturity_date,
  days_to_maturity,
  CASE
    WHEN days_to_maturity <= 30 THEN '🔴 Maturing Soon'
    WHEN days_to_maturity <= 90 THEN '🟡 Within 90 Days'
    ELSE '🟢 Stable'
  END as rollover_status,
  CASE
    WHEN days_to_maturity <= 30 THEN '#DC2626'
    WHEN days_to_maturity <= 90 THEN '#D97706'
    ELSE '#059669'
  END as status_color
FROM brokered_deposits
ORDER BY days_to_maturity


-- ============================================================================
-- QUERY 58: Blended Funding Cost Waterfall
-- Dataset Name: e09a2409
-- ============================================================================

WITH cost_components AS (
  SELECT 'Starting Blended Cost' as component, 2.45 as rate_bps, 1 as sort_order, '#64748B' as color
  UNION ALL SELECT 'Core Deposit Repricing', 0.15, 2, '#DC2626'
  UNION ALL SELECT 'CD Rollover Impact', 0.25, 3, '#DC2626'
  UNION ALL SELECT 'Brokered Deposit Increase', 0.18, 4, '#DC2626'
  UNION ALL SELECT 'FHLB Advance Change', -0.08, 5, '#059669'
  UNION ALL SELECT 'Mix Shift (Core Growth)', -0.12, 6, '#059669'
  UNION ALL SELECT 'Ending Blended Cost', 2.83, 7, '#1E3A8A'
)
SELECT
  component,
  rate_bps,
  SUM(rate_bps) OVER (ORDER BY sort_order) as cumulative_rate_bps,
  sort_order,
  color
FROM cost_components
ORDER BY sort_order


-- ============================================================================
-- QUERY 59: Real-Time Treasury Alerts Feed
-- Dataset Name: b594f5e0
-- ============================================================================

WITH treasury_alerts AS (
  SELECT CURRENT_TIMESTAMP() as alert_timestamp, 'LCR below 105%' as alert_message, 'Warning' as severity, 'Liquidity' as category, '#D97706' as severity_color
  UNION ALL SELECT TIMESTAMP(CURRENT_DATE() || ' 14:30:00'), 'Large withdrawal: $25M from account 12345', 'Info', 'Operations', '#0891B2'
  UNION ALL SELECT TIMESTAMP(CURRENT_DATE() || ' 12:15:00'), 'Wholesale funding maturing in 5 days: $850M', 'Critical', 'Funding', '#DC2626'
  UNION ALL SELECT TIMESTAMP(CURRENT_DATE() || ' 10:45:00'), 'Deposit rate 20bps below market average', 'Warning', 'Pricing', '#D97706'
  UNION ALL SELECT TIMESTAMP(CURRENT_DATE() || ' 09:20:00'), 'Daily net outflow exceeds $200M', 'Warning', 'Liquidity', '#D97706'
)
SELECT
  alert_timestamp,
  alert_message,
  severity,
  category,
  TIMESTAMPDIFF(HOUR, alert_timestamp, CURRENT_TIMESTAMP()) as hours_ago,
  severity_color
FROM treasury_alerts
ORDER BY alert_timestamp DESC
LIMIT 10

