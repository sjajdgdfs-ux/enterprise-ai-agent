# 🛡️ Enterprise AI Support & Operations Multi-Agent System

[![Python Version](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-LangGraph%20%7C%20FastAPI-green.svg)](https://langchain-ai.github.io/langgraph/)
[![Model](https://img.shields.io/badge/LLM-Gemini%202.0%20Flash-orange.svg)](https://aistudio.google.com/)
[![Security Pass](https://img.shields.io/badge/Promptfoo%20Security-100%25%20Passed-brightgreen.svg)](https://promptfoo.dev/)
[![Live Demo](https://img.shields.io/badge/Streamlit-Live%20Demo-red.svg)](https://enterprise-ai-agent-x54egp6faq6wtdgsaccxo8.streamlit.app/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A **production-hardened, secure, and asynchronous Multi-Agent Support Portal** built with **LangGraph**, **Gemini 2.0 Flash**, **FastAPI**, **ChromaDB RAG**, and **Streamlit**.

The system features dynamic intent routing, Human-in-the-Loop (HITL) manager approvals, Role-Based Access Control (RBAC), built-in prompt injection defense, PII redaction, and full execution observability.

---

## 🌐 Live Interactive Application

👉 **Try the Live Agent Demo:** [Enterprise AI Support Portal](https://enterprise-ai-agent-x54egp6faq6wtdgsaccxo8.streamlit.app/)

---

## 🏗️ System Architecture

```text
                               ┌───────────────────────────┐
                               │     User Query / Streamlit│
                               └─────────────┬─────────────┘
                                             │
                                             ▼
                               ┌───────────────────────────┐
                               │  Security Shield Filter   │
                               │(Injection & PII Redaction)│
                               └─────────────┬─────────────┘
                                             │
                                             ▼
                               ┌───────────────────────────┐
                               │   LangGraph Router Node   │
                               └──────┬──────────┬─────────┘
                                      │          │
            ┌─────────────────────────┘          └────────────────────────┐
            ▼                                     ▼                       ▼
┌───────────────────────┐             ┌───────────────────────┐ ┌───────────────────┐
│ Technical Support RAG │             │ Billing Support Agent │ │ General AI Agent  │
│ (ChromaDB + HF Vector)│             │  (HITL Check Trigger) │ │ (Customer Success)│
└───────────────────────┘             └──────────┬────────────┘ └───────────────────┘
                                                 │
                                                 ▼
                                      ┌───────────────────────┐
                                      │ Manager Approval Gate │
                                      │  (RBAC PIN Protected) │
                                      └───────────────────────┘
                                      ✨ Key Features & Production Capabilities
🧠 1. Multi-Agent Intent Routing & RAG
Router Agent: Classifies user intent (TECHNICAL, BILLING, GENERAL) and routes queries dynamically.
Agentic RAG Engine: Powered by ChromaDB and local sentence-transformers/all-MiniLM-L6-v2 embeddings for zero-hallucination technical support.
🛡️ 2. Enterprise Security & Hardening (10/10 Security Checklist)
Prompt Injection Defense: Intercepts malicious system prompt overrides and blocks unauthorized instructions.
PII Redaction: Automatically masks sensitive information (Emails, Phone Numbers) before LLM execution.
SSRF Protection: Validates URLs against internal metadata IPs (169.254.169.254, localhost).
Rate Limiting: Managed via slowapi (10 requests/minute per IP) to prevent DDoS attacks.
Strict CORS Policy: Restricted strictly to authorized Streamlit origins.
Token Cost Control: Hard capped at max_output_tokens=1024 to prevent API token exhaustion.
🔐 3. Human-in-the-Loop (HITL) & Role-Based Access Control (RBAC)
Sensitive financial operations (e.g., Refund Requests) trigger a HITL pending state.
Only authenticated users with the manager role (secured via a Manager Security PIN) can approve or reject financial transactions.
📊 4. Full Observability & Tracing
Custom AgentTracer records execution steps, inputs/outputs, and latency metrics in capstone_traces.jsonl.
Built-in Admin Observability Dashboard for real-time trace viewing.
📈 Performance & Security Benchmarks
🧪 Red-Teaming Evaluation (Promptfoo)
The system was evaluated against automated prompt injection, RAG retrieval accuracy, and PII masking tests using Promptfoo:

Result: ✓ 3 passed (100.00%) | 0 failed | 0 errors.
⚡ Async Load & Stress Test (Python Async Load Tester)
Under concurrent simulated users, the production system achieved:

Success Rate: 100% (30/30 Requests - 0% Error Rate)
Throughput: 10.2 Requests / Second (RPS)
Average Response Latency: 943 ms
🛠️ Tech Stack
Language: Python 3.11+
LLM Engine: Google Gemini 2.0 Flash (langchain-google-genai)
Agent Orchestration: LangGraph (StateGraph, MemorySaver, AsyncSqliteSaver)
Vector Database: ChromaDB (langchain-chroma)
Embeddings: HuggingFace sentence-transformers/all-MiniLM-L6-v2
API Framework: FastAPI, Uvicorn, SlowAPI
Frontend UI: Streamlit
Security & QA: Promptfoo, Custom PII/SSRF Regex Filters
📂 Directory Structure
text

capstone_system/
├── build_kb.py             # Vectorstore & Knowledge Base Generation
├── graph_agent.py          # Core LangGraph Multi-Agent Architecture
├── server.py               # Production Hardened FastAPI REST API
├── security.py             # Security Shield (Prompt Injection, PII, SSRF)
├── tracer.py               # Observability & Trace Logging Engine
├── capstone_ui.py          # Interactive Streamlit Web Portal (RBAC Protected)
├── promptfooconfig.yaml    # Automated QA & Security Evaluation Config
├── load_test.py            # Async Concurrency Load Testing Script
├── requirements.txt        # Production Dependencies
├── start.sh                # Container Startup Shell Script
└── Dockerfile              # Docker Container Build Blueprint
🚀 Local Quickstart Guide
1️⃣ Clone the Repository
Bash

git clone https://github.com/sjajdgdfs-ux/enterprise-ai-agent.git
cd enterprise-ai-agent
2️⃣ Install Dependencies
Bash

pip install -r requirements.txt
3️⃣ Set Environment Variables
Bash

# On Linux/macOS
export GEMINI_API_KEY="your_google_gemini_api_key"

# On Windows PowerShell
$env:GEMINI_API_KEY="your_google_gemini_api_key"
4️⃣ Build Knowledge Base
Bash

python build_kb.py
5️⃣ Run the Application (Streamlit UI)
Bash

python -m streamlit run capstone_ui.py
🐳 Docker Deployment
Build Image:
Bash

docker build -t enterprise-ai-agent .
Run Container:
Bash

docker run -d \
  -p 7860:7860 \
  -p 8000:8000 \
  -e GEMINI_API_KEY="your_gemini_api_key" \
  --name ai_agent_app \
  enterprise-ai-agent
📜 License
Distributed under the MIT License. See LICENSE for more information.

👨‍💻 Author
Sameh - Enterprise AI Agent Engineer

GitHub: @sjajdgdfs-ux
```
