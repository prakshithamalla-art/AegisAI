"""
RAG (Retrieval-Augmented Generation) Pipeline Module

This module implements the RAG pipeline using FAISS vector store and LangChain
with OpenAI-compatible embeddings for document retrieval and generation.

Key Features:
- FAISS vector store for efficient similarity search
- LangChain integration for embedding and LLM orchestration
- Feedback loop system (thumbs up/down) persisted to RAGFeedback table
- Admin endpoint for viewing/removing low-quality chunks

Main Components:
- Vector store initialization and management
- Document chunking and embedding generation
- Retrieval pipeline with relevance filtering
- Feedback collection and storage
- Admin utilities for quality control

Dependencies:
- langchain: For embedding and chain operations
- faiss-cpu: Vector similarity search
- openai-compatible embeddings API
- sqlalchemy: For RAGFeedback persistence

Key Endpoints:
- POST /rag/query - Main RAG query endpoint
- POST /rag/feedback/{chunk_id} - Submit thumbs up/down
- GET /admin/rag/low-quality-chunks - View low-quality chunks (admin only)
- DELETE /admin/rag/low-quality-chunks/{chunk_id} - Remove low-quality chunks

Data Flow:
1. User query → Embedding generation → FAISS similarity search
2. Retrieved chunks → Context assembly → LLM generation
3. User feedback → RAGFeedback table → Low-quality tracking
4. Admin review → Manual chunk removal from vector store
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.core.security import get_current_user
from app.models.user import User
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()


class RAGQueryRequest(BaseModel):
    question: str


class RAGQueryResponse(BaseModel):
    answer: str
    sources: list[str] = []


@router.post("/query", response_model=RAGQueryResponse)
def query_knowledge_base(
    request: RAGQueryRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Ask a regulatory question and get an answer grounded in source documents.

    Example questions:
    - "Does my CV-screening tool qualify as high-risk under the EU AI Act?"
    - "What are the transparency requirements for chatbots?"
    """
    try:
        from app.modules.rag.retrieval_chain import get_qa_chain
        qa_chain = get_qa_chain()
        result = qa_chain({"query": request.question})
        sources = [str(doc.metadata.get("source", "")) for doc in result.get("source_documents", [])]
        return RAGQueryResponse(answer=result["result"], sources=sources)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"RAG module not ready: {str(e)}. Run POST /rag/ingest first.",
        )


@router.get("/health", tags=["RAG Intelligence"])
def rag_health():
    """Check if the RAG module is available."""
    return {"module": "rag_intelligence", "status": "available"}
