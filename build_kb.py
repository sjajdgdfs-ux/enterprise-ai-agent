import os
import warnings
import logging
import shutil

warnings.filterwarnings("ignore")
os.environ["GRPC_VERBOSITY"] = "ERROR"
logging.getLogger("google_genai").setLevel(logging.ERROR)

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

def build_knowledge_base():
    # إزالة قاعدة البيانات القديمة إن وجدت لإعادة البناء النظيف
    if os.path.exists("./chroma_db"):
        try:
            shutil.rmtree("./chroma_db")
        except Exception:
            pass

    docs = [
        # 1. وثيقة قدرات النظام العامة (System Capabilities & Features)
        Document(
            page_content=(
                "System Capabilities & Overview: This Enterprise AI Agent System is an advanced support "
                "and operations assistant. It can: 1) Answer technical support questions automatically using RAG "
                "(Retrieval-Augmented Generation). 2) Process billing inquiry and refund requests. 3) Enforce "
                "Human-in-the-Loop (HITL) manager approvals for sensitive refund operations. 4) Automatically "
                "detect and block malicious Prompt Injection attacks. 5) Automatically redact sensitive PII "
                "(Personally Identifiable Information) such as emails and phone numbers. 6) Maintain conversation "
                "state and memory across user threads."
            ),
            metadata={"category": "system", "topic": "capabilities"}
        ),
        # 2. وثيقة الدعم الفني (Technical Support Knowledge)
        Document(
            page_content=(
                "Technical Support Knowledge: To reset or regenerate your API key, navigate to Account Settings > "
                "Security > API Keys and click 'Regenerate Key'. Your old key will be invalidated instantly."
            ),
            metadata={"category": "technical", "topic": "api_key"}
        ),
        # 3. وثيقة اتفاقية مستوى الخدمة والحدود (SLA & Rate Limits)
        Document(
            page_content=(
                "SLA Uptime & Rate Limits: Enterprise tier guarantees 99.9% uptime with 10,000 requests per minute. "
                "Standard tier guarantees 99.0% uptime with 60 requests per minute."
            ),
            metadata={"category": "sla", "topic": "limits"}
        ),
        # 4. وثيقة سياسة الاسترداد المالي (Billing & Refund Policy)
        Document(
            page_content=(
                "Refund Policy: Subscription refunds are allowed within 14 days of purchase if API usage is "
                "under 1,000 calls. All refund requests require manual approval from a user with the Manager role."
            ),
            metadata={"category": "billing", "topic": "refund"}
        )
    ]

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    Chroma.from_documents(documents=docs, embedding=embeddings, persist_directory="./chroma_db")
    print("Knowledge Base created and persisted successfully in ./chroma_db")

if __name__ == "__main__":
    build_knowledge_base()