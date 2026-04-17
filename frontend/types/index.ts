export interface UploadResponse {
  document_id: string;
  filename: string;
  page_count: number;
  chunks_indexed: number;
  message: string;
}

export interface LayerSources {
  document_chunks_used: number;
  standards_chunks_used: number;
}

export interface TokenUsage {
  input: number;
  output: number;
}

export interface QueryResponse {
  answer: string;
  compliance_status: "MEETS" | "PARTIALLY_MEETS" | "FAILS" | "INSUFFICIENT_DATA";
  document_citations: string[];
  standard_citations: string[];
  confidence: "HIGH" | "MEDIUM" | "LOW";
  gaps: string[];
  layer_sources: LayerSources;
  hallucination_warning: string | null;
  tokens_used: TokenUsage;
  cost_usd: number;
  session_total_cost_usd: number;
}

export interface ReportCategory {
  standard: string;
  section: string;
  status: "MEETS" | "PARTIALLY_MEETS" | "FAILS" | "FLAG" | "INSUFFICIENT_DATA";
  finding: string;
  document_citation: string;
  standard_citation: string;
  confidence: "HIGH" | "MEDIUM" | "LOW";
}

export interface ComplianceReport {
  document_name: string;
  document_id: string;
  generated_at: string;
  overall_risk: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  categories: ReportCategory[];
  total_cost_usd: number;
  session_total_cost_usd: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  response?: QueryResponse;
  timestamp: Date;
}
