"use client";

import { QueryResponse } from "@/types";
import { CostTracker } from "./CostTracker";
import { FileText, BookOpen, AlertTriangle } from "lucide-react";

interface Props {
  response: QueryResponse | null;
}

export function SourcePanel({ response }: Props) {
  if (!response) {
    return (
      <div className="h-full flex flex-col items-center justify-center py-12 px-4 text-center">
        <BookOpen className="w-8 h-8 text-gray-300 mb-3" />
        <p className="text-sm text-ink-muted font-medium">Source Inspector</p>
        <p className="text-xs text-ink-subtle mt-1">
          Sources appear here after your first query.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-5 text-sm p-4">
      {/* Layer 1 */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <FileText className="w-3.5 h-3.5 text-brand-blue" />
          <span className="text-xs font-semibold text-ink-secondary uppercase tracking-wider">
            Layer 1 — Document
          </span>
        </div>
        <div className="rounded-lg border border-border bg-white p-3 shadow-card">
          <p className="text-xs text-ink-muted mb-2">
            <span className="font-semibold text-brand-blue text-sm">
              {response.layer_sources.document_chunks_used}
            </span>{" "}
            chunks retrieved
          </p>
          {response.document_citations.length > 0 ? (
            <ul className="space-y-1">
              {response.document_citations.map((c, i) => (
                <li key={i} className="flex items-start gap-1.5 text-xs text-ink-secondary">
                  <span className="text-brand-blue mt-0.5">›</span>
                  {c}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-ink-subtle italic">No page citations returned.</p>
          )}
        </div>
      </div>

      {/* Layer 2 */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <BookOpen className="w-3.5 h-3.5 text-brand-blue" />
          <span className="text-xs font-semibold text-ink-secondary uppercase tracking-wider">
            Layer 2 — Standards KB
          </span>
        </div>
        <div className="rounded-lg border border-border bg-white p-3 shadow-card">
          <p className="text-xs text-ink-muted mb-2">
            <span className="font-semibold text-brand-blue text-sm">
              {response.layer_sources.standards_chunks_used}
            </span>{" "}
            standards retrieved
          </p>
          {response.standard_citations.length > 0 ? (
            <ul className="space-y-1">
              {response.standard_citations.map((c, i) => (
                <li key={i} className="flex items-start gap-1.5 text-xs text-ink-secondary">
                  <span className="text-brand-blue mt-0.5">›</span>
                  {c}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-ink-subtle italic">No standard sections cited.</p>
          )}
        </div>
      </div>

      {/* Gaps */}
      {response.gaps.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
            <span className="text-xs font-semibold text-ink-secondary uppercase tracking-wider">
              Information Gaps
            </span>
          </div>
          <ul className="space-y-1.5">
            {response.gaps.map((g, i) => (
              <li
                key={i}
                className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded px-2.5 py-1.5"
              >
                {g}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Cost */}
      <CostTracker
        callCost={response.cost_usd}
        sessionTotal={response.session_total_cost_usd}
        inputTokens={response.tokens_used.input}
        outputTokens={response.tokens_used.output}
      />
    </div>
  );
}
