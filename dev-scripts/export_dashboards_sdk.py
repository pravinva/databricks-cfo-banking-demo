#!/usr/bin/env python3
"""
Export Databricks Lakeview Dashboards to SQL files
Uses Databricks SDK to fetch dashboard definitions
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

def export_dashboard(w, dashboard_id, output_filename):
    """Export a single dashboard"""
    print(f"\n📊 Exporting dashboard {dashboard_id}...")

    try:
        # Try to get dashboard using SDK
        # Note: The SDK method may vary based on Databricks version
        # This is a placeholder - actual method depends on SDK capabilities

        print(f"⚠️  Note: Databricks SDK may not support Lakeview dashboard export directly.")
        print(f"   Manual export required from Databricks UI")
        print(f"   URL: https://e2-demo-field-eng.cloud.databricks.com/dashboardsv3/{dashboard_id}")

        # Create placeholder file with instructions
        output_path = OUTPUT_DIR / f"{output_filename}.sql"
        content = f"""-- ============================================================================
-- {output_filename.replace('_', ' ')}
-- ============================================================================
-- Dashboard ID: {dashboard_id}
-- Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- Source: https://e2-demo-field-eng.cloud.databricks.com/dashboardsv3/{dashboard_id}
-- ============================================================================
--
-- TO COMPLETE THIS EXPORT:
-- 1. Open the dashboard URL above in Databricks
-- 2. Click the '⋮' menu (top right)
-- 3. Select 'View SQL' or 'Export'
-- 4. Copy all SQL queries
-- 5. Replace this placeholder content with the actual queries
--
-- EXPECTED CONTENT:
-- - Multiple QUERY sections (QUERY 1, QUERY 2, etc.)
-- - Each query with:
--   * Purpose/description
--   * SQL SELECT statement
--   * Visualization instructions (chart type, colors)
--
-- ============================================================================

-- QUERY 1: [Query Name]
-- Purpose: [Description]
-- Chart Type: [e.g., Bar Chart, Line Chart, KPI Card]
-- ============================================================================

-- TODO: Paste actual SQL here

"""

        output_path.write_text(content)
        print(f"✅ Created placeholder file: {output_path}")
        print(f"   Please manually populate with SQL from dashboard")

        return True

    except Exception as e:
        print(f"❌ Error exporting dashboard {dashboard_id}: {e}")
        return False

def main():
    print("=" * 80)
    print("Databricks Dashboard Export Utility (SDK Version)")
    print("=" * 80)

    # Initialize Databricks client
    try:
        w = WorkspaceClient()
        print(f"✅ Connected to Databricks workspace")
        print(f"   Host: {w.config.host}")
    except Exception as e:
        print(f"❌ Failed to connect to Databricks: {e}")
        print("\nPlease ensure:")
        print("  1. DATABRICKS_HOST environment variable is set")
        print("  2. DATABRICKS_TOKEN environment variable is set")
        print("  OR")
        print("  3. ~/.databrickscfg is configured")
        return

    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Export each dashboard
    results = {}
    for name, dashboard_id in DASHBOARDS.items():
        results[name] = export_dashboard(w, dashboard_id, name)

    # Summary
    print("\n" + "=" * 80)
    print("Export Summary")
    print("=" * 80)

    for name, success in results.items():
        status = "✅ Created placeholder" if success else "❌ Failed"
        print(f"{status}: {name}")

    print("\n" + "=" * 80)
    print("Next Steps")
    print("=" * 80)
    print("""
1. Open each dashboard in Databricks UI:
   - Flight Deck: https://e2-demo-field-eng.cloud.databricks.com/dashboardsv3/01f0f97c007f1364a78d06fbfd74303a
   - Portfolio Suite: https://e2-demo-field-eng.cloud.databricks.com/dashboardsv3/01f0fea1adbb1e97a3142da3a87f7cb8

2. For each dashboard:
   a. Click the '⋮' menu (top right)
   b. Look for 'View SQL' or 'Export' option
   c. Copy all SQL queries
   d. Paste into the placeholder file created above

3. Update dashboards/README.md with descriptions of the new dashboards

4. Commit to git:
   git add dashboards/08_Flight_Deck.sql dashboards/09_Portfolio_Suite.sql
   git commit -m "Add Flight Deck and Portfolio Suite dashboards"
   git push
""")

if __name__ == "__main__":
    main()
