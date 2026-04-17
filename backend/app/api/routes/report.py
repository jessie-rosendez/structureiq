"""
Full compliance report across all standards categories.
Runs targeted queries for each standard and aggregates results.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException

from app.core.rag import run_two_layer_rag
from app.core.cost_tracker import session_total_cost, record_usage
from app.models.report import ComplianceReport, ReportCategory
from app.api.routes.upload import get_document

router = APIRouter()

# Representative compliance queries per standards category
REPORT_QUERIES = [
    {
        "standard": "ADA Standards 2010",
        "section": "206.2",
        "query": "Does this document specify accessible routes, entrances, parking spaces, and ramp slopes meeting ADA requirements?",
    },
    {
        "standard": "ADA Standards 2010",
        "section": "604",
        "query": "Does this document address accessible restroom requirements including grab bars, toilet clearance, and lavatory height?",
    },
    {
        "standard": "OSHA 1926",
        "section": "1926.502",
        "query": "Does this document address fall protection measures including guardrail heights, personal fall arrest systems, and safety nets?",
    },
    {
        "standard": "OSHA 1926",
        "section": "1926.451",
        "query": "Does this document specify scaffolding requirements including load capacity, platform width, and fall protection?",
    },
    {
        "standard": "IBC 2021",
        "section": "903",
        "query": "Does this document specify automatic fire sprinkler systems and does the design comply with NFPA 13 requirements?",
    },
    {
        "standard": "IBC 2021",
        "section": "1011",
        "query": "Does this document address stairway requirements including riser heights, tread depth, handrails, and exit enclosures?",
    },
    {
        "standard": "IBC 2021",
        "section": "1006",
        "query": "Does this document specify means of egress including number of exits and exit access travel distances?",
    },
    {
        "standard": "ASHRAE 90.1-2019",
        "section": "5.4.3",
        "query": "Does this document specify wall insulation R-values and do they meet ASHRAE 90.1 minimums for the applicable climate zone?",
    },
    {
        "standard": "ASHRAE 90.1-2019",
        "section": "5.5.3",
        "query": "Does this document specify roof insulation R-values and do they meet ASHRAE 90.1 minimums?",
    },
    {
        "standard": "ASHRAE 90.1-2019",
        "section": "9.4.1",
        "query": "Does this document address lighting power density and automatic shutoff controls per ASHRAE 90.1?",
    },
]

STATUS_RISK_WEIGHT = {
    "FAILS": 3,
    "PARTIALLY_MEETS": 2,
    "FLAG": 2,
    "INSUFFICIENT_DATA": 1,
    "MEETS": 0,
}


def _compute_overall_risk(categories: list[ReportCategory]) -> str:
    total = sum(STATUS_RISK_WEIGHT.get(c.status, 0) for c in categories)
    n = len(categories) or 1
    avg = total / n
    if avg >= 2.5:
        return "HIGH"
    if avg >= 1.5:
        return "MEDIUM"
    if avg >= 0.5:
        return "LOW"
    return "LOW"


@router.post("/report", response_model=ComplianceReport)
async def generate_report(document_id: str) -> ComplianceReport:
    doc = get_document(document_id)
    if doc is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_id} not found. Upload a document first.",
        )

    if doc.get("type") != "pdf":
        raise HTTPException(
            status_code=422,
            detail="Full compliance reports are only available for PDF documents.",
        )

    categories: list[ReportCategory] = []
    report_cost = 0.0

    for query_spec in REPORT_QUERIES:
        try:
            result = run_two_layer_rag(
                question=query_spec["query"],
                document_session_id=document_id,
            )
            status = result.get("compliance_status", "INSUFFICIENT_DATA")
            if status not in ("MEETS", "PARTIALLY_MEETS", "FAILS", "INSUFFICIENT_DATA"):
                status = "FLAG"
            doc_citations = result.get("document_citations", [])
            std_citations = result.get("standard_citations", [])
            categories.append(
                ReportCategory(
                    standard=query_spec["standard"],
                    section=query_spec["section"],
                    status=status,
                    finding=result.get("answer", "")[:500],
                    document_citation=doc_citations[0] if doc_citations else "Not found in document",
                    standard_citation=std_citations[0] if std_citations else query_spec["standard"],
                    confidence=result.get("confidence", "LOW"),
                )
            )
            report_cost += result.get("cost_usd", 0.0)
        except Exception:
            categories.append(
                ReportCategory(
                    standard=query_spec["standard"],
                    section=query_spec["section"],
                    status="INSUFFICIENT_DATA",
                    finding="Analysis unavailable — Gemini returned a transient error for this check.",
                    document_citation="Not found in document",
                    standard_citation=query_spec["standard"],
                    confidence="LOW",
                )
            )

    overall_risk = _compute_overall_risk(categories)

    return ComplianceReport(
        document_name=doc.get("filename", "Unknown"),
        document_id=document_id,
        generated_at=datetime.now(timezone.utc),
        overall_risk=overall_risk,
        categories=categories,
        total_cost_usd=round(report_cost, 6),
        session_total_cost_usd=session_total_cost(),
    )
