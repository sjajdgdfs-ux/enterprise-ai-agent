import os
import warnings
import logging

warnings.filterwarnings("ignore")
os.environ["GRPC_VERBOSITY"] = "ERROR"
logging.getLogger("google_genai").setLevel(logging.ERROR)

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

def build_knowledge_base():
    docs = [
        Document(
            page_content="To reset your API key, navigate to Account Settings > Security > API Keys and click 'Regenerate Key'. Existing keys will be invalidated instantly.",
            metadata={"category": "technical", "topic": "api_key"}
        ),
        Document(
            page_content="Our platform guarantees 99.9% SLA uptime for Enterprise tier customers. Standard tier guarantees 99.0% uptime.",
            metadata={"category": "sla", "topic": "uptime"}
        ),
        Document(
            page_content="Refund Policy: Subscription refunds are permitted within 14 days of purchase if usage is under 1,000 API calls. Refunds exceeding $500 require manual manager approval.",
            metadata={"category": "billing", "topic": "refund"}
        ),
        Document(
            page_content="Rate limits: Standard plan allows 60 requests per minute. Enterprise plan allows 10,000 requests per minute.",
            metadata={"category": "technical", "topic": "rate_limit"}
        )
    ]

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )

    print("Knowledge Base created and persisted successfully in ./chroma_db")

if __name__ == "__main__":
    build_knowledge_base()