#!/usr/bin/env python3
"""
Parse exported dashboard JSON and extract SQL queries
"""

import json
from pathlib import Path

def parse_dashboard(json_path, output_sql_path):
    """Parse dashboard JSON and create SQL file"""

    with open(json_path) as f:
        dashboard = json.load(f)

    # Parse the serialized_dashboard JSON string
    serialized = json.loads(dashboard['serialized_dashboard'])

    display_name = dashboard['display_name']
    dashboard_id = dashboard['dashboard_id']

    sql_content = f"""-- ============================================================================
-- {display_name}
-- ============================================================================
-- Dashboard ID: {dashboard_id}
-- Exported: {dashboard['update_time']}
-- Warehouse: {dashboard['warehouse_id']}
-- Source: https://e2-demo-field-eng.cloud.databricks.com/dashboardsv3/{dashboard_id}
-- ============================================================================

"""

    # Extract datasets (these contain the SQL queries)
    datasets = serialized.get('datasets', [])

    print(f"Found {len(datasets)} datasets in {display_name}")

    for i, dataset in enumerate(datasets, 1):
        query_name = dataset.get('displayName', f'Query {i}')
        query_lines = dataset.get('queryLines', [])

        # Join query lines to form complete SQL
        sql_query = ''.join(query_lines)

        sql_content += f"""
-- ============================================================================
-- QUERY {i}: {query_name}
-- Dataset Name: {dataset.get('name', 'Unknown')}
-- ============================================================================

{sql_query}

"""

    # Write to SQL file
    with open(output_sql_path, 'w') as f:
        f.write(sql_content)

    print(f"✅ Created SQL file: {output_sql_path}")
    print(f"   Contains {len(datasets)} queries")

    return len(datasets)

def main():
    dashboards_dir = Path(__file__).parent.parent / 'dashboards'

    dashboards = [
        ('08_Flight_Deck_raw.json', '08_Flight_Deck.sql'),
        ('09_Portfolio_Suite_raw.json', '09_Portfolio_Suite.sql')
    ]

    print("=" * 80)
    print("Parsing Dashboard JSON Files")
    print("=" * 80)

    total_queries = 0
    for json_file, sql_file in dashboards:
        json_path = dashboards_dir / json_file
        sql_path = dashboards_dir / sql_file

        if json_path.exists():
            print(f"\n📊 Processing {json_file}...")
            count = parse_dashboard(json_path, sql_path)
            total_queries += count
        else:
            print(f"⚠️  {json_file} not found")

    print("\n" + "=" * 80)
    print(f"✅ Export Complete: {total_queries} total queries extracted")
    print("=" * 80)

if __name__ == "__main__":
    main()
