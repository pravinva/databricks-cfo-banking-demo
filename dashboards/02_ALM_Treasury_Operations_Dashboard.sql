-- ============================================================================
-- DASHBOARD 2: ALM & TREASURY OPERATIONS
-- Audience: Treasury Team, ALM Committee, Risk Management
-- ============================================================================

-- ============================================================================
-- QUERY 1: Component Decay Metrics KPIs (3 Cards)
-- ============================================================================

-- Card 1: Strategic Deposits Component Metrics
SELECT
  'Strategic Deposits' as segment,
  closure_rate * 100 as closure_rate_pct,
  abgr * 100 as abgr_pct,
  ROUND((1 - closure_rate) * (1 + abgr), 4) as compound_factor,
  '#059669' as color  -- Emerald Green
FROM cfo_banking_demo.ml_models.component_decay_metrics
WHERE relationship_category = 'Strategic'
ORDER BY analysis_date DESC
LIMIT 1;

-- Card 2: Tactical Deposits Component Metrics
SELECT
  'Tactical Deposits' as segment,
  closure_rate * 100 as closure_rate_pct,
  abgr * 100 as abgr_pct,
  ROUND((1 - closure_rate) * (1 + abgr), 4) as compound_factor,
  '#0891B2' as color  -- Teal
FROM cfo_banking_demo.ml_models.component_decay_metrics
WHERE relationship_category = 'Tactical'
ORDER BY analysis_date DESC
LIMIT 1;

-- Card 3: Expendable Deposits Component Metrics
SELECT
  'Expendable Deposits' as segment,
  closure_rate * 100 as closure_rate_pct,
  abgr * 100 as abgr_pct,
  ROUND((1 - closure_rate) * (1 + abgr), 4) as compound_factor,
  '#DC2626' as color  -- Red
FROM cfo_banking_demo.ml_models.component_decay_metrics
WHERE relationship_category = 'Expendable'
ORDER BY analysis_date DESC
LIMIT 1;


-- ============================================================================
-- QUERY 2: Cohort Survival Curves (Kaplan-Meier) - Line Chart
-- ============================================================================
SELECT
  c.cohort_quarter,
  c.months_since_open,
  c.relationship_category,
  s.survival_rate,
  s.remaining_balance / 1e9 as remaining_balance_billions,
  CASE
    WHEN c.relationship_category = 'Strategic' THEN '#059669'
    WHEN c.relationship_category = 'Tactical' THEN '#0891B2'
    WHEN c.relationship_category = 'Expendable' THEN '#DC2626'
  END as line_color
FROM cfo_banking_demo.ml_models.deposit_cohort_analysis c
JOIN cfo_banking_demo.ml_models.cohort_survival_rates s
  ON c.cohort_quarter = s.cohort_quarter
  AND c.relationship_category = s.relationship_category
  AND c.product_type = s.product_type
  AND c.months_since_open = s.months_since_open
WHERE c.cohort_quarter >= DATE_TRUNC('quarter', ADD_MONTHS(CURRENT_DATE(), -24))  -- Last 2 years of cohorts
  AND c.months_since_open <= 36
ORDER BY c.cohort_quarter, c.months_since_open, c.relationship_category;


-- ============================================================================
-- QUERY 3: Closure Rate (λ) vs ABGR (g) Scatter Plot
-- ============================================================================
SELECT
  relationship_category,
  product_type,
  ROUND(closure_rate * 100, 2) as closure_rate_pct,
  ROUND(abgr * 100, 2) as abgr_pct,
  total_accounts,
  total_balance / 1e9 as balance_billions,
  CASE
    WHEN relationship_category = 'Strategic' THEN '#059669'
    WHEN relationship_category = 'Tactical' THEN '#0891B2'
    WHEN relationship_category = 'Expendable' THEN '#DC2626'
  END as dot_color,
  -- Quadrant classification
  CASE
    WHEN closure_rate < 0.05 AND abgr > 0 THEN 'Core Growth'
    WHEN closure_rate < 0.05 AND abgr <= 0 THEN 'Core Stable'
    WHEN closure_rate >= 0.05 AND abgr > 0 THEN 'Non-Core Growth'
    ELSE 'High Risk Runoff'
  END as quadrant
FROM cfo_banking_demo.ml_models.component_decay_metrics
WHERE analysis_date = (SELECT MAX(analysis_date) FROM cfo_banking_demo.ml_models.component_decay_metrics)
ORDER BY balance_billions DESC;


-- ============================================================================
-- QUERY 4: Vintage Analysis Heatmap (Opening Regime Performance)
-- ============================================================================
WITH cohort_performance AS (
  SELECT
    DATE_TRUNC('year', cohort_quarter) as cohort_year,
    opening_regime,
    relationship_category,
    AVG(survival_rate) as avg_survival_rate,
    SUM(remaining_balance) / 1e9 as total_remaining_billions
  FROM cfo_banking_demo.ml_models.cohort_survival_rates
  WHERE months_since_open = 12  -- Focus on 1-year retention
  GROUP BY DATE_TRUNC('year', cohort_quarter), opening_regime, relationship_category
)
SELECT
  YEAR(cohort_year) as year,
  opening_regime,
  relationship_category,
  ROUND(avg_survival_rate * 100, 1) as survival_pct,
  ROUND(total_remaining_billions, 2) as balance_billions,
  -- Color gradient based on survival rate
  CASE
    WHEN avg_survival_rate >= 0.95 THEN '#059669'  -- Excellent (>95%)
    WHEN avg_survival_rate >= 0.90 THEN '#0891B2'  -- Good (90-95%)
    WHEN avg_survival_rate >= 0.85 THEN '#D97706'  -- Fair (85-90%)
    ELSE '#DC2626'                                  -- Poor (<85%)
  END as heatmap_color
FROM cohort_performance
ORDER BY year DESC, opening_regime, relationship_category;


-- ============================================================================
-- QUERY 5: Product-Specific Decay Rates (Bar Chart)
-- ============================================================================
SELECT
  product_type,
  ROUND(AVG(closure_rate) * 100, 2) as avg_closure_rate_pct,
  ROUND(AVG(abgr) * 100, 2) as avg_abgr_pct,
  SUM(total_balance) / 1e9 as balance_billions,
  SUM(total_accounts) as account_count,
  -- Expected ranking: Checking < Savings < Money Market < CD
  CASE
    WHEN product_type = 'Checking' THEN '#059669'
    WHEN product_type = 'Savings' THEN '#0891B2'
    WHEN product_type = 'Money Market' THEN '#D97706'
    WHEN product_type = 'CD' THEN '#DC2626'
    ELSE '#64748B'
  END as product_color,
  CASE
    WHEN AVG(closure_rate) < 0.03 THEN 'Very Sticky'
    WHEN AVG(closure_rate) < 0.08 THEN 'Moderately Sticky'
    ELSE 'Rate Sensitive'
  END as stickiness_label
FROM cfo_banking_demo.ml_models.component_decay_metrics
WHERE analysis_date = (SELECT MAX(analysis_date) FROM cfo_banking_demo.ml_models.component_decay_metrics)
GROUP BY product_type
ORDER BY avg_closure_rate_pct;


-- ============================================================================
-- QUERY 6: Dynamic Beta Function Curves (Line Chart)
-- ============================================================================
-- Note: Phase 3 data - using training data as proxy for historical calibration
WITH rate_scenarios AS (
  SELECT rate / 100.0 as fed_funds_rate
  FROM (
    SELECT EXPLODE(SEQUENCE(0, 600, 25)) as rate  -- 0% to 6% in 25bps increments
  )
),
beta_by_rate AS (
  SELECT
    r.fed_funds_rate,
    c.relationship_category,
    AVG(b.beta) as avg_beta,
    STDDEV(b.beta) as stddev_beta
  FROM rate_scenarios r
  CROSS JOIN (
    SELECT DISTINCT relationship_category
    FROM cfo_banking_demo.ml_models.deposit_cohort_analysis
    WHERE relationship_category IS NOT NULL
  ) c
  LEFT JOIN cfo_banking_demo.ml_models.deposit_beta_training_phase2 b
    ON c.relationship_category = b.relationship_category
    AND ABS(b.market_fed_funds_rate - r.fed_funds_rate) < 0.005  -- Match within 50bps
  GROUP BY r.fed_funds_rate, c.relationship_category
)
SELECT
  ROUND(fed_funds_rate * 100, 2) as rate_pct,
  relationship_category,
  COALESCE(ROUND(avg_beta, 3), 0.40) as beta_estimate,  -- Default 0.40 if no data
  CASE
    WHEN relationship_category = 'Strategic' THEN '#059669'
    WHEN relationship_category = 'Tactical' THEN '#0891B2'
    WHEN relationship_category = 'Expendable' THEN '#DC2626'
  END as curve_color
FROM beta_by_rate
ORDER BY rate_pct, relationship_category;


-- ============================================================================
-- QUERY 7: Core vs Non-Core Classification (Donut Chart)
-- ============================================================================
SELECT
  CASE
    WHEN closure_rate < 0.05 THEN 'Core Deposits'
    ELSE 'Non-Core Deposits'
  END as deposit_class,
  SUM(total_balance) / 1e9 as balance_billions,
  SUM(total_accounts) as account_count,
  ROUND(AVG(closure_rate) * 100, 2) as avg_closure_rate_pct,
  CASE
    WHEN closure_rate < 0.05 THEN '#059669'  -- Core (green)
    ELSE '#D97706'                           -- Non-Core (amber)
  END as class_color
FROM cfo_banking_demo.ml_models.component_decay_metrics
WHERE analysis_date = (SELECT MAX(analysis_date) FROM cfo_banking_demo.ml_models.component_decay_metrics)
GROUP BY CASE WHEN closure_rate < 0.05 THEN 'Core Deposits' ELSE 'Non-Core Deposits' END;


-- ============================================================================
-- QUERY 8: Surge Balance Detection (2020-2022 Pandemic Era)
-- ============================================================================
SELECT
  DATE_TRUNC('quarter', cohort_quarter) as cohort_quarter,
  SUM(CASE WHEN is_surge_balance = TRUE THEN current_balance ELSE 0 END) / 1e9 as surge_balance_billions,
  SUM(CASE WHEN is_surge_balance = FALSE THEN current_balance ELSE 0 END) / 1e9 as normal_balance_billions,
  SUM(CASE WHEN is_surge_balance = TRUE THEN current_balance ELSE 0 END) /
    NULLIF(SUM(current_balance), 0) * 100 as surge_pct,
  CASE
    WHEN DATE_PART('year', cohort_quarter) BETWEEN 2020 AND 2022 THEN '#DC2626'  -- Pandemic era (red)
    ELSE '#0891B2'  -- Normal periods (teal)
  END as period_color
FROM cfo_banking_demo.ml_models.deposit_cohort_analysis
WHERE is_current = TRUE
  AND cohort_quarter >= '2019-01-01'
GROUP BY DATE_TRUNC('quarter', cohort_quarter)
ORDER BY cohort_quarter;


-- ============================================================================
-- DASHBOARD AGENT PROMPT FOR DASHBOARD 2
-- ============================================================================

/*
PASTE THIS INTO DATABRICKS AI/BI DASHBOARD AGENT:

Create "ALM & Treasury Operations Dashboard" with this layout:

TOP ROW (3 Component Decay KPI Cards):
- Use Query 1 results (3 separate cards for Strategic/Tactical/Expendable)
- Show: Closure Rate (λ), ABGR (g), Compound Factor
- Format: "λ: X.XX% | g: +X.XX% | Factor: 0.XXXX"
- Apply color field to card accent

SECOND ROW (2 Visualizations):
LEFT (60% width):
- Multi-line chart from Query 2 (Cohort Survival Curves)
- Title: "Cohort Survival Analysis (Last 2 Years)"
- X-axis: Months Since Open (0-36)
- Y-axis: Survival Rate (0-100%)
- Group by cohort_quarter, color by relationship_category
- Add smoothing for clarity

RIGHT (40% width):
- Scatter plot from Query 3 (Closure vs Growth)
- Title: "Component Decay Matrix"
- X-axis: Closure Rate (λ) %
- Y-axis: ABGR (g) %
- Size bubbles by balance_billions
- Color by relationship_category
- Add quadrant lines at λ=5%, g=0%

THIRD ROW (Full Width):
- Heatmap from Query 4 (Vintage Performance)
- Title: "Cohort Performance by Opening Regime"
- Rows: Years (2019-2026)
- Columns: Opening Regime × Relationship Category
- Cell color: Gradient from red (poor) to green (excellent)
- Cell value: Survival % at 12 months

FOURTH ROW (2 Visualizations):
LEFT (50% width):
- Horizontal bar chart from Query 5 (Product Decay Rates)
- Title: "Runoff Rates by Product Type"
- Show closure_rate_pct as primary bar
- Color by product_color
- Add stickiness_label as annotation

RIGHT (50% width):
- Line chart from Query 6 (Dynamic Beta Curves)
- Title: "Rate Sensitivity by Rate Environment"
- X-axis: Fed Funds Rate (0-6%)
- Y-axis: Beta (0.0-1.0)
- 3 curves (Strategic/Tactical/Expendable)
- Show non-linear dynamics

BOTTOM ROW (2 Visualizations):
LEFT (40% width):
- Donut chart from Query 7 (Core vs Non-Core)
- Title: "Core Deposit Classification"
- Show balance_billions and avg_closure_rate_pct
- Color by class_color

RIGHT (60% width):
- Stacked area chart from Query 8 (Surge Balance Detection)
- Title: "Surge Balance Evolution (Pandemic Era)"
- X-axis: Cohort Quarter
- Y-axis: Balance ($B)
- 2 layers: Surge vs Normal
- Highlight 2020-2022 period

DESIGN:
- Professional treasury aesthetic
- Use Navy, Teal, Emerald, Gold, Red palette
- Add tooltips with detailed metrics
- Enable drill-down by clicking segments
*/
