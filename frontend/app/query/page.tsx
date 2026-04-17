"use client";

import { useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { ChatInterface } from "@/components/ChatInterface";
import { SourcePanel } from "@/components/SourcePanel";
import { QueryResponse } from "@/types";
import { BarChart2, ChevronLeft, FileText } from "lucide-react";

function QueryPageInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const documentId = searchParams.get("doc") ?? "";
  const [lastResponse, setLastResponse] = useState<QueryResponse | null>(null);

  if (!documentId) {
    router.replace("/");
    return null;
  }

  return (
    <div className="h-screen flex flex-col bg-surface-secondary">
      {/* Header */}
      <header className="bg-white border-b border-border flex-shrink-0">
        <div className="h-14 px-5 flex items-center justify-between gap-4">
          {/* Left */}
          <div className="flex items-center gap-3 min-w-0">
            <button
              onClick={() => router.push("/")}
              className="text-ink-muted hover:text-ink transition-colors flex-shrink-0"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <div className="w-6 h-6 bg-brand-blue rounded flex items-center justify-center flex-shrink-0">
              <span className="text-white text-xs font-bold">SQ</span>
            </div>
            <span className="font-semibold text-ink text-sm">StructureIQ</span>
            <span className="text-border hidden sm:block">·</span>
            <div className="hidden sm:flex items-center gap-1.5 text-xs text-ink-muted min-w-0">
              <FileText className="w-3.5 h-3.5 flex-shrink-0" />
              <span className="font-mono truncate">{documentId.slice(0, 8)}...</span>
            </div>
          </div>

          {/* Right */}
          <button
            onClick={() => router.push(`/report?doc=${documentId}`)}
            className="flex items-center gap-2 text-sm font-medium text-white bg-brand-blue hover:bg-brand-blue-dark rounded-lg px-4 py-2 transition-colors shadow-card flex-shrink-0"
          >
            <BarChart2 className="w-4 h-4" />
            Generate Report
          </button>
        </div>
      </header>

      {/* Two-panel layout */}
      <div className="flex-1 flex overflow-hidden min-h-0">
        {/* Left — Chat */}
        <div className="flex-1 min-w-0 flex flex-col bg-white border-r border-border">
          <div className="px-6 py-3 border-b border-border bg-surface-secondary flex-shrink-0">
            <h2 className="text-xs font-semibold text-ink-secondary uppercase tracking-wider">
              Compliance Query
            </h2>
          </div>
          <div className="flex-1 min-h-0 flex flex-col">
            <ChatInterface documentId={documentId} onNewResponse={setLastResponse} />
          </div>
        </div>

        {/* Right — Source inspector */}
        <div className="w-72 flex-shrink-0 flex flex-col bg-white overflow-hidden">
          <div className="px-4 py-3 border-b border-border bg-surface-secondary flex-shrink-0">
            <h2 className="text-xs font-semibold text-ink-secondary uppercase tracking-wider">
              Source Inspector
            </h2>
          </div>
          <div className="flex-1 overflow-y-auto">
            <SourcePanel response={lastResponse} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default function QueryPage() {
  return (
    <Suspense>
      <QueryPageInner />
    </Suspense>
  );
}
