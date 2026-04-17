"use client";

import { ComplianceReport as ReportType } from "@/types";
import { ComplianceStatusBadge } from "./ComplianceStatusBadge";
import { ConfidenceBadge } from "./ConfidenceBadge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Printer, FileText, TrendingUp } from "lucide-react";

interface Props {
  report: ReportType;
}

const riskConfig: Record<string, { label: string; color: string; bg: string }> = {
  LOW: { label: "Low Risk", color: "text-emerald-700", bg: "bg-emerald-50 border-emerald-200" },
  MEDIUM: { label: "Medium Risk", color: "text-amber-700", bg: "bg-amber-50 border-amber-200" },
  HIGH: { label: "High Risk", color: "text-red-700", bg: "bg-red-50 border-red-200" },
  CRITICAL: { label: "Critical Risk", color: "text-red-900", bg: "bg-red-100 border-red-300" },
};

const rowBgMap: Record<string, string> = {
  MEETS: "hover:bg-emerald-50/50",
  PARTIALLY_MEETS: "hover:bg-amber-50/50",
  FAILS: "hover:bg-red-50/50",
  FLAG: "hover:bg-amber-50/50",
  INSUFFICIENT_DATA: "hover:bg-gray-50/50",
};

const statusCounts = (categories: ReportType["categories"]) => ({
  MEETS: categories.filter((c) => c.status === "MEETS").length,
  PARTIAL: categories.filter((c) => c.status === "PARTIALLY_MEETS").length,
  FAILS: categories.filter((c) => c.status === "FAILS").length,
  FLAG: categories.filter((c) => c.status === "FLAG").length,
  INSUFFICIENT: categories.filter((c) => c.status === "INSUFFICIENT_DATA").length,
});

export function ComplianceReport({ report }: Props) {
  const risk = riskConfig[report.overall_risk] ?? riskConfig.MEDIUM;
  const counts = statusCounts(report.categories);

  return (
    <div className="space-y-6 print:space-y-4">
      {/* Document header */}
      <div className="bg-white border border-border rounded-xl shadow-card p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-11 h-11 rounded-lg bg-brand-blue-light flex items-center justify-center flex-shrink-0">
              <FileText className="w-5 h-5 text-brand-blue" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-ink">{report.document_name}</h2>
              <p className="text-sm text-ink-muted mt-0.5">
                Generated {new Date(report.generated_at).toLocaleString()} ·{" "}
                <span className="font-medium">${report.total_cost_usd.toFixed(4)}</span> analysis cost
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 flex-shrink-0">
            <div className={`flex items-center gap-2.5 px-4 py-2 rounded-lg border ${risk.bg}`}>
              <TrendingUp className={`w-4 h-4 ${risk.color}`} />
              <div>
                <p className="text-xs text-ink-muted leading-none mb-0.5">Overall Risk</p>
                <p className={`text-sm font-bold ${risk.color}`}>{risk.label}</p>
              </div>
            </div>
            <button
              onClick={() => window.print()}
              className="flex items-center gap-2 text-sm text-ink-secondary font-medium border border-border rounded-lg px-3.5 py-2 hover:bg-surface-secondary transition-colors"
            >
              <Printer className="w-4 h-4" />
              Export PDF
            </button>
          </div>
        </div>
      </div>

      {/* Summary grid */}
      <div className="grid grid-cols-5 gap-3">
        {[
          { label: "Meets", value: counts.MEETS, color: "text-emerald-700", bg: "bg-emerald-50 border-emerald-200" },
          { label: "Partial", value: counts.PARTIAL, color: "text-amber-700", bg: "bg-amber-50 border-amber-200" },
          { label: "Fails", value: counts.FAILS, color: "text-red-700", bg: "bg-red-50 border-red-200" },
          { label: "Flag", value: counts.FLAG, color: "text-amber-700", bg: "bg-amber-50 border-amber-200" },
          { label: "Insufficient", value: counts.INSUFFICIENT, color: "text-gray-600", bg: "bg-gray-50 border-gray-200" },
        ].map(({ label, value, color, bg }) => (
          <div key={label} className={`rounded-xl border p-4 text-center ${bg} shadow-card`}>
            <p className={`text-2xl font-bold ${color}`}>{value}</p>
            <p className="text-xs text-ink-muted mt-1 font-medium">{label}</p>
          </div>
        ))}
      </div>

      {/* Results table */}
      <div className="bg-white rounded-xl border border-border shadow-card overflow-hidden">
        <div className="px-6 py-4 border-b border-border">
          <h3 className="font-semibold text-ink text-sm">Compliance Findings</h3>
          <p className="text-xs text-ink-muted mt-0.5">{report.categories.length} standards checked across ADA, OSHA, IBC, and ASHRAE</p>
        </div>
        <Table>
          <TableHeader>
            <TableRow className="bg-surface-secondary border-border hover:bg-surface-secondary">
              <TableHead className="text-xs font-semibold text-ink-secondary uppercase tracking-wider w-36">Standard</TableHead>
              <TableHead className="text-xs font-semibold text-ink-secondary uppercase tracking-wider w-24">Section</TableHead>
              <TableHead className="text-xs font-semibold text-ink-secondary uppercase tracking-wider w-28">Status</TableHead>
              <TableHead className="text-xs font-semibold text-ink-secondary uppercase tracking-wider">Finding</TableHead>
              <TableHead className="text-xs font-semibold text-ink-secondary uppercase tracking-wider w-36">Document Ref.</TableHead>
              <TableHead className="text-xs font-semibold text-ink-secondary uppercase tracking-wider w-24">Confidence</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {report.categories.map((cat, i) => (
              <TableRow
                key={i}
                className={`border-border text-sm transition-colors ${rowBgMap[cat.status] ?? ""}`}
              >
                <TableCell className="font-medium text-ink text-xs">{cat.standard}</TableCell>
                <TableCell className="font-mono text-xs text-ink-muted">{cat.section}</TableCell>
                <TableCell>
                  <ComplianceStatusBadge status={cat.status as never} />
                </TableCell>
                <TableCell className="text-xs text-ink-secondary max-w-xs">
                  <p className="line-clamp-3 leading-relaxed">{cat.finding}</p>
                </TableCell>
                <TableCell className="text-xs text-ink-muted">{cat.document_citation}</TableCell>
                <TableCell>
                  <ConfidenceBadge confidence={cat.confidence} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-ink-subtle py-2">
        <span>StructureIQ · Grounded AEC Compliance Intelligence</span>
        <span>Session cost: ${report.session_total_cost_usd.toFixed(4)}</span>
      </div>
    </div>
  );
}
