import os, warnings, logging
from typing import Optional
from contextlib import asynccontextmanager

warnings.filterwarnings("ignore")
os.environ["GRPC_VERBOSITY"] = "ERROR"
logging.getLogger("google_genai").setLevel(logging.ERROR)

from fastapi import FastAPI, HTTPException, Security, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import aiosqlite

from security import SecurityShield
from graph_agent import builder, MOCK_PAYMENTS_DB, extract_clean_text

# ==========================================
# 1. Environment & Production Settings
# ==========================================
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
BEARER_SECRET_TOKEN = os.getenv("API_AUTH_TOKEN", "enterprise_secret_bearer_token_2025")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:7860,http://127.0.0.1:7860").split(",")

# Toggle /docs dynamically (Disabled in production)
docs_url = None if ENVIRONMENT == "production" else "/docs"
redoc_url = None if ENVIRONMENT == "production" else "/redoc"
openapi_url = None if ENVIRONMENT == "production" else "/openapi.json"

limiter = Limiter(key_func=get_remote_address)
security_bearer = HTTPBearer(auto_error=False)
shield = SecurityShield()

compiled_graph = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global compiled_graph
    async with aiosqlite.connect("checkpoints.sqlite") as conn:
        memory = AsyncSqliteSaver(conn)
        compiled_graph = builder.compile(checkpointer=memory)
        yield

app = FastAPI(
    title="Enterprise Hardened AI Agent API",
    version="4.0.0",
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url,
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ==========================================
# Strict Production Origins Configuration
# ==========================================
ALLOWED_ORIGINS = [
    "https://enterprise-ai-agent-x54egp6faq6wtdgsaccxo8.streamlit.app",
    "http://localhost:7860",
    "http://127.0.0.1:7860",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Authentication Verification Dependency
async def verify_auth_token(credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)):
    # In production, require bearer auth. In dev/testing, allow fallback for ease of access.
    if ENVIRONMENT == "production":
        if not credentials or credentials.credentials != BEARER_SECRET_TOKEN:
            raise HTTPException(status_code=401, detail="Access Denied: Invalid Authorization Bearer Token.")
    return True

# ==========================================
# 2. Schemas
# ==========================================
class SupportQuery(BaseModel):
    user_id: str
    query: str
    optional_url: Optional[str] = Field(default=None, description="Optional URL input for checking")

class QueryResponse(BaseModel):
    user_id: str
    intent: str
    response: str
    requires_approval: bool
    status: str

class ApprovalRequest(BaseModel):
    user_id: str
    action: str
    requestor_role: str

# ==========================================
# 3. Endpoints
# ==========================================
@app.get("/health")
async def health():
    return {"status": "healthy", "environment": ENVIRONMENT, "hardened": True}

@app.post("/support", response_model=QueryResponse)
@limiter.limit("10/minute")  # Rate Limit: 10 calls per minute
async def handle_support_query(
    request: Request,
    req: SupportQuery,
    authenticated: bool = Depends(verify_auth_token)
):
    # SSRF Protection Check
    if req.optional_url and not shield.validate_url_ssrf(req.optional_url):
        logging.warning(f"SECURITY ALERT: SSRF Attack pattern detected from user '{req.user_id}' - URL: {req.optional_url}")
        raise HTTPException(status_code=400, detail="Security Violation: Target URL is restricted.")

    # Prompt Injection Check + Logging
    if shield.check_prompt_injection(req.query):
        logging.warning(f"SECURITY ALERT: Prompt Injection attempt detected from user '{req.user_id}'. Query: {req.query}")
        return QueryResponse(
            user_id=req.user_id,
            intent="SECURITY_BLOCK",
            response="Security Violation: Malicious injection pattern detected and blocked.",
            requires_approval=False,
            status="blocked"
        )

    clean_query = shield.redact_pii(req.query)
    config = {"configurable": {"thread_id": req.user_id}}
    initial_state = {"messages": [HumanMessage(content=clean_query)], "intent": "", "requires_approval": False, "final_response": ""}

    try:
        result = await compiled_graph.ainvoke(initial_state, config=config)
        cleaned_res = extract_clean_text(result.get("final_response", ""))
        return QueryResponse(
            user_id=req.user_id,
            intent=result.get("intent", "UNKNOWN"),
            response=cleaned_res,
            requires_approval=result.get("requires_approval", False),
            status="success"
        )
    except Exception as e:
        logging.error(f"Execution Error for user '{req.user_id}': {str(e)}")
        return QueryResponse(
            user_id=req.user_id,
            intent="SYSTEM_FALLBACK",
            response="Our AI service is experiencing high demand. Please try again shortly.",
            requires_approval=False,
            status="degraded_fallback"
        )

@app.post("/approve")
@limiter.limit("5/minute")
async def handle_approval(
    request: Request,
    req: ApprovalRequest,
    authenticated: bool = Depends(verify_auth_token)
):
    # Strict RBAC Enforcement
    if req.requestor_role != "manager":
        logging.warning(f"SECURITY ALERT: Unauthorized approval attempt by user '{req.user_id}' with role '{req.requestor_role}'.")
        raise HTTPException(status_code=403, detail="Access Denied: Only users with 'manager' role can approve actions.")

    if req.action == "approve":
        if req.user_id in MOCK_PAYMENTS_DB:
            MOCK_PAYMENTS_DB[req.user_id]["status"] = "REFUNDED"
        return {"status": "success", "message": f"APPROVED BY MANAGER: Refund for user '{req.user_id}' executed."}
    else:
        return {"status": "rejected", "message": f"REJECTED BY MANAGER: Refund for user '{req.user_id}' declined."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)