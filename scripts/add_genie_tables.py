#!/usr/bin/env python3
"""
Add Tables to Genie Space: Treasury Modeling - Deposits & Fee Income

This script adds all 12 required tables to the Genie Space.

Tables to add:
1. cfo_banking_demo.ml_models.deposit_beta_training_enhanced
2. cfo_banking_demo.bronze_core_banking.deposit_accounts
3. cfo_banking_demo.ml_models.component_decay_metrics
4. cfo_banking_demo.ml_models.cohort_survival_rates
5. cfo_banking_demo.ml_models.deposit_runoff_forecasts
6. cfo_banking_demo.ml_models.dynamic_beta_parameters
7. cfo_banking_demo.ml_models.stress_test_results
8. cfo_banking_demo.gold_regulatory.lcr_daily
9. cfo_banking_demo.ml_models.ppnr_forecasts
10. cfo_banking_demo.ml_models.non_interest_income_training_data
11. cfo_banking_demo.ml_models.non_interest_expense_training_data
"""

import json
import subprocess

SPACE_ID = "01f101adda151c09835a99254d4c308c"
SPACE_NAME = "Treasury Modeling - Deposits & Fee Income"


def get_current_space_config():
    """Fetch current Genie space configuration"""
    cmd = [
        "databricks", "api", "get",
        f"/api/2.0/genie/spaces/{SPACE_ID}",
        "--output", "json"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    space_data = json.loads(result.stdout)

    # Parse serialized_space JSON string
    serialized_space_str = space_data.get("serialized_space", "{}")
    if serialized_space_str:
        serialized_space = json.loads(serialized_space_str)
    else:
        serialized_space = {"version": 2, "data_sources": {}, "config": {}}

    return serialized_space


def create_tables_config():
    """
    Create tables configuration for Genie Space

    Returns list of table configurations with identifiers
    """
    tables = [
        {"identifier": "cfo_banking_demo.ml_models.deposit_beta_training_enhanced"},
        {"identifier": "cfo_banking_demo.bronze_core_banking.deposit_accounts"},
        {"identifier": "cfo_banking_demo.ml_models.component_decay_metrics"},
        {"identifier": "cfo_banking_demo.ml_models.cohort_survival_rates"},
        {"identifier": "cfo_banking_demo.ml_models.deposit_runoff_forecasts"},
        {"identifier": "cfo_banking_demo.ml_models.dynamic_beta_parameters"},
        {"identifier": "cfo_banking_demo.ml_models.stress_test_results"},
        {"identifier": "cfo_banking_demo.gold_regulatory.lcr_daily"},
        {"identifier": "cfo_banking_demo.ml_models.ppnr_forecasts"},
        {"identifier": "cfo_banking_demo.ml_models.non_interest_income_training_data"},
        {"identifier": "cfo_banking_demo.ml_models.non_interest_expense_training_data"},
    ]

    # Sort by identifier (API requirement)
    tables.sort(key=lambda x: x["identifier"])

    return tables


def add_tables_to_space():
    """Main execution: fetch config, add tables, update space"""

    print("=" * 70)
    print("Add Tables to Genie Space")
    print("=" * 70)
    print(f"\nSpace: {SPACE_NAME}")
    print(f"Space ID: {SPACE_ID}")

    # Fetch current configuration
    print("\n📥 Fetching current Genie space configuration...")
    current_config = get_current_space_config()

    current_tables = current_config.get("data_sources", {}).get("tables", [])
    print(f"   ✅ Current tables: {len(current_tables)}")

    # Generate tables config
    print("\n📊 Generating tables configuration...")
    tables = create_tables_config()
    print(f"   ✅ Tables to add: {len(tables)}")

    # Show table list
    print("\n   Tables:")
    for i, tbl in enumerate(tables, 1):
        print(f"   {i:2d}. {tbl['identifier']}")

    # Ensure version is set
    if "version" not in current_config or current_config["version"] is None:
        current_config["version"] = 2

    # Add tables to config
    if "data_sources" not in current_config:
        current_config["data_sources"] = {}
    current_config["data_sources"]["tables"] = tables

    # Save updated config
    output_file = "/tmp/genie_space_with_tables.json"
    with open(output_file, "w") as f:
        json.dump(current_config, f, indent=2)
    print(f"\n   ✅ Saved updated config to {output_file}")

    # Prepare API payload
    payload = {
        "serialized_space": json.dumps(current_config)
    }

    payload_file = "/tmp/genie_tables_payload.json"
    with open(payload_file, "w") as f:
        json.dump(payload, f, indent=2)

    # Execute PATCH request
    print("\n🚀 Updating Genie Space via API...")
    try:
        cmd = [
            "databricks", "api", "patch",
            f"/api/2.0/genie/spaces/{SPACE_ID}",
            "--json", f"@{payload_file}"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        print("\n✅ SUCCESS - Tables added to Genie Space!")
        print("\n" + "=" * 70)
        print("TABLES ADDED (12 total)")
        print("=" * 70)

        print("\n📊 Deposit Beta Modeling (2 tables):")
        print("   • cfo_banking_demo.ml_models.deposit_beta_training_enhanced")
        print("   • cfo_banking_demo.bronze_core_banking.deposit_accounts")

        print("\n📊 Vintage Analysis (3 tables):")
        print("   • cfo_banking_demo.ml_models.component_decay_metrics")
        print("   • cfo_banking_demo.ml_models.cohort_survival_rates")
        print("   • cfo_banking_demo.ml_models.deposit_runoff_forecasts")

        print("\n📊 Stress Testing (3 tables):")
        print("   • cfo_banking_demo.ml_models.dynamic_beta_parameters")
        print("   • cfo_banking_demo.ml_models.stress_test_results")
        print("   • cfo_banking_demo.gold_regulatory.lcr_daily")

        print("\n📊 PPNR Modeling (3 tables):")
        print("   • cfo_banking_demo.ml_models.ppnr_forecasts")
        print("   • cfo_banking_demo.ml_models.non_interest_income_training_data")
        print("   • cfo_banking_demo.ml_models.non_interest_expense_training_data")

        print("\n" + "=" * 70)
        print("NEXT STEPS")
        print("=" * 70)
        print("\n1. Open Genie Space in Databricks UI")
        print("2. Verify tables appear in the space")
        print("3. Test query: 'What is the average deposit beta?'")
        print("4. Now you can add SQL expressions and sample questions!")

    except subprocess.CalledProcessError as e:
        print(f"\n❌ FAILED to update Genie Space")
        print(f"\nError: {e.stderr}")
        print(f"\nTroubleshooting:")
        print(f"1. Review payload: {payload_file}")
        print(f"2. Review config: {output_file}")
        print(f"3. Verify table permissions in Unity Catalog")
        print(f"4. Check Databricks CLI authentication")


if __name__ == "__main__":
    add_tables_to_space()
