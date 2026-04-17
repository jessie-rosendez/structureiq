from pydantic import BaseModel
from datetime import datetime


class ReportCategory(BaseModel):
    standard: str
    section: str
    status: str  # MEETS | PARTIALLY_MEETS | FAILS | FLAG | INSUFFICIENT_DATA
    finding: str
    document_citation: str
    standard_citation: str
    confidence: str


class ComplianceReport(BaseModel):
    document_name: str
    document_id: str
    generated_at: datetime
    overall_risk: str  # LOW | MEDIUM | HIGH | CRITICAL
    categories: list[ReportCategory]
    total_cost_usd: float
    session_total_cost_usd: float
    standards_checked: list[str] = []
