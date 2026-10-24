import os, warnings, logging
from contextlib import asynccontextmanager
warnings.filterwarnings("ignore")
os.environ["GRPC_VERBOSITY"] = "ERROR"
logging.getLogger("google_genai").setLevel(logging.ERROR)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import aiosqlite

from security import SecurityShield
from graph_agent import builder, MOCK_PAYMENTS_DB, extract_clean_text

compiled_graph = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global compiled_graph
    async with aiosqlite.connect("checkpoints.sqlite") as conn:
        memory = AsyncSqliteSaver(conn)
        compiled_graph = builder.compile(checkpointer=memory)
        yield

app = FastAPI(title="Enterprise Support AI Agent API", version="3.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
shield = SecurityShield()

class SupportQuery(BaseModel):
    user_id: str
    query: str

class QueryResponse(BaseModel):
    user_id: str
    intent: str
    response: str
    requires_approval: bool
    status: str = "success"

class ApprovalRequest(BaseModel):
    user_id: str
    action: str
    requestor_role: str

class ApprovalResponse(BaseModel):
    status: str
    message: str

@app.get("/")
async def health():
    return {"status": "healthy", "system": "Enterprise Support Agent System", "version": "3.0.0"}

@app.post("/support", response_model=QueryResponse)
async def handle_support_query(req: SupportQuery):
    if shield.check_prompt_injection(req.query):
        return QueryResponse(
            user_id=req.user_id,
            intent="SECURITY_BLOCK",
            response="Security Violation: Malicious injection pattern detected.",
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
        import traceback
        print("\n" + "="*50)
        print("❌ DETAILED EXECUTION ERROR:")
        traceback.print_exc()
        print("="*50 + "\n")
        return QueryResponse(
            user_id=req.user_id,
            intent="SYSTEM_FALLBACK",
            response="Our AI service is experiencing high demand. Please try again shortly.",
            requires_approval=False,
            status="degraded_fallback"
        )

@app.post("/approve", response_model=ApprovalResponse)
async def handle_approval(req: ApprovalRequest):
    if req.requestor_role != "manager":
        raise HTTPException(status_code=403, detail="Access Denied: Only users with 'manager' role can approve actions.")
    if req.action == "approve":
        if req.user_id in MOCK_PAYMENTS_DB:
            MOCK_PAYMENTS_DB[req.user_id]["status"] = "REFUNDED"
        return ApprovalResponse(status="success", message=f"APPROVED BY MANAGER: Refund for user '{req.user_id}' executed.")
    else:
        return ApprovalResponse(status="rejected", message=f"REJECTED BY MANAGER: Refund for user '{req.user_id}' declined.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)