from typing import Any


def check_hallucination(
    answer: str,
    document_chunks: list[dict[str, Any]],
    standards_chunks: list[dict[str, Any]],
    min_similarity: float = 0.75,
) -> dict[str, Any]:
    """
    Two-stage hallucination check.

    Stage 1 — Source grounding: verify standard citations in the answer appear
    in the retrieved standards chunks.
    Stage 2 — Confidence threshold: if all retrieval similarity scores are below
    min_similarity, force LOW confidence and emit warning.

    Returns dict with keys: warning (str|None), forced_confidence (str|None).
    """
    warning = None
    forced_confidence = None

    # Stage 1: check that cited standards IDs appear in retrieved chunks
    retrieved_standard_ids = {
        c.get("metadata", {}).get("section_id", "") for c in standards_chunks
    }
    retrieved_standard_ids.update(
        c.get("section_id", "") for c in standards_chunks
    )

    # Simple heuristic: look for standard section patterns in answer
    import re
    cited_sections = set(re.findall(r"(?:ADA|OSHA|IBC|ASHRAE)[- ]\d[\d.]*[\d]", answer))
    for cited in cited_sections:
        # Normalize for comparison
        normalized = cited.replace(" ", "-").upper()
        if not any(normalized in sid.upper() for sid in retrieved_standard_ids if sid):
            warning = (
                f"Answer references '{cited}' which was not in the retrieved standards context. "
                "Manual verification recommended."
            )
            break

    # Stage 2: confidence threshold check
    all_scores = [
        c.get("score", 1.0)
        for c in (document_chunks + standards_chunks)
        if "score" in c
    ]
    if all_scores and max(all_scores) < min_similarity:
        forced_confidence = "LOW"
        low_confidence_warning = (
            "Insufficient document context for high-confidence determination. "
            "Manual review recommended."
        )
        warning = low_confidence_warning if not warning else f"{warning} | {low_confidence_warning}"

    return {"warning": warning, "forced_confidence": forced_confidence}


def apply_confidence_floor(
    confidence: str,
    document_chunks: list[dict[str, Any]],
    standards_chunks: list[dict[str, Any]],
    threshold: float = 0.75,
) -> str:
    """Downgrade confidence to LOW if retrieval scores are all below threshold."""
    all_scores = [
        c.get("score", 1.0)
        for c in (document_chunks + standards_chunks)
        if "score" in c
    ]
    if all_scores and max(all_scores) < threshold:
        return "LOW"
    return confidence
