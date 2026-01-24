#!/usr/bin/env python3
"""
Verify dependencies for WS1-06
"""

from databricks.sdk import WorkspaceClient
from datetime import datetime

def log_message(message, level="INFO"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def main():
    log_message("Verifying dependencies for WS1-06...")

    w = WorkspaceClient()

    # Check required schemas
    required_schemas = [
        "cfo_banking_demo.bronze_core_banking",
        "cfo_banking_demo.silver_finance",
        "cfo_banking_demo.silver_treasury"
    ]

    for schema_full_name in required_schemas:
        catalog_name, schema_name = schema_full_name.split('.')
        try:
            schemas = list(w.schemas.list(catalog_name=catalog_name))
            schema_names = [s.name for s in schemas]
            if schema_name in schema_names:
                log_message(f"✓ Schema exists: {schema_full_name}")
            else:
                log_message(f"✗ Schema missing: {schema_full_name}", "ERROR")
                return 1
        except Exception as e:
            log_message(f"✗ Error checking schema {schema_full_name}: {e}", "ERROR")
            return 1

    log_message("✅ All dependencies verified!")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
