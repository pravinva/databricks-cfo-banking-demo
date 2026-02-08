"""
Claude Agent Integration with Databricks Model Serving
Provides intelligent AI agent with tool calling capabilities
"""

import os
import json
import requests
from typing import Dict, List, Any, Optional
from databricks.sdk import WorkspaceClient


class ClaudeAgent:
    """
    Claude Sonnet 4.5 integration via Databricks Model Serving
    with tool calling for CFO banking operations
    """

    TOOL_DEFINITIONS = [
        {
            "name": "call_deposit_beta_model",
            "description": "Treasury deposit modeling tool. Predict deposit runoff based on interest rate changes using the deposit beta model outputs. Use for rate shock scenarios (e.g., +50 bps on MMDA) and to explain beta sensitivity. Returns runoff amounts and runoff % for a given product type and rate change (bps).",
            "input_schema": {
                "type": "object",
                "properties": {
                    "rate_change_bps": {
                        "type": "integer",
                        "description": "Rate change in basis points (e.g., +50 for 50 bps increase, -25 for 25 bps decrease)"
                    },
                    "product_type": {
                        "type": "string",
                        "enum": ["MMDA", "DDA", "NOW", "Savings"],
                        "description": "Deposit product type: MMDA (Money Market Deposit Account), DDA (Demand Deposit Account), NOW (Negotiable Order of Withdrawal), or Savings"
                    }
                },
                "required": ["rate_change_bps", "product_type"]
            }
        },
        {
            "name": "calculate_lcr",
            "description": "Optional treasury stress tool. Calculate the Liquidity Coverage Ratio (LCR) under stress scenarios. Use only when asked about liquidity stress impacts or regulatory buffers. Returns LCR ratio, HQLA amounts, net cash outflows, and Pass/Fail status.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "deposit_runoff_multiplier": {
                        "type": "number",
                        "description": "Stress multiplier for deposit outflows. Use 1.0 for baseline, 1.5 for moderate stress, 2.0 for severe stress. Default is 1.0.",
                        "default": 1.0
                    }
                },
                "required": []
            }
        },
        {
            "name": "get_current_treasury_yields",
            "description": "Market data tool. Get the latest U.S. Treasury yield curve data (3M/2Y/5Y/10Y/30Y). Use to ground deposit pricing, beta discussions, and PPNR drivers in the current rate environment.",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "get_portfolio_summary",
            "description": "Treasury context tool. Get a high-level portfolio summary (focus on deposits for this demo). Use for quick context (e.g., total deposits) before diving into deposit beta, vintage, or PPNR results.",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "get_ppnr_forecasts",
            "description": "PPNR tool. Fetch the latest monthly PPNR forecast series (net interest income, non-interest income, non-interest expense, PPNR) from Unity Catalog. Use when summarizing PPNR outlook or explaining fee income drivers.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of months to return (default 24).",
                        "default": 24
                    }
                },
                "required": []
            }
        },
        {
            "name": "get_deposit_beta_by_product",
            "description": "Approach 1 helper. Return deposit beta distribution by product type from cfo_banking_demo.ml_models.deposit_beta_predictions (account_count, total_balance, avg_beta, beta_tier). Use this for 'deposit beta by product' questions.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Max number of products to return (default 10).",
                        "default": 10
                    }
                },
                "required": []
            }
        },
        {
            "name": "get_latest_yield_curve",
            "description": "Yield curve helper. Fetch the latest available curve (3M/2Y/5Y/10Y/30Y) from cfo_banking_demo.silver_treasury.yield_curves.",
            "input_schema": {"type": "object", "properties": {}, "required": []}
        },
        {
            "name": "query_unity_catalog",
            "description": "Execute custom SQL queries against Unity Catalog for treasury modeling. Use for ad-hoc analysis across deposits, yield curves, deposit beta predictions, vintage/runoff outputs, stress testing outputs, and PPNR forecasts.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL query to execute (SELECT only). Core tables: bronze_core_banking.deposit_accounts, silver_treasury.yield_curves, ml_models.deposit_beta_predictions, ml_models.component_decay_metrics, ml_models.cohort_survival_rates, ml_models.deposit_runoff_forecasts, ml_models.dynamic_beta_parameters, ml_models.stress_test_results, ml_models.ppnr_forecasts."
                    },
                    "max_rows": {
                        "type": "integer",
                        "description": "Maximum number of rows to return. Default is 100.",
                        "default": 100
                    }
                },
                "required": ["query"]
            }
        }
    ]

    SYSTEM_PROMPT = """You are a domain-specific Treasury Modeling assistant focused ONLY on Deposits and PPNR (fee income modeling) for this demo. You are not a general banking/CFO assistant.

Your job is to help users understand and interpret treasury modeling outputs in a practical way:
- Approach 1: Deposit Beta (static beta predictions)
- Approach 2: Vintage Analysis (Chen component decay + Kaplan-Meier survival)
- Approach 3: Stress Testing (dynamic beta curves + CCAR/DFAST-style scenarios)
- PPNR: monthly forecasts (net interest income, non-interest income, non-interest expense, PPNR)
- Market context: U.S. Treasury yield curve

How you should behave:
1. Stay in scope: deposits, yield curves, deposit beta/vintage/stress outputs, and PPNR.
2. Use tools for facts (tables/metrics). If you mention numeric values (balances, betas, runoff, PPNR), obtain them via tools. Prefer the specialized helpers first: get_deposit_beta_by_product, get_ppnr_forecasts, get_latest_yield_curve.
   Avoid repetitive tool loops: aim for 1 tool round-trip per question unless the user asks for follow-ups.
3. When asked for numbers, show the key aggregates and one or two supporting cuts (by product, by segment).
4. When asked for drivers, relate results to rates (yield curve), rate gap, beta tier, and segment behavior.

Key concepts:
- Deposit beta: sensitivity of deposit rates to market rates (0–1).
- Chen component decay: D(t+1)=D(t)×(1-λ)×(1+g) where λ=closure rate and g=ABGR.
- Kaplan-Meier: survival/retention curves by segment.
- PPNR: NII + non-interest income − non-interest expense.

## Unity Catalog tables (core)
Catalog: cfo_banking_demo

- bronze_core_banking.deposit_accounts
- silver_treasury.yield_curves
- ml_models.deposit_beta_predictions
- ml_models.component_decay_metrics
- ml_models.cohort_survival_rates
- ml_models.deposit_runoff_forecasts
- ml_models.dynamic_beta_parameters
- ml_models.stress_test_results
- ml_models.ppnr_forecasts

Use query_unity_catalog for custom SQL. Prefer the dedicated tools (get_current_treasury_yields, call_deposit_beta_model, get_ppnr_forecasts) when applicable."""

    def __init__(self, endpoint_name: str = "databricks-claude-sonnet-4-5"):
        """
        Initialize Claude agent with Databricks Model Serving endpoint

        Args:
            endpoint_name: Name of the Claude Sonnet 4.5 endpoint in Databricks
        """
        self.w = WorkspaceClient()
        self.endpoint_name = endpoint_name
        # Store conversation histories per session
        self.conversation_histories: Dict[str, List[Dict[str, Any]]] = {}

        # Setup REST API credentials
        self.host = self.w.config.host.replace("https://", "").replace("http://", "")
        self.url = f"https://{self.host}/serving-endpoints/{endpoint_name}/invocations"

        # Get authentication token
        if hasattr(self.w.config, 'token') and self.w.config.token:
            self.token = self.w.config.token
        else:
            # Use OAuth or other auth method
            auth_headers = self.w.config.authenticate()
            self.token = auth_headers.get('Authorization', '').replace('Bearer ', '')

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def _call_claude(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Call Claude via Databricks Model Serving endpoint using REST API.
        The serving endpoint returns OpenAI-compatible chat.completion responses.
        """
        payload: Dict[str, Any] = {"messages": messages, "max_tokens": 4096}
        if tools:
            openai_tools = []
            for tool in tools:
                openai_tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool["name"],
                            "description": tool["description"],
                            "parameters": tool["input_schema"],
                        },
                    }
                )
            payload["tools"] = openai_tools

        response = requests.post(self.url, headers=self.headers, json=payload, timeout=60)
        if response.status_code != 200:
            raise Exception(f"Claude API error ({response.status_code}): {response.text}")

        return response.json()

    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any], agent_tools) -> Dict[str, Any]:
        """
        Execute a tool call by invoking the corresponding agent_tools method

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool
            agent_tools: CFOAgentTools instance

        Returns:
            Tool execution result
        """
        if tool_name == "call_deposit_beta_model":
            return agent_tools.call_deposit_beta_model(
                rate_change_bps=tool_input.get("rate_change_bps"),
                product_type=tool_input.get("product_type", "MMDA")
            )
        elif tool_name == "calculate_lcr":
            return agent_tools.calculate_lcr(
                deposit_runoff_multiplier=tool_input.get("deposit_runoff_multiplier", 1.0)
            )
        elif tool_name == "get_current_treasury_yields":
            return agent_tools.get_current_treasury_yields()
        elif tool_name == "get_portfolio_summary":
            return agent_tools.get_portfolio_summary()
        elif tool_name == "get_ppnr_forecasts":
            limit = int(tool_input.get("limit", 24))
            limit = max(1, min(limit, 120))
            query = f"""
                SELECT
                    month,
                    net_interest_income,
                    non_interest_income,
                    non_interest_expense,
                    ppnr
                FROM cfo_banking_demo.ml_models.ppnr_forecasts
                ORDER BY month DESC
                LIMIT {limit}
            """
            return agent_tools.query_unity_catalog(query=query, max_rows=limit)
        elif tool_name == "get_deposit_beta_by_product":
            limit = int(tool_input.get("limit", 10))
            limit = max(1, min(limit, 50))
            query = f"""
                SELECT
                    product_type,
                    COUNT(*) AS account_count,
                    SUM(current_balance) AS total_balance,
                    AVG(predicted_beta) AS avg_beta,
                    CASE
                        WHEN AVG(predicted_beta) >= 0.60 THEN 'High Beta'
                        WHEN AVG(predicted_beta) >= 0.35 THEN 'Medium Beta'
                        ELSE 'Low Beta'
                    END AS beta_tier
                FROM cfo_banking_demo.ml_models.deposit_beta_predictions
                GROUP BY product_type
                ORDER BY total_balance DESC
                LIMIT {limit}
            """
            return agent_tools.query_unity_catalog(query=query, max_rows=limit)
        elif tool_name == "get_latest_yield_curve":
            query = """
                SELECT
                    date,
                    rate_3m,
                    rate_2y,
                    rate_5y,
                    rate_10y,
                    rate_30y
                FROM cfo_banking_demo.silver_treasury.yield_curves
                ORDER BY date DESC
                LIMIT 1
            """
            return agent_tools.query_unity_catalog(query=query, max_rows=1)
        elif tool_name == "query_unity_catalog":
            return agent_tools.query_unity_catalog(
                query=tool_input.get("query"),
                max_rows=tool_input.get("max_rows", 100)
            )
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

    def _format_tool_result(self, result: Dict[str, Any]) -> str:
        """
        Format tool execution result for Claude

        Args:
            result: Tool execution result dictionary

        Returns:
            Formatted string representation
        """
        if not result.get("success"):
            return f"Error: {result.get('error', 'Tool execution failed')}"

        # Remove success flag and format as JSON
        result_copy = {k: v for k, v in result.items() if k != "success"}
        return json.dumps(result_copy, indent=2, default=str)

    def chat(self, user_message: str, agent_tools, session_id: str = "default") -> str:
        """
        Process a user message with Claude and execute any tool calls

        Args:
            user_message: User's input message
            agent_tools: CFOAgentTools instance for executing tool calls
            session_id: Session identifier for conversation tracking

        Returns:
            Claude's response as a string
        """
        # Conversation history is stored in OpenAI message format (excluding system):
        # [{"role":"user"|"assistant"|"tool", ...}, ...]
        if session_id not in self.conversation_histories:
            self.conversation_histories[session_id] = []

        conversation_history = self.conversation_histories[session_id]
        conversation_history.append({"role": "user", "content": user_message})

        system_messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]

        max_iterations = 5
        iteration = 0
        retried_after_reset = False

        while iteration < max_iterations:
            messages = system_messages + conversation_history.copy()
            try:
                response = self._call_claude(messages, tools=self.TOOL_DEFINITIONS)
            except Exception as e:
                msg = str(e)
                if (not retried_after_reset) and ("tool_use" in msg and "tool_result" in msg):
                    # Session got poisoned with a dangling tool call; reset and retry once.
                    retried_after_reset = True
                    self.reset_conversation(session_id=session_id)
                    self.conversation_histories[session_id] = [{"role": "user", "content": user_message}]
                    conversation_history = self.conversation_histories[session_id]
                    continue
                raise

            if "choices" not in response or not response["choices"]:
                return "Error: No response from Claude"

            choice = response["choices"][0]
            message = choice.get("message", {})
            finish_reason = choice.get("finish_reason")

            tool_calls = message.get("tool_calls")
            if finish_reason == "tool_calls" and tool_calls:
                # Record the assistant tool call message (include content even if null)
                conversation_history.append(
                    {"role": "assistant", "content": message.get("content"), "tool_calls": tool_calls}
                )

                # Execute tool calls and append tool results immediately after
                for tool_call in tool_calls:
                    function_name = tool_call["function"]["name"]
                    function_args = json.loads(tool_call["function"]["arguments"])
                    tool_call_id = tool_call["id"]
                    result = self._execute_tool(function_name, function_args, agent_tools)
                    conversation_history.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": self._format_tool_result(result),
                        }
                    )

                iteration += 1
                continue

            # Final response
            final_response = message.get("content") or ""
            conversation_history.append({"role": "assistant", "content": final_response})
            return final_response

        return "Error: Too many tool-calling iterations. Please try a narrower question (e.g., one product or one table)."

    def reset_conversation(self, session_id: str = "default"):
        """Clear conversation history for a specific session"""
        if session_id in self.conversation_histories:
            del self.conversation_histories[session_id]
