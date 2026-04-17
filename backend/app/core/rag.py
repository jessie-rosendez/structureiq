"""
Two-layer RAG orchestration — the heart of StructureIQ.

Every query retrieves from BOTH the user's uploaded document AND the
compliance standards knowledge base, then synthesizes with Gemini 1.5 Pro.
"""

import json
import asyncio
from typing import Any

import google.generativeai as genai
from google.cloud.aiplatform.matching_engine import MatchingEngineIndexEndpoint

from app.core.config import get_settings
from app.core.compliance import query_standards, format_standards_context
from app.core.guardrails import check_hallucination, apply_confidence_floor
from app.core.cost_tracker import record_usage, session_total_cost
from app.ingestion.embedder import embed_single


SYNTHESIS_PROMPT = """
You are a senior AEC compliance engineer analyzing construction documents.

USER DOCUMENT CONTEXT:
{document_chunks}

APPLICABLE REGULATORY STANDARDS:
{standards_chunks}

QUESTION: {question}

Instructions:
1. Answer using BOTH the document context and regulatory standards
2. State whether the document MEETS, PARTIALLY_MEETS, FAILS, or INSUFFICIENT_DATA for each standard
3. Cite specific page numbers from the document and section IDs from standards
4. If information is missing, say so explicitly — never fabricate
5. Assign confidence: HIGH (clear evidence), MEDIUM (inferred), LOW (insufficient data)

Return structured JSON only:
{{
  "answer": "...",
  "compliance_status": "MEETS | PARTIALLY_MEETS | FAILS | INSUFFICIENT_DATA",
  "document_citations": ["Page X, Section Y"],
  "standard_citations": ["ADA 4.1.1", "OSHA 1926.502"],
  "confidence": "HIGH | MEDIUM | LOW",
  "gaps": ["Missing information needed for full determination"]
}}
"""


def _query_document_layer(
    query_text: str, document_index_id: str, top_k: int
) -> list[dict[str, Any]]:
    """Retrieve top-K chunks from the user's uploaded document index."""
    settings = get_settings()
    query_embedding = embed_single(query_text)

    endpoint = MatchingEngineIndexEndpoint(
        index_endpoint_name=settings.documents_endpoint_resource_name
    )

    try:
        response = endpoint.find_neighbors(
            deployed_index_id=settings.vertex_documents_deployed_index_id,
            queries=[query_embedding],
            num_neighbors=top_k,
        )
        results = []
        for neighbor in response[0]:
            results.append(
                {
                    "id": neighbor.id,
                    "score": neighbor.distance,
                    "metadata": {},
                }
            )
        return results
    except Exception:
        # Document may not yet be indexed; return empty
        return []


def _format_document_context(doc_chunks: list[dict[str, Any]]) -> str:
    if not doc_chunks:
        return "No document context retrieved. The uploaded document may not yet be indexed."
    lines = []
    for i, chunk in enumerate(doc_chunks, 1):
        meta = chunk.get("metadata", {})
        page = meta.get("page", ["?"])
        if isinstance(page, list):
            page = page[0] if page else "?"
        text = chunk.get("text", "")
        score = chunk.get("score", 0)
        lines.append(f"[Document Chunk {i}] Page: {page} | Relevance: {score:.3f}\n{text}")
    return "\n\n".join(lines)


def run_two_layer_rag(
    question: str,
    document_session_id: str,
    document_chunks_override: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Core two-layer RAG query.

    Runs document retrieval and standards retrieval in parallel,
    then synthesizes with Gemini 1.5 Pro.
    """
    settings = get_settings()

    # Run both layers — standards query always runs; doc query uses session ID
    standards_chunks = query_standards(question, top_k=settings.retrieval_top_k_standards)

    if document_chunks_override is not None:
        doc_chunks = document_chunks_override
    else:
        doc_chunks = _query_document_layer(
            question, document_session_id, settings.retrieval_top_k_docs
        )

    document_context = _format_document_context(doc_chunks)
    standards_context = format_standards_context(standards_chunks)

    prompt = SYNTHESIS_PROMPT.format(
        document_chunks=document_context,
        standards_chunks=standards_context,
        question=question,
    )

    genai.configure(api_key=settings.google_api_key)
    model = genai.GenerativeModel("gemini-1.5-pro-002")

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.1,
        ),
    )

    raw_text = response.text.strip()
    # Strip markdown code fences if present
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[-1]
        raw_text = raw_text.rsplit("```", 1)[0].strip()

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        result = {
            "answer": raw_text,
            "compliance_status": "INSUFFICIENT_DATA",
            "document_citations": [],
            "standard_citations": [],
            "confidence": "LOW",
            "gaps": ["LLM response could not be parsed as JSON"],
        }

    # Token tracking
    usage = response.usage_metadata
    input_tokens = getattr(usage, "prompt_token_count", 0)
    output_tokens = getattr(usage, "candidates_token_count", 0)
    from app.core.cost_tracker import record_usage, session_total_cost
    call_cost = record_usage(input_tokens, output_tokens)

    # Guardrails
    guardrail = check_hallucination(
        result.get("answer", ""),
        doc_chunks,
        standards_chunks,
        min_similarity=settings.confidence_threshold,
    )
    if guardrail["forced_confidence"]:
        result["confidence"] = guardrail["forced_confidence"]
    else:
        result["confidence"] = apply_confidence_floor(
            result.get("confidence", "MEDIUM"),
            doc_chunks,
            standards_chunks,
            settings.confidence_threshold,
        )

    result["hallucination_warning"] = guardrail["warning"]
    result["layer_sources"] = {
        "document_chunks_used": len(doc_chunks),
        "standards_chunks_used": len(standards_chunks),
    }
    result["tokens_used"] = {"input": input_tokens, "output": output_tokens}
    result["cost_usd"] = call_cost
    result["session_total_cost_usd"] = session_total_cost()

    return result
