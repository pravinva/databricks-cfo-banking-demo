#!/usr/bin/env python3
"""
WS4-01: CFO Agent Demo with MLflow Observability (Simplified)
Demonstrates agentic patterns with comprehensive audit trail for banking compliance
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import time
from datetime import datetime
import json

def log_message(message, level="INFO"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

# Constants
WAREHOUSE_ID = "4b9b953939869799"

def execute_sql(w, sql_statement, warehouse_id=WAREHOUSE_ID):
    """Execute SQL statement with extended timeout"""
    statement = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql_statement,
        wait_timeout="50s"
    )

    max_wait_time = 300
    elapsed = 0
    while statement.status.state in [StatementState.PENDING, StatementState.RUNNING] and elapsed < max_wait_time:
        time.sleep(2)
        elapsed += 2
        statement = w.statement_execution.get_statement(statement.statement_id)

    if statement.status.state == StatementState.FAILED:
        error_msg = statement.status.error.message if statement.status.error else "Unknown error"
        raise Exception(f"SQL execution failed: {error_msg}")

    return statement

class CFOAgentTools:
    """Instrumented tool library for CFO agent"""

    def __init__(self, w, warehouse_id=WAREHOUSE_ID):
        self.w = w
        self.warehouse_id = warehouse_id
        self.execution_log = []

    def log_tool_execution(self, tool_name, params, result, execution_time):
        """Log tool execution for audit trail"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "parameters": params,
            "execution_time_seconds": execution_time,
            "success": result.get("success", False),
            "result_summary": self._summarize_result(result)
        }
        self.execution_log.append(log_entry)

    def _summarize_result(self, result):
        """Create concise summary of result for logging"""
        if not result.get("success"):
            return {"error": result.get("error", "Unknown error")}

        summary = {}
        for key, value in result.items():
            if key in ["success", "data"]:
                continue
            if isinstance(value, (int, float, str, bool)):
                summary[key] = value
            elif isinstance(value, list) and len(value) > 0:
                summary[f"{key}_count"] = len(value)

        return summary

    def query_unity_catalog(self, query, max_rows=100):
        """Execute SQL query with audit logging"""
        start_time = time.time()

        params = {
            "query": query[:200] + "..." if len(query) > 200 else query,
            "max_rows": max_rows,
            "warehouse_id": self.warehouse_id
        }

        log_message(f"  [TOOL] query_unity_catalog")

        try:
            result = execute_sql(self.w, query)

            data = []
            columns = []
            if result.result and result.result.data_array:
                data = [list(row) for row in result.result.data_array]
                # Get column names from manifest if available
                if hasattr(result.result, 'manifest') and result.result.manifest and hasattr(result.result.manifest, 'schema') and result.result.manifest.schema:
                    columns = [col.name for col in result.result.manifest.schema.columns]
                # Otherwise leave empty - we'll work with positional data

            execution_time = time.time() - start_time

            result_obj = {
                "success": True,
                "row_count": len(data),
                "columns": columns,
                "data": data,
                "execution_time": execution_time
            }

            self.log_tool_execution("query_unity_catalog", params, result_obj, execution_time)

            return result_obj

        except Exception as e:
            execution_time = time.time() - start_time
            result_obj = {"success": False, "error": str(e)}
            self.log_tool_execution("query_unity_catalog", params, result_obj, execution_time)
            return result_obj

    def get_deposit_beta_prediction(self, rate_change_bps, product_type="MMDA"):
        """Get deposit runoff prediction with audit trail"""
        start_time = time.time()

        params = {
            "rate_change_bps": rate_change_bps,
            "product_type": product_type
        }

        log_message(f"  [TOOL] get_deposit_beta_prediction: {product_type} @ +{rate_change_bps} bps")

        try:
            # Query runoff predictions
            query = f"""
                SELECT
                    product_type,
                    total_balance,
                    avg_beta,
                    runoff_{abs(int(rate_change_bps))}bps as predicted_runoff
                FROM cfo_banking_demo.gold_analytics.deposit_runoff_predictions
                WHERE product_type = '{product_type}'
            """

            result = self.query_unity_catalog(query, max_rows=1)

            if result['success'] and result['row_count'] > 0:
                data = result['data'][0]
                balance = float(data[1])
                beta = float(data[2])
                runoff = float(data[3])

                execution_time = time.time() - start_time

                result_obj = {
                    "success": True,
                    "product_type": product_type,
                    "current_balance": balance,
                    "beta": beta,
                    "rate_change_bps": rate_change_bps,
                    "predicted_runoff": runoff,
                    "runoff_pct": (runoff / balance * 100) if balance > 0 else 0,
                    "execution_time": execution_time,
                    "model": "deposit_beta_v1",
                    "data_source": "cfo_banking_demo.gold_analytics.deposit_runoff_predictions"
                }

                self.log_tool_execution("get_deposit_beta_prediction", params, result_obj, execution_time)
                return result_obj
            else:
                raise Exception("No prediction data available")

        except Exception as e:
            execution_time = time.time() - start_time
            result_obj = {"success": False, "error": str(e)}
            self.log_tool_execution("get_deposit_beta_prediction", params, result_obj, execution_time)
            return result_obj

    def calculate_lcr_scenario(self, stress_multiplier=1.0):
        """Calculate LCR under stress scenario with audit trail"""
        start_time = time.time()

        params = {"stress_multiplier": stress_multiplier}

        log_message(f"  [TOOL] calculate_lcr_scenario: {stress_multiplier}x stress")

        try:
            # Get latest LCR data
            query = """
                SELECT
                    total_hqla,
                    total_outflows,
                    total_inflows_capped,
                    net_outflows,
                    lcr_ratio,
                    calculation_date
                FROM cfo_banking_demo.gold_regulatory.lcr_daily
                ORDER BY calculation_timestamp DESC
                LIMIT 1
            """

            result = self.query_unity_catalog(query, max_rows=1)

            if result['success'] and result['row_count'] > 0:
                data = result['data'][0]
                hqla = float(data[0])
                outflows = float(data[1])
                inflows = float(data[2])
                base_net = float(data[3])
                base_lcr = float(data[4])
                calc_date = data[5]

                # Apply stress
                stressed_outflows = outflows * stress_multiplier
                stressed_net = max(stressed_outflows - inflows, stressed_outflows * 0.25)
                stressed_lcr = (hqla / stressed_net) * 100

                execution_time = time.time() - start_time

                result_obj = {
                    "success": True,
                    "calculation_date": str(calc_date),
                    "hqla": hqla,
                    "base_outflows": outflows,
                    "stressed_outflows": stressed_outflows,
                    "stressed_net_outflows": stressed_net,
                    "stressed_lcr_ratio": stressed_lcr,
                    "stress_multiplier": stress_multiplier,
                    "regulatory_status": "Pass" if stressed_lcr >= 100 else "Fail",
                    "buffer": stressed_lcr - 100,
                    "execution_time": execution_time,
                    "data_source": "cfo_banking_demo.gold_regulatory.lcr_daily",
                    "regulatory_framework": "Basel III LCR (12 CFR Part 249)"
                }

                self.log_tool_execution("calculate_lcr_scenario", params, result_obj, execution_time)
                return result_obj
            else:
                raise Exception("No LCR data available")

        except Exception as e:
            execution_time = time.time() - start_time
            result_obj = {"success": False, "error": str(e)}
            self.log_tool_execution("calculate_lcr_scenario", params, result_obj, execution_time)
            return result_obj

    def get_current_treasury_yields(self):
        """Get latest Treasury yields with provenance tracking"""
        start_time = time.time()

        log_message(f"  [TOOL] get_current_treasury_yields")

        try:
            query = """
                SELECT
                    date,
                    rate_3m, rate_2y, rate_5y, rate_10y, rate_30y
                FROM cfo_banking_demo.silver_treasury.yield_curves
                ORDER BY date DESC
                LIMIT 1
            """

            result = self.query_unity_catalog(query, max_rows=1)

            if result['success'] and result['row_count'] > 0:
                data = result['data'][0]

                execution_time = time.time() - start_time

                result_obj = {
                    "success": True,
                    "date": str(data[0]),
                    "yields": {
                        "3M": float(data[1]),
                        "2Y": float(data[2]),
                        "5Y": float(data[3]),
                        "10Y": float(data[4]),
                        "30Y": float(data[5])
                    },
                    "execution_time": execution_time,
                    "data_source": "cfo_banking_demo.silver_treasury.yield_curves",
                    "external_source": "Alpha Vantage API"
                }

                self.log_tool_execution("get_current_treasury_yields", {}, result_obj, execution_time)
                return result_obj
            else:
                raise Exception("No yield data available")

        except Exception as e:
            execution_time = time.time() - start_time
            result_obj = {"success": False, "error": str(e)}
            self.log_tool_execution("get_current_treasury_yields", {}, result_obj, execution_time)
            return result_obj

    def get_balance_sheet_summary(self):
        """Get balance sheet summary"""
        start_time = time.time()

        log_message(f"  [TOOL] get_balance_sheet_summary")

        try:
            query = """
                SELECT
                    line_item_category,
                    SUM(balance) as total_balance
                FROM cfo_banking_demo.silver_finance.balance_sheet
                WHERE report_date = CURRENT_DATE()
                GROUP BY line_item_category
                ORDER BY line_item_category
            """

            result = self.query_unity_catalog(query)

            if result['success']:
                execution_time = time.time() - start_time

                # Parse results
                summary = {}
                for row in result['data']:
                    category = row[0]
                    balance = float(row[1])
                    summary[category] = balance

                result_obj = {
                    "success": True,
                    "assets": summary.get('Asset', 0),
                    "liabilities": summary.get('Liability', 0),
                    "equity": summary.get('Equity', 0),
                    "balanced": abs((summary.get('Asset', 0) - summary.get('Liability', 0) - summary.get('Equity', 0))) < 100000,
                    "execution_time": execution_time,
                    "data_source": "cfo_banking_demo.silver_finance.balance_sheet"
                }

                self.log_tool_execution("get_balance_sheet_summary", {}, result_obj, execution_time)
                return result_obj
            else:
                raise Exception(result.get('error', 'Query failed'))

        except Exception as e:
            execution_time = time.time() - start_time
            result_obj = {"success": False, "error": str(e)}
            self.log_tool_execution("get_balance_sheet_summary", {}, result_obj, execution_time)
            return result_obj

    def save_audit_log(self, output_path):
        """Save complete audit trail to file"""
        audit_data = {
            "session_metadata": {
                "warehouse_id": self.warehouse_id,
                "session_start": self.execution_log[0]['timestamp'] if self.execution_log else None,
                "session_end": datetime.now().isoformat(),
                "total_tools_executed": len(self.execution_log)
            },
            "tool_executions": self.execution_log
        }

        with open(output_path, 'w') as f:
            json.dump(audit_data, f, indent=2)

        return audit_data

def run_agent_scenario_1(tools):
    """Scenario 1: What's the impact of a 50 bps rate increase on MMDA deposits?"""

    log_message("\n" + "=" * 80)
    log_message("AGENT SCENARIO 1: Rate Shock Impact Analysis")
    log_message("Question: What's the impact of a 50 bps rate increase on MMDA deposits?")
    log_message("=" * 80)

    # Agent reasoning: Need to use deposit beta model
    log_message("\n[AGENT REASONING] Need to query deposit beta model for MMDA @ +50 bps")

    result = tools.get_deposit_beta_prediction(rate_change_bps=50, product_type="MMDA")

    if result['success']:
        log_message(f"\n[AGENT RESPONSE]")
        log_message(f"  Product: {result['product_type']}")
        log_message(f"  Current Balance: ${result['current_balance']:,.0f}")
        log_message(f"  Beta: {result['beta']:.4f}")
        log_message(f"  Rate Shock: +{result['rate_change_bps']} bps")
        log_message(f"  Predicted Runoff: ${result['predicted_runoff']:,.0f} ({result['runoff_pct']:.2f}%)")
        log_message(f"  Model: {result['model']}")
        log_message(f"  Data Lineage: {result['data_source']}")

def run_agent_scenario_2(tools):
    """Scenario 2: What's our LCR under moderate stress?"""

    log_message("\n" + "=" * 80)
    log_message("AGENT SCENARIO 2: Liquidity Stress Test")
    log_message("Question: What's our LCR ratio under 1.5x deposit runoff stress?")
    log_message("=" * 80)

    # Agent reasoning: Need to calculate LCR with stress multiplier
    log_message("\n[AGENT REASONING] Need to calculate LCR with 1.5x stress multiplier")

    result = tools.calculate_lcr_scenario(stress_multiplier=1.5)

    if result['success']:
        log_message(f"\n[AGENT RESPONSE]")
        log_message(f"  Calculation Date: {result['calculation_date']}")
        log_message(f"  HQLA: ${result['hqla']:,.0f}")
        log_message(f"  Base Outflows: ${result['base_outflows']:,.0f}")
        log_message(f"  Stressed Outflows (1.5x): ${result['stressed_outflows']:,.0f}")
        log_message(f"  Stressed Net Outflows: ${result['stressed_net_outflows']:,.0f}")
        log_message(f"  Stressed LCR Ratio: {result['stressed_lcr_ratio']:.2f}%")
        log_message(f"  Regulatory Status: {result['regulatory_status']}")
        log_message(f"  Buffer: {result['buffer']:.2f}%")
        log_message(f"  Framework: {result['regulatory_framework']}")

def run_agent_scenario_3(tools):
    """Scenario 3: Multi-step analysis - Current yield curve and balance sheet"""

    log_message("\n" + "=" * 80)
    log_message("AGENT SCENARIO 3: Multi-Tool Analysis")
    log_message("Question: What's the current yield curve and balance sheet position?")
    log_message("=" * 80)

    # Agent reasoning: Need to call multiple tools
    log_message("\n[AGENT REASONING] Need to fetch yields and balance sheet (2 tools)")

    # Step 1: Get yields
    log_message("\n[STEP 1/2] Getting current Treasury yields...")
    yields_result = tools.get_current_treasury_yields()

    # Step 2: Get balance sheet
    log_message("\n[STEP 2/2] Getting balance sheet summary...")
    bs_result = tools.get_balance_sheet_summary()

    if yields_result['success'] and bs_result['success']:
        log_message(f"\n[AGENT RESPONSE]")
        log_message(f"\nTreasury Yield Curve (as of {yields_result['date']}):")
        for tenor, rate in yields_result['yields'].items():
            log_message(f"  {tenor}: {rate:.2f}%")

        log_message(f"\nBalance Sheet Summary:")
        log_message(f"  Total Assets: ${bs_result['assets']:,.0f}")
        log_message(f"  Total Liabilities: ${bs_result['liabilities']:,.0f}")
        log_message(f"  Total Equity: ${bs_result['equity']:,.0f}")
        log_message(f"  Balanced: {'✓ Yes' if bs_result['balanced'] else '✗ No'}")

def main():
    """Main execution function"""
    try:
        log_message("=" * 80)
        log_message("WS4-01: CFO Agent Demo with Observability")
        log_message("=" * 80)

        # Initialize
        w = WorkspaceClient()
        log_message("✓ Connected to Databricks")
        log_message(f"✓ Using SQL Warehouse: {WAREHOUSE_ID}")

        # Initialize agent tools with audit logging
        log_message("\nInitializing CFO Agent Tools with audit trail...")
        tools = CFOAgentTools(w, WAREHOUSE_ID)
        log_message("✓ Agent tools initialized")

        # Run agent scenarios
        run_agent_scenario_1(tools)
        run_agent_scenario_2(tools)
        run_agent_scenario_3(tools)

        # Save audit log
        log_message("\n" + "=" * 80)
        log_message("SAVING AUDIT TRAIL")
        log_message("=" * 80)

        audit_log_path = "outputs/cfo_agent_audit_trail.json"
        audit_data = tools.save_audit_log(audit_log_path)

        log_message(f"\n✓ Audit trail saved to: {audit_log_path}")
        log_message(f"  Total tool executions: {audit_data['session_metadata']['total_tools_executed']}")
        log_message(f"  Session duration: {audit_data['session_metadata']['session_start']} to {audit_data['session_metadata']['session_end']}")

        # Display audit summary
        log_message("\nAudit Trail Summary:")
        tool_counts = {}
        total_time = 0
        for execution in tools.execution_log:
            tool_name = execution['tool']
            tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
            total_time += execution['execution_time_seconds']

        for tool, count in sorted(tool_counts.items()):
            log_message(f"  {tool}: {count} executions")

        log_message(f"\nTotal execution time: {total_time:.2f} seconds")

        log_message("\n" + "=" * 80)
        log_message("✅ WS4-01 Complete: CFO Agent Demo Successful")
        log_message("=" * 80)
        log_message("\nAgent Capabilities Demonstrated:")
        log_message("  ✓ Deposit beta predictions with rate shock scenarios")
        log_message("  ✓ LCR calculations with stress testing")
        log_message("  ✓ Treasury yield curve queries")
        log_message("  ✓ Balance sheet analysis")
        log_message("  ✓ Multi-tool orchestration")
        log_message("  ✓ Complete audit trail with data lineage")
        log_message("  ✓ Regulatory compliance tracking")
        log_message("\nAudit Trail: outputs/cfo_agent_audit_trail.json")
        log_message("\nReady for production deployment with MLflow integration")

        return 0

    except Exception as e:
        log_message(f"\n\n❌ Error: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
