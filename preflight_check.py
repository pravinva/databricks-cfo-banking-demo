#!/usr/bin/env python3
"""
Pre-flight checks before executing CFO Banking Demo tasks
Ensures environment is properly configured
"""

import os
import sys
from pathlib import Path

def check_environment():
    """Run all pre-flight checks"""
    
    checks_passed = True
    
    # 1. Check we're not running as root
    if os.geteuid() == 0:
        print("❌ ERROR: Running as root user - FORBIDDEN")
        print("   Please run without sudo")
        checks_passed = False
    else:
        print("✓ Not running as root")
    
    # 2. Check for virtual environment
    if sys.prefix == sys.base_prefix:
        print("❌ ERROR: Not in a virtual environment")
        print("   Please activate venv: source .venv/bin/activate")
        checks_passed = False
    else:
        print(f"✓ Virtual environment active: {sys.prefix}")
    
    # 3. Check for ~/.databrickscfg
    databricks_cfg = Path.home() / ".databrickscfg"
    if not databricks_cfg.exists():
        print("❌ ERROR: ~/.databrickscfg not found")
        checks_passed = False
    else:
        print("✓ Found ~/.databrickscfg")
        
        # Check for DEFAULT profile
        with open(databricks_cfg) as f:
            content = f.read()
            if "[DEFAULT]" not in content:
                print("❌ ERROR: [DEFAULT] profile not found in ~/.databrickscfg")
                checks_passed = False
            else:
                print("✓ [DEFAULT] profile exists")
    
    # 4. Check required packages
    required_packages = [
        'databricks.sdk',
        'databricks',
        'pyspark',
        'pandas',
        'mlflow'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ Package installed: {package}")
        except ImportError:
            print(f"❌ ERROR: Missing package: {package}")
            print(f"   Install with: pip install {package}")
            checks_passed = False
    
    # 5. Test Databricks connection
    print("\nTesting Databricks connection...")
    try:
        from databricks.sdk import WorkspaceClient
        w = WorkspaceClient()
        user = w.current_user.me()
        print(f"✓ Connected as: {user.user_name}")
        print(f"✓ Workspace: {w.config.host}")
    except Exception as e:
        print(f"❌ ERROR: Could not connect to Databricks: {e}")
        checks_passed = False
    
    # 6. Check project structure
    required_dirs = ['prompts', 'outputs', 'logs']
    for dir_name in required_dirs:
        if not Path(dir_name).exists():
            print(f"⚠️  WARNING: Missing directory: {dir_name}")
            Path(dir_name).mkdir(exist_ok=True)
            print(f"   Created: {dir_name}")
        else:
            print(f"✓ Directory exists: {dir_name}")
    
    print("\n" + "="*50)
    if checks_passed:
        print("✅ ALL PRE-FLIGHT CHECKS PASSED")
        print("Environment is ready for execution")
        return 0
    else:
        print("❌ PRE-FLIGHT CHECKS FAILED")
        print("Please fix errors above before proceeding")
        return 1

if __name__ == "__main__":
    sys.exit(check_environment())
