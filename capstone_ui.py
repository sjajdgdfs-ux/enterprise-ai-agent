import os
import asyncio
import streamlit as st
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from security import SecurityShield
from graph_agent import builder, MOCK_PAYMENTS_DB, extract_clean_text
from build_kb import build_knowledge_base

# Suppress verbose logs
os.environ["GRPC_VERBOSITY"] = "ERROR"

st.set_page_config(page_title="Enterprise AI Support Agent", layout="wide")
st.title("🛡️ Enterprise AI Support & Operations Portal")

# Initialize Security and LangGraph Engine in Session State
if "shield" not in st.session_state:
    st.session_state.shield = SecurityShield()

if "compiled_graph" not in st.session_state:
    if not os.path.exists("./chroma_db"):
        build_knowledge_base()
    
    memory = MemorySaver()
    st.session_state.compiled_graph = builder.compile(checkpointer=memory)

# ==========================================
# Production Authenticated User DB
# ==========================================
USERS_DATABASE = {
    "user_101": {"name": "Support Agent Alex", "default_role": "support_agent"},
    "user_102": {"name": "Free Tier Client", "default_role": "support_agent"},
    "user_1022": {"name": "Senior Manager Sameh", "default_role": "manager"}
}

# ==========================================
# Sidebar Authenticated Control Panel
# ==========================================
st.sidebar.header("🔐 Authenticated Access Control")

# 1. Enter User Thread ID
user_id = st.sidebar.text_input("Enter User Thread ID", value="user_1022")

# 2. Determine Profile from Database
user_profile = USERS_DATABASE.get(user_id, {"name": "Guest User", "default_role": "support_agent"})
st.sidebar.caption(f"Authenticated Profile: **{user_profile['name']}**")

# 3. Role Selection with Manager Password Protection
selected_role = st.sidebar.selectbox("Select Role", ["support_agent", "manager"])

user_role = "support_agent" # Default Safe Fallback Role

if selected_role == "manager":
    manager_pin = st.sidebar.text_input("Enter Manager Security PIN", type="password")
    if manager_pin == "admin123":  # Secure Manager Secret PIN
        user_role = "manager"
        st.sidebar.success("✅ Manager Access Granted")
    elif manager_pin:
        st.sidebar.error("❌ Invalid PIN! Downgraded to 'support_agent'")
        user_role = "support_agent"
else:
    user_role = "support_agent"
    st.sidebar.info("Role: Standard Support Agent")

st.sidebar.markdown("---")
st.sidebar.caption(f"Active Session Role: `{user_role}`")
st.sidebar.success("Status: Connected to Hardened Async Engine")

# ==========================================
# Chat UI State Management
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_approval" not in st.session_state:
    st.session_state.pending_approval = False

# Display Chat Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Type your support request (e.g., Refund user_1022)...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.spinner("Processing request through Multi-Agent System..."):
        # 1. Security Input Filter (Prompt Injection Defense)
        if st.session_state.shield.check_prompt_injection(user_input):
            err_msg = "Security Violation: Malicious prompt injection attempt detected and blocked."
            st.error(err_msg)
            st.session_state.messages.append({"role": "assistant", "content": err_msg})
        else:
            # 2. PII Masking
            clean_query = st.session_state.shield.redact_pii(user_input)
            config = {"configurable": {"thread_id": user_id}}
            initial_state = {
                "messages": [HumanMessage(content=clean_query)],
                "intent": "",
                "requires_approval": False,
                "final_response": ""
            }

            try:
                # Run LangGraph Engine
                result = asyncio.run(st.session_state.compiled_graph.ainvoke(initial_state, config=config))
                response_text = extract_clean_text(result.get("final_response", ""))
                requires_approval = result.get("requires_approval", False)

                with st.chat_message("assistant"):
                    st.markdown(response_text)
                    if requires_approval:
                        st.warning("⚠️ Action Required: Manager approval needed for refund processing.")

                st.session_state.messages.append({"role": "assistant", "content": response_text})
                st.session_state.pending_approval = requires_approval
            except Exception as e:
                st.error(f"Execution Error: {str(e)}")

# ==========================================
# Human-In-The-Loop Approval Actions
# ==========================================
if st.session_state.pending_approval:
    st.divider()
    st.subheader("📋 Manager Approval Action Required")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Approve Refund"):
            if user_role != "manager":
                st.error("Access Denied: Only users with 'manager' role can approve actions.")
            else:
                if user_id in MOCK_PAYMENTS_DB:
                    MOCK_PAYMENTS_DB[user_id]["status"] = "REFUNDED"
                st.success(f"APPROVED BY MANAGER: Refund for user '{user_id}' executed successfully.")
                st.session_state.pending_approval = False

    with col2:
        if st.button("❌ Reject Refund"):
            if user_role != "manager":
                st.error("Access Denied: Only users with 'manager' role can approve actions.")
            else:
                st.info(f"REJECTED BY MANAGER: Refund for user '{user_id}' declined.")
                st.session_state.pending_approval = False