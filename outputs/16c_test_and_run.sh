#!/bin/bash
# WS6-01: Test and Run React + FastAPI App

set -e

echo "===================================================================="
echo "WS6-01: Testing React Frontend + FastAPI Backend"
echo "===================================================================="
echo ""

cd ~/Documents/Demo/databricks-cfo-banking-demo

# Step 1: Install frontend dependencies
echo "[1/5] Installing frontend dependencies..."
cd frontend_app
npm install
echo "✓ Frontend dependencies installed"
echo ""

# Step 2: Build frontend
echo "[2/5] Building React frontend..."
npm run build
echo "✓ Frontend built to out/ directory"
echo ""

# Step 3: Install backend dependencies
cd ..
echo "[3/5] Installing backend dependencies..."
source .venv/bin/activate
pip install -r backend/requirements.txt
echo "✓ Backend dependencies installed"
echo ""

# Step 4: Test backend API
echo "[4/5] Testing backend API..."
python3 << 'EOF'
import sys
sys.path.insert(0, "outputs")
from agent_tools_library import CFOAgentTools

print("Testing agent tools...")
tools = CFOAgentTools(warehouse_id="4b9b953939869799")

# Test 1: Portfolio summary
result = tools.get_portfolio_summary()
if result['success']:
    print(f"  ✓ Portfolio Summary: ${result['total_assets']/1e9:.2f}B assets")
else:
    print(f"  ✗ Portfolio Summary failed: {result.get('error', 'Unknown')}")

# Test 2: Treasury yields
result = tools.get_current_treasury_yields()
if result['success']:
    print(f"  ✓ Treasury Yields: 10Y = {result['yields']['10Y']}%")
else:
    print(f"  ✗ Treasury Yields failed: {result.get('error', 'Unknown')}")

# Test 3: LCR
result = tools.calculate_lcr()
if result['success']:
    print(f"  ✓ LCR: {result['lcr_ratio']:.2f}%")
else:
    print(f"  ✗ LCR failed: {result.get('error', 'Unknown')}")

print("Backend API tests complete!")
EOF
echo ""

# Step 5: Instructions for running
echo "[5/5] Setup complete!"
echo ""
echo "===================================================================="
echo "✅ WS6-01 Complete: React + FastAPI Ready"
echo "===================================================================="
echo ""
echo "TO RUN LOCALLY:"
echo "  1. Start FastAPI backend:"
echo "     source .venv/bin/activate"
echo "     uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "  2. Open browser:"
echo "     http://localhost:8000"
echo ""
echo "  3. Test API endpoints:"
echo "     http://localhost:8000/api/health"
echo "     http://localhost:8000/api/data/summary"
echo "     http://localhost:8000/api/data/yield-curve"
echo "     http://localhost:8000/api/data/lcr"
echo ""
echo "FOR DEVELOPMENT (with hot reload):"
echo "  Terminal 1: uvicorn backend.main:app --reload"
echo "  Terminal 2: cd frontend_app && npm run dev"
echo "  Visit: http://localhost:3000 (React dev server)"
echo ""
echo "TO DEPLOY TO DATABRICKS:"
echo "  databricks apps deploy cfo-platform-react \\"
echo "    --source-path . \\"
echo "    --config-file databricks.yml"
echo ""
