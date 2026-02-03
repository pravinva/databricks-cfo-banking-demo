#!/bin/bash
# Export Databricks Dashboards to Local Repository
# Usage: ./export_dashboards.sh

set -e

# Dashboard IDs from your URLs
FLIGHT_DECK_ID="01f0f97c007f1364a78d06fbfd74303a"
PORTFOLIO_SUITE_ID="01f0fea1adbb1e97a3142da3a87f7cb8"

# Output directory
OUTPUT_DIR="../dashboards"

echo "=========================================="
echo "Databricks Dashboard Export Utility"
echo "=========================================="
echo ""

# Check if databricks CLI is installed
if ! command -v databricks &> /dev/null; then
    echo "❌ Databricks CLI not found. Please install:"
    echo "   pip install databricks-cli"
    exit 1
fi

echo "✅ Databricks CLI found"
echo ""

# Check authentication
if ! databricks workspace ls / &> /dev/null; then
    echo "❌ Databricks authentication failed. Please configure:"
    echo "   databricks configure --token"
    exit 1
fi

echo "✅ Databricks authentication successful"
echo ""

# Export Flight Deck Dashboard
echo "📊 Exporting Flight Deck Dashboard (${FLIGHT_DECK_ID})..."
databricks dashboards get ${FLIGHT_DECK_ID} > ${OUTPUT_DIR}/08_Flight_Deck_Dashboard_raw.json 2>/dev/null || {
    echo "⚠️  Dashboard API may not support export. Trying workspace export..."
    # Alternative: Export as workspace object if it's stored there
    # You may need to find the workspace path first
}

# Export Portfolio Suite Dashboard
echo "📊 Exporting Portfolio Suite Dashboard (${PORTFOLIO_SUITE_ID})..."
databricks dashboards get ${PORTFOLIO_SUITE_ID} > ${OUTPUT_DIR}/09_Portfolio_Suite_Dashboard_raw.json 2>/dev/null || {
    echo "⚠️  Dashboard API may not support export. Trying workspace export..."
}

echo ""
echo "=========================================="
echo "Manual Export Instructions"
echo "=========================================="
echo ""
echo "Since Databricks Lakeview dashboards may not support CLI export,"
echo "please follow these manual steps:"
echo ""
echo "1. Open Flight Deck Dashboard:"
echo "   https://e2-demo-field-eng.cloud.databricks.com/dashboardsv3/${FLIGHT_DECK_ID}"
echo ""
echo "2. Click the '⋮' menu (top right) → 'Export' or 'View SQL'"
echo ""
echo "3. Copy all SQL queries and save to:"
echo "   ${OUTPUT_DIR}/08_Flight_Deck_Dashboard.sql"
echo ""
echo "4. Repeat for Portfolio Suite:"
echo "   https://e2-demo-field-eng.cloud.databricks.com/dashboardsv3/${PORTFOLIO_SUITE_ID}"
echo "   Save to: ${OUTPUT_DIR}/09_Portfolio_Suite_Dashboard.sql"
echo ""
echo "5. Update ${OUTPUT_DIR}/README.md with new dashboard descriptions"
echo ""
echo "=========================================="
echo "Alternative: Use Databricks SDK"
echo "=========================================="
echo ""
echo "Run the Python export script instead:"
echo "   python dev-scripts/export_dashboards_sdk.py"
echo ""
