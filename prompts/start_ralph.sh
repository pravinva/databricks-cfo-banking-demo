#!/bin/bash

# CFO Banking Demo - Ralph Wiggum Execution Environment
# This script sets up the environment for autonomous execution

set -e  # Exit on error

echo "=== CFO Banking Demo - Environment Setup ==="

# 1. Check for ~/.databrickscfg
if [ ! -f ~/.databrickscfg ]; then
    echo "ERROR: ~/.databrickscfg not found!"
    echo "Please configure Databricks CLI first"
    exit 1
fi

# Verify default profile exists
if ! grep -q "\[DEFAULT\]" ~/.databrickscfg; then
    echo "ERROR: [DEFAULT] profile not found in ~/.databrickscfg"
    exit 1
fi

echo "✓ Found ~/.databrickscfg with DEFAULT profile"

# 2. Use CURRENT directory instead of hard-coded path
PROJECT_ROOT="$(pwd)"
echo "✓ Project directory: $PROJECT_ROOT"

# Create subdirectories
mkdir -p prompts outputs logs

# 3. Create or activate venv IN CURRENT DIRECTORY
if [ ! -f ".venv/bin/activate" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate venv
source .venv/bin/activate
echo "✓ Virtual environment activated"

# 4. Install required packages
echo "Installing Python dependencies..."
pip install --upgrade pip --quiet
pip install databricks-sdk --quiet
pip install databricks-cli --quiet
pip install pyspark --quiet
pip install pandas --quiet
pip install mlflow --quiet
pip install dspy-ai --quiet
echo "✓ Dependencies installed"

# 5. Verify Databricks connection
echo "Verifying Databricks connection..."
python3 << 'PYTHON'
from databricks.sdk import WorkspaceClient
try:
    w = WorkspaceClient()
    user = w.current_user.me()
    print(f"✓ Connected to workspace as: {user.user_name}")
    print(f"✓ Workspace URL: {w.config.host}")
except Exception as e:
    print(f"ERROR: Could not connect to Databricks: {e}")
    exit(1)
PYTHON

# 6. Copy prompt files if they exist
if [ -d "$HOME/Downloads/cfo-prompts" ]; then
    echo "Copying prompt files from Downloads..."
    cp $HOME/Downloads/cfo-prompts/*.md prompts/ 2>/dev/null || true
    PROMPT_COUNT=$(ls -1 prompts/*.md 2>/dev/null | wc -l)
    echo "✓ Copied $PROMPT_COUNT prompt files"
fi

# 7. Create execution log
LOG_FILE="logs/setup-$(date +%Y%m%d-%H%M%S).log"
echo "Environment setup complete at $(date)" > "$LOG_FILE"
echo "Project root: $PROJECT_ROOT" >> "$LOG_FILE"
echo "Python: $(which python)" >> "$LOG_FILE"
echo "Pip packages: $(pip list)" >> "$LOG_FILE"

echo ""
echo "=== Environment Ready ==="
echo "Project root: $PROJECT_ROOT"
echo "Python venv: .venv (activated)"
echo "Databricks: Connected via ~/.databrickscfg [DEFAULT]"
echo "Prompt files: prompts/ ($PROMPT_COUNT files)"
echo "Outputs: outputs/"
echo "Logs: logs/"
echo ""
echo "✅ You can now start Ralph Loop in Claude Desktop"
echo ""
