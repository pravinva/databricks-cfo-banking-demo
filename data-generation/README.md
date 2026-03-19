# Data Generation

This folder contains SQL-first generators for all backend tables used by deposits, beta, vintage/runoff, stress test, and PPNR endpoints.
To avoid schema-name collisions, everything is created under workstream-prefixed schemas (default prefix: `deposit_ppnr`).

## What gets generated

- `deposit_ppnr_bronze_core_banking.deposit_accounts`
- `deposit_ppnr_bronze_core_banking.deposit_accounts_history`
- `deposit_ppnr_bronze_core_banking.loan_portfolio`
- `deposit_ppnr_silver_finance.deposit_subledger`
- `deposit_ppnr_silver_finance.loan_subledger`
- `deposit_ppnr_silver_finance.gl_entries`
- `deposit_ppnr_silver_finance.gl_entry_lines`
- `deposit_ppnr_silver_treasury.yield_curves`
- `deposit_ppnr_ml_models.deposit_beta_predictions`
- `deposit_ppnr_ml_models.ppnr_forecasts`
- `deposit_ppnr_ml_models.component_decay_metrics`
- `deposit_ppnr_ml_models.cohort_survival_rates`
- `deposit_ppnr_ml_models.deposit_runoff_forecasts`
- `deposit_ppnr_ml_models.dynamic_beta_parameters`
- `deposit_ppnr_ml_models.stress_test_results`
- `deposit_ppnr_gold_finance.ppnr_projection_quarterly`
- `deposit_ppnr_gold_finance.ppnr_projection_quarterly_ml`
- `deposit_ppnr_gold_regulatory.lcr_daily` (Genie compatibility)
- `deposit_ppnr_gold_regulatory.hqla_inventory` (Genie compatibility)
- `deposit_ppnr_ml_models.deposit_beta_training_enhanced` (Genie compatibility view)
- `deposit_ppnr_ml_models.non_interest_income_training_data` (Genie compatibility view)
- `deposit_ppnr_ml_models.non_interest_expense_training_data` (Genie compatibility view)

## On-demand full generation

Run all seed SQL scripts in order:

```bash
python data-generation/run_on_demand_generation.py \
  --warehouse-id <warehouse-id> \
  --profile fins \
  --catalog banking_cfo_treasury \
  --schema-prefix deposit_ppnr
```

Optional:

- `--catalog banking_cfo_treasury` (default and recommended for fins workspace)
- `--schema-prefix deposit_ppnr` (default; prevents naming collisions)
- `--sql-dir data-generation`
- `--dry-run`

## Real-time generation capability

Run a continuous loop that executes one synthetic update tick each interval:

```bash
python data-generation/run_realtime_generation.py \
  --warehouse-id <warehouse-id> \
  --profile fins \
  --catalog banking_cfo_treasury \
  --schema-prefix deposit_ppnr \
  --interval-seconds 60
```

Each tick does:

- small random balance/rate changes on active deposit accounts
- append to `deposit_accounts_history` for trend views
- refresh `deposit_beta_predictions`
- upsert latest `yield_curves` row
- upsert current-month `ppnr_forecasts`

Stop with `Ctrl+C`.

## AlphaVantage refresh in scheduled jobs

The daily job now runs an AlphaVantage refresh task first, then runs full data generation.

Expected secret in workspace:

- scope: `cfo_demo`
- key: `alpha_vantage_api_key`

This refresh writes to:

- `{catalog}.{schema_prefix}_silver_treasury.yield_curves`

## SQL scripts

1. `00_create_schemas.sql`
2. `10_seed_core_banking.sql`
3. `20_seed_finance_ledgers.sql`
4. `30_seed_treasury_and_models.sql`
5. `40_genie_compatibility_assets.sql`
6. `50_realtime_tick.sql` (used by realtime loop)

## Notes

- Scripts are idempotent for demo workflows (`CREATE OR REPLACE` + deterministic seeds).
- The seed scripts are intended for demo/sandbox data regeneration.
- Use `--schema-prefix` to isolate each workstream and avoid confusion with similarly named schemas.
- Full refresh includes a hard QA guard that fails if baseline `non_interest_income / net_interest_income` drifts outside `8%-12%`.
