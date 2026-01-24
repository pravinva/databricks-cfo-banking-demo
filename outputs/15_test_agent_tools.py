#!/usr/bin/env python3
"""
Test Agent Tools - Verify all CFO agent tools work correctly
"""

# Import agent tools
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agent_tools_library import CFOAgentTools

def log_message(message):
    print(message)

def main():
    try:
        # Initialize tools
        log_message("Initializing CFO Agent Tools...")
        tools = CFOAgentTools(warehouse_id="4b9b953939869799")
        log_message("✓ Tools initialized\n")

        log_message("="*60)
        log_message("TESTING AGENT TOOLS")
        log_message("="*60)

        # Test 1: Query Unity Catalog
        log_message("\n1. Testing Unity Catalog Query...")
        result = tools.query_unity_catalog("""
            SELECT COUNT(*) as count
            FROM cfo_banking_demo.bronze_core_banking.chart_of_accounts
        """)
        log_message(f"   Result: {'✓ Success' if result['success'] else '✗ Failed'}")
        if result['success']:
            log_message(f"   Rows: {result.get('row_count', 0)}")
            if result['data']:
                log_message(f"   COA Count: {result['data'][0][0]}")
        else:
            log_message(f"   Error: {result.get('error', 'Unknown')}")

        # Test 2: Get Treasury Yields
        log_message("\n2. Testing Treasury Yields...")
        result = tools.get_current_treasury_yields()
        log_message(f"   Result: {'✓ Success' if result['success'] else '✗ Failed'}")
        if result['success']:
            log_message(f"   Date: {result.get('date', 'N/A')}")
            log_message(f"   10Y Yield: {result['yields']['10Y']}%")
            log_message(f"   30Y Yield: {result['yields']['30Y']}%")
        else:
            log_message(f"   Error: {result.get('error', 'Unknown')}")

        # Test 3: Call Deposit Beta Model
        log_message("\n3. Testing Deposit Beta Model...")
        result = tools.call_deposit_beta_model(rate_change_bps=50, product_type="MMDA")
        log_message(f"   Result: {'✓ Success' if result['success'] else '✗ Failed'}")
        if result['success']:
            log_message(f"   Product: {result['product_type']}")
            log_message(f"   Balance: ${result['current_balance']/1e6:.0f}M")
            log_message(f"   Predicted runoff: ${result['predicted_runoff_amount']/1e6:.1f}M ({result['runoff_pct']:.2f}%)")
            log_message(f"   Beta: {result['beta']:.4f}")
        else:
            log_message(f"   Error: {result.get('error', 'Unknown')}")

        # Test 4: Calculate LCR
        log_message("\n4. Testing LCR Calculator...")
        result = tools.calculate_lcr(deposit_runoff_multiplier=1.0)
        log_message(f"   Result: {'✓ Success' if result['success'] else '✗ Failed'}")
        if result['success']:
            log_message(f"   LCR Ratio: {result['lcr_ratio']:.2f}%")
            log_message(f"   HQLA: ${result['hqla']/1e9:.2f}B")
            log_message(f"   Status: {result['status']}")
            log_message(f"   Buffer: {result['buffer']:.2f}%")
        else:
            log_message(f"   Error: {result.get('error', 'Unknown')}")

        # Test 5: Portfolio Summary
        log_message("\n5. Testing Portfolio Summary...")
        result = tools.get_portfolio_summary()
        log_message(f"   Result: {'✓ Success' if result['success'] else '✗ Failed'}")
        if result['success']:
            log_message(f"   Securities: ${result['securities']/1e9:.2f}B")
            log_message(f"   Loans: ${result['loans']/1e9:.2f}B")
            log_message(f"   Deposits: ${result['deposits']/1e9:.2f}B")
            log_message(f"   Total Assets: ${result['total_assets']/1e9:.2f}B")
        else:
            log_message(f"   Error: {result.get('error', 'Unknown')}")

        log_message("\n" + "="*60)
        log_message("TOOLS TEST COMPLETE")
        log_message("="*60)

        # Save audit log
        audit_file = "outputs/test_audit_trail.json"
        tools.save_audit_log(audit_file)
        log_message(f"\n✓ Audit trail saved to: {audit_file}")
        log_message(f"  Total tool executions: {len(tools.execution_log)}")

        # Count successes
        successes = sum(1 for log in tools.execution_log if log['success'])
        log_message(f"  Success rate: {successes}/{len(tools.execution_log)} ({successes/len(tools.execution_log)*100:.0f}%)")

        return 0

    except Exception as e:
        log_message(f"\n\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
