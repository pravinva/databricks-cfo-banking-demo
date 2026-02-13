-- Query: Cumulative (through-cycle) beta (monthly time series)
-- Definition: cumulative_beta = (dep_rate - dep_rate_t0) / (mkt_rate - mkt_rate_t0)
-- Implementation: uses balance-weighted deposit rate from deposit_accounts_historical and market driver from yield_curves (rate_2y).
-- Baseline month t0 is anchored to the earliest month in the lookback window (approx "cycle start" for the demo data).

WITH bounds AS (
  SELECT date_trunc('month', MAX(effective_date)) AS max_month
  FROM cfo_banking_demo.bronze_core_banking.deposit_accounts_historical
),
dep_monthly AS (
  SELECT
    date_trunc('month', effective_date) AS month,
    -- Balance-weighted portfolio deposit rate
    SUM(current_balance * stated_rate) / NULLIF(SUM(current_balance), 0) AS dep_rate_wavg
  FROM cfo_banking_demo.bronze_core_banking.deposit_accounts_historical
  WHERE effective_date >= add_months((SELECT max_month FROM bounds), -24)
  GROUP BY date_trunc('month', effective_date)
),
mkt_monthly AS (
  SELECT
    date_trunc('month', date) AS month,
    AVG(rate_2y) AS mkt_rate
  FROM cfo_banking_demo.silver_treasury.yield_curves
  WHERE date >= add_months((SELECT max_month FROM bounds), -24)
  GROUP BY date_trunc('month', date)
),
series AS (
  SELECT
    d.month,
    d.dep_rate_wavg,
    m.mkt_rate
  FROM dep_monthly d
  JOIN mkt_monthly m USING (month)
),
baseline AS (
  SELECT
    MIN(month) AS baseline_month
  FROM series
),
base_vals AS (
  SELECT
    s.dep_rate_wavg AS dep_rate_t0,
    s.mkt_rate AS mkt_rate_t0
  FROM series s
  JOIN baseline b
    ON s.month = b.baseline_month
)
SELECT
  s.month,
  b.baseline_month,
  s.dep_rate_wavg,
  s.mkt_rate,
  ROUND((s.dep_rate_wavg - v.dep_rate_t0) * 100, 2) AS dep_rate_delta_pct,
  ROUND((s.mkt_rate - v.mkt_rate_t0) * 100, 2) AS mkt_rate_delta_pct,
  ROUND(
    (s.dep_rate_wavg - v.dep_rate_t0) / NULLIF((s.mkt_rate - v.mkt_rate_t0), 0),
    3
  ) AS cumulative_beta
FROM series s
CROSS JOIN baseline b
CROSS JOIN base_vals v
ORDER BY s.month;

