#!/usr/bin/env python3
"""
WS1-01: Unity Catalog Structure Setup
Creates the foundational Unity Catalog structure for the CFO Banking Demo

Catalog: cfo_banking_demo
Schemas: 12 (bronze, silver, gold layers)
Volumes: 3 (raw data landing zones, model artifacts)
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import VolumeType
import sys
from datetime import datetime

def log_message(message, level="INFO"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def main():
    """Main execution function"""

    log_message("=" * 80)
    log_message("WS1-01: Unity Catalog Structure Setup")
    log_message("=" * 80)

    # Initialize Databricks client
    try:
        w = WorkspaceClient()
        user = w.current_user.me()
        log_message(f"Connected as: {user.user_name}")
        log_message(f"Workspace: {w.config.host}")
    except Exception as e:
        log_message(f"Failed to connect to Databricks: {e}", "ERROR")
        sys.exit(1)

    # Track creation statistics
    stats = {
        "catalog_created": 0,
        "catalog_exists": 0,
        "schemas_created": 0,
        "schemas_exist": 0,
        "volumes_created": 0,
        "volumes_exist": 0,
        "errors": 0
    }

    # =========================================================================
    # STEP 1: Create Catalog
    # =========================================================================
    log_message("\nSTEP 1: Creating Catalog")
    log_message("-" * 80)

    catalog_name = "cfo_banking_demo"
    catalog_comment = "CFO Banking Demo - Data Foundation for US Regional Bank"

    try:
        catalog = w.catalogs.create(
            name=catalog_name,
            comment=catalog_comment
        )
        log_message(f"✓ Created catalog: {catalog.name}")
        stats["catalog_created"] += 1
    except Exception as e:
        if "already exists" in str(e).lower():
            log_message(f"✓ Catalog already exists: {catalog_name}")
            stats["catalog_exists"] += 1
        else:
            log_message(f"✗ Error creating catalog: {e}", "ERROR")
            stats["errors"] += 1
            sys.exit(1)

    # =========================================================================
    # STEP 2: Add Tags to Catalog
    # =========================================================================
    log_message("\nSTEP 2: Adding Tags to Catalog")
    log_message("-" * 80)

    try:
        # Note: Databricks SDK tag support may vary by workspace configuration
        # This is a placeholder - actual tag implementation depends on workspace setup
        log_message("✓ Tags configuration: domain=financial_services, use_case=cfo_office, owner=field_engineering")
        log_message("  (Tags would be set via workspace UI or separate API calls)")
    except Exception as e:
        log_message(f"! Warning: Could not set tags: {e}", "WARN")

    # =========================================================================
    # STEP 3: Create Schemas
    # =========================================================================
    log_message("\nSTEP 3: Creating Schemas (12 total)")
    log_message("-" * 80)

    schemas = [
        # Bronze Layer - Raw data landing zones
        ("bronze_market_data", "External market data feeds (Alpha Vantage, FRED, etc)"),
        ("bronze_core_banking", "Simulated core banking systems (loans, deposits, securities)"),
        ("bronze_payments", "Payment system data (Fedwire, ACH, card settlements)"),
        ("bronze_external", "Other external data sources"),

        # Silver Layer - Cleansed and conformed data
        ("silver_treasury", "Securities portfolio, ALM positions, funding"),
        ("silver_finance", "GL, subledger, FTP, product profitability"),
        ("silver_risk", "Credit exposures, RWA calculations, market risk"),
        ("silver_regulatory", "Regulatory calculations and metrics"),

        # Gold Layer - Business-ready aggregates
        ("gold_regulatory", "Fit-for-purpose regulatory reports (Y9C, 2052a, FFIEC 101)"),
        ("gold_analytics", "ML features, model training datasets, aggregates"),
        ("gold_dashboards", "Pre-computed tables for BI dashboards"),

        # Models - ML model registry
        ("models", "Model registry and artifacts")
    ]

    for schema_name, comment in schemas:
        try:
            schema = w.schemas.create(
                catalog_name=catalog_name,
                name=schema_name,
                comment=comment
            )
            log_message(f"✓ Created schema: {schema.full_name}")
            stats["schemas_created"] += 1
        except Exception as e:
            if "already exists" in str(e).lower():
                log_message(f"✓ Schema already exists: {catalog_name}.{schema_name}")
                stats["schemas_exist"] += 1
            else:
                log_message(f"✗ Error creating schema {schema_name}: {e}", "ERROR")
                stats["errors"] += 1

    # =========================================================================
    # STEP 4: Create Volumes
    # =========================================================================
    log_message("\nSTEP 4: Creating Volumes (3 total)")
    log_message("-" * 80)

    volumes = [
        ("bronze_market_data", "raw", "Raw market data landing zone (CSV, JSON, Parquet)"),
        ("bronze_core_banking", "raw", "Raw core banking data extracts"),
        ("models", "artifacts", "ML model artifacts and checkpoints")
    ]

    for schema_name, volume_name, comment in volumes:
        try:
            volume = w.volumes.create(
                catalog_name=catalog_name,
                schema_name=schema_name,
                name=volume_name,
                volume_type=VolumeType.MANAGED,
                comment=comment
            )
            log_message(f"✓ Created volume: {volume.full_name}")
            stats["volumes_created"] += 1
        except Exception as e:
            if "already exists" in str(e).lower():
                log_message(f"✓ Volume already exists: {catalog_name}.{schema_name}.{volume_name}")
                stats["volumes_exist"] += 1
            else:
                log_message(f"✗ Error creating volume {schema_name}.{volume_name}: {e}", "ERROR")
                stats["errors"] += 1

    # =========================================================================
    # STEP 5: Validation
    # =========================================================================
    log_message("\nSTEP 5: Running Validations")
    log_message("-" * 80)

    validation_passed = True

    # Validate schemas
    try:
        schema_list = list(w.schemas.list(catalog_name=catalog_name))
        schema_names = [s.name for s in schema_list]

        # Filter out system schemas
        system_schemas = ["default", "information_schema"]
        user_schemas = [s for s in schema_names if s not in system_schemas]

        log_message(f"\n✓ Schemas found: {len(schema_names)} total ({len(user_schemas)} user-created)")
        for s in sorted(schema_names):
            marker = "[system]" if s in system_schemas else ""
            log_message(f"  - {s} {marker}")

        if len(user_schemas) != 12:
            log_message(f"✗ Expected 12 user schemas, found {len(user_schemas)}", "ERROR")
            validation_passed = False
        else:
            log_message("✓ Schema count validation passed (12/12)")
    except Exception as e:
        log_message(f"✗ Error validating schemas: {e}", "ERROR")
        validation_passed = False

    # Validate volumes
    try:
        volume_count = 0
        log_message(f"\n✓ Volumes found:")
        for schema_name in ["bronze_market_data", "bronze_core_banking", "models"]:
            try:
                volumes_list = list(w.volumes.list(
                    catalog_name=catalog_name,
                    schema_name=schema_name
                ))
                for v in volumes_list:
                    log_message(f"  - {v.full_name}")
                    volume_count += 1
            except Exception as e:
                log_message(f"  ! Could not list volumes in {schema_name}: {e}", "WARN")

        if volume_count < 3:
            log_message(f"✗ Expected at least 3 volumes, found {volume_count}", "ERROR")
            validation_passed = False
        else:
            log_message(f"✓ Volume validation passed ({volume_count}/3)")
    except Exception as e:
        log_message(f"✗ Error validating volumes: {e}", "ERROR")
        validation_passed = False

    # =========================================================================
    # STEP 6: Summary Report
    # =========================================================================
    log_message("\n" + "=" * 80)
    log_message("EXECUTION SUMMARY")
    log_message("=" * 80)

    log_message(f"\nCatalog:")
    log_message(f"  Created: {stats['catalog_created']}")
    log_message(f"  Already existed: {stats['catalog_exists']}")

    log_message(f"\nSchemas:")
    log_message(f"  Created: {stats['schemas_created']}")
    log_message(f"  Already existed: {stats['schemas_exist']}")
    log_message(f"  Total: {stats['schemas_created'] + stats['schemas_exist']}")

    log_message(f"\nVolumes:")
    log_message(f"  Created: {stats['volumes_created']}")
    log_message(f"  Already existed: {stats['volumes_exist']}")
    log_message(f"  Total: {stats['volumes_created'] + stats['volumes_exist']}")

    log_message(f"\nErrors: {stats['errors']}")

    if validation_passed and stats['errors'] == 0:
        log_message("\n✅ ALL VALIDATIONS PASSED!")
        log_message("✅ Unity Catalog structure successfully created")
        log_message("✅ Ready for WS1-02")
        return 0
    else:
        log_message("\n⚠️  VALIDATION WARNINGS OR ERRORS DETECTED", "WARN")
        log_message("Please review the output above for details")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        log_message("\n\nExecution interrupted by user", "WARN")
        sys.exit(130)
    except Exception as e:
        log_message(f"\n\nUnexpected error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
