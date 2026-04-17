from pydantic import BaseModel, Field
from typing import Any


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    page_count: int
    chunks_indexed: int
    message: str


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    document_id: str


class LayerSources(BaseModel):
    document_chunks_used: int
    standards_chunks_used: int


class TokenUsage(BaseModel):
    input: int
    output: int


class QueryResponse(BaseModel):
    answer: str
    compliance_status: str
    document_citations: list[str]
    standard_citations: list[str]
    confidence: str
    gaps: list[str]
    layer_sources: LayerSources
    hallucination_warning: str | None
    tokens_used: TokenUsage
    cost_usd: float
    session_total_cost_usd: float


class SessionMetrics(BaseModel):
    session_total_cost_usd: float
    total_tokens: dict[str, int]
