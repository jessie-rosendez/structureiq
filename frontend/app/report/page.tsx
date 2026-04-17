"use client";

import { useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { generateReport } from "@/lib/api";
import { ComplianceReport as ReportType } from "@/types";
import { ComplianceReport } from "@/components/ComplianceReport";
import { ChevronLeft, BarChart2 } from "lucide-react";

function ReportPageInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const documentId = searchParams.get("doc") ?? "";
  const [report, setReport] = useState<ReportType | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await generateReport(documentId);
      setReport(result);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Report generation failed");
    } finally {
      setLoading(false);
    }
  };

  if (!documentId) {
    router.replace("/");
    return null;
  }

  return (
    <div className="min-h-screen bg-surface-secondary">
      {/* Header */}
      <header className="bg-white border-b border-border">
        <div className="h-14 px-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push(`/query?doc=${documentId}`)}
              className="text-ink-muted hover:text-ink transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <div className="w-6 h-6 bg-brand-blue rounded flex items-center justify-center">
              <span className="text-white text-xs font-bold">SQ</span>
            </div>
            <span className="font-semibold text-ink text-sm">StructureIQ</span>
            <span className="text-border">·</span>
            <span className="text-xs text-ink-muted">Full Compliance Report</span>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {!report && !loading && (
          <div className="bg-white rounded-2xl border border-border shadow-card-lg p-12 text-center max-w-2xl mx-auto">
            <div className="w-14 h-14 bg-brand-blue-light rounded-2xl flex items-center justify-center mx-auto mb-5">
              <BarChart2 className="w-6 h-6 text-brand-blue" />
            </div>
            <h2 className="text-xl font-bold text-ink mb-2">Generate Compliance Report</h2>
            <p className="text-ink-muted text-sm max-w-md mx-auto mb-2">
              Runs 10 targeted compliance queries across ADA, OSHA, IBC, and ASHRAE standards.
            </p>
            <p className="text-ink-subtle text-xs mb-8">
              Estimated time: 60–90 seconds · Estimated cost: $0.03–0.05
            </p>

            {/* Standards list */}
            <div className="grid grid-cols-2 gap-2 mb-8 text-left">
              {[
                "ADA Standards — Accessible routes & facilities",
                "ADA Standards — Restrooms & grab bars",
                "OSHA 1926 — Fall protection systems",
                "OSHA 1926 — Scaffolding requirements",
                "IBC 2021 — Automatic sprinkler systems",
                "IBC 2021 — Stairway construction",
                "IBC 2021 — Means of egress",
                "ASHRAE 90.1 — Wall insulation R-values",
                "ASHRAE 90.1 — Roof insulation R-values",
                "ASHRAE 90.1 — Lighting power density",
              ].map((item) => (
                <div key={item} className="flex items-start gap-2 text-xs text-ink-muted">
                  <span className="text-brand-blue mt-0.5 font-medium">✓</span>
                  {item}
                </div>
              ))}
            </div>

            <button
              onClick={handleGenerate}
              className="bg-brand-blue hover:bg-brand-blue-dark text-white font-semibold rounded-xl px-8 py-3 transition-colors shadow-card-md text-sm"
            >
              Run Full Compliance Analysis
            </button>

            {error && (
              <p className="mt-4 text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg px-4 py-2.5">
                {error}
              </p>
            )}
          </div>
        )}

        {loading && (
          <div className="bg-white rounded-2xl border border-border shadow-card-lg p-12 text-center max-w-lg mx-auto">
            <div className="relative w-14 h-14 mx-auto mb-5">
              <div className="w-14 h-14 rounded-full border-4 border-brand-blue-mid" />
              <div className="absolute inset-0 w-14 h-14 rounded-full border-4 border-t-brand-blue animate-spin" />
            </div>
            <p className="font-semibold text-ink mb-1">Running compliance analysis...</p>
            <p className="text-ink-muted text-sm">
              Querying across ADA, OSHA, IBC, and ASHRAE — this takes 60–90 seconds
            </p>
            <div className="mt-6 grid grid-cols-4 gap-2">
              {["ADA", "OSHA", "IBC", "ASHRAE"].map((s) => (
                <div key={s} className="text-center">
                  <div className="h-1.5 bg-brand-blue-mid rounded-full overflow-hidden">
                    <div className="h-full bg-brand-blue rounded-full animate-pulse w-2/3" />
                  </div>
                  <p className="text-xs text-ink-muted mt-1.5">{s}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {report && <ComplianceReport report={report} />}
      </div>

      {/* Footer */}
      <footer className="border-t border-border bg-white mt-8">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between text-xs text-ink-subtle">
          <span>StructureIQ · Internal Compliance Tool</span>
          <span>GCP Project: structureiq · Vertex AI · Gemini 2.0 Flash</span>
        </div>
      </footer>
    </div>
  );
}

export default function ReportPage() {
  return (
    <Suspense>
      <ReportPageInner />
    </Suspense>
  );
}
