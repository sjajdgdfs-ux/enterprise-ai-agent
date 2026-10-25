import os
import asyncio
import streamlit as st
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from security import SecurityShield
from graph_agent import builder, MOCK_PAYMENTS_DB, extract_clean_text
from build_kb import build_knowledge_base

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

# Sidebar Controls
st.sidebar.header("User Control Panel")
user_role = st.sidebar.selectbox("Select Your Role", ["support_agent", "manager"])
user_id = st.sidebar.text_input("User Thread ID", value="user_1022")

st.sidebar.markdown("---")
st.sidebar.success("Security Mode: Hardened Production Engine Active")

# Chat UI State
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_approval" not in st.session_state:
    st.session_state.pending_approval = False

# Display Chat Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Type your support request...")

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

# Human-In-The-Loop Approval Actions
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