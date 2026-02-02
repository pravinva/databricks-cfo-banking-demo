-- ============================================================================
-- DASHBOARD 10: REGULATORY RECONCILIATION & DATA QUALITY
-- Audience: Comptroller, CFO, Internal Audit, Regulatory Compliance
-- ============================================================================
-- Purpose: Validate input data quality and lineage for FFIEC 101, FR 2052a,
--          LCR, and RWA regulatory reports. Provides audit trail and
--          reconciliation controls for regulatory submissions.
-- ============================================================================

-- ============================================================================
-- QUERY 1: Data Quality Summary KPIs (4 Cards)
-- ============================================================================

-- Card 1: Data Completeness Score
SELECT
  'Data Completeness' as metric_name,
  99.7 as score_pct,
  '✓ Passing' as status,
  '#059669' as color  -- Green (>99%)
;

-- Card 2: Reconciliation Breaks
SELECT
  'Reconciliation Breaks' as metric_name,
  2 as break_count,
  '$1.2M total variance' as status,
  CASE
    WHEN 2 = 0 THEN '#059669'        -- No breaks
    WHEN 2 <= 3 THEN '#D97706'       -- Minor breaks (caution)
    ELSE '#DC2626'                    -- Major breaks (fail)
  END as color
;

-- Card 3: Source Systems Status
SELECT
  'Source Systems Online' as metric_name,
  8 as online_count,
  '8 of 8 systems' as status,
  '#059669' as color
;

-- Card 4: Last Validation Run
SELECT
  'Last Validation Run' as metric_name,
  '2026-02-02 06:00:00' as last_run_time,
  '✓ Automated Daily' as status,
  '#059669' as color
;


-- ============================================================================
-- QUERY 2: Data Lineage - Bronze to Gold (Sankey/Flow Diagram Data)
-- ============================================================================

WITH lineage_flow AS (
  -- Bronze → Silver flows
  SELECT 'Core Banking (Bronze)' as source, 'Deposit Accounts (Silver)' as target, 450000 as record_count, 1 as layer_order
  UNION ALL SELECT 'Core Banking (Bronze)', 'Loan Portfolio (Silver)', 280000, 1
  UNION ALL SELECT 'GL System (Bronze)', 'GL Balances (Silver)', 125000, 1
  UNION ALL SELECT 'Securities System (Bronze)', 'Securities Portfolio (Silver)', 18500, 1
  UNION ALL SELECT 'Treasury System (Bronze)', 'Market Data (Silver)', 95000, 1
  UNION ALL SELECT 'Customer MDM (Bronze)', 'Customer Master (Silver)', 320000, 1

  -- Silver → Gold flows
  UNION ALL SELECT 'Deposit Accounts (Silver)', 'LCR Calculation (Gold)', 450000, 2
  UNION ALL SELECT 'Securities Portfolio (Silver)', 'LCR Calculation (Gold)', 18500, 2
  UNION ALL SELECT 'Loan Portfolio (Silver)', 'RWA Calculation (Gold)', 280000, 2
  UNION ALL SELECT 'GL Balances (Silver)', 'FFIEC 101 Report (Gold)', 125000, 2
  UNION ALL SELECT 'Deposit Accounts (Silver)', 'FR 2052a Report (Gold)', 450000, 2
  UNION ALL SELECT 'Loan Portfolio (Silver)', 'FR 2052a Report (Gold)', 280000, 2
  UNION ALL SELECT 'Securities Portfolio (Silver)', 'FR 2052a Report (Gold)', 18500, 2

  -- Gold → Regulatory Reports
  UNION ALL SELECT 'LCR Calculation (Gold)', 'LCR Report', 1, 3
  UNION ALL SELECT 'RWA Calculation (Gold)', 'RWA Report', 1, 3
  UNION ALL SELECT 'FFIEC 101 Report (Gold)', 'FFIEC 101 Filing', 1, 3
  UNION ALL SELECT 'FR 2052a Report (Gold)', 'FR 2052a Filing', 1, 3
)
SELECT
  source,
  target,
  record_count,
  layer_order,
  CASE
    WHEN layer_order = 1 THEN '#94A3B8'  -- Bronze→Silver (gray-blue)
    WHEN layer_order = 2 THEN '#0891B2'  -- Silver→Gold (cyan)
    WHEN layer_order = 3 THEN '#059669'  -- Gold→Report (green)
  END as flow_color
FROM lineage_flow
ORDER BY layer_order, source;


-- ============================================================================
-- QUERY 3: Data Quality Checks by Source System (Table)
-- ============================================================================

WITH quality_checks AS (
  SELECT 'Core Banking' as source_system, 'Deposit Accounts' as table_name,
         450000 as total_records, 449850 as valid_records, 150 as null_values,
         0 as duplicates, 0 as schema_errors, 99.97 as quality_score_pct, 1 as sort_order
  UNION ALL SELECT 'Core Banking', 'Loan Portfolio', 280000, 279950, 50, 0, 0, 99.98, 2
  UNION ALL SELECT 'GL System', 'GL Balances', 125000, 124820, 180, 0, 0, 99.86, 3
  UNION ALL SELECT 'Securities System', 'Securities Portfolio', 18500, 18485, 15, 0, 0, 99.92, 4
  UNION ALL SELECT 'Treasury System', 'Market Data', 95000, 94950, 50, 0, 0, 99.95, 5
  UNION ALL SELECT 'Customer MDM', 'Customer Master', 320000, 319200, 650, 150, 0, 99.75, 6
  UNION ALL SELECT 'Regulatory Calc', 'LCR Daily', 365 as total_records, 365 as valid_records,
         0 as null_values, 0 as duplicates, 0 as schema_errors, 100.00 as quality_score_pct, 7
  UNION ALL SELECT 'Regulatory Calc', 'RWA Daily', 365, 365, 0, 0, 0, 100.00, 8
)
SELECT
  source_system,
  table_name,
  total_records,
  valid_records,
  null_values,
  duplicates,
  schema_errors,
  ROUND(quality_score_pct, 2) as quality_score_pct,
  CASE
    WHEN quality_score_pct >= 99.9 THEN '✓ Excellent'
    WHEN quality_score_pct >= 99.5 THEN '✓ Good'
    WHEN quality_score_pct >= 99.0 THEN '⚠ Fair'
    ELSE '✗ Poor'
  END as quality_status,
  CASE
    WHEN quality_score_pct >= 99.9 THEN '#059669'
    WHEN quality_score_pct >= 99.5 THEN '#0891B2'
    WHEN quality_score_pct >= 99.0 THEN '#D97706'
    ELSE '#DC2626'
  END as status_color
FROM quality_checks
ORDER BY sort_order;


-- ============================================================================
-- QUERY 4: Reconciliation Breaks - Detail View (Table with Drill-Down)
-- ============================================================================

WITH reconciliation_breaks AS (
  SELECT
    'LCR-001' as break_id,
    'LCR Report' as report_name,
    'HQLA Level 1' as component,
    8450.2 as source_amount_millions,
    8451.4 as gold_amount_millions,
    -1.2 as variance_millions,
    ROUND((-1.2 / 8450.2) * 100, 4) as variance_pct,
    'Timing difference - bond settlement' as root_cause,
    'Open' as status,
    '2026-02-02' as identified_date,
    'John Smith' as assigned_to,
    '#D97706' as severity_color,
    1 as sort_order

  UNION ALL SELECT
    'RWA-002', 'RWA Report', 'Commercial Loans',
    15200.5, 15205.8, -5.3,
    ROUND((-5.3 / 15200.5) * 100, 4),
    'Credit rating update lag (1 day)' as root_cause,
    'Investigating' as status,
    '2026-02-01' as identified_date,
    'Sarah Johnson' as assigned_to,
    '#DC2626' as severity_color,
    2 as sort_order
)
SELECT
  break_id,
  report_name,
  component,
  ROUND(source_amount_millions, 2) as source_amount_millions,
  ROUND(gold_amount_millions, 2) as gold_amount_millions,
  ROUND(variance_millions, 2) as variance_millions,
  ROUND(variance_pct, 4) as variance_pct,
  root_cause,
  status,
  identified_date,
  assigned_to,
  CASE
    WHEN ABS(variance_pct) < 0.01 THEN '✓ Immaterial'
    WHEN ABS(variance_pct) < 0.05 THEN '⚠ Review'
    ELSE '✗ Material'
  END as materiality,
  severity_color
FROM reconciliation_breaks
ORDER BY ABS(variance_millions) DESC;


-- ============================================================================
-- QUERY 5: Regulatory Report Status Dashboard (Table)
-- ============================================================================

WITH report_status AS (
  SELECT
    'FFIEC 101' as report_name,
    'Completed' as status,
    '2026-02-01 08:00:00' as last_run_time,
    'Q4 2025' as reporting_period,
    '2026-02-15' as submission_deadline,
    14 as days_until_deadline,
    99.8 as data_quality_pct,
    0 as reconciliation_breaks,
    'Jane Doe' as prepared_by,
    'Mike Wilson' as reviewed_by,
    '#059669' as status_color,
    1 as sort_order

  UNION ALL SELECT
    'FR 2052a', 'Completed', '2026-02-01 09:30:00', 'January 2026', '2026-02-10', 8,
    99.7, 2, 'Jane Doe', 'Mike Wilson', '#D97706', 2

  UNION ALL SELECT
    'LCR Report', 'Completed', '2026-02-02 06:00:00', '2026-02-01', '2026-02-03', 1,
    100.0, 0, 'Auto-Generated', 'Sarah Johnson', '#059669', 3

  UNION ALL SELECT
    'RWA Report', 'In Progress', '2026-02-02 06:00:00', '2026-02-01', '2026-02-03', 1,
    99.9, 1, 'Auto-Generated', 'Pending', '#0891B2', 4

  UNION ALL SELECT
    'Call Report', 'Pending', NULL, 'Q4 2025', '2026-02-28', 26,
    98.5, 0, 'Not Started', NULL, '#94A3B8', 5
)
SELECT
  report_name,
  status,
  last_run_time,
  reporting_period,
  submission_deadline,
  days_until_deadline,
  ROUND(data_quality_pct, 2) as data_quality_pct,
  reconciliation_breaks,
  prepared_by,
  reviewed_by,
  CASE
    WHEN status = 'Completed' AND reconciliation_breaks = 0 THEN '✓ Ready for Submission'
    WHEN status = 'Completed' AND reconciliation_breaks > 0 THEN '⚠ Breaks Pending'
    WHEN status = 'In Progress' THEN '⏳ In Progress'
    WHEN status = 'Pending' THEN '○ Not Started'
    ELSE status
  END as submission_status,
  status_color
FROM report_status
ORDER BY sort_order;


-- ============================================================================
-- QUERY 6: Data Freshness by Source System (Horizontal Bar Chart)
-- ============================================================================

WITH data_freshness AS (
  SELECT
    'Core Banking' as source_system,
    'Deposit Accounts' as table_name,
    CURRENT_TIMESTAMP() as last_updated,
    0.25 as hours_since_update,
    'Real-Time CDC' as update_frequency,
    '#059669' as freshness_color,
    1 as sort_order

  UNION ALL SELECT 'Core Banking', 'Loan Portfolio',
    CURRENT_TIMESTAMP() - INTERVAL 0.5 HOURS, 0.5, 'Real-Time CDC', '#059669', 2

  UNION ALL SELECT 'GL System', 'GL Balances',
    CURRENT_TIMESTAMP() - INTERVAL 2 HOURS, 2.0, 'Hourly Batch', '#0891B2', 3

  UNION ALL SELECT 'Securities System', 'Securities Portfolio',
    CURRENT_TIMESTAMP() - INTERVAL 1 HOURS, 1.0, 'Hourly Batch', '#0891B2', 4

  UNION ALL SELECT 'Treasury System', 'Market Data',
    CURRENT_TIMESTAMP() - INTERVAL 0.1 HOURS, 0.1, 'Real-Time API', '#059669', 5

  UNION ALL SELECT 'Customer MDM', 'Customer Master',
    CURRENT_TIMESTAMP() - INTERVAL 4 HOURS, 4.0, 'Daily Batch', '#D97706', 6

  UNION ALL SELECT 'Regulatory Calc', 'LCR Daily',
    CURRENT_TIMESTAMP() - INTERVAL 6 HOURS, 6.0, 'Daily 6am', '#059669', 7

  UNION ALL SELECT 'Regulatory Calc', 'RWA Daily',
    CURRENT_TIMESTAMP() - INTERVAL 6 HOURS, 6.0, 'Daily 6am', '#059669', 8
)
SELECT
  source_system,
  table_name,
  last_updated,
  ROUND(hours_since_update, 2) as hours_since_update,
  update_frequency,
  CASE
    WHEN hours_since_update < 1 THEN '✓ Fresh'
    WHEN hours_since_update < 6 THEN '✓ Current'
    WHEN hours_since_update < 24 THEN '⚠ Aging'
    ELSE '✗ Stale'
  END as freshness_status,
  freshness_color
FROM data_freshness
ORDER BY sort_order;


-- ============================================================================
-- QUERY 7: Schema Validation Results (Table)
-- ============================================================================

WITH schema_validation AS (
  SELECT
    'cfo_banking_demo.bronze_core_banking.deposit_accounts' as table_name,
    18 as expected_columns,
    18 as actual_columns,
    0 as missing_columns,
    0 as extra_columns,
    0 as type_mismatches,
    'Pass' as validation_status,
    CURRENT_TIMESTAMP() - INTERVAL 1 HOURS as last_validated,
    '#059669' as status_color,
    1 as sort_order

  UNION ALL SELECT
    'cfo_banking_demo.silver_finance.deposit_portfolio',
    22, 22, 0, 0, 0, 'Pass',
    CURRENT_TIMESTAMP() - INTERVAL 1 HOURS, '#059669', 2

  UNION ALL SELECT
    'cfo_banking_demo.gold_regulatory.lcr_daily',
    15, 15, 0, 0, 0, 'Pass',
    CURRENT_TIMESTAMP() - INTERVAL 6 HOURS, '#059669', 3

  UNION ALL SELECT
    'cfo_banking_demo.gold_regulatory.rwa_daily',
    12, 12, 0, 0, 0, 'Pass',
    CURRENT_TIMESTAMP() - INTERVAL 6 HOURS, '#059669', 4

  UNION ALL SELECT
    'cfo_banking_demo.gold_regulatory.ffiec_101',
    45, 45, 0, 0, 0, 'Pass',
    CURRENT_TIMESTAMP() - INTERVAL 24 HOURS, '#059669', 5
)
SELECT
  table_name,
  expected_columns,
  actual_columns,
  missing_columns,
  extra_columns,
  type_mismatches,
  validation_status,
  last_validated,
  CASE
    WHEN validation_status = 'Pass' THEN '✓ Schema Valid'
    ELSE '✗ Schema Issues'
  END as status_label,
  status_color
FROM schema_validation
ORDER BY sort_order;


-- ============================================================================
-- QUERY 8: LCR Calculation Reconciliation (Detailed Breakdown)
-- ============================================================================

WITH lcr_reconciliation AS (
  SELECT
    'Treasury Securities (Level 1)' as hqla_component,
    8450.2 as source_system_amount,
    8451.4 as gold_table_amount,
    -1.2 as variance,
    'cfo_banking_demo.bronze_market.treasury_securities' as source_table,
    'cfo_banking_demo.gold_regulatory.lcr_daily' as gold_table,
    'bond_settlement_pending' as variance_reason,
    'Immaterial' as materiality,
    '#D97706' as status_color,
    1 as sort_order

  UNION ALL SELECT
    'Agency MBS (Level 1)', 2100.5, 2100.5, 0.0,
    'cfo_banking_demo.bronze_market.agency_securities',
    'cfo_banking_demo.gold_regulatory.lcr_daily',
    NULL, 'N/A', '#059669', 2

  UNION ALL SELECT
    'Corporate Bonds (Level 2A)', 1200.8, 1200.8, 0.0,
    'cfo_banking_demo.bronze_market.corporate_bonds',
    'cfo_banking_demo.gold_regulatory.lcr_daily',
    NULL, 'N/A', '#059669', 3

  UNION ALL SELECT
    'Cash & Reserves', 500.0, 500.0, 0.0,
    'cfo_banking_demo.bronze_core_banking.cash_balances',
    'cfo_banking_demo.gold_regulatory.lcr_daily',
    NULL, 'N/A', '#059669', 4

  UNION ALL SELECT
    'Retail Deposits (Stable)', 18500.0, 18500.0, 0.0,
    'cfo_banking_demo.bronze_core_banking.deposit_accounts',
    'cfo_banking_demo.gold_regulatory.lcr_daily',
    NULL, 'N/A', '#059669', 5

  UNION ALL SELECT
    'Wholesale Deposits', 8200.0, 8200.0, 0.0,
    'cfo_banking_demo.bronze_core_banking.deposit_accounts',
    'cfo_banking_demo.gold_regulatory.lcr_daily',
    NULL, 'N/A', '#059669', 6
)
SELECT
  hqla_component,
  ROUND(source_system_amount, 2) as source_amount_millions,
  ROUND(gold_table_amount, 2) as gold_amount_millions,
  ROUND(variance, 2) as variance_millions,
  CASE
    WHEN variance = 0 THEN 0.00
    ELSE ROUND((variance / source_system_amount) * 100, 4)
  END as variance_pct,
  source_table,
  gold_table,
  COALESCE(variance_reason, 'N/A') as variance_reason,
  materiality,
  CASE
    WHEN variance = 0 THEN '✓ Reconciled'
    WHEN ABS(variance) < 5 THEN '⚠ Minor Variance'
    ELSE '✗ Material Variance'
  END as reconciliation_status,
  status_color
FROM lcr_reconciliation
ORDER BY sort_order;


-- ============================================================================
-- QUERY 9: RWA Calculation Reconciliation (Detailed Breakdown)
-- ============================================================================

WITH rwa_reconciliation AS (
  SELECT
    'Commercial Real Estate' as asset_class,
    12500.5 as exposure_at_default_millions,
    100 as risk_weight_pct,
    12500.5 as rwa_calculated,
    12500.5 as rwa_gold_table,
    0.0 as variance,
    'cfo_banking_demo.bronze_core_banking.loan_portfolio' as source_table,
    'cfo_banking_demo.gold_regulatory.rwa_daily' as gold_table,
    NULL as variance_reason,
    '#059669' as status_color,
    1 as sort_order

  UNION ALL SELECT
    'Residential Mortgages', 25000.0, 50, 12500.0, 12500.0, 0.0,
    'cfo_banking_demo.bronze_core_banking.loan_portfolio',
    'cfo_banking_demo.gold_regulatory.rwa_daily',
    NULL, '#059669', 2

  UNION ALL SELECT
    'Corporate Loans (IG)', 8500.2, 100, 8500.2, 8505.5, -5.3,
    'cfo_banking_demo.bronze_core_banking.loan_portfolio',
    'cfo_banking_demo.gold_regulatory.rwa_daily',
    'credit_rating_update_lag', '#DC2626', 3

  UNION ALL SELECT
    'Small Business Loans', 3200.8, 100, 3200.8, 3200.8, 0.0,
    'cfo_banking_demo.bronze_core_banking.loan_portfolio',
    'cfo_banking_demo.gold_regulatory.rwa_daily',
    NULL, '#059669', 4

  UNION ALL SELECT
    'Consumer Credit Cards', 1800.0, 75, 1350.0, 1350.0, 0.0,
    'cfo_banking_demo.bronze_core_banking.loan_portfolio',
    'cfo_banking_demo.gold_regulatory.rwa_daily',
    NULL, '#059669', 5
)
SELECT
  asset_class,
  ROUND(exposure_at_default_millions, 2) as ead_millions,
  risk_weight_pct,
  ROUND(rwa_calculated, 2) as rwa_calculated_millions,
  ROUND(rwa_gold_table, 2) as rwa_gold_millions,
  ROUND(variance, 2) as variance_millions,
  CASE
    WHEN variance = 0 THEN 0.00
    ELSE ROUND((variance / rwa_calculated) * 100, 4)
  END as variance_pct,
  source_table,
  gold_table,
  COALESCE(variance_reason, 'N/A') as variance_reason,
  CASE
    WHEN variance = 0 THEN '✓ Reconciled'
    WHEN ABS(variance) < 10 THEN '⚠ Minor Variance'
    ELSE '✗ Material Variance'
  END as reconciliation_status,
  status_color
FROM rwa_reconciliation
ORDER BY sort_order;


-- ============================================================================
-- QUERY 10: Audit Trail - Recent Data Changes (Table)
-- ============================================================================

WITH audit_trail AS (
  SELECT
    'DEP-450123' as record_id,
    'cfo_banking_demo.bronze_core_banking.deposit_accounts' as table_name,
    'UPDATE' as operation,
    'current_balance' as field_changed,
    '125000.00' as old_value,
    '127500.00' as new_value,
    'Nightly CDC Sync' as changed_by,
    CURRENT_TIMESTAMP() - INTERVAL 2 HOURS as change_timestamp,
    'Automated' as change_source,
    1 as sort_order

  UNION ALL SELECT
    'LCR-2026-02-01', 'cfo_banking_demo.gold_regulatory.lcr_daily',
    'INSERT', 'lcr_ratio', NULL, '118.5',
    'LCR Calculation Job', CURRENT_TIMESTAMP() - INTERVAL 6 HOURS,
    'Automated', 2

  UNION ALL SELECT
    'RWA-2026-02-01', 'cfo_banking_demo.gold_regulatory.rwa_daily',
    'INSERT', 'total_rwa', NULL, '42500.5',
    'RWA Calculation Job', CURRENT_TIMESTAMP() - INTERVAL 6 HOURS,
    'Automated', 3

  UNION ALL SELECT
    'LOAN-280055', 'cfo_banking_demo.bronze_core_banking.loan_portfolio',
    'UPDATE', 'credit_rating', 'BBB', 'BBB+',
    'jane.doe@bank.com', CURRENT_TIMESTAMP() - INTERVAL 1 DAYS,
    'Manual', 4

  UNION ALL SELECT
    'FFIEC-Q4-2025', 'cfo_banking_demo.gold_regulatory.ffiec_101',
    'INSERT', 'report_data', NULL, '[JSON DATA]',
    'FFIEC Report Generator', CURRENT_TIMESTAMP() - INTERVAL 1 DAYS,
    'Automated', 5
)
SELECT
  record_id,
  table_name,
  operation,
  field_changed,
  COALESCE(old_value, 'N/A') as old_value,
  new_value,
  changed_by,
  change_timestamp,
  change_source,
  CASE
    WHEN operation = 'INSERT' THEN '#059669'
    WHEN operation = 'UPDATE' THEN '#0891B2'
    WHEN operation = 'DELETE' THEN '#DC2626'
  END as operation_color
FROM audit_trail
ORDER BY change_timestamp DESC
LIMIT 50;


-- ============================================================================
-- VISUALIZATION INSTRUCTIONS
-- ============================================================================

/*
Create "Regulatory Reconciliation & Data Quality Dashboard" with this layout:

TOP ROW (4 KPI Cards):
-----------------------
- Query 1 (4 separate cards): Data Completeness, Reconciliation Breaks,
  Source Systems Status, Last Validation Run

ROW 2 - DATA LINEAGE:
---------------------
LEFT (70%):
- Sankey/Flow diagram from Query 2 (Data Lineage)
- Title: "Regulatory Data Lineage (Bronze → Silver → Gold)"
- Show flow from 6 source systems through silver to 4 regulatory reports
- Color-coded by layer (bronze=gray, silver=cyan, gold=green)

RIGHT (30%):
- Table from Query 5 (Regulatory Report Status)
- Title: "Regulatory Report Status"
- Show status, deadlines, quality scores
- Sort by submission deadline

ROW 3 - DATA QUALITY:
--------------------
LEFT (60%):
- Table from Query 3 (Data Quality Checks)
- Title: "Data Quality by Source System"
- Show quality scores, null counts, duplicates
- Color-coded by quality score

RIGHT (40%):
- Horizontal bar chart from Query 6 (Data Freshness)
- Title: "Data Freshness by Source"
- X-axis: Hours since last update
- Color-coded by freshness (green < 1hr, cyan < 6hr, orange < 24hr)

ROW 4 - RECONCILIATION BREAKS:
-----------------------------
FULL WIDTH:
- Table from Query 4 (Reconciliation Breaks Detail)
- Title: "Active Reconciliation Breaks"
- Show break ID, report, component, variance, root cause, assigned to
- Highlight material variances (>0.05%) in red
- Enable drill-down to source records

ROW 5 - LCR & RWA RECONCILIATION:
---------------------------------
LEFT (50%):
- Table from Query 8 (LCR Reconciliation)
- Title: "LCR Component Reconciliation"
- Show HQLA components, source vs gold amounts, variances

RIGHT (50%):
- Table from Query 9 (RWA Reconciliation)
- Title: "RWA Asset Class Reconciliation"
- Show asset classes, EAD, risk weights, RWA calculated vs gold

ROW 6 - SCHEMA & AUDIT:
-----------------------
LEFT (60%):
- Table from Query 7 (Schema Validation)
- Title: "Schema Validation Results"
- Show expected vs actual columns, type mismatches

RIGHT (40%):
- Table from Query 10 (Audit Trail)
- Title: "Recent Data Changes (Last 24hrs)"
- Show record ID, table, operation, changed by, timestamp
- Color-coded by operation type

FILTERS (Top of Dashboard):
---------------------------
- Date Range Selector (default: Last 7 days)
- Report Type (FFIEC 101, FR 2052a, LCR, RWA, All)
- Source System (dropdown, multi-select)
- Status Filter (Pass, Warning, Fail, All)

DASHBOARD COLORS:
----------------
- Background: #F8FAFC (light gray)
- Cards: White with colored left border
- Success: #059669 (green)
- Warning: #D97706 (orange)
- Error: #DC2626 (red)
- Info: #0891B2 (cyan)
- Neutral: #94A3B8 (gray)

INTERACTIVITY:
--------------
- Click on reconciliation break → drill to source records
- Click on data quality issue → view detailed validation results
- Click on audit trail entry → show full change details
- Export to Excel for compliance documentation
- Schedule daily email summary to Comptroller

REFRESH SCHEDULE:
-----------------
- Automated refresh: Daily at 7:00 AM (after regulatory calcs complete)
- On-demand refresh: Available for Comptroller
- Historical snapshots: Retained for 7 years (compliance requirement)
*/
