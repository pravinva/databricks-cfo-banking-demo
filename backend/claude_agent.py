"""
Claude Agent Integration with Databricks Model Serving
Provides intelligent AI agent with tool calling capabilities
"""

import os
import json
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
            "description": "Predict deposit runoff based on interest rate changes. Use this when analyzing rate shock scenarios, deposit sensitivity to rate changes, or beta coefficients. Returns predicted runoff amounts and percentages for a given product type and rate change in basis points.",
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
            "description": "Calculate the Liquidity Coverage Ratio (LCR) under stress scenarios. Use this when analyzing liquidity, regulatory compliance, Basel III requirements, or stress testing. Returns LCR ratio, HQLA amounts, net cash outflows, and compliance status.",
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
            "description": "Get the latest U.S. Treasury yield curve data. Use this when analyzing market rates, yield curves, treasury bonds, interest rate environment, or economic indicators. Returns yields for 3M, 2Y, 5Y, 10Y, and 30Y maturities with curve shape analysis.",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "get_portfolio_summary",
            "description": "Get comprehensive portfolio summary across securities, loans, and deposits. Use this when analyzing overall balance sheet, asset allocation, portfolio composition, or liabilities. Returns total amounts and breakdowns by category.",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "query_unity_catalog",
            "description": "Execute custom SQL queries against Unity Catalog banking database. Use this for ad-hoc analysis, custom reports, or when specific data needs that other tools don't cover. Available schemas: bronze_core_banking (loans, deposits), silver_treasury (securities, yields), gold_analytics (predictions), gold_regulatory (LCR, HQLA).",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL query to execute. Must be a SELECT statement. Available tables include loan_portfolio, deposit_accounts, securities_portfolio, yield_curves, deposit_runoff_predictions, lcr_daily, hqla_inventory."
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

    SYSTEM_PROMPT = """You are an expert AI assistant for CFO and Treasury operations at a banking institution. You have access to real-time banking data through Databricks Unity Catalog and specialized tools for financial analysis.

Your capabilities include:
- **Rate Shock Analysis**: Predict deposit runoff based on interest rate changes using ML-based deposit beta models
- **Liquidity Analysis**: Calculate LCR (Liquidity Coverage Ratio) under various stress scenarios
- **Market Data**: Access current U.S. Treasury yield curves and analyze interest rate environments
- **Portfolio Analysis**: Provide comprehensive views of securities, loans, and deposits
- **Custom Queries**: Execute SQL queries for ad-hoc analysis and reporting

Key banking concepts you should be familiar with:
- **Deposit Beta**: A coefficient (0 to 1) measuring how sensitive deposit rates are to market rate changes. Higher beta = more sensitive to rate changes.
- **LCR (Liquidity Coverage Ratio)**: Basel III regulatory requirement. Must be ≥100%. Formula: HQLA / Net Cash Outflows. Measures ability to survive 30-day liquidity stress.
- **HQLA (High-Quality Liquid Assets)**: Level 1 (cash, reserves, treasuries), Level 2A (GSE bonds, AAA corporates), Level 2B (high-quality equities, some corporates)
- **Rate Shock**: Instantaneous parallel shift in interest rate curve, used for stress testing
- **Runoff**: Expected outflows from deposit accounts due to rate changes or other factors

When users ask questions:
1. First understand their intent - are they asking for analysis (use tools) or concepts (explain directly)
2. Use appropriate tools to fetch data when needed
3. Provide clear, professional explanations with relevant context
4. Format responses in a clean, readable way
5. Include relevant metrics, percentages, and dollar amounts
6. Explain the business implications of the data

Be concise but thorough. Use technical terminology appropriately but explain key concepts when relevant."""

    def __init__(self, endpoint_name: str = "databricks-claude-sonnet-4-5"):
        """
        Initialize Claude agent with Databricks Model Serving endpoint

        Args:
            endpoint_name: Name of the Claude Sonnet 4.5 endpoint in Databricks
        """
        self.w = WorkspaceClient()
        self.endpoint_name = endpoint_name
        self.conversation_history: List[Dict[str, Any]] = []

    def _call_claude(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Call Claude via Databricks Model Serving endpoint

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            tools: Optional list of tool definitions

        Returns:
            Claude API response
        """
        payload = {
            "messages": messages,
            "max_tokens": 4096,
            "anthropic_version": "bedrock-2023-05-31"
        }

        if tools:
            payload["tools"] = tools

        # Call Databricks Model Serving endpoint
        response = self.w.serving_endpoints.query(
            name=self.endpoint_name,
            inputs=[payload]
        )

        # Parse response
        if hasattr(response, 'predictions') and response.predictions:
            return response.predictions[0]
        else:
            raise Exception("Invalid response from Claude endpoint")

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
        # Add user message to conversation
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Prepare messages with system prompt
        messages = [
            {"role": "user", "content": self.SYSTEM_PROMPT}
        ] + self.conversation_history

        # Initial Claude call with tools
        response = self._call_claude(messages, tools=self.TOOL_DEFINITIONS)

        # Handle tool use iterations
        max_iterations = 5
        iteration = 0

        while iteration < max_iterations:
            # Check if Claude wants to use tools
            if response.get("stop_reason") == "tool_use":
                # Extract tool uses from response
                tool_uses = [block for block in response.get("content", []) if block.get("type") == "tool_use"]

                if not tool_uses:
                    break

                # Execute all tool calls
                tool_results = []
                for tool_use in tool_uses:
                    tool_name = tool_use.get("name")
                    tool_input = tool_use.get("input", {})
                    tool_use_id = tool_use.get("id")

                    # Execute tool
                    result = self._execute_tool(tool_name, tool_input, agent_tools)

                    # Format result
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": self._format_tool_result(result)
                    })

                # Add assistant message with tool use to conversation
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response.get("content", [])
                })

                # Add tool results to conversation
                self.conversation_history.append({
                    "role": "user",
                    "content": tool_results
                })

                # Call Claude again with tool results
                messages = [
                    {"role": "user", "content": self.SYSTEM_PROMPT}
                ] + self.conversation_history

                response = self._call_claude(messages, tools=self.TOOL_DEFINITIONS)
                iteration += 1
            else:
                # No more tool uses, break
                break

        # Extract final text response
        content_blocks = response.get("content", [])
        text_blocks = [block.get("text", "") for block in content_blocks if block.get("type") == "text"]
        final_response = "\n".join(text_blocks)

        # Add assistant's final response to conversation history
        self.conversation_history.append({
            "role": "assistant",
            "content": final_response
        })

        return final_response

    def reset_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []
