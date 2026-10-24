import os
import sys
import time
import subprocess
import streamlit as st
import requests

# 🚀 Auto-start FastAPI Backend in Background (For Hugging Face Streamlit SDK)
if "BACKEND_STARTED" not in os.environ:
    os.environ["BACKEND_STARTED"] = "true"
    try:
        # 1. Build Vector Knowledge Base
        subprocess.Popen([sys.executable, "build_kb.py"])
        time.sleep(2)
        # 2. Launch FastAPI Server in background on port 8000
        subprocess.Popen([sys.executable, "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"])
        time.sleep(3)
    except Exception as e:
        print(f"Backend Start Error: {e}")

# Dynamic API URL Resolution
API_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Enterprise AI Support Agent", layout="wide")
st.title("🛡️ Enterprise AI Support & Operations Portal")

# Sidebar Role Selection & Configuration
st.sidebar.header("User Control Panel")
user_role = st.sidebar.selectbox("Select Your Role", ["support_agent", "manager"])
user_id = st.sidebar.text_input("User Thread ID", value="user_1022")

st.sidebar.markdown("---")
st.sidebar.info(f"Connected to Backend: `{API_URL}`")

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
        try:
            payload = {"user_id": user_id, "query": user_input}
            res = requests.post(f"{API_URL}/support", json=payload)

            if res.status_code == 200:
                data = res.json()
                response_text = data.get("response", "")
                requires_approval = data.get("requires_approval", False)

                with st.chat_message("assistant"):
                    st.markdown(response_text)
                    if requires_approval:
                        st.warning("⚠️ Action Required: Manager approval needed for refund processing.")

                st.session_state.messages.append({"role": "assistant", "content": response_text})
                st.session_state.pending_approval = requires_approval
            else:
                err_msg = f"Error {res.status_code}: {res.json().get('detail', 'Unknown error')}"
                st.error(err_msg)
        except Exception as e:
            st.error(f"Failed to connect to backend: {str(e)}")

# Human-in-the-Loop (HITL) Manager Approval UI
if st.session_state.pending_approval:
    st.divider()
    st.subheader("📋 Manager Approval Action Required")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Approve Refund"):
            try:
                payload = {"user_id": user_id, "action": "approve", "requestor_role": user_role}
                res = requests.post(f"{API_URL}/approve", json=payload)
                if res.status_code == 200:
                    st.success(res.json().get("message", "Approved successfully."))
                    st.session_state.pending_approval = False
                else:
                    st.error(res.json().get("detail", "Approval failed."))
            except Exception as e:
                st.error(f"Error executing approval: {str(e)}")

    with col2:
        if st.button("❌ Reject Refund"):
            try:
                payload = {"user_id": user_id, "action": "reject", "requestor_role": user_role}
                res = requests.post(f"{API_URL}/approve", json=payload)
                if res.status_code == 200:
                    st.info(res.json().get("message", "Rejected successfully."))
                    st.session_state.pending_approval = False
                else:
                    st.error(res.json().get("detail", "Rejection failed."))
            except Exception as e:
                st.error(f"Error executing rejection: {str(e)}")