"""
Two-layer RAG orchestration — the heart of StructureIQ.

Every query retrieves from BOTH the user's uploaded document AND the
compliance standards knowledge base, then synthesizes with Gemini 2.0 Flash.
"""

import json
import asyncio
import time
from typing import Any

from google import genai
from google.genai import types as genai_types
from google.genai.errors import ClientError
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
    query_text: str, document_session_id: str, top_k: int
) -> list[dict[str, Any]]:
    """Retrieve top-K relevant chunks from this document, hydrated with text."""
    from app.api.routes.upload import get_document
    from google.cloud.aiplatform.matching_engine import matching_engine_index_endpoint as _mee

    settings = get_settings()

    # Hydration source — memory cache first, then GCS
    doc = get_document(document_session_id)
    chunks: list[dict[str, Any]] = doc.get("chunks", []) if doc else []
    chunk_by_index: dict[int, dict[str, Any]] = {i: c for i, c in enumerate(chunks)}

    query_embedding = embed_single(query_text)
    endpoint = MatchingEngineIndexEndpoint(
        index_endpoint_name=settings.documents_endpoint_resource_name
    )

    neighbors = []
    try:
        # Server-side restriction filter: only return datapoints for this document
        ns_filter = [
            _mee.Namespace(
                name="document_id",
                allow_tokens=[document_session_id],
                deny_tokens=[],
            )
        ]
        response = endpoint.find_neighbors(
            deployed_index_id=settings.vertex_documents_deployed_index_id,
            queries=[query_embedding],
            num_neighbors=top_k,
            filter=ns_filter,
        )
        neighbors = response[0] if response else []
    except Exception:
        pass

    # GCS fallback: if Vertex returned nothing, serve chunks directly by score 1.0
    if not neighbors and chunks:
        return [
            {
                "id": f"{document_session_id}__chunk_{i}",
                "text": c["text"],
                "page": c["page"],
                "score": 1.0,
                "metadata": {"page": [str(c["page"])], "document_id": [document_session_id]},
            }
            for i, c in enumerate(chunks[:top_k])
        ]

    results = []
    for neighbor in neighbors:
        try:
            idx = int(neighbor.id.split("__chunk_")[-1])
            chunk = chunk_by_index.get(idx, {})
        except (ValueError, IndexError):
            chunk = {}
        results.append(
            {
                "id": neighbor.id,
                "text": chunk.get("text", ""),
                "page": chunk.get("page", "?"),
                "score": neighbor.distance,
                "metadata": {
                    "page": [str(chunk.get("page", "?"))],
                    "document_id": [document_session_id],
                },
            }
        )
    return results


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


def _generate_with_retry(
    client: genai.Client,
    settings: Any,
    contents: Any,
) -> Any:
    models = [settings.gemini_model]
    if settings.gemini_fallback_model != settings.gemini_model:
        models.append(settings.gemini_fallback_model)

    last_429: ClientError | None = None

    for model_name in models:
        for attempt in range(settings.gemini_max_retries):
            try:
                return client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=genai_types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.1,
                    ),
                )
            except ClientError as exc:
                status_code = getattr(exc, "status_code", None)
                if status_code == 404:
                    raise RuntimeError(
                        "Gemini model "
                        f"`{model_name}` is unavailable for project "
                        f"`{settings.google_cloud_project}` in `{settings.gemini_location}`. "
                        "Update GEMINI_MODEL to a currently supported Vertex model, such as "
                        "`gemini-2.5-flash`."
                    ) from exc
                if status_code not in (429, 500, 503):
                    raise

                last_429 = exc
                if attempt < settings.gemini_max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                break
            except Exception as exc:
                # Catch non-ClientError transient errors (e.g. google.api_core exceptions)
                last_429 = exc  # type: ignore[assignment]
                if attempt < settings.gemini_max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                break

    raise RuntimeError(
        "Vertex Gemini is temporarily out of capacity for this request after multiple retries. "
        f"Tried `{settings.gemini_model}`"
        + (
            f" and fallback `{settings.gemini_fallback_model}`"
            if settings.gemini_fallback_model != settings.gemini_model
            else ""
        )
        + ". Try again in 1-2 minutes."
    ) from last_429


def run_two_layer_rag(
    question: str,
    document_session_id: str,
    document_chunks_override: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Core two-layer RAG query.

    Runs document retrieval and standards retrieval in parallel,
    then synthesizes with Gemini 2.0 Flash.
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

    client = genai.Client(
        vertexai=True,
        project=settings.google_cloud_project,
        location=settings.gemini_location,
    )

    response = _generate_with_retry(client, settings, prompt)

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
