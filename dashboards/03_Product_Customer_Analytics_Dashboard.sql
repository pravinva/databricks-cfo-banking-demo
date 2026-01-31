-- ============================================================================
-- DASHBOARD 3: PRODUCT & CUSTOMER ANALYTICS
-- Audience: Retail Banking, Product Managers, Marketing
-- ============================================================================

-- ============================================================================
-- QUERY 1: Relationship Value KPIs (4 Cards)
-- ============================================================================

-- Card 1: Strategic Customers
SELECT
  'Strategic Customers' as segment,
  COUNT(DISTINCT customer_id) as customer_count,
  SUM(relationship_balance) / 1e9 as total_balance_billions,
  ROUND(AVG(relationship_balance) / 1e6, 1) as avg_balance_millions,
  '#059669' as color  -- Emerald
FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
WHERE relationship_category = 'Strategic'
  AND is_current = TRUE;

-- Card 2: Tactical Customers
SELECT
  'Tactical Customers' as segment,
  COUNT(DISTINCT customer_id) as customer_count,
  SUM(relationship_balance) / 1e9 as total_balance_billions,
  ROUND(AVG(relationship_balance) / 1e6, 1) as avg_balance_millions,
  '#0891B2' as color  -- Teal
FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
WHERE relationship_category = 'Tactical'
  AND is_current = TRUE;

-- Card 3: Expendable Customers
SELECT
  'Expendable Customers' as segment,
  COUNT(DISTINCT customer_id) as customer_count,
  SUM(relationship_balance) / 1e9 as total_balance_billions,
  ROUND(AVG(relationship_balance) / 1e6, 1) as avg_balance_millions,
  '#DC2626' as color  -- Red
FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
WHERE relationship_category = 'Expendable'
  AND is_current = TRUE;

-- Card 4: Average Products per Customer
SELECT
  'Cross-Sell Ratio' as metric,
  ROUND(AVG(product_count), 2) as avg_products_per_customer,
  ROUND(MAX(product_count), 0) as max_products,
  '#D97706' as color  -- Amber
FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
WHERE is_current = TRUE;


-- ============================================================================
-- QUERY 2: Customer Journey Sankey (Relationship Evolution)
-- ============================================================================
WITH customer_segments AS (
  SELECT
    customer_id,
    relationship_category as current_segment,
    customer_segment as demographic_segment,
    product_count,
    relationship_tenure_years,
    relationship_balance / 1e6 as balance_millions
  FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
  WHERE is_current = TRUE
)
SELECT
  demographic_segment as source,
  current_segment as target,
  COUNT(DISTINCT customer_id) as flow_count,
  SUM(balance_millions) as flow_value_millions,
  CASE
    WHEN current_segment = 'Strategic' THEN '#059669'
    WHEN current_segment = 'Tactical' THEN '#0891B2'
    WHEN current_segment = 'Expendable' THEN '#DC2626'
  END as flow_color
FROM customer_segments
GROUP BY demographic_segment, current_segment
ORDER BY flow_value_millions DESC;


-- ============================================================================
-- QUERY 3: Product Penetration Matrix (Heatmap)
-- ============================================================================
SELECT
  relationship_category,
  product_type,
  COUNT(DISTINCT account_id) as account_count,
  SUM(current_balance) / 1e9 as balance_billions,
  ROUND(AVG(beta), 3) as avg_beta,
  ROUND(COUNT(DISTINCT account_id) * 100.0 /
    SUM(COUNT(DISTINCT account_id)) OVER (PARTITION BY relationship_category), 1) as penetration_pct,
  -- Heatmap color based on penetration rate
  CASE
    WHEN COUNT(DISTINCT account_id) * 100.0 /
         SUM(COUNT(DISTINCT account_id)) OVER (PARTITION BY relationship_category) >= 40 THEN '#059669'
    WHEN COUNT(DISTINCT account_id) * 100.0 /
         SUM(COUNT(DISTINCT account_id)) OVER (PARTITION BY relationship_category) >= 20 THEN '#0891B2'
    WHEN COUNT(DISTINCT account_id) * 100.0 /
         SUM(COUNT(DISTINCT account_id)) OVER (PARTITION BY relationship_category) >= 10 THEN '#D97706'
    ELSE '#DC2626'
  END as heatmap_color
FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
WHERE is_current = TRUE
GROUP BY relationship_category, product_type
ORDER BY relationship_category, balance_billions DESC;


-- ============================================================================
-- QUERY 4: Tenure vs Beta Correlation (Scatter Plot)
-- ============================================================================
SELECT
  relationship_category,
  product_type,
  ROUND(relationship_tenure_years, 1) as tenure_years,
  ROUND(beta, 3) as beta,
  current_balance / 1e6 as balance_millions,
  CASE
    WHEN has_direct_deposit = TRUE THEN 'Direct Deposit'
    ELSE 'No Direct Deposit'
  END as direct_deposit_flag,
  CASE
    WHEN relationship_category = 'Strategic' THEN '#059669'
    WHEN relationship_category = 'Tactical' THEN '#0891B2'
    WHEN relationship_category = 'Expendable' THEN '#DC2626'
  END as dot_color
FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
WHERE is_current = TRUE
  AND beta IS NOT NULL
  AND relationship_tenure_years IS NOT NULL
  AND relationship_tenure_years <= 20  -- Cap outliers
ORDER BY RAND()
LIMIT 1000;  -- Sample for performance


-- ============================================================================
-- QUERY 5: Digital Engagement Impact (Bar Chart)
-- ============================================================================
SELECT
  CASE
    WHEN has_online_banking = TRUE AND has_mobile_banking = TRUE THEN 'Full Digital'
    WHEN has_online_banking = TRUE OR has_mobile_banking = TRUE THEN 'Partial Digital'
    ELSE 'No Digital'
  END as digital_engagement,
  COUNT(DISTINCT account_id) as account_count,
  SUM(current_balance) / 1e9 as balance_billions,
  ROUND(AVG(beta), 3) as avg_beta,
  ROUND(AVG(transaction_count_30d), 1) as avg_monthly_txns,
  CASE
    WHEN has_online_banking = TRUE AND has_mobile_banking = TRUE THEN '#059669'
    WHEN has_online_banking = TRUE OR has_mobile_banking = TRUE THEN '#0891B2'
    ELSE '#64748B'
  END as engagement_color
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
WHERE is_current = TRUE
GROUP BY CASE
    WHEN has_online_banking = TRUE AND has_mobile_banking = TRUE THEN 'Full Digital'
    WHEN has_online_banking = TRUE OR has_mobile_banking = TRUE THEN 'Partial Digital'
    ELSE 'No Digital'
  END
ORDER BY balance_billions DESC;


-- ============================================================================
-- QUERY 6: Top 20 Strategic Relationships (Table)
-- ============================================================================
SELECT
  customer_id,
  product_count as products,
  ROUND(relationship_tenure_years, 1) as tenure_years,
  relationship_balance / 1e6 as balance_millions,
  ROUND(AVG(beta), 3) as avg_beta,
  CASE
    WHEN has_direct_deposit = TRUE THEN '✓' ELSE '✗'
  END as direct_deposit,
  CASE
    WHEN has_online_banking = TRUE THEN '✓' ELSE '✗'
  END as online,
  CASE
    WHEN has_mobile_banking = TRUE THEN '✓' ELSE '✗'
  END as mobile,
  CASE
    WHEN autopay_enrolled = TRUE THEN '✓' ELSE '✗'
  END as autopay,
  -- Risk score: Low beta + high tenure + digital = low risk
  CASE
    WHEN AVG(beta) < 0.35 AND relationship_tenure_years > 5 AND has_direct_deposit = TRUE THEN '🟢 Low Risk'
    WHEN AVG(beta) < 0.50 THEN '🟡 Medium Risk'
    ELSE '🔴 High Risk'
  END as retention_risk
FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
WHERE relationship_category = 'Strategic'
  AND is_current = TRUE
GROUP BY customer_id, product_count, relationship_tenure_years, relationship_balance,
         has_direct_deposit, has_online_banking, has_mobile_banking, autopay_enrolled
ORDER BY relationship_balance DESC
LIMIT 20;


-- ============================================================================
-- QUERY 7: Cross-Sell Opportunity Matrix (Bubble Chart)
-- ============================================================================
WITH customer_products AS (
  SELECT
    customer_id,
    relationship_category,
    product_count,
    relationship_balance / 1e6 as balance_millions,
    CASE
      WHEN product_count = 1 THEN 'Single Product'
      WHEN product_count = 2 THEN 'Two Products'
      WHEN product_count >= 3 THEN 'Multi-Product'
    END as product_tier
  FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
  WHERE is_current = TRUE
)
SELECT
  relationship_category,
  product_tier,
  COUNT(DISTINCT customer_id) as customer_count,
  ROUND(AVG(balance_millions), 2) as avg_balance_millions,
  ROUND(SUM(balance_millions), 2) as total_balance_millions,
  -- Opportunity score: Strategic customers with 1-2 products = high opportunity
  CASE
    WHEN relationship_category = 'Strategic' AND product_tier = 'Single Product' THEN '#DC2626'  -- High opportunity
    WHEN relationship_category = 'Strategic' AND product_tier = 'Two Products' THEN '#D97706'    -- Medium opportunity
    WHEN relationship_category = 'Tactical' AND product_tier = 'Single Product' THEN '#D97706'
    ELSE '#059669'  -- Saturated
  END as opportunity_color
FROM customer_products
GROUP BY relationship_category, product_tier
ORDER BY relationship_category, product_tier;


-- ============================================================================
-- QUERY 8: Autopay & Direct Deposit Impact (Grouped Bar Chart)
-- ============================================================================
SELECT
  relationship_category,
  CASE
    WHEN has_direct_deposit = TRUE AND autopay_enrolled = TRUE THEN 'DD + Autopay'
    WHEN has_direct_deposit = TRUE THEN 'Direct Deposit Only'
    WHEN autopay_enrolled = TRUE THEN 'Autopay Only'
    ELSE 'Neither'
  END as convenience_tier,
  COUNT(DISTINCT account_id) as account_count,
  SUM(current_balance) / 1e9 as balance_billions,
  ROUND(AVG(beta), 3) as avg_beta,
  ROUND(AVG(transaction_count_30d), 1) as avg_monthly_txns,
  CASE
    WHEN has_direct_deposit = TRUE AND autopay_enrolled = TRUE THEN '#059669'  -- Stickiest
    WHEN has_direct_deposit = TRUE OR autopay_enrolled = TRUE THEN '#0891B2'
    ELSE '#DC2626'  -- Least sticky
  END as tier_color
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
WHERE is_current = TRUE
GROUP BY relationship_category,
  CASE
    WHEN has_direct_deposit = TRUE AND autopay_enrolled = TRUE THEN 'DD + Autopay'
    WHEN has_direct_deposit = TRUE THEN 'Direct Deposit Only'
    WHEN autopay_enrolled = TRUE THEN 'Autopay Only'
    ELSE 'Neither'
  END
ORDER BY relationship_category, balance_billions DESC;


-- ============================================================================
-- QUERY 9: Balance Tier Distribution (Stacked Bar Chart)
-- ============================================================================
SELECT
  relationship_category,
  CASE
    WHEN current_balance >= 1000000 THEN '$1M+'
    WHEN current_balance >= 250000 THEN '$250K-$1M'
    WHEN current_balance >= 100000 THEN '$100K-$250K'
    WHEN current_balance >= 50000 THEN '$50K-$100K'
    WHEN current_balance >= 10000 THEN '$10K-$50K'
    ELSE '<$10K'
  END as balance_tier,
  COUNT(DISTINCT account_id) as account_count,
  SUM(current_balance) / 1e9 as balance_billions,
  ROUND(COUNT(DISTINCT account_id) * 100.0 /
    SUM(COUNT(DISTINCT account_id)) OVER (PARTITION BY relationship_category), 1) as pct_of_segment,
  CASE
    WHEN current_balance >= 1000000 THEN '#059669'
    WHEN current_balance >= 250000 THEN '#0891B2'
    WHEN current_balance >= 100000 THEN '#64748B'
    WHEN current_balance >= 50000 THEN '#D97706'
    ELSE '#DC2626'
  END as tier_color
FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
WHERE is_current = TRUE
GROUP BY relationship_category,
  CASE
    WHEN current_balance >= 1000000 THEN '$1M+'
    WHEN current_balance >= 250000 THEN '$250K-$1M'
    WHEN current_balance >= 100000 THEN '$100K-$250K'
    WHEN current_balance >= 50000 THEN '$50K-$100K'
    WHEN current_balance >= 10000 THEN '$10K-$50K'
    ELSE '<$10K'
  END
ORDER BY relationship_category,
  CASE balance_tier
    WHEN '$1M+' THEN 1
    WHEN '$250K-$1M' THEN 2
    WHEN '$100K-$250K' THEN 3
    WHEN '$50K-$100K' THEN 4
    WHEN '$10K-$50K' THEN 5
    ELSE 6
  END;


-- ============================================================================
-- DASHBOARD AGENT PROMPT FOR DASHBOARD 3
-- ============================================================================

/*
PASTE THIS INTO DATABRICKS AI/BI DASHBOARD AGENT:

Create "Product & Customer Analytics Dashboard" with this layout:

TOP ROW (4 Relationship KPI Cards):
- Use Query 1 results (4 cards: Strategic, Tactical, Expendable, Cross-Sell Ratio)
- Show: Customer count, balance, avg balance per customer
- Format: Large number with trend indicator
- Apply color field to card accent

SECOND ROW (2 Visualizations):
LEFT (50% width):
- Sankey diagram from Query 2 (Customer Journey)
- Title: "Customer Relationship Evolution"
- Flow from demographic_segment → current_segment
- Width by flow_value_millions
- Color by target relationship category

RIGHT (50% width):
- Heatmap from Query 3 (Product Penetration)
- Title: "Product Mix by Relationship Category"
- Rows: Relationship Category
- Columns: Product Type
- Cell color: Gradient by penetration_pct
- Cell value: Balance ($B)

THIRD ROW (Full Width):
- Scatter plot from Query 4 (Tenure vs Beta)
- Title: "Relationship Tenure Impact on Rate Sensitivity"
- X-axis: Tenure (years)
- Y-axis: Beta
- Size bubbles by balance_millions
- Color by relationship_category
- Shape by direct_deposit_flag
- Add trend line

FOURTH ROW (2 Visualizations):
LEFT (40% width):
- Grouped bar chart from Query 5 (Digital Engagement)
- Title: "Digital Adoption Impact"
- X-axis: Digital engagement tier
- Y-axis: Balance ($B) and avg_beta (dual axis)
- Color by engagement_color

RIGHT (60% width):
- Table from Query 6 (Top Strategic Relationships)
- Title: "Top 20 Strategic Customers"
- Columns: Customer ID, Products, Tenure, Balance, Beta, DD/Online/Mobile/Autopay flags
- Apply conditional formatting to retention_risk column
- Highlight High Risk rows in light red

FIFTH ROW (3 Visualizations):
LEFT (33% width):
- Bubble chart from Query 7 (Cross-Sell Opportunities)
- Title: "Cross-Sell Opportunity Matrix"
- X-axis: Product tier
- Y-axis: Relationship category
- Size by total_balance_millions
- Color by opportunity_color (red = high opportunity)

MIDDLE (33% width):
- Grouped bar chart from Query 8 (Autopay & Direct Deposit)
- Title: "Convenience Features Impact"
- Group by relationship_category
- Stack by convenience_tier
- Color by tier_color

RIGHT (33% width):
- Stacked bar chart from Query 9 (Balance Tiers)
- Title: "Balance Distribution by Segment"
- X-axis: Relationship category
- Y-axis: Account count (%)
- Stack by balance_tier
- Color by tier_color

DESIGN:
- Consumer banking aesthetic (friendly but professional)
- Use full color palette: Navy, Teal, Emerald, Gold, Red, Gray
- Large, readable fonts for customer-facing insights
- Add filters: Relationship Category, Product Type, Digital Flags
- Enable drill-down to individual customers
*/
