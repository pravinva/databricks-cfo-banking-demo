# Databricks notebook source
# MAGIC %md
# MAGIC # WS1: Data Foundation & Unity Catalog Governance Demo
# MAGIC
# MAGIC **Purpose**: Demonstrate the complete data foundation for the CFO Banking Demo
# MAGIC
# MAGIC **What You'll See**:
# MAGIC - Unity Catalog governance structure (bronze/silver/gold)
# MAGIC - 500,000+ realistic banking records
# MAGIC - Cross-domain querying (loans, deposits, securities, market data)
# MAGIC - Data lineage and quality metrics
# MAGIC
# MAGIC **Demo Flow**:
# MAGIC 1. Show Unity Catalog structure
# MAGIC 2. Query loan portfolio (97,200 loans)
# MAGIC 3. Query deposit portfolio (402,000 accounts)
# MAGIC 4. Query securities holdings (1,000 securities)
# MAGIC 5. Query market data (treasury yields)
# MAGIC 6. Demonstrate cross-domain analytics
# MAGIC 7. Show data lineage

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Unity Catalog Structure

# COMMAND ----------

# Show catalog and schemas
spark.sql("SHOW SCHEMAS IN cfo_banking_demo").display()

# COMMAND ----------

# MAGIC %md
# MAGIC ### Bronze Layer - Raw Ingestion
# MAGIC - `bronze_core_banking`: Core banking system data (loans, deposits)
# MAGIC - `bronze_market`: Market data (treasury yields, rates)

# COMMAND ----------

# Show bronze_core_banking tables
spark.sql("SHOW TABLES IN cfo_banking_demo.bronze_core_banking").display()

# COMMAND ----------

# Show bronze_market tables
spark.sql("SHOW TABLES IN cfo_banking_demo.bronze_market").display()

# COMMAND ----------

# MAGIC %md
# MAGIC ### Silver Layer - Curated Analytics-Ready
# MAGIC - `silver_finance`: Curated financial data with business logic applied

# COMMAND ----------

spark.sql("SHOW TABLES IN cfo_banking_demo.silver_finance").display()

# COMMAND ----------

# MAGIC %md
# MAGIC ### Gold Layer - Business Aggregates
# MAGIC - `gold_finance`: Executive dashboards and regulatory reports
# MAGIC - `gold_analytics`: Advanced analytics and ML features

# COMMAND ----------

spark.sql("SHOW TABLES IN cfo_banking_demo.gold_finance").display()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Loan Portfolio Analytics (97,200 Loans)

# COMMAND ----------

# Total loan portfolio summary
loan_summary = spark.sql("""
    SELECT
        COUNT(*) as total_loans,
        ROUND(SUM(current_balance)/1e9, 2) as total_balance_billions,
        ROUND(AVG(interest_rate), 2) as avg_rate_pct,
        COUNT(DISTINCT product_type) as product_types
    FROM cfo_banking_demo.silver_finance.loan_portfolio
    WHERE is_current = true
""")
loan_summary.display()

# COMMAND ----------

# Breakdown by product type
product_breakdown = spark.sql("""
    SELECT
        product_type,
        COUNT(*) as loan_count,
        ROUND(SUM(current_balance)/1e9, 2) as balance_billions,
        ROUND(AVG(interest_rate), 2) as avg_rate,
        ROUND(AVG(remaining_term_months), 0) as avg_term_months,
        ROUND(SUM(current_balance) / (SELECT SUM(current_balance) FROM cfo_banking_demo.silver_finance.loan_portfolio WHERE is_current = true) * 100, 1) as portfolio_pct
    FROM cfo_banking_demo.silver_finance.loan_portfolio
    WHERE is_current = true
    GROUP BY product_type
    ORDER BY balance_billions DESC
""")
product_breakdown.display()

# COMMAND ----------

# Credit quality distribution
credit_quality = spark.sql("""
    SELECT
        CASE
            WHEN credit_score >= 750 THEN 'A (750+)'
            WHEN credit_score >= 700 THEN 'B (700-749)'
            WHEN credit_score >= 650 THEN 'C (650-699)'
            ELSE 'D (<650)'
        END as risk_rating,
        COUNT(*) as loan_count,
        ROUND(SUM(current_balance)/1e9, 2) as balance_billions,
        ROUND(AVG(interest_rate), 2) as avg_rate
    FROM cfo_banking_demo.silver_finance.loan_portfolio
    WHERE is_current = true
    GROUP BY risk_rating
    ORDER BY risk_rating
""")
credit_quality.display()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Deposit Portfolio Analytics (402,000 Accounts)

# COMMAND ----------

# Total deposit portfolio summary
deposit_summary = spark.sql("""
    SELECT
        COUNT(*) as total_accounts,
        ROUND(SUM(current_balance)/1e9, 2) as total_balance_billions,
        ROUND(AVG(interest_rate), 2) as avg_rate_pct,
        COUNT(DISTINCT product_type) as product_types
    FROM cfo_banking_demo.silver_finance.deposit_portfolio
    WHERE is_current = true
""")
deposit_summary.display()

# COMMAND ----------

# Deposit product breakdown with beta analysis
deposit_breakdown = spark.sql("""
    SELECT
        product_type,
        COUNT(*) as account_count,
        ROUND(SUM(current_balance)/1e9, 2) as balance_billions,
        ROUND(AVG(interest_rate), 2) as avg_rate,
        CASE product_type
            WHEN 'MMDA' THEN 0.85
            WHEN 'DDA' THEN 0.20
            WHEN 'NOW' THEN 0.45
            WHEN 'Savings' THEN 0.60
            WHEN 'CD' THEN 0.95
            ELSE 0.50
        END as deposit_beta,
        ROUND(SUM(current_balance) / (SELECT SUM(current_balance) FROM cfo_banking_demo.silver_finance.deposit_portfolio WHERE is_current = true) * 100, 1) as portfolio_pct
    FROM cfo_banking_demo.silver_finance.deposit_portfolio
    WHERE is_current = true
    GROUP BY product_type
    ORDER BY balance_billions DESC
""")
deposit_breakdown.display()

# COMMAND ----------

# MAGIC %md
# MAGIC **Key Insight**: MMDA (Money Market) has highest beta (0.85) = most rate-sensitive
# MAGIC
# MAGIC **Key Insight**: DDA (Demand Deposits) has lowest beta (0.20) = most stable funding

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Securities Portfolio (1,000 Securities)

# COMMAND ----------

# Securities portfolio summary
securities_summary = spark.sql("""
    SELECT
        security_type,
        COUNT(*) as security_count,
        ROUND(SUM(market_value)/1e9, 2) as market_value_billions,
        ROUND(AVG(ytm) * 100, 2) as avg_yield_pct,
        ROUND(AVG(effective_duration), 1) as avg_duration_years,
        ROUND(SUM(market_value) / (SELECT SUM(market_value) FROM cfo_banking_demo.silver_finance.securities WHERE is_current = true) * 100, 1) as portfolio_pct
    FROM cfo_banking_demo.silver_finance.securities
    WHERE is_current = true
    GROUP BY security_type
    ORDER BY market_value_billions DESC
""")
securities_summary.display()

# COMMAND ----------

# HQLA (High-Quality Liquid Assets) classification
hqla_analysis = spark.sql("""
    SELECT
        CASE
            WHEN security_type IN ('UST', 'Agency MBS') THEN 'Level 1 HQLA'
            WHEN security_type IN ('Agency CMO', 'GSE Debt') THEN 'Level 2A HQLA'
            WHEN security_type IN ('Corporate Bond', 'Municipal Bond') THEN 'Level 2B HQLA'
            ELSE 'Non-HQLA'
        END as hqla_level,
        COUNT(*) as security_count,
        ROUND(SUM(market_value)/1e9, 2) as market_value_billions,
        ROUND(AVG(ytm) * 100, 2) as avg_yield_pct
    FROM cfo_banking_demo.silver_finance.securities
    WHERE is_current = true
    GROUP BY hqla_level
    ORDER BY
        CASE hqla_level
            WHEN 'Level 1 HQLA' THEN 1
            WHEN 'Level 2A HQLA' THEN 2
            WHEN 'Level 2B HQLA' THEN 3
            ELSE 4
        END
""")
hqla_analysis.display()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Market Data - Treasury Yield Curve

# COMMAND ----------

# Latest treasury yield curve
latest_yields = spark.sql("""
    SELECT
        observation_date,
        tenor_years,
        ROUND(yield_rate * 100, 2) as yield_pct
    FROM cfo_banking_demo.bronze_market.treasury_yields
    WHERE observation_date = (
        SELECT MAX(observation_date)
        FROM cfo_banking_demo.bronze_market.treasury_yields
    )
    ORDER BY tenor_years
""")
latest_yields.display()

# COMMAND ----------

# Yield curve visualization (line chart)
display(latest_yields)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Cross-Domain Analytics

# COMMAND ----------

# MAGIC %md
# MAGIC ### Asset-Liability Gap Analysis

# COMMAND ----------

# Interest rate sensitivity gap
gap_analysis = spark.sql("""
    WITH asset_side AS (
        SELECT
            'Loans' as category,
            SUM(current_balance) as amount,
            AVG(interest_rate) as avg_rate,
            'Asset' as side
        FROM cfo_banking_demo.silver_finance.loan_portfolio
        WHERE is_current = true

        UNION ALL

        SELECT
            'Securities' as category,
            SUM(market_value) as amount,
            AVG(ytm * 100) as avg_rate,
            'Asset' as side
        FROM cfo_banking_demo.silver_finance.securities
        WHERE is_current = true
    ),
    liability_side AS (
        SELECT
            'Deposits' as category,
            SUM(current_balance) as amount,
            AVG(interest_rate) as avg_rate,
            'Liability' as side
        FROM cfo_banking_demo.silver_finance.deposit_portfolio
        WHERE is_current = true
    )
    SELECT
        category,
        side,
        ROUND(amount/1e9, 2) as balance_billions,
        ROUND(avg_rate, 2) as avg_rate_pct
    FROM asset_side
    UNION ALL
    SELECT * FROM liability_side
    ORDER BY side DESC, balance_billions DESC
""")
gap_analysis.display()

# COMMAND ----------

# Net Interest Margin (NIM) calculation
nim_calc = spark.sql("""
    WITH interest_income AS (
        SELECT SUM(current_balance * interest_rate / 100.0) as annual_interest_income
        FROM cfo_banking_demo.silver_finance.loan_portfolio
        WHERE is_current = true
    ),
    interest_expense AS (
        SELECT SUM(current_balance * interest_rate / 100.0) as annual_interest_expense
        FROM cfo_banking_demo.silver_finance.deposit_portfolio
        WHERE is_current = true
    ),
    earning_assets AS (
        SELECT SUM(current_balance) as total_earning_assets
        FROM cfo_banking_demo.silver_finance.loan_portfolio
        WHERE is_current = true
    )
    SELECT
        ROUND((i.annual_interest_income - e.annual_interest_expense) / ea.total_earning_assets * 100, 2) as nim_pct,
        ROUND(i.annual_interest_income / 1e9, 2) as interest_income_billions,
        ROUND(e.annual_interest_expense / 1e9, 2) as interest_expense_billions,
        ROUND((i.annual_interest_income - e.annual_interest_expense) / 1e9, 2) as net_interest_income_billions
    FROM interest_income i, interest_expense e, earning_assets ea
""")
nim_calc.display()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Regulatory Metrics

# COMMAND ----------

# Capital adequacy calculations
capital_adequacy = spark.sql("""
    SELECT
        'CET1' as capital_type,
        ROUND((SUM(common_stock + retained_earnings - goodwill - intangibles)/1e9) / 25.0 * 100, 1) as ratio_pct,
        7.0 as minimum_pct,
        8.5 as well_capitalized_pct,
        CASE
            WHEN ROUND((SUM(common_stock + retained_earnings - goodwill - intangibles)/1e9) / 25.0 * 100, 1) >= 8.5 THEN 'Well Capitalized'
            WHEN ROUND((SUM(common_stock + retained_earnings - goodwill - intangibles)/1e9) / 25.0 * 100, 1) >= 7.0 THEN 'Adequately Capitalized'
            ELSE 'Undercapitalized'
        END as status
    FROM cfo_banking_demo.gold_finance.capital_structure

    UNION ALL

    SELECT
        'Tier 1',
        ROUND((SUM(tier1_capital)/1e9) / 25.0 * 100, 1),
        8.5,
        10.0,
        CASE
            WHEN ROUND((SUM(tier1_capital)/1e9) / 25.0 * 100, 1) >= 10.0 THEN 'Well Capitalized'
            WHEN ROUND((SUM(tier1_capital)/1e9) / 25.0 * 100, 1) >= 8.5 THEN 'Adequately Capitalized'
            ELSE 'Undercapitalized'
        END
    FROM cfo_banking_demo.gold_finance.capital_structure

    UNION ALL

    SELECT
        'Total Capital',
        ROUND((SUM(tier1_capital + tier2_capital)/1e9) / 25.0 * 100, 1),
        10.5,
        13.0,
        CASE
            WHEN ROUND((SUM(tier1_capital + tier2_capital)/1e9) / 25.0 * 100, 1) >= 13.0 THEN 'Well Capitalized'
            WHEN ROUND((SUM(tier1_capital + tier2_capital)/1e9) / 25.0 * 100, 1) >= 10.5 THEN 'Adequately Capitalized'
            ELSE 'Undercapitalized'
        END
    FROM cfo_banking_demo.gold_finance.capital_structure
""")
capital_adequacy.display()

# COMMAND ----------

# Liquidity Coverage Ratio (LCR)
lcr_calc = spark.sql("""
    SELECT
        ROUND(AVG(hqla)/1e9, 2) as hqla_billions,
        ROUND(AVG(net_cash_outflow)/1e9, 2) as net_outflow_billions,
        ROUND(AVG(lcr_ratio) * 100, 1) as lcr_pct,
        100.0 as minimum_pct,
        CASE
            WHEN AVG(lcr_ratio) * 100 >= 100.0 THEN 'Compliant'
            ELSE 'Non-Compliant'
        END as status
    FROM cfo_banking_demo.gold_finance.liquidity_coverage_ratio
""")
lcr_calc.display()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Data Lineage
# MAGIC
# MAGIC **Unity Catalog automatically tracks**:
# MAGIC - Which tables were read
# MAGIC - Which tables were written
# MAGIC - Transformation logic
# MAGIC - User access patterns
# MAGIC
# MAGIC **View lineage in**:
# MAGIC - Catalog Explorer → Select table → Lineage tab
# MAGIC - Data Explorer → Table details → Lineage graph

# COMMAND ----------

# MAGIC %md
# MAGIC ## Demo Summary
# MAGIC
# MAGIC **What We Built**:
# MAGIC - ✅ Unity Catalog with bronze/silver/gold medallion
# MAGIC - ✅ 97,200 loans ($31B)
# MAGIC - ✅ 402,000 deposit accounts ($28B)
# MAGIC - ✅ 1,000 securities ($8B)
# MAGIC - ✅ 900 treasury yield data points
# MAGIC - ✅ Capital adequacy calculations
# MAGIC - ✅ Liquidity metrics (LCR)
# MAGIC - ✅ NIM analytics
# MAGIC
# MAGIC **Next Steps**:
# MAGIC - WS2: Real-time loan origination streaming
# MAGIC - WS3: Mosaic AI deposit beta model training
# MAGIC - WS5: Lakeview executive dashboards
# MAGIC - WS6: React frontend with AI assistant
