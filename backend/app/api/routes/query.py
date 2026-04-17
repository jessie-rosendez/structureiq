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

    try:
        result = run_two_layer_rag(
            question=request.question,
            document_session_id=request.document_id,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ClientError as exc:
        raise HTTPException(
            status_code=503,
            detail="Vertex Gemini is temporarily unavailable. Please try again in a moment.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Vertex Gemini is temporarily unavailable. Please try again in a moment.",
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
