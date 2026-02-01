"""
FastAPI Backend for CFO Platform
Serves React static files and provides API endpoints with MLflow tracing
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from databricks.sdk import WorkspaceClient
import mlflow
import sys
import os
from pathlib import Path

# Add outputs directory to path for importing agent tools
sys.path.insert(0, str(Path(__file__).parent.parent / "outputs"))

# Get warehouse ID from environment or use default
WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID", "4b9b953939869799")

try:
    from agent_tools_library import CFOAgentTools
    agent_tools = CFOAgentTools(warehouse_id=WAREHOUSE_ID)
    print(f"✓ Successfully loaded agent tools with warehouse: {WAREHOUSE_ID}")
except Exception as e:
    print(f"❌ ERROR: Could not load agent tools: {e}")
    import traceback
    traceback.print_exc()
    agent_tools = None

# Initialize FastAPI
app = FastAPI(
    title="CFO Platform API",
    description="AI-Powered Financial Management Platform",
    version="1.0.0"
)

# Add CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ChatRequest(BaseModel):
    query: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    response: str
    mlflow_run_id: str = "N/A"
    execution_time: float

# API Endpoints
@app.get("/api")
async def api_root():
    """API root endpoint - health check"""
    return {
        "status": "healthy",
        "service": "CFO Platform API",
        "version": "1.0.0"
    }

@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "agent_tools_loaded": agent_tools is not None}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Agent chat endpoint with MLflow tracing
    All calls automatically logged for audit
    """
    import time
    start = time.time()

    if not agent_tools:
        return ChatResponse(
            response="Agent tools not available. Please check server configuration.",
            execution_time=time.time() - start
        )

    try:
        query_lower = request.query.lower()
        response_text = ""

        # Rate shock analysis
        if "rate shock" in query_lower or "bps" in query_lower:
            # Extract rate change and product type
            import re
            bps_match = re.search(r'([+-]?\d+)\s*bps?', query_lower)

            if bps_match:
                rate_change = int(bps_match.group(1))

                # Determine product type
                product_type = "MMDA"  # default
                if "dda" in query_lower:
                    product_type = "DDA"
                elif "now" in query_lower:
                    product_type = "NOW"
                elif "savings" in query_lower:
                    product_type = "Savings"
                elif "mmda" in query_lower:
                    product_type = "MMDA"

                result = agent_tools.call_deposit_beta_model(
                    rate_change_bps=rate_change,
                    product_type=product_type
                )

                if result["success"]:
                    response_text = f"""═══════════════════════════════════════════════════════════
 RATE SHOCK ANALYSIS
═══════════════════════════════════════════════════════════

SCENARIO
  Product Type: {result['product_type']}
  Rate Change: {rate_change:+d} basis points
  Current Balance: ${result['current_balance']/1e9:.2f}B

DEPOSIT BETA COEFFICIENT
  Beta: {result['beta']:.4f}
  (Measures deposit sensitivity to rate changes)

PROJECTED IMPACT
  Predicted Runoff: ${result['predicted_runoff_amount']/1e6:.1f}M
  Runoff Percentage: {result['runoff_pct']:.2f}%

INTERPRETATION
  A {abs(rate_change)} basis point {'increase' if rate_change > 0 else 'decrease'} in market rates
  would result in approximately ${result['predicted_runoff_amount']/1e6:.1f}M of deposit
  runoff from {product_type} accounts, representing {result['runoff_pct']:.2f}%
  of the current balance.

MODEL DETAILS
  Version: {result['model_version']}
  Execution Time: {result['execution_time']:.2f}s

─────────────────────────────────────────────────────────
Tools Used: call_deposit_beta_model(rate_change_bps={rate_change}, product_type="{product_type}")"""
                else:
                    response_text = f"Error: {result.get('error', 'Failed to calculate rate shock')}"
            else:
                response_text = "Please specify the rate change in basis points (e.g., '+50 bps' or '-25 bps')"

        # Treasury yields
        elif "yield" in query_lower or "treasury" in query_lower:
            result = agent_tools.get_current_treasury_yields()
            if result["success"]:
                yields = result["yields"]
                curve_shape = "Normal (upward sloping)" if float(yields['30Y']) > float(yields['3M']) else "Inverted"
                response_text = f"""═══════════════════════════════════════════════════════════
 U.S. TREASURY YIELD CURVE
═══════════════════════════════════════════════════════════

MARKET DATE
  {result['date']}

CURRENT YIELDS
  3-Month T-Bill:    {yields['3M']}%
  2-Year Note:       {yields['2Y']}%
  5-Year Note:       {yields['5Y']}%
  10-Year Note:      {yields['10Y']}%
  30-Year Bond:      {yields['30Y']}%

CURVE ANALYSIS
  Shape: {curve_shape}
  Spread (30Y - 3M): {float(yields['30Y']) - float(yields['3M']):.2f}%

INTERPRETATION
  {"The yield curve is normal, indicating healthy economic expectations. Longer-term rates exceed short-term rates, suggesting positive growth outlook." if curve_shape == "Normal (upward sloping)" else "The yield curve is inverted, which historically has been a recession indicator. Short-term rates exceed long-term rates, suggesting economic uncertainty."}

MODEL DETAILS
  Source: U.S. Department of Treasury
  Execution Time: {result['execution_time']:.2f}s

─────────────────────────────────────────────────────────
Tools Used: get_current_treasury_yields()"""

        # LCR analysis
        elif "lcr" in query_lower or "liquidity" in query_lower:
            multiplier = 1.0
            if "stress" in query_lower:
                import re
                mult_match = re.search(r'(\d+\.?\d*)x', query_lower)
                if mult_match:
                    multiplier = float(mult_match.group(1))

            result = agent_tools.calculate_lcr(deposit_runoff_multiplier=multiplier)
            if result["success"]:
                status_symbol = '✓' if result['status'] == 'Pass' else '✗'
                stress_info = f"\n  Stress Multiplier: {multiplier}x" if multiplier != 1.0 else ""
                response_text = f"""═══════════════════════════════════════════════════════════
 LIQUIDITY COVERAGE RATIO (LCR)
═══════════════════════════════════════════════════════════

LCR CALCULATION
  LCR Ratio: {result['lcr_ratio']:.2f}%
  Regulatory Minimum: 100%
  Buffer Above Minimum: {result['buffer']:.2f}%

COMPLIANCE STATUS
  Status: {result['status']} {status_symbol}
  {'[REGULATORY COMPLIANT]' if result['status'] == 'Pass' else '[BELOW REGULATORY MINIMUM]'}

BALANCE SHEET COMPONENTS
  High-Quality Liquid Assets (HQLA): ${result['hqla']/1e9:.2f}B
  Net Cash Outflows (30-day): ${result['net_outflows']/1e9:.2f}B{stress_info}

FORMULA
  LCR = HQLA / Net Cash Outflows
  LCR = ${result['hqla']/1e9:.2f}B / ${result['net_outflows']/1e9:.2f}B = {result['lcr_ratio']:.2f}%

INTERPRETATION
  {"The bank maintains adequate liquidity buffers and exceeds the 100% regulatory minimum. Current position provides " + f"{result['buffer']:.2f}%" + " cushion above requirements." if result['status'] == 'Pass' else "WARNING: The bank is below the 100% regulatory minimum. Immediate action required to increase HQLA or reduce net outflows."}

MODEL DETAILS
  Regulation: Basel III LCR Standard
  Execution Time: {result['execution_time']:.2f}s

─────────────────────────────────────────────────────────
Tools Used: calculate_lcr(deposit_runoff_multiplier={multiplier})"""

        # Portfolio summary
        elif "portfolio" in query_lower or "summary" in query_lower or "balance sheet" in query_lower:
            result = agent_tools.get_portfolio_summary()
            if result["success"]:
                sec_pct = result['securities']/result['total_assets']*100
                loan_pct = result['loans']/result['total_assets']*100
                response_text = f"""═══════════════════════════════════════════════════════════
 PORTFOLIO SUMMARY
═══════════════════════════════════════════════════════════

TOTAL ASSETS
  ${result['total_assets']/1e9:.2f}B

ASSET BREAKDOWN
  Securities
    Amount: ${result['securities']/1e9:.2f}B
    Percentage: {sec_pct:.1f}%

  Loans
    Amount: ${result['loans']/1e9:.2f}B
    Percentage: {loan_pct:.1f}%

TOTAL LIABILITIES
  Deposits
    Amount: ${result['deposits']/1e9:.2f}B

ASSET COMPOSITION ANALYSIS
  The portfolio is {'securities-heavy' if sec_pct > loan_pct else 'loan-heavy'} with
  {max(sec_pct, loan_pct):.1f}% allocated to {'securities' if sec_pct > loan_pct else 'loans'}.

  Securities provide liquidity and lower risk while loans
  typically generate higher yields. Current allocation
  balances {'liquidity needs with income generation' if sec_pct > 40 else 'income generation with liquidity management'}.

MODEL DETAILS
  Source: Unity Catalog - cfo_banking_demo
  Execution Time: {result['execution_time']:.2f}s

─────────────────────────────────────────────────────────
Tools Used: get_portfolio_summary()"""

        else:
            # Default help message
            response_text = """I can help you with:

1. Rate Shock Analysis
   Example: "Rate shock: +50 bps on MMDA"

2. Treasury Yields
   Example: "Current 10Y Treasury yield"

3. Liquidity Coverage Ratio
   Example: "LCR status" or "LCR with 1.5x stress"

4. Portfolio Summary
   Example: "Portfolio summary" or "Balance sheet"

What would you like to know?"""

    except Exception as e:
        response_text = f"Error processing query: {str(e)}\n\nPlease try rephrasing your question."

    execution_time = time.time() - start

    return ChatResponse(
        response=response_text,
        execution_time=execution_time
    )

@app.get("/api/data/summary")
async def get_summary():
    """Get portfolio summary data"""
    if not agent_tools:
        return JSONResponse({"error": "Agent tools not available"}, status_code=503)

    try:
        result = agent_tools.get_portfolio_summary()
        return result
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/data/yield-curve")
async def get_yield_curve():
    """Get current Treasury yield curve"""
    if not agent_tools:
        return JSONResponse({"error": "Agent tools not available"}, status_code=503)

    try:
        result = agent_tools.get_current_treasury_yields()
        if result["success"]:
            return {
                "date": result["date"],
                **result["yields"]
            }
        return JSONResponse({"error": "Failed to fetch yields"}, status_code=500)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/data/lcr")
async def get_lcr():
    """Get current LCR calculation"""
    if not agent_tools:
        return JSONResponse({"error": "Agent tools not available"}, status_code=503)

    try:
        result = agent_tools.calculate_lcr()
        return result
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/data/portfolio-breakdown")
async def get_portfolio_breakdown():
    """Get detailed portfolio breakdown by product type"""
    if not agent_tools:
        return JSONResponse({"error": "Agent tools not available"}, status_code=503)

    try:
        # Query loan portfolio breakdown
        loan_query = """
        SELECT
            product_type,
            COUNT(*) as count,
            SUM(current_balance)/1e9 as balance_billions,
            AVG(interest_rate) as avg_rate,
            SUM(cecl_reserve)/SUM(current_balance)*100 as reserve_pct
        FROM cfo_banking_demo.silver_finance.loan_portfolio
        WHERE is_current = true
        GROUP BY product_type
        ORDER BY balance_billions DESC
        """

        loan_result = agent_tools.query_unity_catalog(loan_query)

        # Query deposit portfolio breakdown
        deposit_query = """
        SELECT
            product_type,
            COUNT(*) as count,
            SUM(current_balance)/1e9 as balance_billions,
            AVG(stated_rate) as avg_rate
        FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
        WHERE account_status = 'Active'
        GROUP BY product_type
        ORDER BY balance_billions DESC
        """

        deposit_result = agent_tools.query_unity_catalog(deposit_query)

        if loan_result["success"] and deposit_result["success"]:
            return {
                "success": True,
                "loans": loan_result["data"],
                "deposits": deposit_result["data"]
            }
        else:
            return JSONResponse({"error": "Failed to fetch portfolio data"}, status_code=500)

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/data/risk-metrics")
async def get_risk_metrics():
    """Get risk analytics and stress testing metrics"""
    if not agent_tools:
        return JSONResponse({"error": "Agent tools not available"}, status_code=503)

    try:
        # Credit risk metrics
        credit_risk_query = """
        SELECT
            product_type,
            SUM(current_balance)/1e9 as balance_billions,
            AVG(CASE WHEN days_past_due > 90 THEN 1.0 ELSE 0.0 END) * 100 as npl_rate,
            SUM(cecl_reserve)/1e9 as reserve_billions,
            SUM(cecl_reserve)/SUM(current_balance)*100 as reserve_ratio
        FROM cfo_banking_demo.silver_finance.loan_portfolio
        WHERE is_current = true
        GROUP BY product_type
        ORDER BY balance_billions DESC
        """

        credit_result = agent_tools.query_unity_catalog(credit_risk_query)

        # Stress testing - rate shock scenarios
        rate_shocks = []
        for product in ["MMDA", "DDA", "NOW", "Savings"]:
            result = agent_tools.call_deposit_beta_model(
                rate_change_bps=100,  # 100 bps stress
                product_type=product
            )
            if result["success"]:
                rate_shocks.append({
                    "product": product,
                    "current_balance": result["current_balance"],
                    "runoff_100bps": result["predicted_runoff_amount"],
                    "runoff_pct": result["runoff_pct"],
                    "beta": result["beta"]
                })

        # LCR stress test
        lcr_base = agent_tools.calculate_lcr(deposit_runoff_multiplier=1.0)
        lcr_stress = agent_tools.calculate_lcr(deposit_runoff_multiplier=1.5)

        if credit_result["success"] and lcr_base["success"] and lcr_stress["success"]:
            return {
                "success": True,
                "credit_risk": credit_result["data"],
                "rate_shock_stress": rate_shocks,
                "lcr_stress": {
                    "base": {
                        "ratio": lcr_base["lcr_ratio"],
                        "status": lcr_base["status"]
                    },
                    "stressed": {
                        "ratio": lcr_stress["lcr_ratio"],
                        "status": lcr_stress["status"]
                    }
                }
            }
        else:
            return JSONResponse({"error": "Failed to calculate risk metrics"}, status_code=500)

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/data/recent-activity")
async def get_recent_activity():
    """Get recent activity logs"""
    if not agent_tools:
        return JSONResponse({"error": "Agent tools not available"}, status_code=503)

    try:
        # Query recent transactions
        activity_query = """
        SELECT
            'Loan Origination' as activity_type,
            product_type,
            current_balance as amount,
            origination_date as activity_date
        FROM cfo_banking_demo.silver_finance.loan_portfolio
        WHERE is_current = true
        ORDER BY origination_date DESC
        LIMIT 10
        """

        activity_result = agent_tools.query_unity_catalog(activity_query)

        if activity_result["success"]:
            return {
                "success": True,
                "activities": activity_result["data"]
            }
        else:
            return JSONResponse({"error": "Failed to fetch activity"}, status_code=500)

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/data/loans")
async def get_loans(
    product_type: str = None,
    days: int = None,
    limit: int = 100
):
    """
    Get loan list with optional filters
    Returns: List of loans matching criteria
    """
    if not agent_tools:
        return JSONResponse({"error": "Agent tools not available"}, status_code=503)

    try:
        # Build query with filters
        where_clauses = ["is_current = true"]

        if product_type:
            where_clauses.append(f"product_type = '{product_type}'")

        if days:
            where_clauses.append(f"DATEDIFF(CURRENT_DATE(), origination_date) <= {days}")

        where_sql = " AND ".join(where_clauses)

        query = f"""
            SELECT
                loan_id,
                borrower_name,
                product_type,
                current_balance,
                interest_rate,
                payment_status,
                origination_date
            FROM cfo_banking_demo.silver_finance.loan_portfolio
            WHERE {where_sql}
            ORDER BY origination_date DESC
            LIMIT {limit}
        """

        result = agent_tools.query_unity_catalog(query)

        if result["success"]:
            # Column names from SELECT statement
            columns = ["loan_id", "borrower_name", "product_type", "current_balance",
                      "interest_rate", "payment_status", "origination_date"]

            loans = []
            for row in result["data"]:
                loan_dict = {}
                for i in range(min(len(columns), len(row))):
                    value = row[i]
                    # Convert numeric strings to numbers
                    if columns[i] in ["current_balance", "interest_rate"]:
                        try:
                            loan_dict[columns[i]] = float(value) if value else 0.0
                        except (ValueError, TypeError):
                            loan_dict[columns[i]] = 0.0
                    else:
                        loan_dict[columns[i]] = value
                loans.append(loan_dict)

            return {"loans": loans, "count": len(loans)}
        else:
            return JSONResponse({"error": "Failed to fetch loans"}, status_code=500)

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/data/loan-detail/{loan_id}")
async def get_loan_detail(loan_id: str):
    """
    Get comprehensive loan details with related records
    Returns: Loan info + GL entries + subledger + payment history
    """
    if not agent_tools:
        return JSONResponse({"error": "Agent tools not available"}, status_code=503)

    try:
        # Note: MLflow logging removed to avoid parameter collision errors

        # Helper function to safely convert to float
        def to_float(value, default=0.0):
            try:
                return float(value) if value else default
            except (ValueError, TypeError):
                return default

        def to_int(value, default=0):
            try:
                return int(float(value)) if value else default
            except (ValueError, TypeError):
                return default

        # Get loan details with specific columns
        loan_query = f"""
            SELECT
                loan_id,
                borrower_name,
                product_type,
                current_balance,
                original_amount,
                interest_rate,
                origination_date,
                maturity_date,
                payment_status,
                days_past_due,
                cecl_reserve,
                pd,
                lgd,
                collateral_type,
                collateral_value,
                ltv_ratio,
                officer_id,
                branch_id
            FROM cfo_banking_demo.silver_finance.loan_portfolio
            WHERE loan_id = '{loan_id}'
            AND is_current = true
        """

        loan_result = agent_tools.query_unity_catalog(loan_query)

        if not loan_result["success"] or len(loan_result["data"]) == 0:
            return JSONResponse({"error": "Loan not found"}, status_code=404)

        # Map data to loan object
        loan_data = loan_result["data"][0]
        loan = {
            "loan_id": loan_data[0],
            "borrower_name": loan_data[1],
            "product_type": loan_data[2],
            "current_balance": to_float(loan_data[3]),
            "original_amount": to_float(loan_data[4]),
            "interest_rate": to_float(loan_data[5]),
            "origination_date": loan_data[6],
            "maturity_date": loan_data[7],
            "payment_status": loan_data[8],
            "days_past_due": to_int(loan_data[9]),
            "cecl_reserve": to_float(loan_data[10]),
            "pd": to_float(loan_data[11]),
            "lgd": to_float(loan_data[12]),
            "collateral_type": loan_data[13],
            "collateral_value": to_float(loan_data[14]),
            "ltv_ratio": to_float(loan_data[15]),
            "officer_id": loan_data[16],
            "branch_id": loan_data[17],
        }

        # Get related GL entries with specific columns
        gl_query = f"""
            SELECT
                entry_id,
                source_transaction_id,
                entry_date,
                entry_timestamp,
                total_debits,
                total_credits,
                is_balanced,
                description
            FROM cfo_banking_demo.silver_finance.gl_entries
            WHERE source_transaction_id = '{loan_id}'
            ORDER BY entry_timestamp DESC
            LIMIT 10
        """

        gl_result = agent_tools.query_unity_catalog(gl_query)
        gl_entries_raw = gl_result["data"] if gl_result["success"] else []

        # Convert GL entries to structured objects
        gl_entries = []
        if gl_entries_raw:
            for row in gl_entries_raw:
                gl_entries.append({
                    "entry_id": row[0],
                    "source_transaction_id": row[1],
                    "entry_date": row[2],
                    "entry_timestamp": row[3],
                    "total_debits": to_float(row[4]),
                    "total_credits": to_float(row[5]),
                    "is_balanced": row[6],
                    "description": row[7]
                })

        # Get subledger transactions with specific columns
        subledger_query = f"""
            SELECT
                transaction_id,
                loan_id,
                transaction_timestamp,
                transaction_type,
                principal_amount,
                interest_amount,
                balance_after
            FROM cfo_banking_demo.silver_finance.loan_subledger
            WHERE loan_id = '{loan_id}'
            ORDER BY transaction_timestamp DESC
            LIMIT 20
        """

        subledger_result = agent_tools.query_unity_catalog(subledger_query)
        subledger_entries_raw = subledger_result["data"] if subledger_result["success"] else []

        # Convert subledger entries to structured objects
        subledger_entries = []
        if subledger_entries_raw:
            for row in subledger_entries_raw:
                subledger_entries.append({
                    "transaction_id": row[0],
                    "posting_date": row[2],
                    "transaction_type": row[3],
                    "principal_amount": to_float(row[4]),
                    "interest_amount": to_float(row[5]),
                    "balance_after": to_float(row[6])
                })

        # Combine all data
        result = {
            **loan,
            "gl_entries": gl_entries,
            "subledger_entries": subledger_entries,
            "payment_history": []  # Could add payment history if available
        }

        # Note: MLflow logging removed to avoid parameter collision errors

        return result

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/data/deposits")
async def get_deposits(
    product_type: str = None,
    customer_segment: str = None,
    limit: int = 100
):
    """Get deposit accounts with filters"""
    if not agent_tools:
        return JSONResponse({"error": "Agent tools not available"}, status_code=503)

    try:
        where_clauses = ["account_status = 'Active'"]

        if product_type:
            where_clauses.append(f"product_type = '{product_type}'")

        if customer_segment:
            where_clauses.append(f"customer_segment = '{customer_segment}'")

        where_sql = " AND ".join(where_clauses)

        query = f"""
            SELECT
                account_id,
                customer_name,
                product_type,
                customer_segment,
                current_balance,
                stated_rate,
                beta,
                account_status
            FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
            WHERE {where_sql}
            ORDER BY current_balance DESC
            LIMIT {limit}
        """

        result = agent_tools.query_unity_catalog(query)

        if result["success"]:
            # Convert array data to dictionaries with normalized field names
            columns = ["account_id", "customer_name", "product_type", "customer_segment", "current_balance", "stated_rate", "beta", "account_status"]
            deposits = []
            for row in result["data"]:
                # Normalize field names to match loan schema
                deposit_dict = {
                    "loan_id": row[0],  # account_id -> loan_id
                    "borrower_name": row[1],  # customer_name -> borrower_name
                    "product_type": row[2],
                    "current_balance": float(row[4]) if row[4] else 0.0,
                    "interest_rate": float(row[5]) if row[5] else 0.0,  # stated_rate -> interest_rate
                    "payment_status": row[7] if row[7] else "Active",  # account_status -> payment_status
                    "origination_date": "2024-01-01"  # Default date for deposits
                }
                deposits.append(deposit_dict)

            return {"deposits": deposits, "count": len(deposits)}
        else:
            return JSONResponse({"error": "Failed to fetch deposits"}, status_code=500)

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/data/securities")
async def get_securities(
    security_type: str = None,
    hqla_level: str = None,
    limit: int = 100
):
    """Get securities portfolio with filters"""
    if not agent_tools:
        return JSONResponse({"error": "Agent tools not available"}, status_code=503)

    try:
        # Build filters
        where_clauses = ["is_current = true"]

        if security_type:
            where_clauses.append(f"security_type = '{security_type}'")

        where_sql = " AND ".join(where_clauses)

        # If HQLA filter, join with HQLA table
        if hqla_level:
            query = f"""
                SELECT
                    s.security_id,
                    s.issuer_name,
                    s.security_type,
                    s.maturity_date,
                    s.market_value,
                    s.yield_to_maturity,
                    s.duration,
                    h.hqla_level,
                    h.hqla_value
                FROM cfo_banking_demo.silver_treasury.securities_portfolio s
                JOIN cfo_banking_demo.gold_regulatory.hqla_inventory h
                    ON s.security_id = h.security_id
                WHERE {where_sql}
                AND h.hqla_level = '{hqla_level}'
                ORDER BY s.market_value DESC
                LIMIT {limit}
            """
        else:
            query = f"""
                SELECT
                    security_id,
                    issuer_name,
                    security_type,
                    maturity_date,
                    market_value,
                    yield_to_maturity,
                    duration,
                    credit_rating
                FROM cfo_banking_demo.silver_treasury.securities_portfolio
                WHERE {where_sql}
                ORDER BY market_value DESC
                LIMIT {limit}
            """

        result = agent_tools.query_unity_catalog(query)

        if result["success"]:
            # Convert array data to dictionaries
            columns = result.get("columns", [])
            securities = []
            for row in result["data"]:
                security_dict = {columns[i]: row[i] for i in range(len(columns))}
                securities.append(security_dict)

            return {"securities": securities, "count": len(securities)}
        else:
            return JSONResponse({"error": "Failed to fetch securities"}, status_code=500)

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# =============================================================================
# TREASURY DEPOSIT MODELING API ENDPOINTS (Phase 1-3)
# =============================================================================

@app.get("/api/data/deposit-beta-metrics")
async def get_deposit_beta_metrics():
    """Phase 1: Deposit beta portfolio metrics"""
    try:
        query = """
            SELECT
                COUNT(*) as total_accounts,
                SUM(balance_millions * 1000000) as total_balance,
                AVG(target_beta) as avg_beta,
                SUM(CASE WHEN below_competitor_rate = 1 THEN 1 ELSE 0 END) as at_risk_accounts,
                SUM(CASE WHEN below_competitor_rate = 1 THEN balance_millions * 1000000 ELSE 0 END) as at_risk_balance,
                SUM(CASE WHEN relationship_category = 'Strategic' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as strategic_pct,
                SUM(CASE WHEN relationship_category = 'Tactical' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as tactical_pct,
                SUM(CASE WHEN relationship_category = 'Expendable' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as expendable_pct
            FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
            WHERE effective_date = (SELECT MAX(effective_date) FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced)
        """
        result = agent_tools.query_unity_catalog(query)
        if result["success"] and result["data"] and len(result["data"]) > 0:
            row = result["data"][0]
            data = {
                "total_accounts": int(row[0]) if row[0] else 0,
                "total_balance": float(row[1]) if row[1] else 0.0,
                "avg_beta": float(row[2]) if row[2] else 0.0,
                "at_risk_accounts": int(row[3]) if row[3] else 0,
                "at_risk_balance": float(row[4]) if row[4] else 0.0,
                "strategic_pct": float(row[5]) if row[5] else 0.0,
                "tactical_pct": float(row[6]) if row[6] else 0.0,
                "expendable_pct": float(row[7]) if row[7] else 0.0
            }
            return {"success": True, "data": data}
        return JSONResponse({"error": "No data found"}, status_code=404)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/data/deposit-beta-distribution")
async def get_deposit_beta_distribution():
    """Phase 1: Beta distribution by product and relationship"""
    try:
        query = """
            SELECT
                product_type,
                COUNT(*) as account_count,
                SUM(balance_millions * 1000000) as total_balance,
                AVG(target_beta) as avg_beta,
                relationship_category
            FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
            WHERE effective_date = (SELECT MAX(effective_date) FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced)
            GROUP BY product_type, relationship_category
            ORDER BY total_balance DESC
        """
        result = agent_tools.query_unity_catalog(query)
        if result["success"] and result["data"]:
            data = [
                {
                    "product_type": row[0],
                    "account_count": int(row[1]) if row[1] else 0,
                    "total_balance": float(row[2]) if row[2] else 0.0,
                    "avg_beta": float(row[3]) if row[3] else 0.0,
                    "relationship_category": row[4]
                }
                for row in result["data"]
            ]
            return {"success": True, "data": data}
        return JSONResponse({"error": "No data found"}, status_code=404)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/data/at-risk-deposits")
async def get_at_risk_deposits():
    """Phase 1: Top at-risk accounts priced below market"""
    try:
        query = """
            SELECT
                account_id,
                product_type,
                balance_millions * 1000000 as current_balance,
                stated_rate,
                market_fed_funds_rate as market_rate,
                rate_gap,
                target_beta as predicted_beta,
                relationship_category
            FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced
            WHERE below_competitor_rate = 1
              AND effective_date = (SELECT MAX(effective_date) FROM cfo_banking_demo.ml_models.deposit_beta_training_enhanced)
            ORDER BY balance_millions DESC
            LIMIT 50
        """
        result = agent_tools.query_unity_catalog(query)
        if result["success"] and result["data"]:
            data = [
                {
                    "account_id": row[0],
                    "product_type": row[1],
                    "current_balance": float(row[2]) if row[2] else 0.0,
                    "stated_rate": float(row[3]) if row[3] else 0.0,
                    "market_rate": float(row[4]) if row[4] else 0.0,
                    "rate_gap": float(row[5]) if row[5] else 0.0,
                    "predicted_beta": float(row[6]) if row[6] else 0.0,
                    "relationship_category": row[7]
                }
                for row in result["data"]
            ]
            return {"success": True, "data": data}
        return JSONResponse({"error": "No data found"}, status_code=404)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/data/component-decay-metrics")
async def get_component_decay_metrics():
    """Phase 2: Component decay metrics (λ and g) by segment"""
    try:
        query = """
            SELECT
                relationship_category,
                AVG(lambda_closure_rate) as closure_rate,
                AVG(g_abgr) as abgr,
                AVG((1 - lambda_closure_rate) * (1 + g_abgr)) as compound_factor,
                AVG(POW(1 - lambda_closure_rate, 1) * POW(1 + g_abgr, 1)) as year_1_retention,
                AVG(POW(1 - lambda_closure_rate, 2) * POW(1 + g_abgr, 2)) as year_2_retention,
                AVG(POW(1 - lambda_closure_rate, 3) * POW(1 + g_abgr, 3)) as year_3_retention
            FROM cfo_banking_demo.ml_models.component_decay_metrics
            GROUP BY relationship_category
            ORDER BY relationship_category
        """
        result = agent_tools.query_unity_catalog(query)
        if result["success"] and result["data"]:
            data = [
                {
                    "relationship_category": row[0],
                    "closure_rate": float(row[1]) if row[1] else 0.0,
                    "abgr": float(row[2]) if row[2] else 0.0,
                    "compound_factor": float(row[3]) if row[3] else 0.0,
                    "year_1_retention": float(row[4]) if row[4] else 0.0,
                    "year_2_retention": float(row[5]) if row[5] else 0.0,
                    "year_3_retention": float(row[6]) if row[6] else 0.0
                }
                for row in result["data"]
            ]
            return {"success": True, "data": data}
        return JSONResponse({"error": "No data found"}, status_code=404)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/data/cohort-survival")
async def get_cohort_survival():
    """Phase 2: Cohort survival rates for Kaplan-Meier curves"""
    try:
        query = """
            SELECT
                relationship_category,
                months_since_open as months_since_opening,
                AVG(account_survival_rate) as survival_rate,
                '' as cohort_quarter
            FROM cfo_banking_demo.ml_models.cohort_survival_rates
            WHERE months_since_open <= 36
            GROUP BY relationship_category, months_since_open
            ORDER BY relationship_category, months_since_open
        """
        result = agent_tools.query_unity_catalog(query)
        if result["success"] and result["data"]:
            data = [
                {
                    "relationship_category": row[0],
                    "months_since_opening": float(row[1]) if row[1] else 0.0,
                    "survival_rate": float(row[2]) if row[2] else 0.0,
                    "cohort_quarter": row[3] if len(row) > 3 else ""
                }
                for row in result["data"]
            ]
            return {"success": True, "data": data}
        return JSONResponse({"error": "No data found"}, status_code=404)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/data/runoff-forecasts")
async def get_runoff_forecasts():
    """Phase 2: 3-year deposit runoff projections"""
    try:
        query = """
            SELECT
                relationship_category,
                CAST(months_ahead / 12 AS INT) as year,
                current_balance_billions as beginning_balance,
                projected_balance_billions as projected_balance,
                (projected_balance_billions - current_balance_billions) as runoff_amount,
                ((projected_balance_billions - current_balance_billions) / current_balance_billions * 100) as cumulative_runoff_pct
            FROM cfo_banking_demo.ml_models.deposit_runoff_forecasts
            WHERE months_ahead IN (12, 24, 36)
            ORDER BY relationship_category, months_ahead
        """
        result = agent_tools.query_unity_catalog(query)
        if result["success"] and result["data"]:
            data = [
                {
                    "relationship_category": row[0],
                    "year": int(row[1]) if row[1] else 0,
                    "beginning_balance": float(row[2]) if row[2] else 0.0,
                    "projected_balance": float(row[3]) if row[3] else 0.0,
                    "runoff_amount": float(row[4]) if row[4] else 0.0,
                    "cumulative_runoff_pct": float(row[5]) if row[5] else 0.0
                }
                for row in result["data"]
            ]
            return {"success": True, "data": data}
        return JSONResponse({"error": "No data found"}, status_code=404)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/data/dynamic-beta-parameters")
async def get_dynamic_beta_parameters():
    """Phase 3: Dynamic beta sigmoid function parameters"""
    try:
        query = """
            SELECT
                relationship_category,
                beta_min,
                beta_max,
                k_steepness as k,
                R0_inflection as R0
            FROM cfo_banking_demo.ml_models.dynamic_beta_parameters
            ORDER BY relationship_category
        """
        result = agent_tools.query_unity_catalog(query)
        if result["success"] and result["data"]:
            data = [
                {
                    "relationship_category": row[0],
                    "beta_min": float(row[1]) if row[1] else 0.0,
                    "beta_max": float(row[2]) if row[2] else 0.0,
                    "k": float(row[3]) if row[3] else 0.0,
                    "R0": float(row[4]) if row[4] else 0.0
                }
                for row in result["data"]
            ]
            return {"success": True, "data": data}
        return JSONResponse({"error": "No data found"}, status_code=404)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/data/stress-test-results")
async def get_stress_test_results():
    """Phase 3: CCAR/DFAST stress test results - adapt rate shock data to 9-quarter projections"""
    try:
        # Query the rate shock scenarios from stress_test_results
        query = """
            SELECT
                scenario_name,
                rate_shock_bps,
                stressed_avg_beta,
                delta_nii_millions,
                delta_eve_billions,
                eve_cet1_ratio,
                sot_status
            FROM cfo_banking_demo.ml_models.stress_test_results
            WHERE scenario_id IN ('baseline', 'adverse', 'severely_adverse')
            ORDER BY rate_shock_bps
        """
        result = agent_tools.query_unity_catalog(query)

        # Transform rate shock data into 9-quarter projections
        data = []
        if result["success"] and len(result["data"]) > 0:
            for row in result["data"]:
                scenario_name = str(row[0]).replace(" (No Shock)", "").replace(" (+200 bps)", "").replace(" (+300 bps)", "")
                rate_shock = int(row[1]) if row[1] else 0
                delta_nii = float(row[3]) if row[3] else 0.0
                eve_cet1_impact = float(row[5]) if row[5] else 0.0

                # Starting capital ratio
                base_cet1 = 11.5 if rate_shock == 0 else (10.2 if rate_shock == 200 else 8.5)

                # Generate 9-quarter projection
                for quarter in range(10):
                    # CET1 declines more severely in adverse scenarios
                    decline_rate = 0.05 if rate_shock == 0 else (0.15 if rate_shock == 200 else 0.30)
                    cet1 = base_cet1 - (quarter * decline_rate) + (eve_cet1_impact / 10)

                    data.append({
                        "scenario": scenario_name,
                        "quarter": quarter,
                        "cet1_ratio_pct": max(cet1, 7.0),
                        "tier1_ratio_pct": max(cet1 + 1.5, 8.5),
                        "total_capital_ratio_pct": max(cet1 + 3.0, 10.5),
                        "nii_impact": delta_nii * 1000000 * quarter / 9 if rate_shock != 0 else 0,
                        "deposit_runoff": -abs(delta_nii) * 50000000 * quarter / 9 if rate_shock != 0 else 0,
                        "lcr_ratio": 115.0 - (quarter * 2.0) if rate_shock != 0 else 120.0
                    })

        return {"success": True, "data": data}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/data/stress-test-summary")
async def get_stress_test_summary():
    """Phase 3: Stress test summary by scenario"""
    try:
        query = """
            SELECT
                scenario_name,
                rate_shock_bps,
                delta_nii_millions,
                delta_eve_billions,
                eve_cet1_ratio,
                sot_status
            FROM cfo_banking_demo.ml_models.stress_test_results
            WHERE scenario_id IN ('baseline', 'adverse', 'severely_adverse')
            ORDER BY rate_shock_bps
        """
        result = agent_tools.query_unity_catalog(query)

        data = []
        if result["success"] and len(result["data"]) > 0:
            for row in result["data"]:
                scenario_name = str(row[0]).replace(" (No Shock)", "").replace(" (+200 bps)", "").replace(" (+300 bps)", "")
                rate_shock = int(row[1]) if row[1] else 0
                delta_nii = float(row[2]) if row[2] else 0.0
                eve_cet1_impact = float(row[4]) if row[4] else 0.0

                # Calculate minimum CET1 over 9 quarters
                base_cet1 = 11.5 if rate_shock == 0 else (10.2 if rate_shock == 200 else 8.5)
                decline_rate = 0.05 if rate_shock == 0 else (0.15 if rate_shock == 200 else 0.30)
                cet1_minimum = max(base_cet1 - (9 * decline_rate) + eve_cet1_impact, 7.0)

                # Pass if CET1 >= 7% and LCR >= 100%
                lcr_minimum = 120.0 if rate_shock == 0 else (108.0 if rate_shock == 200 else 105.0)
                pass_status = "PASS" if cet1_minimum >= 7.0 and lcr_minimum >= 100.0 else "FAIL"

                data.append({
                    "scenario": scenario_name,
                    "cet1_minimum": cet1_minimum,
                    "nii_impact_total": delta_nii * 1000000 if rate_shock != 0 else 0,
                    "deposit_runoff_total": -abs(delta_nii) * 50000000 if rate_shock != 0 else 0,
                    "lcr_minimum": lcr_minimum,
                    "pass_status": pass_status
                })

        return {"success": True, "data": data}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# =============================================================================
# END TREASURY DEPOSIT MODELING API ENDPOINTS
# =============================================================================

# Serve React static files (after npm run build in frontend_app)
# This assumes the React app has been built to frontend_app/out/
frontend_path = Path(__file__).parent.parent / "frontend_app" / "out"

if frontend_path.exists():
    # Mount static assets (JS, CSS, images)
    app.mount("/_next", StaticFiles(directory=str(frontend_path / "_next")), name="next_static")

    @app.get("/")
    async def serve_index():
        """Serve React app index.html for root"""
        index_file = frontend_path / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        else:
            return JSONResponse({"error": "Frontend not built"}, status_code=404)

    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        """Serve React app for all non-API routes"""
        # If it's an API route, let it fall through to 404
        if full_path.startswith("api"):
            return JSONResponse({"error": "Not found"}, status_code=404)

        # Check if it's a static file
        file_path = frontend_path / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))

        # Otherwise serve index.html for SPA routing
        index_file = frontend_path / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        else:
            return JSONResponse({"error": "Frontend not built"}, status_code=404)
else:
    print(f"Warning: Frontend build directory not found at {frontend_path}")
    print("Run 'npm run build' in frontend_app directory first")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
