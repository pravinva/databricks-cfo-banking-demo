-- Generated SQL COMMENT statements for Genie Space tables
-- Review these statements before executing in Databricks


-- cfo_banking_demo.ml_models.deposit_beta_training_enhanced
-- Columns: 41

COMMENT ON TABLE cfo_banking_demo.ml_models.deposit_beta_training_enhanced IS 'Phase 1 Deposit Beta Model - Training dataset with 41 features for XGBoost model achieving 7.2% MAPE accuracy. Contains rate sensitivity analysis, relationship categorization (Strategic/Tactical/Expendable), and at-risk account identification. Use for: deposit pricing strategy, rate shock analysis, customer retention, and flight risk assessment.';

COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.account_id IS 'Unique deposit account identifier';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.customer_id IS 'Unique customer identifier';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.effective_date IS 'Date of this data snapshot';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.target_beta IS 'Deposit beta coefficient (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.account_open_date IS 'Date field (DATE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.cohort_quarter IS 'Cohort Quarter (TIMESTAMP)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.product_type IS 'Product Type (STRING)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.customer_segment IS 'Customer Segment (STRING)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.account_age_years IS 'Count metric (DECIMAL)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.balance_tier IS 'Account balance (STRING)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.balance_millions IS 'Account balance (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.avg_balance_30d_millions IS 'Account balance (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.stated_rate IS 'Interest rate or rate metric (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.transaction_count_30d IS 'Count metric (INT)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.rate_gap IS 'Interest rate or rate metric (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.rate_spread_3m IS 'Interest rate or rate metric (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.digital_user IS 'Digital User (INT)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.product_count IS 'Count metric (LONG)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.total_relationship_balance_millions IS 'Account balance (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.relationship_length_years IS 'Relationship Length Years (DECIMAL)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.relationship_score IS 'Relationship Score (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.relationship_category IS 'Relationship Category (STRING)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.primary_bank_flag IS 'Boolean flag indicator (INT)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.direct_deposit_flag IS 'Boolean flag indicator (INT)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.cross_sell_online IS 'Cross Sell Online (BOOLEAN)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.cross_sell_mobile IS 'Cross Sell Mobile (BOOLEAN)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.cross_sell_autopay IS 'Cross Sell Autopay (BOOLEAN)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.market_fed_funds_rate IS 'Interest rate or rate metric (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.market_rate_3m IS 'Interest rate or rate metric (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.yield_curve_slope IS 'Yield Curve Slope (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.rate_regime IS 'Interest rate or rate metric (STRING)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.rate_change_velocity_3m IS 'Interest rate or rate metric (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.yield_curve_inverted IS 'Yield Curve Inverted (INT)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.competitor_rate_spread IS 'Interest rate or rate metric (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.online_bank_rate_spread IS 'Interest rate or rate metric (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.market_rate_spread IS 'Interest rate or rate metric (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.below_competitor_rate IS 'Interest rate or rate metric (INT)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.balance_trend_30d IS 'Account balance (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.month_of_year IS 'Month Of Year (INT)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.quarter IS 'Quarter (INT)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_beta_training_enhanced.day_of_week IS 'Day Of Week (INT)';


-- cfo_banking_demo.bronze_core_banking.deposit_accounts
-- Columns: 36

COMMENT ON TABLE cfo_banking_demo.bronze_core_banking.deposit_accounts IS 'Bronze layer deposit account master data from core banking system. Contains current balances, rates, product types, and customer relationships. Updated daily via CDC. Use for: deposit portfolio analysis, customer segmentation, and balance trend monitoring.';

COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.account_id IS 'Unique deposit account identifier';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.account_number IS 'Count metric (STRING)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.customer_id IS 'Unique customer identifier';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.customer_name IS 'Customer Name (STRING)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.customer_type IS 'Customer Type (STRING)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.customer_segment IS 'Customer Segment (STRING)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.product_type IS 'Product Type (STRING)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.product_name IS 'Product Name (STRING)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.account_open_date IS 'Date field (DATE)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.maturity_date IS 'Date field (DATE)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.current_balance IS 'Account balance (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.average_balance_30d IS 'Account balance (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.average_balance_90d IS 'Account balance (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.minimum_balance IS 'Account balance (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.maximum_balance IS 'Account balance (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.stated_rate IS 'Interest rate or rate metric (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.beta IS 'Deposit beta coefficient (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.decay_rate IS 'Interest rate or rate metric (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.interest_accrued IS 'Interest Accrued (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.ytd_interest_paid IS 'Ytd Interest Paid (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.transaction_count_30d IS 'Count metric (INT)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.last_transaction_date IS 'Date field (DATE)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.account_status IS 'Count metric (STRING)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.fdic_insured IS 'Fdic Insured (BOOLEAN)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.relationship_balance IS 'Account balance (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.has_online_banking IS 'Has Online Banking (BOOLEAN)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.has_mobile_banking IS 'Has Mobile Banking (BOOLEAN)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.autopay_enrolled IS 'Autopay Enrolled (BOOLEAN)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.overdraft_protection IS 'Overdraft Protection (BOOLEAN)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.monthly_fee IS 'Monthly Fee (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.fee_waivers IS 'Fee Waivers (STRING)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.geography IS 'Geography (STRING)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.branch_id IS 'Branch Id (STRING)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.officer_id IS 'Officer Id (STRING)';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.effective_date IS 'Date of this data snapshot';
COMMENT ON COLUMN cfo_banking_demo.bronze_core_banking.deposit_accounts.is_current IS 'Boolean indicator (BOOLEAN)';


-- cfo_banking_demo.ml_models.component_decay_metrics
-- Columns: 12

COMMENT ON TABLE cfo_banking_demo.ml_models.component_decay_metrics IS 'Phase 2 Vintage Analysis - Component-level decay metrics tracking deposit runoff patterns by cohort and product. Shows month-over-month decay rates, cumulative survival, and half-life calculations. Use for: liquidity forecasting, deposit stability analysis, and funding cost projections.';

COMMENT ON COLUMN cfo_banking_demo.ml_models.component_decay_metrics.relationship_category IS 'Relationship Category (STRING)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.component_decay_metrics.product_type IS 'Product Type (STRING)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.component_decay_metrics.is_surge_balance IS 'Account balance (INT)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.component_decay_metrics.total_accounts IS 'Count metric (LONG)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.component_decay_metrics.closed_accounts IS 'Count metric (LONG)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.component_decay_metrics.closure_rate_cumulative IS 'Interest rate or rate metric (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.component_decay_metrics.lambda_closure_rate IS 'Interest rate or rate metric (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.component_decay_metrics.survivor_accounts IS 'Count metric (LONG)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.component_decay_metrics.g_abgr IS 'G Abgr (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.component_decay_metrics.stddev_monthly_growth IS 'Stddev Monthly Growth (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.component_decay_metrics.expected_net_growth_rate IS 'Interest rate or rate metric (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.component_decay_metrics.abgr_classification IS 'Abgr Classification (STRING)';


-- cfo_banking_demo.ml_models.cohort_survival_rates
-- Columns: 16

COMMENT ON TABLE cfo_banking_demo.ml_models.cohort_survival_rates IS 'Phase 2 Vintage Analysis - Cohort-based survival rates tracking deposit retention over 36+ months. Essential for deposit runoff forecasting and liquidity stress testing. Use for: LCR forecasting, deposit mix optimization, and retention strategy.';

COMMENT ON COLUMN cfo_banking_demo.ml_models.cohort_survival_rates.cohort_quarter IS 'Cohort Quarter (TIMESTAMP)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.cohort_survival_rates.cohort_year IS 'Cohort Year (INT)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.cohort_survival_rates.cohort_q IS 'Cohort Q (INT)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.cohort_survival_rates.relationship_category IS 'Relationship Category (STRING)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.cohort_survival_rates.product_type IS 'Product Type (STRING)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.cohort_survival_rates.is_surge_balance IS 'Account balance (INT)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.cohort_survival_rates.opening_regime IS 'Opening Regime (STRING)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.cohort_survival_rates.months_since_open IS 'Months Since Open (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.cohort_survival_rates.account_count IS 'Count metric (LONG)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.cohort_survival_rates.total_balance IS 'Account balance (DECIMAL)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.cohort_survival_rates.initial_account_count IS 'Count metric (LONG)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.cohort_survival_rates.initial_balance IS 'Account balance (DECIMAL)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.cohort_survival_rates.account_survival_rate IS 'Interest rate or rate metric (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.cohort_survival_rates.balance_survival_rate IS 'Account balance (DECIMAL)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.cohort_survival_rates.annualized_account_decay_rate IS 'Interest rate or rate metric (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.cohort_survival_rates.annualized_balance_decay_rate IS 'Account balance (DOUBLE)';


-- cfo_banking_demo.ml_models.deposit_runoff_forecasts
-- Columns: 10

COMMENT ON TABLE cfo_banking_demo.ml_models.deposit_runoff_forecasts IS 'Phase 2 Vintage Analysis - Forward-looking deposit runoff forecasts by cohort and product. 12-month rolling forecasts with confidence intervals. Use for: cash flow forecasting, liquidity planning, and ALCO reporting.';

COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_runoff_forecasts.relationship_category IS 'Relationship Category (STRING)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_runoff_forecasts.product_type IS 'Product Type (STRING)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_runoff_forecasts.months_ahead IS 'Months Ahead (INT)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_runoff_forecasts.current_account_count IS 'Count metric (LONG)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_runoff_forecasts.current_balance_billions IS 'Account balance (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_runoff_forecasts.lambda IS 'Lambda (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_runoff_forecasts.g IS 'G (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_runoff_forecasts.net_growth IS 'Net Growth (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_runoff_forecasts.projected_balance_billions IS 'Account balance (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.deposit_runoff_forecasts.projected_account_count IS 'Count metric (DOUBLE)';


-- cfo_banking_demo.ml_models.dynamic_beta_parameters
-- Columns: 6

COMMENT ON TABLE cfo_banking_demo.ml_models.dynamic_beta_parameters IS 'Phase 3 CCAR Stress Testing - Dynamic deposit beta coefficients under different stress scenarios. Models non-linear rate sensitivity across Baseline, Adverse, and Severely Adverse scenarios. Use for: stress testing, CCAR submissions, regulatory capital planning.';

COMMENT ON COLUMN cfo_banking_demo.ml_models.dynamic_beta_parameters.relationship_category IS 'Relationship Category (STRING)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.dynamic_beta_parameters.beta_min IS 'Deposit beta coefficient (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.dynamic_beta_parameters.beta_max IS 'Deposit beta coefficient (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.dynamic_beta_parameters.k_steepness IS 'K Steepness (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.dynamic_beta_parameters.R0_inflection IS 'R0 Inflection (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.dynamic_beta_parameters.calibration_date IS 'Date field (STRING)';


-- cfo_banking_demo.ml_models.stress_test_results
-- Columns: 10

COMMENT ON TABLE cfo_banking_demo.ml_models.stress_test_results IS 'Phase 3 CCAR Stress Testing - Comprehensive deposit balance projections under regulatory stress scenarios. 9-quarter forward projections aligned with Federal Reserve CCAR requirements. Use for: CCAR/DFAST submissions, capital planning, and regulatory reporting.';

COMMENT ON COLUMN cfo_banking_demo.ml_models.stress_test_results.scenario_id IS 'Scenario Id (STRING)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.stress_test_results.scenario_name IS 'Scenario Name (STRING)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.stress_test_results.rate_shock_bps IS 'Interest rate or rate metric (LONG)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.stress_test_results.stressed_market_rate IS 'Interest rate or rate metric (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.stress_test_results.stressed_avg_beta IS 'Deposit beta coefficient (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.stress_test_results.delta_nii_millions IS 'Delta Nii Millions (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.stress_test_results.delta_eve_billions IS 'Delta Eve Billions (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.stress_test_results.eve_cet1_ratio IS 'Ratio metric (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.stress_test_results.sot_status IS 'Sot Status (STRING)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.stress_test_results.calculation_date IS 'Date field (STRING)';


-- cfo_banking_demo.gold_regulatory.lcr_daily
-- Columns: 12

COMMENT ON TABLE cfo_banking_demo.gold_regulatory.lcr_daily IS 'Regulatory LCR (Liquidity Coverage Ratio) calculations per Basel III / 12 CFR Part 249. Daily HQLA and net cash outflow calculations with regulatory weights. Use for: daily LCR monitoring, regulatory reporting (FR 2052a), and liquidity risk management.';

COMMENT ON COLUMN cfo_banking_demo.gold_regulatory.lcr_daily.calculation_date IS 'Date field (DATE)';
COMMENT ON COLUMN cfo_banking_demo.gold_regulatory.lcr_daily.calculation_timestamp IS 'Calculation Timestamp (TIMESTAMP)';
COMMENT ON COLUMN cfo_banking_demo.gold_regulatory.lcr_daily.total_hqla IS 'Total Hqla (DECIMAL)';
COMMENT ON COLUMN cfo_banking_demo.gold_regulatory.lcr_daily.hqla_level_1 IS 'Hqla Level 1 (DECIMAL)';
COMMENT ON COLUMN cfo_banking_demo.gold_regulatory.lcr_daily.hqla_level_2a IS 'Hqla Level 2A (DECIMAL)';
COMMENT ON COLUMN cfo_banking_demo.gold_regulatory.lcr_daily.hqla_level_2b IS 'Hqla Level 2B (DECIMAL)';
COMMENT ON COLUMN cfo_banking_demo.gold_regulatory.lcr_daily.total_outflows IS 'Total Outflows (DECIMAL)';
COMMENT ON COLUMN cfo_banking_demo.gold_regulatory.lcr_daily.total_inflows_uncapped IS 'Total Inflows Uncapped (DECIMAL)';
COMMENT ON COLUMN cfo_banking_demo.gold_regulatory.lcr_daily.total_inflows_capped IS 'Total Inflows Capped (DECIMAL)';
COMMENT ON COLUMN cfo_banking_demo.gold_regulatory.lcr_daily.net_outflows IS 'Net Outflows (DECIMAL)';
COMMENT ON COLUMN cfo_banking_demo.gold_regulatory.lcr_daily.lcr_ratio IS 'Ratio metric (DECIMAL)';
COMMENT ON COLUMN cfo_banking_demo.gold_regulatory.lcr_daily.lcr_status IS 'Lcr Status (STRING)';


-- cfo_banking_demo.ml_models.ppnr_forecasts
-- Columns: 7

COMMENT ON TABLE cfo_banking_demo.ml_models.ppnr_forecasts IS 'PPNR (Pre-Provision Net Revenue) forecasts by stress scenario. 9-quarter projections of Net Interest Income, Non-Interest Income, Non-Interest Expense, and PPNR. Includes efficiency ratio calculations. Use for: CCAR submissions, earnings forecasting, and fee income analysis.';

COMMENT ON COLUMN cfo_banking_demo.ml_models.ppnr_forecasts.month IS 'Month (TIMESTAMP)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.ppnr_forecasts.net_interest_income IS 'Net Interest Income (LONG)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.ppnr_forecasts.non_interest_income IS 'Non Interest Income (FLOAT)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.ppnr_forecasts.non_interest_expense IS 'Non Interest Expense (FLOAT)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.ppnr_forecasts.ppnr IS 'Ppnr (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.ppnr_forecasts.actual_nii IS 'Actual Nii (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.ppnr_forecasts.actual_nie IS 'Actual Nie (DOUBLE)';


-- cfo_banking_demo.ml_models.non_interest_income_training_data
-- Columns: 27

COMMENT ON TABLE cfo_banking_demo.ml_models.non_interest_income_training_data IS 'Non-interest income training data for PPNR forecasting models. Historical fee income by source (deposit fees, overdraft, wire transfer, etc.) with deposit relationship drivers. Use for: fee income modeling, revenue forecasting, and deposit relationship value analysis.';

COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_income_training_data.month IS 'Month (TIMESTAMP)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_income_training_data.target_fee_income IS 'Target Fee Income (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_income_training_data.active_deposit_accounts IS 'Count metric (LONG)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_income_training_data.checking_accounts IS 'Count metric (LONG)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_income_training_data.total_deposits_billions IS 'Total Deposits Billions (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_income_training_data.total_transactions_millions IS 'Total Transactions Millions (DECIMAL)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_income_training_data.avg_monthly_fee IS 'Avg Monthly Fee (DECIMAL)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_income_training_data.retail_deposit_pct IS 'Percentage metric (DECIMAL)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_income_training_data.commercial_deposit_pct IS 'Percentage metric (DECIMAL)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_income_training_data.active_loans IS 'Active Loans (LONG)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_income_training_data.total_loan_balance_billions IS 'Account balance (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_income_training_data.new_loans_30d IS 'New Loans 30D (LONG)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_income_training_data.mortgage_balance_billions IS 'Account balance (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_income_training_data.digital_transactions_millions IS 'Digital Transactions Millions (DECIMAL)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_income_training_data.branch_transactions_millions IS 'Branch Transactions Millions (DECIMAL)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_income_training_data.avg_10y_rate IS 'Interest rate or rate metric (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_income_training_data.avg_2y_rate IS 'Interest rate or rate metric (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_income_training_data.rate_volatility IS 'Interest rate or rate metric (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_income_training_data.yield_curve_slope IS 'Yield Curve Slope (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_income_training_data.checking_account_pct IS 'Count metric (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_income_training_data.digital_transaction_pct IS 'Percentage metric (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_income_training_data.new_loan_rate IS 'Interest rate or rate metric (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_income_training_data.month_sin IS 'Month Sin (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_income_training_data.month_cos IS 'Month Cos (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_income_training_data.quarter IS 'Quarter (INT)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_income_training_data.prior_month_fee_income IS 'Prior Month Fee Income (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_income_training_data.prior_month_transactions IS 'Prior Month Transactions (LONG)';


-- cfo_banking_demo.ml_models.non_interest_expense_training_data
-- Columns: 21

COMMENT ON TABLE cfo_banking_demo.ml_models.non_interest_expense_training_data IS 'Non-interest expense training data for PPNR forecasting models. Historical expense data by category (compensation, technology, occupancy, etc.) with efficiency metrics. Use for: expense forecasting, efficiency ratio analysis, and cost optimization.';

COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_expense_training_data.month IS 'Month (TIMESTAMP)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_expense_training_data.target_operating_expense IS 'Target Operating Expense (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_expense_training_data.active_accounts IS 'Count metric (LONG)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_expense_training_data.total_assets_billions IS 'Total Assets Billions (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_expense_training_data.total_transactions_millions IS 'Total Transactions Millions (DECIMAL)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_expense_training_data.active_branches IS 'Active Branches (INT)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_expense_training_data.digital_users IS 'Digital Users (INT)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_expense_training_data.loan_count IS 'Count metric (LONG)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_expense_training_data.total_loan_balance_billions IS 'Account balance (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_expense_training_data.delinquent_loans IS 'Delinquent Loans (LONG)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_expense_training_data.new_accounts_30d IS 'Count metric (LONG)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_expense_training_data.new_loans_30d IS 'New Loans 30D (LONG)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_expense_training_data.digital_adoption_rate IS 'Interest rate or rate metric (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_expense_training_data.transactions_per_account IS 'Count metric (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_expense_training_data.delinquency_rate IS 'Interest rate or rate metric (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_expense_training_data.avg_10y_rate IS 'Interest rate or rate metric (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_expense_training_data.month_sin IS 'Month Sin (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_expense_training_data.month_cos IS 'Month Cos (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_expense_training_data.quarter IS 'Quarter (INT)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_expense_training_data.prior_month_expense IS 'Prior Month Expense (DOUBLE)';
COMMENT ON COLUMN cfo_banking_demo.ml_models.non_interest_expense_training_data.prior_month_accounts IS 'Count metric (LONG)';

