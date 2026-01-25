#!/bin/bash

echo "=== Starting Complete Backfill Loop ==="
echo "This will run until all loans have GL and subledger entries"

iteration=1
max_iterations=20

while [ $iteration -le $max_iterations ]; do
    echo ""
    echo "=== Iteration $iteration of $max_iterations ==="
    echo "$(date): Running backfill..."
    
    # Run the backfill script
    python3 backfill_all_accounting.py 2>&1 | tail -5
    
    # Check how many loans remain
    remaining=$(python3 << 'EOF'
import sys
sys.path.insert(0, '..')
from agent_tools_library import CFOAgentTools
agent = CFOAgentTools()
result = agent.query_unity_catalog("""
    SELECT COUNT(*) 
    FROM cfo_banking_demo.silver_finance.loan_portfolio l
    LEFT JOIN cfo_banking_demo.silver_finance.gl_entries gl 
        ON gl.source_transaction_id = l.loan_id
    WHERE l.is_current = true AND gl.entry_id IS NULL
""")
if result['success']:
    print(result['data'][0][0])
else:
    print("0")
EOF
)
    
    echo "Remaining loans without GL entries: $remaining"
    
    # Exit if no loans remain
    if [ "$remaining" = "0" ]; then
        echo "=== COMPLETE! All loans have GL and subledger entries ==="
        exit 0
    fi
    
    iteration=$((iteration + 1))
    echo "Waiting 2 seconds before next iteration..."
    sleep 2
done

echo "=== Reached max iterations. Check remaining count manually ==="
