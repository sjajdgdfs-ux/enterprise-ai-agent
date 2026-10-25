import os, time, warnings, logging, ast
from typing import TypedDict, Annotated
warnings.filterwarnings("ignore")
os.environ["GRPC_VERBOSITY"] = "ERROR"
logging.getLogger("google_genai").setLevel(logging.ERROR)

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from tracer import AgentTracer

def extract_clean_text(content) -> str:
    if isinstance(content, list):
        parts = [item["text"] for item in content if isinstance(item, dict) and "text" in item]
        return "\n".join(parts) if parts else str(content)
    elif isinstance(content, str):
        if content.startswith("[{'type': 'text'") or content.startswith('[{"type": "text"'):
            try:
                parsed = ast.literal_eval(content)
                if isinstance(parsed, list) and len(parsed) > 0 and "text" in parsed[0]:
                    return parsed[0]["text"]
            except Exception:
                pass
        return content
    return str(content)

MOCK_PAYMENTS_DB = {
    "user_101": {"has_paid_subscription": True, "amount": 150.0, "plan": "Enterprise Tier", "status": "PAID"},
    "user_102": {"has_paid_subscription": False, "amount": 0.0, "plan": "Free Tier", "status": "UNPAID"},
    "user_1022": {"has_paid_subscription": True, "amount": 150.0, "plan": "Enterprise Tier", "status": "PAID"}
}

class SystemState(TypedDict):
    messages: Annotated[list, add_messages]
    intent: str
    requires_approval: bool
    final_response: str

api_key = os.getenv("GEMINI_API_KEY", "")

# Restrict Output Tokens to 1024 for Cost Control and Prevent ReDoS / Exhaustion
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=api_key if api_key else "INVALID_KEY",
    temperature=0.1,
    max_output_tokens=1024
)

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
tracer = AgentTracer(log_file="capstone_traces.jsonl")

async def router_node(state: SystemState):
    start_time = time.time()
    raw_input = state["messages"][-1].content if state["messages"] else "Hello"
    user_msg = extract_clean_text(raw_input)
    tracer.start_trace(user_input=user_msg, agent_name="enterprise_router_agent")
    
    prompt = f"Classify user intent into exactly ONE word: TECHNICAL, BILLING, or GENERAL. Answer with only the category name.\nQuery: {user_msg}"
    response = await llm.ainvoke(prompt)
    intent = extract_clean_text(response.content).strip().upper()
    
    category = "TECHNICAL" if "TECHNICAL" in intent else ("BILLING" if "BILLING" in intent else "GENERAL")
    tracer.log_step("intent_classification", user_msg, category, round(time.time() - start_time, 2))
    return {"intent": category}

async def technical_node(state: SystemState):
    start_time = time.time()
    raw_input = state["messages"][-1].content if state["messages"] else "API key"
    user_msg = extract_clean_text(raw_input)
    
    retrieved_docs = await retriever.ainvoke(user_msg)
    context = "\n".join([d.page_content for d in retrieved_docs])
    
    prompt = f"You are an Enterprise Technical Support Specialist. Answer the question using ONLY the provided knowledge context:\nContext:\n{context}\n\nQuestion: {user_msg}\nAnswer:"
    response = await llm.ainvoke(prompt)
    output = extract_clean_text(response.content)
    
    tracer.log_step("technical_rag_retrieval", user_msg, output, round(time.time() - start_time, 2))
    tracer.end_trace(final_output=output, status="success")
    return {"final_response": output}

async def billing_node(state: SystemState):
    start_time = time.time()
    raw_input = state["messages"][-1].content if state["messages"] else "Billing"
    user_msg = extract_clean_text(raw_input)
    
    prompt_action = f"Classify action into ONE word: REQUEST_NEW_REFUND or GENERAL_INQUIRY.\nUser Message: {user_msg}"
    action_res = await llm.ainvoke(prompt_action)
    action_str = extract_clean_text(action_res.content).strip().upper()
    
    if "REQUEST_NEW_REFUND" in action_str:
        user_id = "user_1022"
        payment_record = MOCK_PAYMENTS_DB.get(user_id, {"has_paid_subscription": False, "status": "UNPAID"})
        if not payment_record["has_paid_subscription"]:
            output = "No active paid transaction found for your account."
            return {"requires_approval": False, "final_response": output}
        if payment_record.get("status") == "REFUNDED":
            output = "A refund for this transaction has already been processed and issued."
            return {"requires_approval": False, "final_response": output}
            
        output = f"Refund request registered for {payment_record['plan']} (${payment_record['amount']}). Requires Manager Approval."
        tracer.log_step("billing_hitl_check", user_msg, "HITL Triggered", round(time.time() - start_time, 2))
        tracer.end_trace(final_output=output, status="approval_pending")
        return {"requires_approval": True, "final_response": output}
        
    prompt = f"You are a Billing Support Agent. Answer the customer query:\nQuery: {user_msg}"
    response = await llm.ainvoke(prompt)
    output = extract_clean_text(response.content)
    tracer.log_step("billing_query_response", user_msg, output, round(time.time() - start_time, 2))
    tracer.end_trace(final_output=output, status="success")
    return {"requires_approval": False, "final_response": output}

async def general_node(state: SystemState):
    start_time = time.time()
    raw_input = state["messages"][-1].content if state["messages"] else "Hello"
    user_msg = extract_clean_text(raw_input)
    
    prompt = f"You are a helpful customer success assistant. Answer politely:\nUser Message: {user_msg}"
    response = await llm.ainvoke(prompt)
    output = extract_clean_text(response.content)
    tracer.log_step("general_llm_response", user_msg, output, round(time.time() - start_time, 2))
    tracer.end_trace(final_output=output, status="success")
    return {"final_response": output}

def route_decision(state: SystemState):
    intent = state.get("intent", "GENERAL")
    return "technical_node" if intent == "TECHNICAL" else ("billing_node" if intent == "BILLING" else "general_node")

builder = StateGraph(SystemState)
builder.add_node("router_node", router_node)
builder.add_node("technical_node", technical_node)
builder.add_node("billing_node", billing_node)
builder.add_node("general_node", general_node)
builder.add_edge(START, "router_node")
builder.add_conditional_edges("router_node", route_decision)
builder.add_edge("technical_node", END)
builder.add_edge("billing_node", END)
builder.add_edge("general_node", END)