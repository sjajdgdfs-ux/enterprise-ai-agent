import os
import sys
import asyncio
import streamlit as st

# Suppress gRPC and Google GenAI Verbose Logs
os.environ["GRPC_VERBOSITY"] = "ERROR"

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from security import SecurityShield
from graph_agent import builder, MOCK_PAYMENTS_DB, extract_clean_text, build_knowledge_base if hasattr(sys.modules.get('graph_agent'), 'build_knowledge_base') else None

st.set_page_config(page_title="Enterprise AI Support Agent", layout="wide")
st.title("🛡️ Enterprise AI Support & Operations Portal")

# Initialize Security and LangGraph Memory in Streamlit Session State
if "shield" not in st.session_state:
    st.session_state.shield = SecurityShield()

if "compiled_graph" not in st.session_state:
    # Ensure ChromaDB Knowledge Base exists
    if not os.path.exists("./chroma_db"):
        from build_kb import build_knowledge_base
        build_knowledge_base()
    
    memory = MemorySaver()
    st.session_state.compiled_graph = builder.compile(checkpointer=memory)

# Sidebar Role Selection & Configuration
st.sidebar.header("User Control Panel")
user_role = st.sidebar.selectbox("Select Your Role", ["support_agent", "manager"])
user_id = st.sidebar.text_input("User Thread ID", value="user_1022")

st.sidebar.markdown("---")
st.sidebar.success("Status: Connected to Internal Async Graph Engine")

# Chat UI State Management
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_approval" not in st.session_state:
    st.session_state.pending_approval = False

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input Handler
user_input = st.chat_input("Type your support request...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.spinner("Processing request through Multi-Agent System..."):
        # 1. Security Check: Prompt Injection
        if st.session_state.shield.check_prompt_injection(user_input):
            err_msg = "Security Violation: Malicious injection pattern detected."
            st.error(err_msg)
            st.session_state.messages.append({"role": "assistant", "content": err_msg})
        else:
            # 2. PII Redaction
            clean_query = st.session_state.shield.redact_pii(user_input)
            config = {"configurable": {"thread_id": user_id}}
            initial_state = {
                "messages": [HumanMessage(content=clean_query)],
                "intent": "",
                "requires_approval": False,
                "final_response": ""
            }

            try:
                # Run LangGraph Engine directly
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

# Human-in-the-Loop (HITL) Manager Approval UI
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