#!/usr/bin/env python3
"""
Check for existing volumes in cfo_banking_demo catalog
"""
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

print("=" * 80)
print("CHECKING VOLUMES IN cfo_banking_demo CATALOG")
print("=" * 80)

# Check for existing volumes in cfo_banking_demo
try:
    catalogs = list(w.catalogs.list())
    for cat in catalogs:
        if cat.name == 'cfo_banking_demo':
            print(f'\n✓ Found catalog: {cat.name}')

            # List schemas
            schemas = list(w.schemas.list(catalog_name='cfo_banking_demo'))
            print(f'\nSchemas in catalog:')
            for schema in schemas:
                print(f'  - {schema.name}')

            # Check for volumes in each schema
            print(f'\nChecking for volumes in each schema:')
            for schema in schemas:
                try:
                    volumes = list(w.volumes.list(catalog_name='cfo_banking_demo', schema_name=schema.name))
                    if volumes:
                        print(f'  {schema.name}:')
                        for v in volumes:
                            print(f'    - {v.name} (type: {v.volume_type})')
                    else:
                        print(f'  {schema.name}: No volumes')
                except Exception as e:
                    print(f'  {schema.name}: Error checking volumes - {e}')
            break
    else:
        print('✗ Catalog cfo_banking_demo not found')
except Exception as e:
    print(f'✗ Error: {e}')

print("\n" + "=" * 80)
