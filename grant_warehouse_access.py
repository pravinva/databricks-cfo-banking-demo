#!/usr/bin/env python3
"""
Grant warehouse access to the app service principal
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import PermissionLevel

# Initialize workspace client
w = WorkspaceClient()

# Warehouse ID and service principal info
warehouse_id = "4b9b953939869799"
service_principal_id = 70728936211001  # From databricks apps list output

print("=" * 80)
print("GRANTING WAREHOUSE ACCESS TO APP SERVICE PRINCIPAL")
print("=" * 80)
print(f"Warehouse ID: {warehouse_id}")
print(f"Service Principal ID: {service_principal_id}")
print()

try:
    # Set warehouse permissions
    w.warehouses.set_workspace_warehouse_config(
        data_access_config=[
            {
                "principal": str(service_principal_id),
                "permission_level": PermissionLevel.CAN_USE
            }
        ]
    )

    print("✓ Successfully granted warehouse access!")

except Exception as e:
    print(f"❌ ERROR: {e}")
    print()
    print("Alternative: Grant warehouse access via UI:")
    print("  1. Go to: Compute > SQL Warehouses")
    print(f"  2. Select warehouse: {warehouse_id}")
    print("  3. Click 'Permissions' tab")
    print("  4. Click 'Grant'")
    print("  5. Search for: app-40zbx9 cfo-banking-demo")
    print("  6. Select 'Can Use' permission")
    print("  7. Click 'Save'")
