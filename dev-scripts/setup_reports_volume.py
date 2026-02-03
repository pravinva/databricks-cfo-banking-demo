#!/usr/bin/env python3
"""
Create a UC Volume for storing analytics reports
"""
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import VolumeType

w = WorkspaceClient()

print("=" * 80)
print("SETTING UP REPORTS VOLUME IN UNITY CATALOG")
print("=" * 80)

catalog_name = "cfo_banking_demo"
schema_name = "gold_finance"
volume_name = "reports"

print(f"\nCreating volume: {catalog_name}.{schema_name}.{volume_name}")

try:
    # Check if volume already exists
    existing_volumes = list(w.volumes.list(catalog_name=catalog_name, schema_name=schema_name))
    if any(v.name == volume_name for v in existing_volumes):
        print(f"  ⚠️  Volume already exists, skipping creation")
    else:
        # Create the volume
        volume = w.volumes.create(
            catalog_name=catalog_name,
            schema_name=schema_name,
            name=volume_name,
            volume_type=VolumeType.MANAGED,
            comment="Managed volume for deposit analytics reports and other finance reports"
        )
        print(f"  ✓ Volume created successfully")
        print(f"    - Name: {volume.name}")
        print(f"    - Type: {volume.volume_type}")
        print(f"    - Full name: {volume.full_name}")
        print(f"    - Storage location: {volume.storage_location}")

    print(f"\n✓ Reports volume is ready")
    print(f"  Path to use in notebooks: /Volumes/{catalog_name}/{schema_name}/{volume_name}/")
    print(f"  Example: /Volumes/{catalog_name}/{schema_name}/{volume_name}/deposit_analytics_report.html")

except Exception as e:
    print(f"  ✗ Error creating volume: {e}")
    print(f"\nNote: Make sure you have CREATE VOLUME privileges on {catalog_name}.{schema_name}")

print("\n" + "=" * 80)
