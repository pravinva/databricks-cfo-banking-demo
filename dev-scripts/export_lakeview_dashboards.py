#!/usr/bin/env python3
"""
Export Databricks Lakeview Dashboards using SDK lakeview API
"""

from databricks.sdk import WorkspaceClient
import json
from pathlib import Path
from datetime import datetime

# Dashboard IDs from URLs
DASHBOARDS = {
    "08_Flight_Deck": "01f0f97c007f1364a78d06fbfd74303a",
    "09_Portfolio_Suite": "01f0fea1adbb1e97a3142da3a87f7cb8"
}

OUTPUT_DIR = Path(__file__).parent.parent / "dashboards"

def extract_sql_from_dashboard(dashboard_obj):
    """Extract SQL queries from dashboard definition"""
    queries = []

    try:
        # Dashboard structure may vary, try different paths
        if hasattr(dashboard_obj, 'pages'):
            for page in dashboard_obj.pages:
                if hasattr(page, 'layout'):
                    for widget in page.layout:
                        if hasattr(widget, 'spec') and hasattr(widget.spec, 'query'):
                            query_text = widget.spec.query.get('query')
                            if query_text:
                                queries.append({
                                    'name': widget.spec.get('title', 'Unnamed Query'),
                                    'sql': query_text,
                                    'viz_type': widget.spec.get('viz_type', 'table')
                                })

        # Alternative structure
        if hasattr(dashboard_obj, 'datasets'):
            for dataset in dashboard_obj.datasets:
                if hasattr(dataset, 'query'):
                    queries.append({
                        'name': dataset.get('name', 'Unnamed Query'),
                        'sql': dataset.query,
                        'viz_type': 'unknown'
                    })

    except Exception as e:
        print(f"   Warning: Error extracting queries: {e}")

    return queries

def export_dashboard_lakeview(w, dashboard_id, output_filename):
    """Export dashboard using Lakeview API"""
    print(f"\n📊 Exporting dashboard {dashboard_id}...")

    try:
        # Try using the lakeview API
        dashboard = w.lakeview.get(dashboard_id)

        print(f"✅ Retrieved dashboard: {dashboard.display_name if hasattr(dashboard, 'display_name') else 'Unnamed'}")

        # Save raw JSON for reference
        json_path = OUTPUT_DIR / f"{output_filename}_raw.json"
        with open(json_path, 'w') as f:
            # Convert to dict if needed
            if hasattr(dashboard, 'as_dict'):
                json.dump(dashboard.as_dict(), f, indent=2)
            else:
                json.dump(str(dashboard), f, indent=2)
        print(f"✅ Saved raw JSON: {json_path}")

        # Extract SQL queries
        queries = extract_sql_from_dashboard(dashboard)

        if queries:
            print(f"✅ Found {len(queries)} queries")

            # Create SQL file with queries
            sql_content = f"""-- ============================================================================
-- {output_filename.replace('_', ' ')}
-- ============================================================================
-- Dashboard ID: {dashboard_id}
-- Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- Display Name: {dashboard.display_name if hasattr(dashboard, 'display_name') else 'Unknown'}
-- Source: https://e2-demo-field-eng.cloud.databricks.com/dashboardsv3/{dashboard_id}
-- ============================================================================

"""

            for i, query in enumerate(queries, 1):
                sql_content += f"""
-- ============================================================================
-- QUERY {i}: {query['name']}
-- Visualization Type: {query['viz_type']}
-- ============================================================================

{query['sql']}

"""

            sql_path = OUTPUT_DIR / f"{output_filename}.sql"
            sql_path.write_text(sql_content)
            print(f"✅ Created SQL file: {sql_path}")

        else:
            print(f"⚠️  No SQL queries found in dashboard definition")
            print(f"   Check the raw JSON file: {json_path}")

        return True

    except AttributeError as e:
        print(f"❌ Lakeview API not available in SDK: {e}")
        print(f"   Your SDK version may not support Lakeview dashboards")
        return False

    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"\nTrying alternative approach using workspace export...")

        # Try workspace export as fallback
        try:
            # Dashboard might be stored in workspace at a path
            # Try to find it
            workspace_path = f"/Workspace/Users/{w.current_user.me().user_name}/dashboards/{dashboard_id}"
            content = w.workspace.export(workspace_path, format='SOURCE')

            output_path = OUTPUT_DIR / f"{output_filename}_workspace.txt"
            output_path.write_bytes(content.content)
            print(f"✅ Exported via workspace: {output_path}")
            return True

        except Exception as e2:
            print(f"❌ Workspace export also failed: {e2}")
            return False

def export_via_api_request(w, dashboard_id, output_filename):
    """Try direct API request to dashboard endpoint"""
    print(f"\n🔄 Attempting direct API request for {dashboard_id}...")

    try:
        # Use the workspace client's api_client to make direct request
        response = w.api_client.do(
            'GET',
            f'/api/2.0/lakeview/dashboards/{dashboard_id}'
        )

        print(f"✅ API request successful")

        # Save response
        json_path = OUTPUT_DIR / f"{output_filename}_api.json"
        with open(json_path, 'w') as f:
            json.dump(response, f, indent=2)

        print(f"✅ Saved API response: {json_path}")

        # Try to parse and create SQL file
        if 'pages' in response or 'datasets' in response:
            print(f"✅ Dashboard definition contains data")
            # TODO: Parse and extract SQL

        return True

    except Exception as e:
        print(f"❌ Direct API request failed: {e}")
        return False

def main():
    print("=" * 80)
    print("Databricks Lakeview Dashboard Export (SDK Version)")
    print("=" * 80)

    # Initialize Databricks client
    try:
        w = WorkspaceClient()
        print(f"✅ Connected to Databricks workspace")
        print(f"   Host: {w.config.host}")
        print(f"   User: {w.current_user.me().user_name}")
    except Exception as e:
        print(f"❌ Failed to connect to Databricks: {e}")
        return

    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Try each export method
    for name, dashboard_id in DASHBOARDS.items():
        print(f"\n{'=' * 80}")
        print(f"Processing: {name}")
        print(f"{'=' * 80}")

        # Method 1: Lakeview API
        success = export_dashboard_lakeview(w, dashboard_id, name)

        # Method 2: Direct API request (if method 1 failed)
        if not success:
            success = export_via_api_request(w, dashboard_id, name)

        if not success:
            print(f"\n⚠️  All export methods failed for {name}")
            print(f"   The dashboard may need to be manually exported from the UI")

    print("\n" + "=" * 80)
    print("Export Complete")
    print("=" * 80)
    print(f"\nCheck the {OUTPUT_DIR} directory for exported files:")
    print(f"  - *_raw.json: Raw dashboard definitions")
    print(f"  - *_api.json: API responses")
    print(f"  - *.sql: Extracted SQL queries")

if __name__ == "__main__":
    main()
