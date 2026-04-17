from fastapi import APIRouter, HTTPException
from google.genai.errors import ClientError

from app.core.rag import run_two_layer_rag
from app.models.document import QueryRequest, QueryResponse
from app.api.routes.upload import get_document

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_document(request: QueryRequest) -> QueryResponse:
    doc = get_document(request.document_id)
    if doc is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document {request.document_id} not found. Upload a document first.",
        )

    # Pass cached chunks directly to avoid redundant Vertex retrieval in same session
    cached_chunks = []
    if doc.get("type") == "pdf" and doc.get("chunks"):
        raw_chunks = doc["chunks"]
        embeddings = doc.get("embeddings", [])
        # We pass cached chunks directly; rag.py accepts override
        for i, chunk in enumerate(raw_chunks):
            cached_chunks.append(
                {
                    "text": chunk["text"],
                    "page": chunk["page"],
                    "score": 1.0,  # local cache = fully relevant
                    "metadata": {"page": [str(chunk["page"])], "document_id": [request.document_id]},
                }
            )

    try:
        result = run_two_layer_rag(
            question=request.question,
            document_session_id=request.document_id,
            document_chunks_override=cached_chunks if cached_chunks else None,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ClientError as exc:
        raise HTTPException(
            status_code=503,
            detail="Vertex Gemini is temporarily unavailable. Restart the backend to pick up the latest retry logic, then try the query again.",
        ) from exc

    return QueryResponse(
        answer=result["answer"],
        compliance_status=result.get("compliance_status", "INSUFFICIENT_DATA"),
        document_citations=result.get("document_citations", []),
        standard_citations=result.get("standard_citations", []),
        confidence=result.get("confidence", "LOW"),
        gaps=result.get("gaps", []),
        layer_sources=result["layer_sources"],
        hallucination_warning=result.get("hallucination_warning"),
        tokens_used=result["tokens_used"],
        cost_usd=result["cost_usd"],
        session_total_cost_usd=result["session_total_cost_usd"],
    )
