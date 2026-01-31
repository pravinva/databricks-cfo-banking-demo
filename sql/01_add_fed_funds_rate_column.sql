-- ============================================================================
-- Add Fed Funds Rate Column to Yield Curves Table
-- ============================================================================
-- Purpose: Add missing fed_funds_rate column required by deposit beta notebooks
-- Method: Derive from 3M Treasury rate (quick fix for demo)
-- Production: Replace with actual data from AlphaVantage FRED API
-- ============================================================================

-- Step 1: Add column if not exists
ALTER TABLE cfo_banking_demo.silver_treasury.yield_curves
ADD COLUMN IF NOT EXISTS fed_funds_rate DOUBLE
COMMENT 'Federal Funds Effective Rate (derived from 3M Treasury)';

-- Step 2: Derive from 3M Treasury rate
-- Typical spread: Fed Funds ≈ 3M Treasury - 15 basis points
UPDATE cfo_banking_demo.silver_treasury.yield_curves
SET fed_funds_rate = rate_3m - 0.15
WHERE fed_funds_rate IS NULL;

-- Step 3: Verify results
SELECT
    date,
    fed_funds_rate,
    rate_3m,
    rate_2y,
    rate_10y,
    (rate_10y - rate_2y) as curve_slope,
    CASE
        WHEN fed_funds_rate < 2.0 THEN 'Low'
        WHEN fed_funds_rate < 4.0 THEN 'Medium'
        ELSE 'High'
    END as rate_regime
FROM cfo_banking_demo.silver_treasury.yield_curves
ORDER BY date DESC
LIMIT 10;

-- Step 4: Show statistics
SELECT
    COUNT(*) as total_rows,
    COUNT(fed_funds_rate) as rows_with_fed_funds,
    MIN(date) as earliest_date,
    MAX(date) as latest_date,
    AVG(fed_funds_rate) as avg_fed_funds_rate,
    MIN(fed_funds_rate) as min_fed_funds_rate,
    MAX(fed_funds_rate) as max_fed_funds_rate
FROM cfo_banking_demo.silver_treasury.yield_curves;
