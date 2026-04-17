"""
Compliance standards knowledge base query logic.
Queries the Vertex AI Vector Search standards index and returns
the top-K most relevant regulatory sections.
"""

from typing import Any

from google.cloud.aiplatform.matching_engine import MatchingEngineIndexEndpoint

from app.core.config import get_settings
from app.ingestion.embedder import embed_single


def query_standards(query_text: str, top_k: int | None = None) -> list[dict[str, Any]]:
    """
    Embed the query and retrieve top-K matching standards sections.

    Returns list of dicts with keys: section_id, standard, title,
    category, requirement_snippet, score.
    """
    settings = get_settings()
    if top_k is None:
        top_k = settings.retrieval_top_k_standards

    query_embedding = embed_single(query_text)

    endpoint = MatchingEngineIndexEndpoint(
        index_endpoint_name=settings.standards_endpoint_resource_name
    )

    response = endpoint.find_neighbors(
        deployed_index_id=settings.vertex_standards_deployed_index_id,
        queries=[query_embedding],
        num_neighbors=top_k,
    )

    results = []
    for neighbor in response[0]:
        results.append(
            {
                "id": neighbor.id,
                "score": neighbor.distance,
                "section_id": _extract_section_id(neighbor.id),
                "metadata": {},
            }
        )

    return results


def _extract_section_id(datapoint_id: str) -> str:
    """Convert datapoint ID back to section_id format (best effort)."""
    parts = datapoint_id.split("__", 1)
    if len(parts) == 2:
        return parts[1].replace("_", ".").replace("-..", "-").strip(".")
    return datapoint_id


def format_standards_context(standards_chunks: list[dict[str, Any]]) -> str:
    """Format retrieved standards for inclusion in LLM prompt."""
    if not standards_chunks:
        return "No matching regulatory standards retrieved."
    lines = []
    for i, chunk in enumerate(standards_chunks, 1):
        sid = chunk.get("section_id", chunk.get("id", ""))
        meta = chunk.get("metadata", {})
        standard = meta.get("standard", ["Unknown standard"])
        if isinstance(standard, list):
            standard = standard[0] if standard else "Unknown standard"
        text = chunk.get("text", chunk.get("requirement", ""))
        score = chunk.get("score", 0)
        lines.append(
            f"[Standard {i}] ID: {sid} | Source: {standard} | Relevance: {score:.3f}\n{text}"
        )
    return "\n\n".join(lines)
