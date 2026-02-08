#!/usr/bin/env python3
"""
Agent Tools Library - Standalone CFO Agent Tools with MLflow Instrumentation
Can be imported by other scripts for agent integration
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import time
from datetime import datetime
import json

class CFOAgentTools:
    """
    Production-grade tool library with comprehensive observability
    for banking regulatory compliance
    """

    def __init__(self, warehouse_id="4b9b953939869799"):
        self.w = WorkspaceClient()
        self.warehouse_id = warehouse_id
        self.execution_log = []

    def _execute_sql(self, sql_statement):
        """Execute SQL statement"""
        statement = self.w.statement_execution.execute_statement(
            warehouse_id=self.warehouse_id,
            statement=sql_statement,
            wait_timeout="50s"
        )

        max_wait_time = 300
        elapsed = 0
        while statement.status.state in [StatementState.PENDING, StatementState.RUNNING] and elapsed < max_wait_time:
            time.sleep(2)
            elapsed += 2
            statement = self.w.statement_execution.get_statement(statement.statement_id)

        if statement.status.state == StatementState.FAILED:
            error_msg = statement.status.error.message if statement.status.error else "Unknown error"
            raise Exception(f"SQL execution failed: {error_msg}")

        return statement

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

        try:
            result = self._execute_sql(query)

            data = []
            columns = []
            if result.result and result.result.data_array:
                data = [list(row) for row in result.result.data_array]
                if hasattr(result.result, 'manifest') and result.result.manifest and hasattr(result.result.manifest, 'schema') and result.result.manifest.schema:
                    columns = [col.name for col in result.result.manifest.schema.columns]

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

    def call_deposit_beta_model(self, rate_change_bps, product_type="MMDA"):
        """Get deposit runoff prediction"""
        start_time = time.time()

        params = {
            "rate_change_bps": rate_change_bps,
            "product_type": product_type
        }

        try:
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
                    "predicted_runoff_amount": runoff,
                    "runoff_pct": (runoff / balance * 100) if balance > 0 else 0,
                    "execution_time": execution_time,
                    "model_version": "deposit_beta_v1"
                }

                self.log_tool_execution("call_deposit_beta_model", params, result_obj, execution_time)
                return result_obj
            else:
                raise Exception("No prediction data available")

        except Exception as e:
            execution_time = time.time() - start_time
            result_obj = {"success": False, "error": str(e)}
            self.log_tool_execution("call_deposit_beta_model", params, result_obj, execution_time)
            return result_obj

    def calculate_lcr(self, deposit_runoff_multiplier=1.0):
        """Calculate LCR under stress scenario"""
        start_time = time.time()

        params = {"deposit_runoff_multiplier": deposit_runoff_multiplier}

        try:
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

                stressed_outflows = outflows * deposit_runoff_multiplier
                stressed_net = max(stressed_outflows - inflows, stressed_outflows * 0.25)
                stressed_lcr = (hqla / stressed_net) * 100

                execution_time = time.time() - start_time

                result_obj = {
                    "success": True,
                    "lcr_ratio": stressed_lcr,
                    "hqla": hqla,
                    "net_outflows": stressed_net,
                    "status": "Pass" if stressed_lcr >= 100 else "Fail",
                    "buffer": stressed_lcr - 100,
                    "deposit_runoff_multiplier": deposit_runoff_multiplier,
                    "execution_time": execution_time
                }

                self.log_tool_execution("calculate_lcr", params, result_obj, execution_time)
                return result_obj
            else:
                raise Exception("No LCR data available")

        except Exception as e:
            execution_time = time.time() - start_time
            result_obj = {"success": False, "error": str(e)}
            self.log_tool_execution("calculate_lcr", params, result_obj, execution_time)
            return result_obj

    def get_current_treasury_yields(self):
        """Get latest Treasury yields"""
        start_time = time.time()

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
                    "execution_time": execution_time
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

    def get_portfolio_summary(self):
        """Get portfolio summary across loans and deposits"""
        start_time = time.time()

        try:
            # Get loans
            loans_query = """
                SELECT SUM(current_balance) as total
                FROM cfo_banking_demo.bronze_core_banking.loan_portfolio
                WHERE is_current = true
            """
            loans_result = self.query_unity_catalog(loans_query, max_rows=1)
            loans = float(loans_result['data'][0][0]) if loans_result['success'] else 0

            # Get deposits
            deposits_query = """
                SELECT SUM(current_balance) as total
                FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
                WHERE account_status = 'Active'
            """
            deposits_result = self.query_unity_catalog(deposits_query, max_rows=1)
            deposits = float(deposits_result['data'][0][0]) if deposits_result['success'] else 0

            execution_time = time.time() - start_time

            result_obj = {
                "success": True,
                "loans": loans,
                "deposits": deposits,
                "total_assets": loans,
                "execution_time": execution_time
            }

            self.log_tool_execution("get_portfolio_summary", {}, result_obj, execution_time)
            return result_obj

        except Exception as e:
            execution_time = time.time() - start_time
            result_obj = {"success": False, "error": str(e)}
            self.log_tool_execution("get_portfolio_summary", {}, result_obj, execution_time)
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
