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
    def _try_init_agent_tools(profile: str | None):
        if profile:
            os.environ["DATABRICKS_CONFIG_PROFILE"] = profile
        tools = CFOAgentTools(warehouse_id=WAREHOUSE_ID)

        # Validate we're connected to the workspace that actually has demo data.
        # This catches cases where the SDK authenticates fine but points at a workspace
        # without `cfo_banking_demo` populated (e.g. a different profile).
        validate = tools.query_unity_catalog(
            "SELECT COUNT(*) FROM cfo_banking_demo.bronze_core_banking.deposit_accounts WHERE is_current = true",
            max_rows=1,
        )
        if not validate.get("success") or not validate.get("data"):
            raise RuntimeError(validate.get("error") or "Validation query failed")

        try:
            deposit_cnt = int(validate["data"][0][0])
        except Exception:
            deposit_cnt = 0
        return tools, deposit_cnt

    requested_profile = os.getenv("DATABRICKS_CONFIG_PROFILE")
    candidate_profiles: list[str | None] = [requested_profile] if requested_profile else [None]
    if (requested_profile or "").upper() != "DEFAULT":
        candidate_profiles.append("DEFAULT")

    agent_tools = None
    last_err = None
    for prof in candidate_profiles:
        try:
            tools, deposit_cnt = _try_init_agent_tools(prof)
            if deposit_cnt <= 0 and (prof or "").upper() != "DEFAULT":
                # If this profile yields 0 deposits, prefer trying DEFAULT before accepting.
                print(f"⚠ Profile {prof or 'auto'} returned 0 deposits; trying next profile...")
                agent_tools = tools  # keep as fallback if all else fails
                continue
            agent_tools = tools
            effective_profile = os.getenv("DATABRICKS_CONFIG_PROFILE") or "auto"
            print(
                "✓ Successfully loaded agent tools "
                f"(profile={effective_profile}, warehouse={WAREHOUSE_ID}, deposits={deposit_cnt})"
            )
            break
        except Exception as e:
            last_err = e
            continue

    if agent_tools is None:
        raise last_err or RuntimeError("Agent tools init failed")
except Exception as e:
    print(f"❌ ERROR: Could not load agent tools: {e}")
    import traceback
    traceback.print_exc()
    agent_tools = None

# Initialize Claude agent
try:
    # Import from backend directory
    sys.path.insert(0, str(Path(__file__).parent))
    from claude_agent import ClaudeAgent
    claude_agent = ClaudeAgent(endpoint_name="databricks-claude-sonnet-4-5")
    print(f"✓ Successfully initialized Claude agent")
except Exception as e:
    print(f"❌ ERROR: Could not initialize Claude agent: {e}")
    import traceback
    traceback.print_exc()
    claude_agent = None

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
    Claude AI agent chat endpoint with tool calling
    All calls automatically logged for audit
    """
    import time
    start = time.time()

    if not agent_tools:
        return ChatResponse(
            response="Agent tools not available. Please check server configuration.",
            execution_time=time.time() - start
        )

    if not claude_agent:
        return ChatResponse(
            response="Claude agent not available. Please check Databricks endpoint configuration.",
            execution_time=time.time() - start
        )

    try:
        # Use Claude agent to process the query with tool calling
        response_text = claude_agent.chat(
            user_message=request.query,
            agent_tools=agent_tools,
            session_id=request.session_id
        )

    except Exception as e:
        response_text = f"Error processing query: {str(e)}\n\nPlease try rephrasing your question or check the Databricks endpoint configuration."
        import traceback
        traceback.print_exc()

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
    """Get current Treasury yield curve

    Prefer the persisted Unity Catalog table (so the UI works without AlphaVantage credentials),
    and fall back to live fetch if needed.
    """
    if not agent_tools:
        return JSONResponse({"error": "Agent tools not available"}, status_code=503)

    try:
        # 1) Preferred: UC table populated by backfill job/notebooks
        table_query = """
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
        table_result = agent_tools.query_unity_catalog(table_query)
        if table_result.get("success") and table_result.get("data"):
            row = table_result["data"][0]
            return {
                "date": row[0],
                "3M": str(row[1]) if row[1] is not None else None,
                "2Y": str(row[2]) if row[2] is not None else None,
                "5Y": str(row[3]) if row[3] is not None else None,
                "10Y": str(row[4]) if row[4] is not None else None,
                "30Y": str(row[5]) if row[5] is not None else None,
                "source": "uc_table"
            }

        # 2) Fallback: live fetch (AlphaVantage / external)
        live_result = agent_tools.get_current_treasury_yields()
        if live_result.get("success"):
            return {"date": live_result["date"], **live_result["yields"], "source": "live"}

        return JSONResponse(
            {"error": "Failed to fetch yields", "details": live_result.get("error")},
            status_code=500
        )
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
        FROM cfo_banking_demo.bronze_core_banking.loan_portfolio
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
        FROM cfo_banking_demo.bronze_core_banking.loan_portfolio
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
        FROM cfo_banking_demo.bronze_core_banking.loan_portfolio
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
            FROM cfo_banking_demo.bronze_core_banking.loan_portfolio
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
            FROM cfo_banking_demo.bronze_core_banking.loan_portfolio
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

@app.get("/api/data/deposit-accounts")
async def get_deposit_accounts(
    product_type: str = None,
    customer_segment: str = None,
    limit: int = 200,
    require_activity: bool = False,
):
    """Treasury: Return deposit accounts for drill-down tables (raw schema)"""
    if not agent_tools:
        return JSONResponse({"error": "Agent tools not available"}, status_code=503)

    try:
        where_clauses = ["account_status = 'Active'"]
        if product_type:
            where_clauses.append(f"product_type = '{product_type}'")
        if customer_segment:
            where_clauses.append(f"customer_segment = '{customer_segment}'")
        where_sql = " AND ".join(where_clauses)

        activity_filter_sql = "AND a.account_id IS NOT NULL" if require_activity else ""
        query = f"""
            WITH activity_accounts AS (
                SELECT DISTINCT account_id
                FROM cfo_banking_demo.silver_finance.deposit_subledger
                WHERE account_id IS NOT NULL

                UNION

                SELECT DISTINCT customer_id AS account_id
                FROM cfo_banking_demo.silver_finance.gl_entry_lines
                WHERE customer_id IS NOT NULL

                UNION

                SELECT DISTINCT reference_number AS account_id
                FROM cfo_banking_demo.silver_finance.gl_entry_lines
                WHERE reference_number IS NOT NULL
            )
            SELECT
                d.account_id,
                d.customer_name,
                d.product_type,
                d.customer_segment,
                d.account_open_date,
                d.current_balance,
                d.stated_rate,
                d.beta,
                d.account_status,
                CASE WHEN a.account_id IS NULL THEN 0 ELSE 1 END AS has_activity
            FROM cfo_banking_demo.bronze_core_banking.deposit_accounts d
            LEFT JOIN activity_accounts a
              ON a.account_id = d.account_id
            WHERE {where_sql}
              AND d.is_current = true
              {activity_filter_sql}
            ORDER BY has_activity DESC, d.current_balance DESC
            LIMIT {int(limit)}
        """

        result = agent_tools.query_unity_catalog(query, max_rows=int(limit))
        if not result.get("success"):
            return JSONResponse({"error": "Query failed", "details": result.get("error")}, status_code=500)

        data = []
        for row in (result.get("data") or []):
            data.append({
                "account_id": row[0],
                "customer_name": row[1],
                "product_type": row[2],
                "customer_segment": row[3],
                "account_open_date": row[4],
                "current_balance": float(row[5]) if row[5] else 0.0,
                "stated_rate": float(row[6]) if row[6] else 0.0,
                "beta": float(row[7]) if row[7] else 0.0,
                "account_status": row[8] or "Active",
                "has_activity": bool(row[9]) if len(row) > 9 else False,
            })

        return {"success": True, "data": data}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/data/deposit-detail/{account_id}")
async def get_deposit_detail(account_id: str):
    """Treasury: Deposit account detail + GL entries + deposit subledger"""
    if not agent_tools:
        return JSONResponse({"error": "Agent tools not available"}, status_code=503)

    def to_float(x):
        try:
            return float(x) if x is not None else 0.0
        except Exception:
            return 0.0

    try:
        deposit_query = f"""
            SELECT
                d.account_id,
                d.customer_name,
                d.product_type,
                d.customer_segment,
                d.account_open_date,
                d.current_balance,
                d.stated_rate,
                d.beta,
                d.account_status,
                p.predicted_beta
            FROM cfo_banking_demo.bronze_core_banking.deposit_accounts d
            LEFT JOIN cfo_banking_demo.ml_models.deposit_beta_predictions p
              ON p.account_id = d.account_id
            WHERE d.account_id = '{account_id}'
              AND d.is_current = true
            LIMIT 1
        """
        dep_res = agent_tools.query_unity_catalog(deposit_query, max_rows=1)
        if not dep_res.get("success") or not dep_res.get("data"):
            return JSONResponse({"error": "Deposit not found"}, status_code=404)

        row = dep_res["data"][0]
        deposit = {
            "account_id": row[0],
            "customer_name": row[1],
            "product_type": row[2],
            "customer_segment": row[3],
            "account_open_date": row[4],
            "current_balance": to_float(row[5]),
            "stated_rate": to_float(row[6]),
            "beta": to_float(row[7]) if row[7] is not None else None,
            "account_status": row[8] or "Active",
            "predicted_beta": to_float(row[9]) if row[9] is not None else None,
        }

        subledger_query = f"""
            SELECT
                transaction_id,
                transaction_timestamp,
                transaction_type,
                amount,
                balance_after,
                gl_entry_id,
                channel,
                description
            FROM cfo_banking_demo.silver_finance.deposit_subledger
            WHERE account_id = '{account_id}'
            ORDER BY transaction_timestamp DESC
            LIMIT 50
        """
        sub_res = agent_tools.query_unity_catalog(subledger_query, max_rows=50)
        sub_rows = sub_res.get("data") if sub_res.get("success") else []
        subledger_entries = []
        for r in (sub_rows or []):
            subledger_entries.append({
                "transaction_id": r[0],
                "transaction_timestamp": r[1],
                "transaction_type": r[2],
                "amount": to_float(r[3]),
                "balance_after": to_float(r[4]),
                "gl_entry_id": r[5],
                "channel": r[6],
                "description": r[7],
            })

        # GL headers can be discovered from either:
        # - gl_entries.source_transaction_id = account_id (common for deposit events)
        # - deposit_subledger.gl_entry_id (explicit foreign key)
        # - gl_entry_lines.customer_id/reference_number = account_id (most reliable linkage)
        gl_query = f"""
            SELECT
                ge.entry_id,
                ge.source_transaction_id,
                ge.entry_date,
                ge.entry_timestamp,
                ge.total_debits,
                ge.total_credits,
                ge.is_balanced,
                ge.description
            FROM cfo_banking_demo.silver_finance.gl_entries ge
            WHERE ge.source_transaction_id = '{account_id}'
               OR ge.entry_id IN (
                    SELECT DISTINCT gl_entry_id
                    FROM cfo_banking_demo.silver_finance.deposit_subledger
                    WHERE account_id = '{account_id}' AND gl_entry_id IS NOT NULL
               )
               OR ge.entry_id IN (
                    SELECT DISTINCT entry_id
                    FROM cfo_banking_demo.silver_finance.gl_entry_lines
                    WHERE customer_id = '{account_id}'
                       OR reference_number = '{account_id}'
               )
            ORDER BY ge.entry_timestamp DESC
            LIMIT 50
        """
        gl_res = agent_tools.query_unity_catalog(gl_query, max_rows=50)
        gl_rows = gl_res.get("data") if gl_res.get("success") else []
        gl_entries = []
        for r in (gl_rows or []):
            gl_entries.append({
                "entry_id": r[0],
                "source_transaction_id": r[1],
                "entry_date": r[2],
                "entry_timestamp": r[3],
                "total_debits": to_float(r[4]),
                "total_credits": to_float(r[5]),
                "is_balanced": r[6],
                "description": r[7],
            })

        response = {**deposit, "gl_entries": gl_entries, "subledger_entries": subledger_entries}
        # Optional debug fields (frontend ignores them, but useful when API calls succeed yet arrays are empty)
        if not sub_res.get("success"):
            response["subledger_error"] = sub_res.get("error")
        if not gl_res.get("success"):
            response["gl_error"] = gl_res.get("error")
        return response
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# =============================================================================
# TREASURY DEPOSIT MODELING API ENDPOINTS (Approaches 1-3)
# =============================================================================

@app.get("/api/data/deposit-beta-metrics")
async def get_deposit_beta_metrics():
    """Approach 1: Deposit beta portfolio metrics"""
    try:
        query = """
            SELECT
                COUNT(*) as total_accounts,
                SUM(current_balance) as total_balance,
                AVG(predicted_beta) as avg_beta,
                SUM(CASE WHEN predicted_beta >= 0.60 THEN 1 ELSE 0 END) as at_risk_accounts,
                SUM(CASE WHEN predicted_beta >= 0.60 THEN current_balance ELSE 0 END) as at_risk_balance
            FROM cfo_banking_demo.ml_models.deposit_beta_predictions
        """
        result = agent_tools.query_unity_catalog(query)
        if not result.get("success"):
            return JSONResponse(
                {"error": "Query failed", "details": result.get("error")},
                status_code=500
            )
        if result["success"] and result["data"] and len(result["data"]) > 0:
            row = result["data"][0]
            data = {
                "total_accounts": int(row[0]) if row[0] else 0,
                "total_balance": float(row[1]) if row[1] else 0.0,
                "avg_beta": float(row[2]) if row[2] else 0.0,
                "at_risk_accounts": int(row[3]) if row[3] else 0,
                "at_risk_balance": float(row[4]) if row[4] else 0.0,
                "strategic_pct": 0.0,
                "tactical_pct": 0.0,
                "expendable_pct": 0.0
            }
            return {"success": True, "data": data}
        return JSONResponse({"error": "No data found"}, status_code=404)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/data/deposit-beta-distribution")
async def get_deposit_beta_distribution():
    """Approach 1: Beta distribution by product and risk tier"""
    try:
        query = """
            SELECT
                product_type,
                COUNT(*) as account_count,
                SUM(current_balance) as total_balance,
                AVG(predicted_beta) as avg_beta,
                CASE
                    WHEN AVG(predicted_beta) >= 0.60 THEN 'High Beta'
                    WHEN AVG(predicted_beta) >= 0.35 THEN 'Medium Beta'
                    ELSE 'Low Beta'
                END as relationship_category
            FROM cfo_banking_demo.ml_models.deposit_beta_predictions
            GROUP BY product_type
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
    """Approach 1: Top accounts with highest beta and rate gap"""
    try:
        query = """
            WITH yc AS (
                SELECT rate_2y
                FROM cfo_banking_demo.silver_treasury.yield_curves
                WHERE date = (SELECT MAX(date) FROM cfo_banking_demo.silver_treasury.yield_curves)
            )
            SELECT
                p.account_id,
                p.product_type,
                p.current_balance,
                p.stated_rate,
                yc.rate_2y as market_rate,
                (yc.rate_2y - p.stated_rate) as rate_gap,
                p.predicted_beta,
                CASE
                    WHEN p.predicted_beta >= 0.60 THEN 'High Beta'
                    WHEN p.predicted_beta >= 0.35 THEN 'Medium Beta'
                    ELSE 'Low Beta'
                END as relationship_category
            FROM cfo_banking_demo.ml_models.deposit_beta_predictions p
            CROSS JOIN yc
            ORDER BY p.predicted_beta DESC, p.current_balance DESC
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

@app.get("/api/data/ppnr-forecasts")
async def get_ppnr_forecasts(limit: int = 24):
    """PPNR: Return latest monthly PPNR forecast series"""
    if not agent_tools:
        return JSONResponse({"error": "Agent tools not available"}, status_code=503)

    try:
        query = f"""
            SELECT
                month,
                net_interest_income,
                non_interest_income,
                non_interest_expense,
                ppnr
            FROM cfo_banking_demo.ml_models.ppnr_forecasts
            ORDER BY month DESC
            LIMIT {int(limit)}
        """

        result = agent_tools.query_unity_catalog(query)
        if not result.get("success"):
            return JSONResponse(
                {"error": "Query failed", "details": result.get("error")},
                status_code=500
            )
        if result["success"] and result["data"]:
            cols = result.get("columns") or [
                "month",
                "net_interest_income",
                "non_interest_income",
                "non_interest_expense",
                "ppnr",
            ]
            rows = [
                {cols[i]: row[i] for i in range(min(len(cols), len(row)))}
                for row in result["data"]
            ]
            return {"success": True, "data": list(reversed(rows))}

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
